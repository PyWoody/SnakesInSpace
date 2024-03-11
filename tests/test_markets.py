import copy
import httpx
import inspect
import json
import os
import pytest

import snisp

from . import DATA_DIR


# 4600: MarketInsufficientCredits
# 4601: MarketTradeNoPurchaseError
# 4602: MarketTradeNotSoldError
# 4604: MarketTradeUnitLimitError


class TestMarkets:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_repr(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert repr(ship.markets) == f'Markets({ship.agent!r}, ' \
                                     f'{ship.location})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_iter(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        markets_side_effect = MarketsSideEffect(waypoints_data)
        market_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        market_route.side_effect = markets_side_effect

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        with markets_side_effect:
            for market in ship.markets:
                assert any(i.symbol == 'MARKETPLACE' for i in market.traits)
            assert len(list(ship.markets)) == 1

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_call(self, respx_mock):
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['traits'][0]['symbol'] = 'MARKETPLACE'
        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])
        market_side_effect = MarketSideEffect(waypoint_data)
        market_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        )
        market_route.side_effect = market_side_effect
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        market = ship.markets()

        assert len(market) == len(market.to_dict())
        assert 'to_dict' in dir(market)
        assert market == ship.markets()

        assert ship.markets(waypoint_symbol='TEST-SYSTEM-WAYPOINT') == market
        assert ship.markets(waypoint=waypoint) == market
        with market_side_effect as tmp:
            tmp.invalid = True
            assert ship.markets().to_dict() == {}

        # 4603: MarketNotFoundError
        with market_side_effect as tmp:
            tmp.not_found = True
            with pytest.raises(snisp.exceptions.MarketNotFoundError):
                ship.markets()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_search(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        imports = ship.markets.search(imports='IRON')
        assert inspect.isgenerator(imports)
        imports = list(imports)
        assert len(imports) == 1
        assert imports[0][0].symbol == 'TEST-SYSTEM-FARTHESTWAYPOINT'
        assert snisp.markets.has_import(imports[0][1], 'IRON')

        exports = ship.markets.search(exports='PRECIOUS_STONES')
        assert inspect.isgenerator(exports)
        exports = list(exports)
        assert len(exports) == 2
        assert exports[0][0].symbol != 'TEST-SYSTEM-FARTHESTWAYPOINT'
        assert exports[1][0].symbol != 'TEST-SYSTEM-FARTHESTWAYPOINT'
        assert snisp.markets.has_export(exports[0][1], 'PRECIOUS_STONES')

        exchanges = ship.markets.search(exchanges='PRECIOUS_STONES')
        assert inspect.isgenerator(exchanges)
        exchanges = list(exchanges)
        assert len(exchanges) == 2
        assert exchanges[0][0].symbol != 'TEST-SYSTEM-FARTHESTWAYPOINT'
        assert exchanges[1][0].symbol != 'TEST-SYSTEM-FARTHESTWAYPOINT'
        assert snisp.markets.has_exchange(exchanges[0][1], 'PRECIOUS_STONES')

        invalid = ship.markets.search(imports='INVALID')
        assert inspect.isgenerator(invalid)
        assert len(list(invalid)) == 0

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_import(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'IMPORT':
                good['sellPrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_import('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-WAYPOINT'
        assert not ship.markets.cheapest_import('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_import_no_probed(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del expensive_market_data['data']['tradeGoods']
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del cheapest_market_data['data']['tradeGoods']
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        del iron_market_data['data']['tradeGoods']
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_import('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.cheapest_import('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_export_or_exchange(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in expensive_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['symbol'] = 'IRON'
                good['purchasePrice'] = 1_000
                good['sellPrice'] = 1
        expensive_market_data['data']['exports'][0]['symbol'] = 'IRON'
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON_ORE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_export_or_exchange('IRON')
        assert market[0].symbol == 'TEST-SYSTEM-FARTHESTWAYPOINT'
        assert not ship.markets.cheapest_export_or_exchange('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_export_or_exchange_no_probe(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del expensive_market_data['data']['tradeGoods']
        expensive_market_data['data']['exports'][0]['symbol'] = 'IRON'
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del cheapest_market_data['data']['tradeGoods']
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del iron_market_data['data']['tradeGoods']
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON_ORE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_export_or_exchange('IRON')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.cheapest_export_or_exchange('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_exchange(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_exchange('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.cheapest_exchange('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_exchange_no_probe(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del expensive_market_data['data']['tradeGoods']
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del cheapest_market_data['data']['tradeGoods']
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del iron_market_data['data']['tradeGoods']
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_exchange('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.cheapest_exchange('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_most_expensive_import(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del expensive_market_data['data']['tradeGoods']
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del cheapest_market_data['data']['tradeGoods']
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del iron_market_data['data']['tradeGoods']
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.most_expensive_import('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.most_expensive_import('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_most_expensive_import_no_probe(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.most_expensive_import('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.most_expensive_import('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_export(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_export('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-WAYPOINT'
        assert not ship.markets.cheapest_export('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cheapest_export_no_probe(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del expensive_market_data['data']['tradeGoods']
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del cheapest_market_data['data']['tradeGoods']
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del iron_market_data['data']['tradeGoods']
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.cheapest_export('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.cheapest_export('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_most_expensive_export(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.most_expensive_export('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.most_expensive_export('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_most_expensive_export_no_probe(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del expensive_market_data['data']['tradeGoods']
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del cheapest_market_data['data']['tradeGoods']
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        del iron_market_data['data']['tradeGoods']
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        market = ship.markets.most_expensive_export('PRECIOUS_STONES')
        assert market[0].symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert not ship.markets.most_expensive_export('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_imports(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        markets = ship.markets.imports('PRECIOUS_STONES')
        assert inspect.isgenerator(markets)
        assert len(list(markets)) == 2
        assert not list(ship.markets.imports('INVALID'))

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_exports(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        markets = ship.markets.exports('PRECIOUS_STONES')
        assert inspect.isgenerator(markets)
        assert len(list(markets)) == 2
        assert not list(ship.markets.exports('INVALID'))

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_exchanges(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'EXCHANGE':
                good['purchasePrice'] = 1
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['imports'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        iron_market_data['data']['exports'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        markets = ship.markets.exchanges('PRECIOUS_STONES')
        assert inspect.isgenerator(markets)
        assert len(list(markets)) == 2
        assert not list(ship.markets.exchanges('INVALID'))

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_shipyard_market_data(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        shipyards_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/shipyard'
        )
        shipyards_route.side_effect = shipyards_side_effect
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        with shipyards_side_effect as tmp:
            tmp.waypoints['data'][1]['traits'][0]['symbol'] = 'SHIPYARD'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            shipyard_data = ship.markets.shipyard_market_data('SHIP_PROBE')
            assert len(shipyard_data) == 2
            assert shipyard_data[0].symbol == 'TEST-SYSTEM-WAYPOINT'
            assert shipyard_data[1].type == 'SHIP_PROBE'

        with shipyards_side_effect as tmp:
            tmp.waypoints['data'][1]['traits'][0]['symbol'] = 'SHIPYARD'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            shipyard_data = ship.markets.shipyard_market_data('SHIP_ORE_HOUND')
            assert len(shipyard_data) == 2
            assert shipyard_data[0] is None
            assert shipyard_data[1] is None

        with shipyards_side_effect as tmp:
            tmp.waypoints['data'][1]['traits'][0]['symbol'] = 'SHIPYARD'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.SpaceAttributeError):
                shipyard_data = ship.markets.shipyard_market_data('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_best_market_pairs(self, respx_mock):
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        for wp in waypoints_data['data']:
            wp['traits'][0]['symbol'] = 'MARKETPLACE'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=waypoints_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        # lazy
        expensive_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        cheapest_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        for good in cheapest_market_data['data']['tradeGoods']:
            if good['type'] == 'IMPORT':
                good['symbol'] = 'CHEAPEST'
        for good in expensive_market_data['data']['tradeGoods']:
            if good['type'] == 'EXPORT' or good['type'] == 'EXCHANGE':
                good['symbol'] = 'EXPENSIVE'
            elif good['type'] == 'IMPORT':
                good['sellPrice'] = 1_000
        cheapest_market_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        expensive_market_data['data']['symbol'] = 'TEST-SYSTEM-CLOSESTWAYPOINT'
        iron_market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        iron_market_data['data']['symbol'] = 'TEST-SYSTEM-FARTHESTWAYPOINT'
        for good in iron_market_data['data']['tradeGoods']:
            good['symbol'] = 'IRON'
        iron_market_data['data']['exchange'][0]['symbol'] = 'IRON'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT'
        ).mock(
            return_value=httpx.Response(
                200, json={'data': waypoints_data['data'][1]}
            )
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT'
        ).mock(
            return_value=httpx.Response(
                200, json={'data': waypoints_data['data'][0]}
            )
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-FARTHESTWAYPOINT'
        ).mock(
            return_value=httpx.Response(
                200, json={'data': waypoints_data['data'][2]}
            )
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-CLOSESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=expensive_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-FARTHESTWAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=iron_market_data)
        )
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        ).mock(
            return_value=httpx.Response(200, json=cheapest_market_data)
        )
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        agent_data['data']['credits'] = 100_000
        respx_mock.get('/my/agent').mock(
            return_value=httpx.Response(200, json=agent_data)
        )

        market_data = [m.data for m in ship.markets]
        pairs = snisp.markets.best_market_pairs(self.agent, ship, market_data)
        assert int(pairs[0].distance) == 70
        assert pairs[0].trade_symbol == 'PRECIOUS_STONES'
        assert pairs[0].import_market.symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert pairs[0].export_market.symbol == 'TEST-SYSTEM-WAYPOINT'


class MarketSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.invalid = False
        self.not_found = False

    def __call__(self, request, route):
        if self.invalid:
            return httpx.Response(
                400, json={'error': {'data': {'code': 404}}}
            )
        if self.not_found:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4603}}}
            )
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.invalid = False
        self.not_found = False


class MarketsSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': []})
        traits = request.url.params.get('traits')
        output = []
        for wp in self.data['data']:
            if any(i['symbol'] == traits for i in wp['traits']):
                output.append(wp)
        self.data['data'] = output
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)


class ShipyardsSideEffect:

    def __init__(self, *, data, waypoints):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_waypoints = waypoints
        self.waypoints = copy.deepcopy(self.orig_waypoints)

    def __call__(self, request, route):
        return httpx.Response(200, json=self.data)

    def waypoints_side_effect(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': []})
        traits = request.url.params.get('traits')
        output = []
        for wp in self.waypoints['data']:
            if any(i['symbol'] == traits for i in wp['traits']):
                output.append(wp)
        self.waypoints['data'] = output
        return httpx.Response(200, json=self.waypoints)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.waypoints = copy.deepcopy(self.orig_waypoints)
