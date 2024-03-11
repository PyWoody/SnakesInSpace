import httpx
import json
import os
import pytest

import snisp

from . import DATA_DIR


class TestFactions:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    def test_repr(self, respx_mock):
        assert repr(self.agent.factions) == f'Factions({self.agent!r})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_call(self, respx_mock):
        faction_data = json.load(
            open(os.path.join(DATA_DIR, 'faction.json'), encoding='utf8')
        )
        for symbol in snisp.utils.FACTION_SYMBOL:
            faction_data['data']['symbol'] = symbol
            respx_mock.get(f'/factions/{symbol}').mock(
                return_value=httpx.Response(200, json=faction_data)
            )
            faction = self.agent.factions(symbol)
            assert faction.to_dict() == faction_data['data']

        with pytest.raises(snisp.exceptions.WaypointNoFactionError):
            self.agent.factions('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_iter(self, respx_mock):
        factions_data = json.load(
            open(os.path.join(DATA_DIR, 'factions.json'), encoding='utf8')
        )
        respx_mock.get(
            '/factions', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=factions_data)
        )
        respx_mock.get(
            '/factions', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        factions = list(self.agent.factions)
        assert len(factions) == 1
        assert factions[0].symbol == 'COSMIC'
