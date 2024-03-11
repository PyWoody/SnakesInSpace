import httpx
import json
import os
import pytest


import snisp

from . import DATA_DIR


class TestCache:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')
    client = agent.client
    client.testing = False

    def test_in_test(self, respx_mock):
        assert self.client.testing is False

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_get_fuel_stations(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        fuel_stations_data = json.load(
            open(os.path.join(DATA_DIR, 'fuel_stations.json'), encoding='utf8')
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=fuel_stations_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )

        market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-NEXTCLOSESTFUEL/market'
        ).mock(
            return_value=httpx.Response(200, json=market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-FARTHESTFUEL/market'
        ).mock(
            return_value=httpx.Response(200, json=market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTFUEL/market'
        ).mock(
            return_value=httpx.Response(200, json=market_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        fuel_stations = list(ship.markets.fuel_stations())
        assert fuel_stations == list(ship.markets.fuel_stations())
