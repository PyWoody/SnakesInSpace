import logging

from snisp import exceptions, fleet, utils, waypoints
from snisp.decorators import retry


logger = logging.getLogger(__name__)


class Shipyards:

    def __init__(self, ship, location):
        self.ship = ship
        self.location = location

    def __repr__(self):
        cls = self.__class__.__name__
        return f'{cls}({self.ship.agent!r}, {self.location!r})'

    def __iter__(self):
        waypoint = waypoints.Waypoints(self.ship.agent, self.location)
        for shipyard in waypoint(traits='SHIPYARD'):
            yield Shipyard(self.ship.agent, shipyard.to_dict())

    def autopurchase(self, *, ship_type, max_units=1, buffer=300_000):
        max_units = int(max_units)
        transactions = []
        smd = self.ship.markets.shipyard_market_data
        with self.ship.agent.lock:
            while max_units > 0:
                shipyard, market_data = smd(ship_type)
                if not market_data or not shipyard:
                    logger.warning(
                        f'SYSTEM: {self.location.system} | '
                        f'No Shipyard found selling {ship_type}s'
                    )
                    return transactions
                credits_buffer = self.ship.agent.data.credits - buffer
                if market_data.purchase_price <= credits_buffer:
                    transactions.append(shipyard.purchase(ship_type))
                    max_units -= 1
                else:
                    return transactions
        return transactions


class Shipyard(utils.AbstractJSONItem):

    # TODO: There needs to be a convient way to get shipyard at
    #       the current location

    def __init__(self, agent, shipyard):
        self.agent = agent
        self._data = shipyard

    @property
    def data(self):
        response = self.agent.client.get(
            f'/systems/{self.system_symbol}/waypoints/'
            f'{self.symbol}/shipyard'
        )
        return ShipyardData(self.agent, response.json()['data'])

    @retry()
    def available_ships(self, ship_type=None):
        if ship_type and ship_type not in utils.SHIP_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{ship_type} is not an acceptable Ship type. '
                'See snisp.utils.SHIP_TYPES for acceptable types.'
            )
        response = self.agent.client.get(
            f'/systems/{self.system_symbol}'
            f'/waypoints/{self.symbol}/shipyard'
        )
        for ship in response.json()['data'].get('ships', []):
            if ship_type is not None and ship_type != ship['type']:
                continue
            if 'shipyard_symbol' not in ship.keys():
                ship['shipyard_symbol'] = self.symbol
            yield ShipyardShip(self.agent, ship)

    @retry()
    def purchase(self, ship_type):
        if ship_type not in utils.SHIP_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{ship_type} is not an acceptable Ship type. '
                'See snisp.utils.SHIP_TYPES for acceptable types.'
            )
        if not utils.a_ship_at_location(self.agent, self.symbol):
            cls = self.__class__.__name__
            raise exceptions.NoShipAtLocationError(
                f'No ships located at {self.symbol!r} for {cls}'
            )
        payload = {
            'shipType': ship_type, 'waypointSymbol': self.symbol
        }
        with self.agent.lock:
            response = self.agent.client.post('/my/ships', json=payload)
            data = response.json()['data']
            logger.info(
                f'Purchased a {data["transaction"]["shipType"]} at '
                f'{data["transaction"]["waypointSymbol"]} for '
                f'${data["transaction"]["price"]:,.2f}'
            )
            self.agent.recent_transactions.appendleft(
                fleet.Transaction(self.agent, data)
            )
            return fleet.Ship(self.agent, data['ship'])

    def transactions(self, page=1):
        if not utils.a_ship_at_location(self.agent, self.symbol):
            cls = self.__class__.__name__
            raise exceptions.NoShipAtLocationError(
                f'No ships located at {self.symbol!r} for {cls}'
            )
        params = {'page': int(page)}
        response = self.agent.client.get(
            f'/systems/{self.system_symbol}/'
            f'waypoints/{self.symbol}/shipyard', params=params
        )
        transactions = response.json()['data'].get('transactions', [])
        while transactions:
            for transaction in transactions:
                yield fleet.Transaction(self.agent, transaction)
            params['page'] += 1
            response = self.agent.client.get(
                f'/systems/{self.system_symbol}/'
                f'waypoints/{self.symbol}/shipyard', params=params
            )
            transactions = response.json()['data'].get('transactions', [])


class ShipyardData(utils.AbstractJSONItem):

    def __init__(self, agent, data):
        self.agent = agent
        self._data = data


class ShipyardShip(utils.AbstractJSONItem):

    def __init__(self, agent, ship):
        self.agent = agent
        self._data = ship

    @retry()
    def purchase(self, *, buffer=200_000):
        # Convenience method used when iterating over available ship types
        # Should be renamed to make it clearer
        payload = {
            'shipType': self.type, 'waypointSymbol': self.shipyard_symbol
        }
        with self.agent.lock:
            if (self.agent.data.credits - buffer) > 0:
                response = self.agent.client.post('/my/ships', json=payload)
                data = response.json()['data']
                logger.info(
                    f'Purchased a {data["transaction"]["shipType"]} at '
                    f'{data["transaction"]["waypointSymbol"]} for '
                    f'${data["transaction"]["price"]:,.2f}'
                )
                return fleet.Ship(self.agent, data['ship'])
