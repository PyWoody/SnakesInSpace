import copy
import httpx
import json
import os
import pytest

import snisp

from . import DATA_DIR, GenericSideEffect


class TestShipyards:

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
        assert repr(ship.shipyards) == f'Shipyards({ship.agent!r}, ' \
                                       f'{ship.location})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_iter(self, respx_mock):
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        waypoints_data['data'][0]['traits'][0]['symbol'] = 'SHIPYARD'
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        with shipyards_side_effect:
            for shipyard in ship.shipyards:
                assert any(i.symbol == 'SHIPYARD' for i in shipyard.traits)
            shipyards = list(ship.shipyards)
            assert len(shipyards) == 1

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_autopurchase(self, respx_mock):
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        shipyards_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        for ship in shipyards_data['data']['ships']:
            if ship['type'] == 'SHIP_PROBE':
                ship['purchasePrice'] = 100_000
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoints_data['data']['traits'][0]['symbol'] = 'SHIPYARD'
        waypoints_data['data'] = [waypoints_data['data']]
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        shipyards_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/shipyard'
        )
        shipyards_route.side_effect = shipyards_side_effect
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_data['data']['nav']['status'] = 'IN_TRANSIT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        agent_side_effect = GenericSideEffect(agent_data)
        agent_route = respx_mock.get('/my/agent')
        agent_route.side_effect = agent_side_effect

        ships_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_ships.json'),
                encoding='utf8'
            )
        )
        fleet_side_effect = FleetSideEffect(ships_data)
        fleet_route = respx_mock.get('/my/ships')
        fleet_route.side_effect = fleet_side_effect

        ship_purchase_data = json.load(
            open(
                os.path.join(DATA_DIR, 'ship_purchase.json'),
                encoding='utf8'
            )
        )
        respx_mock.post('/my/ships').mock(
            return_value=httpx.Response(200, json=ship_purchase_data)
        )

        with fleet_side_effect as tmp:
            tmp.data['data'][0]['nav']['status'] = 'IN_ORBIT'
            tmp.data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')

            assert not ship.shipyards.autopurchase(ship_type='SHIP_PROBE')
            assert not ship.shipyards.autopurchase(
                ship_type='SHIP_REFINING_FREIGHTER'
            )

        with agent_side_effect as agent_tmp, fleet_side_effect as fleet_tmp:
            agent_tmp.data['data']['credits'] = 500_000
            agent = snisp.agent.Agent(symbol='testing', faction='testing')
            fleet_tmp.data['data'][0]['nav']['status'] = 'IN_ORBIT'
            fleet_tmp.data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            ship = agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.shipyards.autopurchase(
                ship_type='SHIP_PROBE', max_units=2
            )
            assert len(transactions) == 2
            for transaction in transactions:
                assert transaction.frame.symbol == 'FRAME_PROBE'

        with fleet_side_effect as tmp:
            tmp.data['data'][0]['nav']['status'] = 'IN_ORBIT'
            tmp.data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.SpaceAttributeError):
                ship.shipyards.autopurchase(ship_type='INVALID')

        with agent_side_effect as agent_tmp, fleet_side_effect as fleet_tmp:
            agent_tmp.data['data']['credits'] = 500_000
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.NoShipAtLocationError):
                list(ship.shipyards.autopurchase(ship_type='SHIP_PROBE'))


class TestShipyard:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_data(self, respx_mock):
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        shipyards_data['data']['symbol'] = 'TEST-SYSTEM-CLOSESTWAYPOINT'
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        waypoints_data['data'][0]['symbol'] = 'TEST-SYSTEM-CLOSESTWAYPOINT'
        waypoints_data['data'][0]['traits'][0]['symbol'] = 'SHIPYARD'
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        shipyards_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-CLOSESTWAYPOINT/shipyard'
        )
        shipyards_route.side_effect = shipyards_side_effect
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        shipyard = next(iter(ship.shipyards))

        assert shipyard.data.symbol == 'TEST-SYSTEM-CLOSESTWAYPOINT'
        assert shipyard.data.to_dict() == shipyards_data['data']

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_purchase(self, respx_mock):
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        shipyards_data['data']['symbol'] = 'TEST-SYSTEM-CLOSESTWAYPOINT'
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        waypoints_data['data'][0]['symbol'] = 'TEST-SYSTEM-CLOSESTWAYPOINT'
        waypoints_data['data'][0]['traits'][0]['symbol'] = 'SHIPYARD'
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        ships_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_ships.json'),
                encoding='utf8'
            )
        )
        for ship in ships_data['data']:
            ship['nav']['waypointSymbol'] = 'TEST-SYSTEM-INVALID'
            ship['nav']['status'] = 'IN_ORBIT'

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=ships_data)
        )

        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        shipyard = next(iter(ship.shipyards))

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            shipyard.purchase('INVALID')

        with ship_side_effect as tmp:
            tmp.data['data']['nav']['waypointSymbol'] = 'NOT-SYSTEM-WAYPOINT'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.NoShipAtLocationError):
                list(shipyard.purchase('SHIP_ORE_HOUND'))

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_transactions(self, respx_mock):
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        shipyards_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        waypoints_data['data'][0]['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        waypoints_data['data'][0]['traits'][0]['symbol'] = 'SHIPYARD'
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        shipyards_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/shipyard'
        )
        shipyards_route.side_effect = shipyards_side_effect
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        ships_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_ships.json'),
                encoding='utf8'
            )
        )
        fleet_side_effect = FleetSideEffect(ships_data)
        fleet_route = respx_mock.get('/my/ships')
        fleet_route.side_effect = fleet_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        shipyard = next(iter(ship.shipyards))

        with fleet_side_effect as tmp:
            tmp.data['data'][0]['nav']['status'] = 'IN_ORBIT'
            tmp.data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            transactions = list(shipyard.transactions())
            assert len(transactions) == 1
            assert transactions[0].price == 0

        with fleet_side_effect as tmp:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            shipyard = snisp.shipyards.Shipyard(self.agent, shipyard.to_dict())
            with pytest.raises(snisp.exceptions.NoShipAtLocationError):
                list(shipyard.transactions())


class TestShipyardShip:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_available_ships(self, respx_mock):
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        shipyards_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        waypoints_data['data'][0]['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        waypoints_data['data'][0]['traits'][0]['symbol'] = 'SHIPYARD'
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        shipyards_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/shipyard'
        )
        shipyards_route.side_effect = shipyards_side_effect
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        shipyard = next(iter(ship.shipyards))
        ships = list(shipyard.available_ships())
        assert len(ships) == 1

        ships = list(shipyard.available_ships('SHIP_EXPLORER'))
        assert len(ships) == 0

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            ships = list(shipyard.available_ships('invalid'))

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_purchase(self, respx_mock):
        shipyards_data = json.load(
            open(os.path.join(DATA_DIR, 'shipyards.json'), encoding='utf8')
        )
        shipyards_data['data']['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        waypoints_data['data'][0]['symbol'] = 'TEST-SYSTEM-WAYPOINT'
        waypoints_data['data'][0]['traits'][0]['symbol'] = 'SHIPYARD'
        shipyards_side_effect = ShipyardsSideEffect(
            data=shipyards_data, waypoints=waypoints_data
        )
        shipyards_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/shipyard'
        )
        shipyards_route.side_effect = shipyards_side_effect
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = shipyards_side_effect.waypoints_side_effect  # noqa: E501

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        agent_side_effect = GenericSideEffect(agent_data)
        agent_route = respx_mock.get('/my/agent')
        agent_route.side_effect = agent_side_effect

        ship_purchase_data = json.load(
            open(
                os.path.join(DATA_DIR, 'ship_purchase.json'),
                encoding='utf8'
            )
        )
        respx_mock.post('/my/ships').mock(
            return_value=httpx.Response(200, json=ship_purchase_data)
        )

        with agent_side_effect as tmp:
            tmp.data['data']['credits'] = 500_000
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            shipyard = next(iter(ship.shipyards))
            shipyard_ship = next(iter((shipyard.available_ships())))
            purchase = shipyard_ship.purchase()
            assert purchase.frame.symbol == 'FRAME_PROBE'

        with agent_side_effect as tmp:
            tmp.data['data']['credits'] = 500
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            shipyard = next(iter(ship.shipyards))
            shipyard_ship = next(iter((shipyard.available_ships())))
            assert not shipyard_ship.purchase(buffer=500_000)


class ShipyardsSideEffect:

    def __init__(self, *, data, waypoints):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_waypoints = waypoints
        self.waypoints = copy.deepcopy(self.orig_waypoints)

    def __call__(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': {}})
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


class FleetSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': {}})
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
