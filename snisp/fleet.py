import dateutil
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

    """Fleet is the top-level class for accessing Ships"""

    def __init__(self, agent):
        self.agent = agent

    def __repr__(self):
        return f'{self.__class__.__name__}({self.agent!r})'

    @retry()
    def __call__(self, ship_symbol):
        """
        Retrieves a Ship instance

        Args:
            ship_symbol: The symbol for the ship to retrieve

        Returns:
            Ship
        """
        ship_symbol = ship_symbol.upper()
        response = self.agent.client.get(f'/my/ships/{ship_symbol}')
        return Ship(self.agent, response.json()['data'])

    def __iter__(self):
        """
        Iterates over the current Agent's Fleet

        Yields:
            Ship
        """
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
        """Yields Ships where ship.frame.symbol == 'FRAME_DRONE'"""
        for ship in self:
            if ship.frame.symbol == 'FRAME_DRONE':
                yield ship

    def freighters(self):
        """Yields Ships where 'FREIGHTER' in ship.frame.symbol"""
        for ship in self:
            if 'FREIGHTER' in ship.frame.symbol:
                yield ship

    def mining_drones(self):
        """Yields Ships that are Drones and have a Mining Laser Mount"""
        for drone in self.drones():
            for mount in drone.mounts:
                if mount.symbol.upper().startswith('MOUNT_MINING_LASER_'):
                    yield drone
                    break

    def siphon_drones(self):
        """Yields Ships that are Drones and have a Gas Siphon MountShip"""
        for drone in self.drones():
            for mount in drone.mounts:
                if mount.symbol.upper().startswith('MOUNT_GAS_SIPHON_'):
                    yield drone
                    break

    def probes(self):
        """Yields Ships where ship.frame.symbol == 'FRAME_PROBE'"""
        for ship in self:
            if ship.frame.symbol == 'FRAME_PROBE':
                yield ship

    def ships(self):
        """Yields Ships that are neither Drone nor Probes"""
        for ship in self:
            if 'DRONE' not in ship.frame.symbol:
                if 'PROBE' not in ship.frame.symbol:
                    yield ship

    def shuttles(self):
        """Yields Ships where 'SHUTTLE' in ship.frame.symbol"""
        for ship in self:
            if 'SHUTTLE' in ship.frame.symbol:
                yield ship


class Ship(utils.AbstractJSONItem):

    """A Ship can be a Drone, Probe, Freighter, etc."""

    def __init__(self, agent, ship_data):
        self.agent = agent
        self._data = ship_data

    @property
    def arrival(self):
        """
        Property that returns the number of seconds until the Ship reaches
        the destination

        Blocks:
            False

        Returns:
            int: sceond to arrival if ship is IN_TRANSIT; else, 0
        """
        if self.nav.status == 'IN_TRANSIT':
            arrival = dateutil.parser.parse(self.nav.route.arrival)
            delta = arrival - datetime.now(timezone.utc)
            return delta.seconds if delta.days >= 0 else 0
        return 0

    @property
    def location(self):
        """Property for the Ship's current Location

        Blocks:
            False

        Returns:
            snisp.system.Location: Ship's current Location
        """
        return systems.Location(self.agent, self.to_dict())

    @property
    def waypoints(self):
        """
        Property that returns the snisp.waypoints.Waypoints
        for the Ship's current System

        .chart, .scan, and .survey are monkey-patched to have the
        ship already loaded as the first argument

        Blocks:
            False

        Returns:
            snisp.waypoints.Waypoints: Waypoints for the Ship's Location
        """
        waypoints = Waypoints(self.agent, self.location)
        waypoints.chart = functools.partial(waypoints.chart, self)
        waypoints.scan = functools.partial(waypoints.scan, self)
        waypoints.survey = functools.partial(waypoints.survey, self)
        return waypoints

    @property
    def markets(self):
        """
        Property that returns the snisp.markets.Markets
        for the Ship's current System

        Blocks:
            False

        Returns:
            snisp.markets.Markets: Markets for the Ship's Location
        """
        return Markets(self, self.location)

    @property
    def shipyards(self):
        """
        Property that returns the snisp.shipyards.Shipyards
        for the Ship's current System

        Blocks:
            False

        Returns:
            snisp.shipyards.Shipyards: Shipyards for the Ship's Location
        """
        return Shipyards(self, self.location)

    @property
    def system(self):
        """
        Property that returns the snisp.system.System
        for the Ship's current System

        .scan will be monkey-patched  to have the ship already
        loaded as the first argument

        Blocks:
            False

        Returns:
            snisp.systems.System: System for the Ship's Location
        """
        _system = System(self.agent)
        _system.scan = functools.partial(_system.scan, self)
        return _system

    @property
    def at_market(self):
        """
        Property that returns True if the Ship is DOCKED or IN_ORBIT
        at a Market; else False

        Blocks:
            False

        Returns:
            bool
        """
        if self.nav.status != 'IN_TRANSIT':
            waypoint = self.waypoints.get()
            return any(
                i.symbol.upper() == 'MARKETPLACE' for i in waypoint.traits
            )
        return False

    @property
    def at_shipyard(self):
        """
        Property that returns True if the Ship is DOCKED or IN_ORBIT
        at a Shipyard; else False

        Blocks:
            False

        Returns:
                bool
        """
        if self.nav.status != 'IN_TRANSIT':
            waypoint = self.waypoints.get()
            return any(
                i.symbol.upper() == 'SHIPYARD' for i in waypoint.traits
            )
        return False

    @property
    def can_mine(self):
        """
        Property that returns True if the Ship has a Mining Mount installed
        and can mine; else, False

        Blocks:
            False

        Returns:
                bool
        """
        for mount in self.mounts:
            if mount.symbol.upper().startswith('MOUNT_MINING_LASER_'):
                return True
        return False

    @property
    def can_refine_gas(self):
        """
        Property that returns True if the Ship has a Gas Processor
        Module installed and refine Gas; else, False

        Blocks:
            False

        Returns:
                bool
        """
        for module in self.modules:
            if module.symbol.upper().startswith('MODULE_GAS_PROCESSOR_'):
                return True
        return False

    @property
    def can_refine_ore(self):
        """
        Property that returns True if the Ship has a Mineral Processor
        Module installed and can refine Ore; else, False

        Blocks:
            False

        Returns:
                bool
        """
        for module in self.modules:
            if module.symbol.upper().startswith('MODULE_MINERAL_PROCESSOR_'):
                return True
        return False

    @property
    def can_siphon(self):
        """
        Property that returns True if the Ship has a Gas Siphon
        Mount installed and can siphon Gas; else, False

        Blocks:
            False

        Returns:
                bool
        """
        for mount in self.mounts:
            if mount.symbol.upper().startswith('MOUNT_GAS_SIPHON_'):
                return True
        return False

    @property
    def can_survey(self):
        """
        Property that returns True if the Ship has a Surveyor
        Mount installed and can survey; else, False

        Blocks:
            False

        Returns:
                bool
        """
        for mount in self.mounts:
            if mount.symbol.upper().startswith('MOUNT_SURVEYOR_'):
                return True
        return False

    def arrived_at_destination(self):
        current_nav = self.nav.to_dict()
        current_nav['status'] = 'IN_ORBIT'
        self.update_data_item('nav', current_nav)

    def closest(self, *iterables):
        """
        Iterates over supplied *iterables and returns the closest Waypoint
        to the Ship's current location

        Args:
            *iterables: Waypoints or Waypoint subclass types

        Blocks:
            False

        Returns:
            Waypoint or Waypoint subclass if *iterables return at least one
            Waypoint or Waypoint subclass; else, None
        """
        try:
            return min(
                (i for i in itertools.chain(*iterables)), key=self.distance
            )
        except ValueError:
            return

    def farthest(self, *iterables):
        """
        Iterates over supplied *iterables and returns the farthest Waypoint
        to the Ship's current location

        Args:
            *iterables: Waypoints or Waypoint subclass types

        Blocks:
            False

        Returns:
            Waypoint or Waypoint subclass if *iterables return at least one
            Waypoint or Waypoint subclass; else, None
        """
        try:
            return max(
                (i for i in itertools.chain(*iterables)), key=self.distance
            )
        except ValueError:
            return

    def distance(self, destination):
        """Returns the distance between the Ship and Waypoint

        Args:
            destination: Waypoint or Waypoint subclass type

        Blocks:
            False

        Returns:
            int
        """
        return utils.calculate_distance(self, destination)

    def closest_fuel(self):
        """
        Returns the closest Fuel Station to the Ship's current location.

        This is a time-consuming operation. The Library will do it's best
        to cache the result and use the cache on all subsequent calls

        Blocks:
            False

        Returns:
            Waypoint or Waypoint subclass
        """
        return self.closest(self.markets.fuel_stations())

    @retry()
    @transit
    def dock(self):
        """
        Dock the Ship at the current Waypoint, if it is not already docked

        If the Ship is IN_TRANSIT, the method will block unti the Ship
        has reached the destination

        Blocks:
            True: Won't be executed until Ship reaches destination
        """
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
        """
        Make an extraction at the current Waypoint.

        Exceptions will be raised if the Ship is at an invalid Waypoint
        type or if it does not have an Extraction Mount

        If the Ship is IN_TRANSIT, the method will block unti the Ship
        has reached the destination.

        An Extraction causes a cooldown period. The method will
        automatically block if the Ship is in a cooldown period.

        Blocks:
            True: Won't be executed until Ship reaches destination
                  and/or cooldown has passed

        Returns:
            Extraction
        """
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
        """
        Make an extraction at the current Waypoint with the supplied Survey

        Exceptions will be raised if the Ship is at an invalid Waypoint
        type, if it does not have an Extraction Mount, or if the Survey
        is invalid

        If the Ship is IN_TRANSIT, the method will block unti the Ship
        has reached the destination.

        An Extraction causes a cooldown period. The method will
        automatically block if the Ship is in a cooldown period.

        Args:
            survey: A Survey from a self.survey().surveys

        Blocks:
            True: Won't be executed until Ship reaches destination
                  and/or cooldown has passed

        Returns:
            ExtractionWithSurvey
        """
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
        """
        Not currently implemented by SpaceTraders

        Installs the listed Mount onto the ship. Must be at a shipyard

        Args:
            mount_symbol: Symbol of the Mount to install.
                          See snisp.utils.SHIP_MOUNTS for all supported
                          Ship Mounts

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
           Mounts: The Ship's current Mounts
        """
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
        """
        Jettison the number of units for the symbol from the Ship's
        cargo.

        Args:
            symbol: The symbol of the item to jettison

        Kwargs:
            units: The number of units to jettison. Default is 1.
        """
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
        """
        Jump Ship to Waypoint. Requires the Ship to be at a full constructed
        JumpGate

        Blocks:
            True: Won't be executed until Ship reaches destination
                  and/or cooldown has passed

        Args:
            waypoint: Waypoint or Waypoint subclass type
        """
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
        """
        Navigates the Ship to the destination Waypoint.

        The method will block until the Ship has reached the destination.

        The method will automatically attempt to refuel and modify the Ship's
        flight_mode as needed.

        done_callback accepteds a callback function that will be performed
        before returning control to the thread

        Failed attempts to reach intermediate Waypoints or refuel attempts
        will be logged at level INFO

        Ships that cannot reach their destinations will be added to the Ship's
        agent.dead_ships dictionary. Dead Ships will not be returned on further
        agent.fleet iterations

        Args:
            waypoint: Waypoint or Waypoint subclass type

        Kwargs:
            flight_mode: Starting flight_mode. Default is CRUISE
            done_callback: callable() item that will be executed before
                           returning

        Blocks:
            True: until Ship reaches destination

        Returns:
            NavigateInsufficientFuelError: Ran out of Fuel
        """
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
                    # If it's *already* as DRIFT at this point, well, :/
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
        """
        Attempts to navigate the Ship to the Waypoint.

        If the Ship is already IN_TRANSIT, the method will block
        until it reaches the previous destination first.

        Optional raise_error kwarg can suppress or raise Exceptions.
        Default is True

        Args:
            waypoint: Waypoint or Waypoint subclass type

        Kwargs:
            raise_error: If False, errors will be suppressed and returned.
                         Default True

        Blocks:
            True: Will block if Ship is already IN_TRANSIT. Oherwise, False

        Returns:
            Exception: Returns an Exception if one is raised and rase_error
                       is False
        """
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
        """
        Negotiates a new Contract.

        The Ship must be at a Wayoint with a Faction offering a Contract
        and the Agent associated with the Ship must not already have an active
        Contract

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Contract
        """
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/negotiate/contract'
        )
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            'Negotiated new contract'
        )
        return Contract(self.agent, response.json()['data']['contract'])

    @retry()
    @transit
    def orbit(self):
        """
        Orbit the Ship at the current Waypoint, if it is not already inorbit

        Blocks:
            True: Won't be executed until Ship reaches destination
        """
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
    def autopurchase(self, trade_symbol, max_units=0, buffer=200_000):
        """
        Purchases up to max_units of trade_symbol, depending on the Ship's
        cargo capacity and the Agent's current credits with regards to
        the buffer

        If max_units <= 0, max_units will be up to how many units
        are available in the Ship's cargo; else, max_units will be up to the
        number supplied

        Buffer will be your credits buffer. The default 200_000 limit means you
        will be able to purchase up to max_units so long as your current
        agent.data.credits - buffer >= purchase price.
        To remove the buffer, just pass a 0

        Args:
            trade_symbol: Symbol of item to purchase.

        Kwargs:
            max_units: Up to max_units to purchase. Default is until the ship's
                       cargo is at capacity
            buffer: Credit buffer. Up to max_units will be purchased so far as
                    the purchase amount - agent.data.credits - buffer > 0.
                    Default is 200_000

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Transactions:  List of successful Transactions or an empty list
        """
        trade_symbol = trade_symbol.upper()
        if trade_symbol not in utils.GOODS_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{trade_symbol} is not an acceptable goods type. '
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
                f'Cannot purchase {max_units:,} of {trade_symbol}.'
            )
            return transactions
        trade_volume = None
        for t_good in market_data.trade_goods:
            if t_good.symbol == trade_symbol:
                trade_volume = t_good.trade_volume
                break
        if trade_volume is None:
            logger.warning(
                f'Market {self.location.waypoint} no '
                f'longer trading {trade_symbol}'
            )
            return transactions
        with self.agent.lock:
            while max_units > 0:
                unit_price = None
                for t_good in self.markets().trade_goods:
                    if t_good.symbol == trade_symbol:
                        unit_price = t_good.purchase_price
                        break
                if unit_price is None:
                    logger.warning(
                        f'Market {self.location.waypoint} no longer '
                        f'trading {trade_symbol}'
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
                cash = self.agent.data.credits
                while purchase_amount > cash - buffer:
                    buy_units -= 1
                    if buy_units == 0:
                        return transactions
                    purchase_amount = buy_units * unit_price
                transactions.append(self.purchase(trade_symbol, buy_units))
                max_units -= buy_units
        return transactions

    @retry()
    @transit
    @docked
    def purchase(self, trade_symbol, units):
        """
        Purchases the specified units of the trade_symbol

        Examples of exceptions are insufficient funds, cargo capacity,
        or if at an invalid waypoint

        Args:
            trade_symbol: Symbol of item to purchase
            units: Number of units to purchase

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Transacaction
        """
        trade_symbol = trade_symbol.upper()
        if trade_symbol not in utils.GOODS_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{trade_symbol} is not an acceptable goods type. '
                'See snisp.utils.GOODS_TYPES for acceptable goods.'
            )
        with self.agent.lock:
            payload = {'symbol': trade_symbol, 'units': int(units)}
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
        """
        Refuels the Ship if the Ship is at a Waypoint that sells Fuel, or,
        if from_cargo is True, Refuels from the Ship cargo

        Kwargs:
            units: If greather than 0, restrict to N units being refilled.
                   Default 0 will refill the fuel tank completely
            from_cargo: If True, refuel from Cargo. Default False
            ignore_errors: If True, errors will be suppressed and returned.
                           Default False

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Exception: Returns an Exception if one occurs and
                       ignore_errors is True
        """
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
        """Refine Ore into a product

        Converts 30 units of Ore into 1 inut of Product

        Args:
            produce: The symbol to produce. i.e., "IRON".
                     See snisp.utils.REFINABLE_SYMBOLS for refinable types

        Blocks:
            True: Blocks during cooldown
        """
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
        """Returns a new Ship class object of the current ship

        Returns:
            A new Ship instance from self
        """
        response = self.agent.client.get(f'/my/ships/{self.symbol}')
        return Ship(self.agent, response.json()['data'])

    @retry()
    @transit
    @docked
    def remove_mount(self, mount_symbol):
        """
        Not currently implemented by SpaceTraders

        Removes the listed Mount onto the ship. Must be at a Shipyard

        Args:
            mount_symbol: Symbol of the Mount to remove

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
           Mounts: The Ship's current Mounts
        """
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
    @docked
    def repair_cost(self):
        """
        Returns the current cost to repair the ship

        Ship must be located at a Shipyard

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            int
        """
        response = self.agent.client.get(f'/my/ships/{self.symbol}/repair')
        data = response.json()['data']
        return int(data['transaction']['totalPrice'])

    @retry()
    @transit
    @docked
    def repair(self):
        """
        Repairs the ship to full working condition

        Ship must be located at a Shipyard

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Transaction
        """
        payload = {'shipSymbol': self.symbol}
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/repair', json=payload
        )
        data = response.json()['data']
        self.update_data_item('frame', data['ship']['frame'])
        self.update_data_item('reactor', data['ship']['reactor'])
        self.update_data_item('engine', data['ship']['engine'])
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            f'Repaired ship for ${data["transaction"]["totalPrice"]:,.2f}'
        )
        transaction = Transaction(self.agent, data['transaction'])
        self.agent.recent_transactions.appendleft(transaction)
        return transaction

    @retry()
    @transit
    @in_orbit
    @cooldown
    def scan(self):
        """
        Scan current System for ships

        NOTE: SpaceTraders does not make it explicit who is the owner of a
              scanned ship. SnakesInSpace currently assumes scanned
              ships are owned by the Agent. Attempting to perform actions on
              a ship you do not own will lead to undefined consequences.

        Blocks:
            True: Won't be executed until Ship reaches destination
                  and/or cooldown has passed

        Yields:
            Ships
        """
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/scan/ships'
        )
        data = response.json()['data']
        self.update_data_item('cooldown', data['cooldown'])
        for ship in data['ships']:
            yield Ship(self.agent, ship)

    @retry()
    @transit
    @docked
    def scrap_price(self):
        """
        Returns the current scrap price for the ship

        Ship must be located at a Shipyard

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            int
        """
        response = self.agent.client.get(f'/my/ships/{self.symbol}/scrap')
        data = response.json()['data']
        return int(data['transaction']['totalPrice'])

    @retry()
    @transit
    @docked
    def scrap(self):
        """
        Sells the ship as scrap to the Shipyard at the ship's location.

        Ship must be located at a Shipyard

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Transaction
        """
        payload = {'shipSymbol': self.symbol}
        response = self.agent.client.post(
            f'/my/ships/{self.symbol}/scrap', json=payload
        )
        data = response.json()['data']
        logger.info(
            f'{self.registration.role}: {self.symbol} | '
            f'Scraped ship for ${data["transaction"]["totalPrice"]:,.2f}'
        )
        transaction = Transaction(self.agent, data['transaction'])
        self.agent.recent_transactions.appendleft(transaction)
        return transaction

    @transit
    def sell_all(self, trade_symbol, units=0):
        """
        Sell goods from the Ship's cargo.

        Args:
            trade_symbol: Good type. Symbol of item to sell

        Kwargs:
            units: The number of units to sell. If units < 0, all will be sold
                   Default 0

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Transactions:  List of successful Transactions or an empty list
        """
        transactions = []
        units = int(units)
        if units <= 0:
            units = next(
                (
                    i.units
                    for i in self.cargo.inventory if i.symbol == trade_symbol
                ), None
            )
            if units is None:
                logger.warning(
                    f'{self.registration.role}: {self.symbol} | '
                    'Attempting to sell {trade_symbol} which '
                    'is not currently in its cargo hold'
                )
                return transactions
        market_data = self.markets()
        if not market_data:
            logger.warning(
                f'{self.registration.role}: {self.symbol} | '
                f'No market at {self.location.waypoint}. '
                f'Cannot sell {units:,} of {trade_symbol}.'
            )
            return transactions
        trade_volume = next(
            (
                i.trade_volume
                for i in market_data.trade_goods
                if i.symbol == trade_symbol
            ), None
        )
        if trade_volume is None:
            logger.warning(
                f'Market {market_data.symbol} no longer trading {trade_symbol}'
            )
            return transactions
        while units:
            sell_units = units
            if units > trade_volume:
                units -= trade_volume
                sell_units = trade_volume
            else:
                units = 0
            transactions.append(self.sell(trade_symbol, sell_units))
        self.agent.recent_transactions.extendleft(transactions)
        return transactions

    def sell_off_cargo(self, trade_symbol=None):
        """
        Sell all goods from the Ship's cargo. Will automatically navigate
        to closest Market which sells the respective goods

        Kwargs:
            trade_symbol: Good type. Symbol of item to sell otherwise sells
                          everything in ship.cargo.inventory. Default is None

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Transactions:  List of successful Transactions or an empty list
        """

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
    def sell(self, trade_symbol, units):
        """
        Sell goods from the Ship's cargo.

        Args:
            trade_symbol: Good type. Symbol of item to sell
            units: The number of units to sell

        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Transaction
        """
        trade_symbol = trade_symbol.upper()
        if trade_symbol not in utils.GOODS_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{trade_symbol} is not an acceptable goods type. '
                'See snisp.utils.GOODS_TYPES for acceptable goods.'
            )
        payload = {'symbol': trade_symbol, 'units': int(units)}
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
        """
        Make a siphon at the current Waypoint.

        Exceptions will be raised if the Ship is at an invalid Waypoint
        type or if it does not have a Siphon Mount

        A Siphon causes a cooldown period. The method will
        automatically block if the Ship is in a cooldown period.

        Blocks:
            True: Won't be executed until Ship reaches destination
                  and/or cooldown has passed

        Returns:
            Siphon
        """
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
        """
        Transfer cargo from Ship to another Ship

        Updates both Ships' cargos. Requires both Ships to be at the
        same Waypoint

        Args:
            receive_ship: The snisp.fleet.Ship instance of another Ship

        Kwargs:
            symbol: The symbol for the goods to transfer
            units: The number of units to transfer

        Blocks:
            True: until both Ships reach destination
        """
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
        """
        Warp Ship to Waypoint.

        Requires the Ship to have a Warp Drive

        Args:
            waypoint: Waypoint or Waypoint subclass type

        Blocks:
            True: Won't be executed until Ship reaches destination
        """
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
        """
        Updates the Ships flight mode if needed

        Args:
            mode: New flight_mode. See snips.utils.FLIGHT_MODES for supported
                  flight modes

        Blocks:
            True: Won't be executed until Ship reaches destination
        """
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
