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
        page = 1
        response = self.get_page(page=page)
        while data := response.json()['data']:
            for system in data:
                yield StarSystem(self.agent, system)
            page += 1
            response = self.get_page(page=page)

    def find(self, **filters):
        try:
            return next(self.find_all(**filters))
        except StopIteration:
            logger.info(f'No system found with {filters!r}')

    def find_all(self, **filters):
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
        response = self.agent.client.get(f'/systems/{system_symbol}')
        return StarSystem(self.agent, response.json()['data'])

    @retry()
    @transit
    @in_orbit
    @cooldown
    def scan(self, ship):
        """Scan will be monkey patched in the Fleet class"""
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

    def __init__(self, agent, location):
        self.agent = agent
        self._data = location

    @property
    def sector(self):
        if hq := self.headquarters:
            return hq.split('-')[0]
        return self.waypoint.split('-')[0]

    @property
    def system(self):
        if hq := self.headquarters:
            return '-'.join(hq.split('-')[0:2])
        return '-'.join(self.waypoint.split('-')[0:2])

    @property
    def waypoint(self):
        if hq := self.headquarters:
            return hq
        return self.nav.waypoint_symbol
