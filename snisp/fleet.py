import functools
import itertools
import logging

from datetime import datetime, timezone

from snisp import exceptions, utils, systems
from snisp.contracts import Contract
from snisp.decorators import cooldown, docked, in_orbit, retry, transit
from snisp.markets import Markets
from snisp.shipyards import Shipyards
from snisp.systems import System
from snisp.waypoints import Waypoints


logger = logging.getLogger(__name__)


class Fleet:

    def __init__(self, agent):
        self.agent = agent

    def __repr__(self):
        return f'{self.__class__.__name__}({self.agent!r})'

    @retry()
    def __call__(self, ship_symbol):
        # Equivalent to ship.refresh()
        ship_symbol = ship_symbol.upper()
        response = self.agent.client.get(f'/my/ships/{ship_symbol}')
        return Ship(self.agent, response.json()['data'])

    def __iter__(self):
        page = 1
        response = self.get_page(page=page)
        while data := response.json()['data']:
            for ship in data:
                if ship['symbol'] not in self.agent.dead_ships:
                    yield Ship(self.agent, ship)
            page += 1
            response = self.get_page(page=page)

    @retry()
    def get_page(self, page=1, limit=20):
        params = {'limit': int(limit), 'page': int(page)}
        return self.agent.client.get('/my/ships', params=params)

    def drones(self):
        for ship in self:
            if ship.frame.symbol == 'FRAME_DRONE':
                yield ship

    def freighters(self):
        for ship in self:
            if 'FREIGHTER' in ship.frame.symbol:
                yield ship

    def mining_drones(self):
        for drone in self.drones():
            for mount in drone.mounts:
                if mount.symbol.upper().startswith('MOUNT_MINING_LASER_'):
                    yield drone

    def siphon_drones(self):
        for drone in self.drones():
            for mount in drone.mounts:
                if mount.symbol.upper().startswith('MOUNT_GAS_SIPHON_'):
                    yield drone

    def probes(self):
        for ship in self:
            if ship.frame.symbol == 'FRAME_PROBE':
                yield ship

    def ships(self):
        for ship in self:
            if 'DRONE' not in ship.frame.symbol:
                if 'PROBE' not in ship.frame.symbol:
                    yield ship

    def shuttles(self):
        for ship in self:
            if 'SHUTTLE' in ship.frame.symbol:
                yield ship


class Ship(utils.AbstractJSONItem):

    def __init__(self, agent, ship_data):
        self.agent = agent
        self._data = ship_data

    @property
    def arrival(self):
        if self.nav.status == 'IN_TRANSIT':
            arrival = datetime.fromisoformat(self.nav.route.arrival)
            delta = arrival - datetime.now(timezone.utc)
            return delta.seconds if delta.days >= 0 else 0
        return 0

    @property
    def location(self):
        return systems.Location(self.agent, self.to_dict())

    @property
    def waypoints(self):
        waypoints = Waypoints(self.agent, self.location)
        waypoints.chart = functools.partial(waypoints.chart, self)
        waypoints.scan = functools.partial(waypoints.scan, self)
        waypoints.survey = functools.partial(waypoints.survey, self)
        return waypoints

    @property
    def markets(self):
        return Markets(self, self.location)

    @property
    def shipyards(self):
        return Shipyards(self, self.location)

    @property
    def system(self):
        _system = System(self.agent)
        _system.scan = functools.partial(_system.scan, self)
        return _system

    @property
    def at_market(self):
        if self.nav.status != 'IN_TRANSIT':
            waypoint = self.waypoints.get()
            return any(
                i.symbol.upper() == 'MARKETPLACE' for i in waypoint.traits
            )
        return False

    @property
    def at_shipyard(self):
        if self.nav.status != 'IN_TRANSIT':
            waypoint = self.waypoints.get()
            return any(
                i.symbol.upper() == 'SHIPYARD' for i in waypoint.traits
            )
        return False

    @property
    def can_mine(self):
        for mount in self.mounts:
            if mount.symbol.upper().startswith('MOUNT_MINING_LASER_'):
                return True
        return False

    @property
    def can_refine_gas(self):
        for module in self.modules:
            if module.symbol.upper().startswith('MODULE_GAS_PROCESSOR_'):
                return True
        return False

    @property
    def can_refine_ore(self):
        for module in self.modules:
            if module.symbol.upper().startswith('MODULE_MINERAL_PROCESSOR_'):
                return True
        return False

    @property
    def can_siphon(self):
        for mount in self.mounts:
            if mount.symbol.upper().startswith('MOUNT_GAS_SIPHON_'):
                return True
        return False

    @property
    def can_survey(self):
        for mount in self.mounts:
            if mount.symbol.upper().startswith('MOUNT_SURVEYOR_'):
                return True
        return False

    def arrived_at_destination(self):
        current_nav = self.nav.to_dict()
        current_nav['status'] = 'IN_ORBIT'
        self.update_data_item('nav', current_nav)

    def closest(self, *iterables):
        try:
            return min(
                (i for i in itertools.chain(*iterables)), key=self.distance
            )
        except ValueError:
            return

    def farthest(self, *iterables):
        try:
            return max(
                (i for i in itertools.chain(*iterables)), key=self.distance
            )
        except ValueError:
            return

    def distance(self, destination):
        return utils.calculate_distance(self, destination)

    def closest_fuel(self):
        return self.closest(self.markets.fuel_stations())

    @retry()
    @transit
    def dock(self):
        if self.nav.status != 'DOCKED':
            response = self.agent.client.post(
                f'/my/ships/{self.symbol}/dock'
            )
            data = response.json()['data']
            self.update_data_item('nav', data['nav'])
            logger.info(
                f'{self.registration.role}: {self.symbol} | '
                f'Docked at {self.nav.waypoint_symbol}'
            )
            return data

    @retry()
    @transit
    @cooldown
    @in_orbit
    def extract(self):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/extract'
        )
        data = response.json()['data']
        self.update_data_item('cargo', data['cargo'])
        self.update_data_item('cooldown', data['cooldown'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | Extracted '
            f'{data["extraction"]["yield"]["units"]:,} units of '
            f'{data["extraction"]["yield"]["symbol"]}'
        )
        return Extraction(self.agent, data['extraction']['yield'])

    @retry()
    @transit
    @cooldown
    @in_orbit
    def extract_with_survey(self, survey):
        try:
            survey = survey.to_dict()
        except AttributeError:
            raise exceptions.ShipSurveyVerificationError(
                'extract_with_survey requires a Survey. '
                f'Received {type(survey)} instead'
            )
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/extract/survey', json=survey
        )
        data = response.json()['data']
        self.update_data_item('cargo', data['cargo'])
        self.update_data_item('cooldown', data['cooldown'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | Extracted '
            f'{data["extraction"]["yield"]["units"]:,} units of '
            f'{data["extraction"]["yield"]["symbol"]}'
        )
        return ExtractionWithSurvey(self.agent, data['extraction']['yield'])

    @retry()
    @transit
    @docked
    def install_mount(self, mount_symbol):
        mount_symbol = mount_symbol.upper()
        if mount_symbol not in utils.SHIP_MOUNTS:
            raise exceptions.SpaceAttributeError(
                f'{mount_symbol} is not an acceptable mount type. '
                'See snisp.utils.SHIP_MOUNTS for acceptable mounts.'
            )
        with self.agent.lock:
            response = self.agent.client.post(
                f'/my/ships/{self.symbol}/mounts/install',
                json={'symbol': mount_symbol}
            )
            data = response.json()['data']
            self.update_data_item('cargo', data['cargo'])
            self.update_data_item('mounts', data['mounts'])
            logger.info(
                f'{self.registration.role}: {self.symbol} | '
                f'Installed mount {data["transaction"]["tradeSymbol"]} '
                f'for ${data["transaction"]["totalPrice"]:,.2f}'
            )
            transaction = Transaction(self.agent, data['transaction'])
            self.agent.recent_transactions.appendleft(transaction)
            return Mounts(self.agent, data['mounts'])

    @retry()
    def jettison(self, symbol, units=1):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/jettison',
            json={'symbol': symbol, 'units': units}
        )
        data = response.json()['data']
        self.update_data_item('cargo', data['cargo'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            f'Jettisoning {units:,} of {symbol}'
        )
        return data

    @retry()
    @transit
    @cooldown
    @in_orbit
    def jump(self, waypoint):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/jump',
            json={'waypointSymbol': waypoint.symbol}
        )
        data = response.json()['data']
        self.update_data_item('nav', data['nav'])
        self.update_data_item('cooldown', data['cooldown'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            f'Jumped to {waypoint.symbol} via '
            f'Will reach destination in {self.arrival / 60:.1f} minutes'
        )
        return data

    def autopilot(
        self,
        waypoint,
        flight_mode='CRUISE',
        done_callback=None,
    ):
        # A complete mess
        if self.nav.waypoint_symbol == waypoint.symbol:
            return
        current_nav = self.nav.to_dict()
        current_nav['status'] = 'IN_TRANSIT'
        self.update_data_item('nav', current_nav)
        self.update_flight_mode(flight_mode)
        self.refuel(ignore_errors=True)
        self.orbit()

        # Can make it to the dest as is. No need to do anything else
        if not self.navigate(waypoint, raise_error=False):
            self.refuel(ignore_errors=True)
            self.orbit()
            if callable(done_callback):
                done_callback()
            return

        closest_fuel_to_wp = sorted(
            self.markets.fuel_stations(),
            key=lambda x: utils.calculate_waypoint_distance(waypoint, x)
        )
        last_successful_fueling = len(closest_fuel_to_wp) + 1
        while self.navigate(waypoint, raise_error=False):
            fuel_index = 0
            next_fuel = closest_fuel_to_wp[fuel_index]
            if self.nav.waypoint_symbol == next_fuel.symbol:
                self.refuel(ignore_errors=True)
                if self.nav.flight_mode == 'DRIFT':
                    with self.agent.lock:
                        self.agent.dead_ships[self.symbol] = self
                    raise exceptions.NavigateInsufficientFuelError(
                        r'¯\_(ツ)_/¯'
                    )
                logger.info(
                    f'{self.registration.role}: {self.symbol} | '
                    'Already at closest fuel '
                    f'but cannot make it to {waypoint.symbol} at '
                    f'{self.nav.flight_mode}. Will now DRIFT.'
                )
                self.update_flight_mode('DRIFT')
                continue
            while self.navigate(next_fuel, raise_error=False):
                fuel_index += 1
                if fuel_index >= last_successful_fueling:
                    # There's a blackhole where the ship could
                    # get to the closest fueling station to the waypoint
                    # but not make it to the waypoint from there.
                    # It would just continually cycle fuel stations if
                    # the flight_mode was not switched to drift.
                    # If it's *already* as DRIFT at this piont, well, :/
                    if self.nav.flight_mode == 'DRIFT':
                        if err := self.navigate(waypoint, raise_error=False):
                            try:
                                logger.warning(err.data)
                            except Exception as e:
                                logger.warning(e)
                            with self.agent.lock:
                                self.agent.dead_ships[self.symbol] = self
                            raise exceptions.NavigateInsufficientFuelError(
                                'Waypoint too far away. SOL'
                            )
                        else:
                            self.orbit()
                            if callable(done_callback):
                                done_callback()
                            return
                    else:
                        logger.info(
                            f'{self.registration.role}: {self.symbol} | '
                            'At last successful fuel stop.  Will now DRIFT.'
                        )
                        self.update_flight_mode('DRIFT')
                        break
                try:
                    next_fuel = closest_fuel_to_wp[fuel_index]
                    logger.info(
                        f'{self.registration.role}: {self.symbol} | '
                        f'Trying next FUEL_STATION: {next_fuel.symbol} | '
                        f'{fuel_index}/{len(closest_fuel_to_wp)}'
                    )
                except IndexError:
                    if self.nav.flight_mode == 'DRIFT':
                        if err := self.navigate(waypoint, raise_error=False):
                            try:
                                logger.warning(err.data)
                            except Exception as e:
                                logger.warning(e)
                            with self.agent.lock:
                                self.agent.dead_ships[self.symbol] = self
                            raise exceptions.NavigateInsufficientFuelError(
                                'No close fuel. SOL, buddy'
                            )
                        else:
                            self.orbit()
                            if callable(done_callback):
                                done_callback()
                            return
                    if (self.fuel.current + 5) >= self.fuel.capacity:
                        # Can't make it to the WP or any close fuel
                        # Weird situation where it'll make the drift
                        # to the closest_fuel_to_wp but also the farthest...
                        self.update_flight_mode('DRIFT')
                    else:
                        # May have started with less than a full fuel tank
                        logger.warning(
                            f'{self.registration.role}: {self.symbol} | '
                            'No CRUISABLE fuel stations. Now drifting.'
                        )
                        self.update_flight_mode('DRIFT')
                        closest_drift_fuel = self.closest_fuel()
                        if err := self.navigate(
                            closest_drift_fuel, raise_error=False
                        ):
                            try:
                                logger.warning(err.data)
                            except Exception as e:
                                logger.warning(e)
                            with self.agent.lock:
                                self.agent.dead_ships[self.symbol] = self
                            raise exceptions.NavigateInsufficientFuelError(
                                'No close fuel. ya burnt'
                            )
                        self.refuel()
                        self.update_flight_mode('CRUISE')
                    break
            else:
                last_successful_fueling = fuel_index
            self.refuel(ignore_errors=True)
        self.refuel(ignore_errors=True)
        self.orbit()
        if callable(done_callback):
            done_callback()

    @retry()
    @transit
    @in_orbit
    def navigate(self, waypoint, raise_error=True):
        if self.nav.waypoint_symbol == waypoint.symbol:
            return
        try:
            response = self.agent.client.post(
                f'/my/ships/{self.symbol}/navigate',
                json={'waypointSymbol': waypoint.symbol}
            )
        except Exception as e:
            if raise_error:
                raise e
            else:
                return e
        data = response.json()['data']
        self.update_data_item('fuel', data['fuel'])
        self.update_data_item('nav', data['nav'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            f'Navigating to {waypoint.symbol} via '
            f'{self.nav.flight_mode}. Will reach destination in '
            f'{self.arrival / 60:.1f} minutes'
        )

    @retry()
    @transit
    @docked
    def negotiate_contract(self):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/negotiate/contract'
        )
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            'Negotiated new contract'
        )
        return Contract(self.agent, response.json()['data']['contract'])

    @retry()
    def updated_mounts(self):
        """NOTE: This function is mostly a placedholder to ensure
        the endpoint has been addressed. You can use the `Ship.mounts`
        attribute instead, in most cases."""
        response = self.agent.client.get(
            f'/my/ships/{self.symbol}/mounts'
        )
        return Mounts(self.agent, response.json()['data'])

    @retry()
    @transit
    def orbit(self):
        if self.nav.status != 'IN_ORBIT':
            response = self.agent.client.post(
                f'/my/ships/{self.symbol}/orbit'
            )
            data = response.json()['data']
            self.update_data_item('nav', data['nav'])
            logger.info(
                f'{self.registration.role}: {self.symbol} | Moved to orbit'
            )
            return data

    @transit
    def autopurchase(self, goods, max_units=0, buffer=200_000):
        goods = goods.upper()
        if goods not in utils.GOODS_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{goods} is not an acceptable goods type. '
                'See snisp.utils.GOODS_TYPES for acceptable goods.'
            )
        max_units = int(max_units)
        if max_units <= 0:
            max_units = self.cargo.capacity
        transactions = []
        market_data = self.markets()
        if not market_data:
            logger.warning(
                f'{self.registration.role}: {self.symbol} | '
                f'No market at {self.location.waypoint} '
                f'Cannot purchase {max_units:,} of {goods}.'
            )
            return transactions
        trade_volume = None
        for t_good in market_data.trade_goods:
            if t_good.symbol == goods:
                if t_good.type == 'EXPORT' or t_good.type == 'EXCHANGE':
                    trade_volume = t_good.trade_volume
                    break
        if trade_volume is None:
            logger.warning(
                f'Market {self.location.waypoint} no longer trading {goods}'
            )
            return transactions
        with self.agent.lock:
            while max_units > 0:
                unit_price = None
                for t_good in self.markets().trade_goods:
                    if t_good.symbol == goods:
                        if t_good.type == 'EXPORT' or t_good.type == 'EXCHANGE':  # noqa: E501
                            unit_price = t_good.purchase_price
                            break
                if unit_price is None:
                    logger.warning(
                        f'Market {self.location.waypoint} no longer '
                        f'trading {goods}'
                    )
                    return transactions
                buy_units = max_units
                if buy_units > trade_volume:
                    buy_units = trade_volume
                buy_units = min(
                    buy_units,
                    self.cargo.capacity - self.cargo.units
                )
                if buy_units <= 0:
                    return transactions
                purchase_amount = buy_units * unit_price
                while purchase_amount > self.agent.data.credits - buffer:
                    buy_units -= 1
                    if buy_units == 0:
                        return transactions
                    purchase_amount = buy_units * unit_price
                transactions.append(self.purchase(goods, buy_units))
                max_units -= buy_units
        return transactions

    @retry()
    @transit
    @docked
    def purchase(self, goods, units):
        goods = goods.upper()
        if goods not in utils.GOODS_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{goods} is not an acceptable goods type. '
                'See snisp.utils.GOODS_TYPES for acceptable goods.'
            )
        with self.agent.lock:
            payload = {'symbol': goods, 'units': int(units)}
            response = self.agent.client.post(
                f'/my/ships/{self.symbol}/purchase', json=payload
            )
            data = response.json()['data']
            self.update_data_item('cargo', data['cargo'])
            logger.info(
                f'{self.registration.role}: {self.symbol} | Purchased '
                f'{data["transaction"]["units"]:,}'
                f' units of {data["transaction"]["tradeSymbol"]} for '
                f'${data["transaction"]["totalPrice"]:,.2f}'
            )
            transaction = Transaction(self.agent, data['transaction'])
            self.agent.recent_transactions.appendleft(transaction)
            return transaction

    @retry()
    @transit
    @docked
    def refuel(self, *, units=0, from_cargo=False, ignore_errors=False):
        if self.fuel.capacity == self.fuel.current:
            return
        payload = {'fromCargo': from_cargo}
        if (units := int(units)) >= 1:
            payload['units'] = units
        with self.agent.lock:
            try:
                response = self.agent.client.post(
                    f'/my/ships/{self.symbol}/refuel', json=payload
                )
            except Exception as e:
                if ignore_errors:
                    logger.warning(
                        f'{self.registration.role}: {self.symbol} | '
                        f'Failed to refuel at {self.location.waypoint}.'
                    )
                    return
                raise e
            data = response.json()['data']
            self.update_data_item('fuel', data['fuel'])
            if from_cargo:
                cargo = self.to_dict()['cargo']
                units = data['transaction']['units']
                for index, item in enumerate(cargo['inventory']):
                    if item['symbol'].upper() == 'FUEL':
                        item['units'] -= units
                        if item['units'] == 0:
                            del cargo['inventory'][index]
                self.update_data_item('cargo', cargo)
            logger.info(
                f'{self.registration.role}: {self.symbol} | Refueled '
                f'{data["transaction"]["units"]:,} '
                f'units at {data["transaction"]["waypointSymbol"]} for '
                f'${data["transaction"]["totalPrice"]:,.2f}'
            )
            return Transaction(self.agent, data['transaction'])

    @retry()
    @cooldown
    def refine(self, produce):
        if produce not in utils.REFINABLE_SYMBOLS:
            raise exceptions.ShipInvalidRefineryGoodError(
                f'{produce} is not an acceptable produce. '
                'See snisp.utils.REFINABLE_SYMBOLS for acceptable produces.'
            )
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/refine', json={'produce': produce}
        )
        data = response.json()['data']
        self.update_data_item('cargo', data['cargo'])
        self.update_data_item('cooldown', data['cooldown'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | Refined '
            f'{data["produced"][0]["units"]:,} units of'
            f'{data["produced"][0]["tradeSymbol"]}'
        )
        return data

    @retry()
    def refresh(self):
        """Returns a new Ship class object of the current ship"""
        response = self.agent.client.get(f'/my/ships/{self.symbol}')
        return Ship(self.agent, response.json()['data'])

    @retry()
    @transit
    @docked
    def remove_mount(self, mount_symbol):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/mounts/remove',
            json={'symbol': mount_symbol}
        )
        data = response.json()['data']
        self.update_data_item('cargo', data['cargo'])
        self.update_data_item('mounts', data['mounts'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            'Removed mount {mount_symbol}'
        )
        return data

    @retry()
    @transit
    @in_orbit
    @cooldown
    def scan(self):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/scan/ships'
        )
        data = response.json()['data']
        self.update_data_item('cooldown', data['cooldown'])
        for ship in data['ships']:
            yield Ship(self.agent, ship)

    @transit
    def sell_all(self, good, units=0):
        transactions = []
        units = int(units)
        if units <= 0:
            units = next(
                (
                    i.units for i in self.cargo.inventory if i.symbol == good
                ), None
            )
            if units is None:
                logger.warning(
                    f'{self.registration.role}: {self.symbol} | '
                    'Attempting to sell {good} which '
                    'is not currently in its cargo hold'
                )
                return transactions
        market_data = self.markets()
        if not market_data:
            logger.warning(
                f'{self.registration.role}: {self.symbol} | '
                f'No market at {self.location.waypoint}. '
                f'Cannot sell {units:,} of {good}.'
            )
            return transactions
        trade_volume = next(
            (
                i.trade_volume
                for i in market_data.trade_goods
                if i.type == 'IMPORT'
                if i.symbol == good
            ), None
        )
        if trade_volume is None:
            logger.warning(
                f'Market {market_data.symbol} no longer trading {good}'
            )
            return transactions
        while units:
            sell_units = units
            if units > trade_volume:
                units -= trade_volume
                sell_units = trade_volume
            else:
                units = 0
            transactions.append(self.sell(good, sell_units))
        self.agent.recent_transactions.extendleft(transactions)
        return transactions

    def sell_off_cargo(self, trade_symbol=None):
        # Just sell to the closest and move on
        # The best will probably be the dest anyways
        transactions = []
        for item in self.cargo.inventory:
            if trade_symbol and item.symbol != trade_symbol:
                continue
            markets = (i for i in self.markets.imports(item.symbol))
            if market := self.closest(markets):
                self.autopilot(market)
                last_transactions = self.sell_all(item.symbol, item.units)
                if not last_transactions:
                    self.jettison(item.symbol, item.units)
                else:
                    transactions.extend(last_transactions)
            else:
                logger.info(
                    f'{self.registration.role}: {self.symbol} | '
                    f'No market buys {item.symbol}'
                )
                self.jettison(item.symbol, item.units)
        return transactions

    @retry()
    @transit
    @docked
    def sell(self, goods, units):
        goods = goods.upper()
        if goods not in utils.GOODS_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{goods} is not an acceptable goods type. '
                'See snisp.utils.GOODS_TYPES for acceptable goods.'
            )
        payload = {'symbol': goods, 'units': int(units)}
        with self.agent.lock:
            response = self.agent.client.post(
                f'/my/ships/{self.symbol}/sell', json=payload
            )
            data = response.json()['data']
            self.update_data_item('cargo', data['cargo'])
            logger.info(
                f'{self.registration.role}: {self.symbol} | '
                f'Sold {data["transaction"]["units"]:,} '
                f'units of {data["transaction"]["tradeSymbol"]} for '
                f'${data["transaction"]["totalPrice"]:,.2f}'
            )
            transaction = Transaction(self.agent, data['transaction'])
            self.agent.recent_transactions.appendleft(transaction)
            return transaction

    @retry()
    @transit
    @cooldown
    @in_orbit
    def siphon(self):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/siphon'
        )
        data = response.json()['data']
        self.update_data_item('cargo', data['cargo'])
        self.update_data_item('cooldown', data['cooldown'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | Siphoned '
            f'{data["siphon"]["yield"]["units"]:,} units of '
            f'{data["siphon"]["yield"]["symbol"]}'
        )
        return Siphon(self.agent, data['siphon']['yield'])

    @retry()
    @transit
    def transfer(self, receive_ship, *, symbol, units):
        symbol = symbol.upper()
        if symbol not in utils.GOODS_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{symbol} is not an acceptable goods type. '
                'See snisp.utils.GOODS_TYPES for acceptable goods.'
            )
        units = int(units)
        payload = {
            'tradeSymbol': symbol,
            'units': units,
            'shipSymbol': receive_ship.symbol,
        }
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/transfer', json=payload
        )
        # NOTE: The response body's cargo shows the cargo of the
        #       transferring ship after the transfer is complete.
        data = response.json()['data']
        self.update_data_item('cargo', data['cargo'])
        new_cargo = receive_ship.cargo.to_dict()
        if not new_cargo.get('inventory'):
            # Placeholder name and description
            new_cargo['inventory'] = [
                {
                    'symbol': symbol,
                    'units': units,
                    'name': symbol,
                    'description': symbol,
                }
            ]
        else:
            if exists := next(
                (
                    i for i in new_cargo['inventory']
                    if i['symbol'] == symbol
                ), None
            ):
                exists['units'] += units
                new_cargo['units'] += units
            else:
                new_cargo['inventory'].append(
                    {
                        'symbol': symbol,
                        'units': units,
                        'name': symbol,
                        'description': symbol,
                    }
                )
                new_cargo['units'] += units
        receive_ship.update_data_item('cargo', new_cargo)
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            f'Transferred {units:,} of {symbol} '
            f'to {receive_ship.symbol}'
        )
        return data

    @retry()
    @transit
    @in_orbit
    def warp(self, waypoint):
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/warp',
            json={'waypointSymbol': waypoint.symbol}
        )
        data = response.json()['data']
        self.update_data_item('nav', data['nav'])
        self.update_data_item('fuel', data['fuel'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            f'Warping to {waypoint.symbol} '
            f'Will reach destination in {self.arrival / 60:.1f} minutes'
        )
        return data

    @retry()
    @transit
    def update_flight_mode(self, mode):
        mode = mode.strip().upper()
        if mode not in utils.FLIGHT_MODES:
            raise exceptions.SpaceAttributeError(
                f'{mode} is not an acceptable flight mode type. '
                'See snisp.utils.FLIGHT_MODES for acceptable flight modes.'
            )
        if self.nav.flight_mode != mode:
            prev_mode = self.nav.flight_mode
            response = self.agent.client.patch(
                f'/my/ships/{self.symbol}/nav', json={'flightMode': mode}
            )
            data = response.json()['data']
            self.update_data_item('nav', data)
            logger.info(
                f'{self.registration.role}: {self.symbol} | '
                f'Changing FLIGHT_MODE from {prev_mode} to {mode}'
            )
            return data


class Extraction(utils.AbstractJSONItem):

    def __init__(self, agent, extraction):
        self.agent = agent
        self._data = extraction


class ExtractionWithSurvey(utils.AbstractJSONItem):

    def __init__(self, agent, extraction):
        self.agent = agent
        self._data = extraction


class Siphon(utils.AbstractJSONItem):

    def __init__(self, agent, siphon):
        self.agent = agent
        self._data = siphon


class Mounts(utils.AbstractJSONItem):

    def __init__(self, agent, mount):
        self.agent = agent
        self._data = mount


class Transaction(utils.AbstractJSONItem):

    def __init__(self, agent, transaction):
        self.agent = agent
        self._data = transaction
