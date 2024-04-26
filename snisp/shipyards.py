import logging

from snisp import exceptions, fleet, utils, waypoints
from snisp.decorators import retry
from snisp.exceptions import ClientError


logger = logging.getLogger(__name__)


class Shipyards:

    def __init__(self, ship, location):
        self.ship = ship
        self.agent = ship.agent
        self.location = location

    def __repr__(self):
        cls = self.__class__.__name__
        return f'{cls}({self.agent!r}, {self.location!r})'

    def __iter__(self):
        """
        Iterates over the Shipyard's in the Ship's current location

        Yields:
            Shipyard
        """
        waypoint = waypoints.Waypoints(self.agent, self.location)
        for shipyard in waypoint(traits='SHIPYARD'):
            yield Shipyard(self.agent, shipyard.to_dict())

    def autopurchase(self, *, ship_type, max_units=1, buffer=300_000):
        """
        Purchases up to max_units of ship_type, depending on
        the Agent's current credits with regards to the buffer and if the
        ship_type is currently available at a known Shipyard

        Buffer will be your credits buffer. The default 300_000 limit means you
        will be able to purchase up to max_units so long as your current
        agent.data.credits - buffer >= purchase price.
        To remove the buffer, just pass a 0

        NOTE: The only way to know the type and cost of a ship available
              for purchase at a Shipyard is to have a Ship or Probe located
              at the Shipyard. Just because nothing is returned, does not
              entail that no Ship's of that type are availble for purchase

        Args:
            ship_type: Ship type to purchase. See snisp.utils.SHIP_TYPES for
                       acceptable Ship types

        Kwargs:
            max_units: Up to max_units to purchase. Default is 1
            buffer: Credit buffer. Up to max_units will be purchased so far as
                    the purchase amount - agent.data.credits - buffer > 0.
                    Default is 300_000

        Returns:
            Transactions:  List of successful Transactions or an empty list
        """
        max_units = int(max_units)
        transactions = []
        smd = self.ship.markets.shipyard_market_data
        with self.agent.lock:
            while max_units > 0:
                shipyard, market_data = smd(ship_type)
                if not market_data or not shipyard:
                    logger.warning(
                        f'SYSTEM: {self.location.system} | '
                        f'No Shipyard found selling {ship_type}s'
                    )
                    return transactions
                credits_buffer = self.agent.data.credits - buffer
                if market_data.purchase_price <= credits_buffer:
                    transactions.append(shipyard.purchase(ship_type))
                    max_units -= 1
                else:
                    return transactions
        return transactions


class Shipyard(utils.AbstractJSONItem):

    def __init__(self, agent, shipyard):
        self.agent = agent
        self._data = shipyard

    @property
    def data(self):
        """Returns the Shipyard's ShipyardData"""
        try:
            response = self.agent.client.get(
                f'/systems/{self.system_symbol}/waypoints/'
                f'{self.symbol}/shipyard'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'Shipyard at {self.location!r} has not been charted.'
                    )
                    return ShipyardData(self.agent, {})
            raise e
        return ShipyardData(self.agent, response.json()['data'])

    @retry()
    def available_ships(self, ship_type=None):
        """
        Yields the ships available for purchasing at the Shipyard

        NOTE: The only way to know the type and cost of a ship available
              for purchase at a Shipyard is to have a Ship or Probe located
              at the Shipyard. Just because nothing is returned, does not
              entail that no Ship's of that type are availble for purchase
              at the Shipyard

        Kwargs:
            ship_type: Ship type to filter. See snisp.utils.SHIP_TYPES for
                       acceptable Ship types. Default is None
        Yields:
            ShipyardShip
        """
        if ship_type and ship_type not in utils.SHIP_TYPES:
            raise exceptions.SpaceAttributeError(
                f'{ship_type} is not an acceptable Ship type. '
                'See snisp.utils.SHIP_TYPES for acceptable types.'
            )
        try:
            response = self.agent.client.get(
                f'/systems/{self.system_symbol}'
                f'/waypoints/{self.symbol}/shipyard'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'Shipyard at {self.location!r} has not been charted.'
                    )
                    yield ShipyardData(self.agent, {})
                    return
            raise e
        for ship in response.json()['data'].get('ships', []):
            if ship_type is not None and ship_type != ship['type']:
                continue
            if 'shipyard_symbol' not in ship.keys():
                ship['shipyard_symbol'] = self.symbol
            yield ShipyardShip(self.agent, ship)

    @retry()
    def purchase(self, ship_type):
        """
        Purchases a Ship of ship_type

        Args:
            ship_type: Ship type to filter. See snisp.utils.SHIP_TYPES for
                       acceptable Ship types
        Returns:
            Ship
        """
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
        """
        Yields the most recent Transactions at the Shipyard

        Requires a Ship or Probe to be located at the Shipyard

        Yields:
            Transaction
        """
        if not utils.a_ship_at_location(self.agent, self.symbol):
            cls = self.__class__.__name__
            raise exceptions.NoShipAtLocationError(
                f'No ships located at {self.symbol!r} for {cls}'
            )
        params = {'page': int(page)}
        try:
            response = self.agent.client.get(
                f'/systems/{self.system_symbol}/'
                f'waypoints/{self.symbol}/shipyard', params=params
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'Shipyard at {self.location!r} has not been charted.'
                    )
                    yield ShipyardData(self.agent, {})
                    return
            raise e
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
        """
        Purchases a Ship of the ShipyardShip's ship_type

        Convenience method used when iterating over available ship types
        for sale

        Buffer will be your credits buffer. The default 200_000 limit means you
        will be able to purchase a Ship so long as your current
        agent.data.credits - buffer >= purchase price.
        To remove the buffer, just pass a 0

        Kwargs:
            buffer: Credit buffer. Up to max_units will be purchased so far as
                    the purchase amount - agent.data.credits - buffer > 0.
                    Default is 200_000

        Returns:
            Ship
        """
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
