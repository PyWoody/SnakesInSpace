import logging

from snisp import exceptions, utils
from snisp.decorators import cooldown, in_orbit, retry, transit


logger = logging.getLogger(__name__)


class Systems:

    def __init__(self, agent):
        self.agent = agent

    def __repr__(self):
        return f'{self.__class__.__name__}({self.agent!r})'

    def __iter__(self):
        """
        Iterates over the System's in the Agent's current universe

        Yields:
            StarSystem
        """
        page = 1
        response = self.get_page(page=page)
        while data := response.json()['data']:
            for system in data:
                yield StarSystem(self.agent, system)
            page += 1
            response = self.get_page(page=page)

    def find(self, **filters):
        """
        Find the first instance of the StarSystems which match the filters

        Kwargs:
            **filters: Top-level key, value pairs used to filter the Systems

        Returns:
            StarSystem if **filters leads to a match; else, None
        """
        try:
            return next(self.find_all(**filters))
        except StopIteration:
            logger.info(f'No system found with {filters!r}')

    def find_all(self, **filters):
        """
        Find the all instances of the StarSystems which match the filters

        Kwargs:
            **filters: Top-level key, value pairs used to filter the Systems

        Yields:
            StarSystem
        """
        if _type := filters.get('type'):
            _type = _type.upper().strip()
            if _type not in utils.SYSTEMS_TYPES:
                raise exceptions.SpaceAttributeError(
                    f'{_type} is not an acceptable System type.'
                )
            filters['type'] = _type
        filters = {utils.camel_case(k): v for k, v in filters.items()}
        for system in self:
            system_dict = system.to_dict()
            if all(system_dict[k] == v for k, v in filters.items()):
                yield system

    @retry()
    def get_page(self, page=1, limit=20):
        params = {'limit': int(limit), 'page': int(page)}
        return self.agent.client.get('/systems', params=params)


class System:

    def __init__(self, agent):
        self.agent = agent

    def __repr__(self):
        return f'{self.__class__.__name__}({self.agent!r})'

    @retry()
    def __call__(self, system_symbol):
        """Returns the System for system_symbol"""
        response = self.agent.client.get(f'/systems/{system_symbol}')
        return StarSystem(self.agent, response.json()['data'])

    @retry()
    @transit
    @in_orbit
    @cooldown
    def scan(self, ship):
        """
        Scans the System in the ship's current System

        Args:
            ship: Ship to use. All snisp.fleet.Ship objects will have this
                  automatically monkey-patched in.
        Blocks:
            True: Won't be executed until Ship reaches destination and/or
                  the cooldown period has passed

        Yields:
            StarSystem
        """
        response = self.agent.client.post(
            f'/my/ships/{ship.symbol}/scan/systems'
        )
        data = response.json()['data']
        ship.update_data_item('cooldown', data['cooldown'])
        for _system in data['systems']:
            yield StarSystem(self.agent, _system)


class StarSystem(utils.AbstractJSONItem):

    def __init__(self, agent, system):
        self.agent = agent
        self._data = system


class Location(utils.AbstractJSONItem):

    """
    Location is used throughout as a convenience class for normalizing
    sector, system, and waypoint symbols
    """

    def __init__(self, agent, location):
        self.agent = agent
        self._data = location

    @property
    def sector(self):
        """Property that returns the Location's sector"""
        if hq := self.headquarters:
            return hq.split('-')[0]
        return self.waypoint.split('-')[0]

    @property
    def system(self):
        """Property that returns the Location's system"""
        if hq := self.headquarters:
            return '-'.join(hq.split('-')[0:2])
        return '-'.join(self.waypoint.split('-')[0:2])

    @property
    def waypoint(self):
        """Property that returns the Location's waypoint"""
        if hq := self.headquarters:
            return hq
        if nav := self.nav:
            if wp := nav.waypoint_symbol:
                return wp
        return self.symbol
