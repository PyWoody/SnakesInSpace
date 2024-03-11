from snisp import exceptions, utils
from snisp.decorators import retry


class Factions:

    def __init__(self, agent):
        self.agent = agent

    def __repr__(self):
        return f'{self.__class__.__name__}({self.agent!r})'

    def __iter__(self):
        page = 1
        response = self.get_page(page=page)
        while data := response.json()['data']:
            for faction in data:
                yield Faction(self.agent, faction)
            page += 1
            response = self.get_page(page=page)

    @retry()
    def __call__(self, faction_symbol):
        faction_symbol = faction_symbol.upper().strip()
        if faction_symbol not in utils.FACTION_SYMBOL:
            raise exceptions.WaypointNoFactionError(
                f'{faction_symbol} is not an acceptable Faction symbol. '
                'See snisp.utils.FACTION_SYMBOLS for acceptable symbols.'
            )
        response = self.agent.client.get(f'/factions/{faction_symbol}')
        return Faction(self.agent, response.json()['data'])

    @retry()
    def get_page(self, page=1, limit=20):
        params = {'limit': int(limit), 'page': int(page)}
        return self.agent.client.get('/factions', params=params)


class Faction(utils.AbstractJSONItem):

    def __init__(self, agent, faction):
        self.agent = agent
        self._data = faction
