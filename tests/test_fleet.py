import copy
import httpx
import inspect
import itertools
import json
import os
import pytest

from datetime import datetime, timedelta, timezone
from respx.patterns import M

import snisp

from . import DATA_DIR, GenericSideEffect, attribute_test


class TestFleet:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    def test_repr(self, respx_mock):
        assert repr(self.agent.fleet) == f'Fleet({self.agent!r})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list_drones(self, respx_mock):
        drone_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_drones.json'),
                encoding='utf8'
            )
        )

        respx_mock.get(
            '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=drone_data)
        )
        respx_mock.get(
            '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        drones = self.agent.fleet.drones()
        assert inspect.isgenerator(drones)
        drones = list(drones)
        assert len(drones) == 1
        assert drones[0].frame.symbol == 'FRAME_DRONE'
        attribute_test(drones[0], drone_data['data'][0])

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list_ships(self, respx_mock):
        ship_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_ships.json'),
                encoding='utf8'
            )
        )

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        ships = self.agent.fleet.ships()
        assert inspect.isgenerator(ships)
        ships = list(ships)
        assert len(ships) == 2
        assert ships[0].frame.symbol == 'FRAME_FREIGHTER'
        assert ships[1].frame.symbol == 'FRAME_SHUTTLE'
        attribute_test(ships[0], ship_data['data'][0])
        attribute_test(ships[1], ship_data['data'][1])

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list_probes(self, respx_mock):
        probe_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_probes.json'),
                encoding='utf8'
            )
        )

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=probe_data)
        )
        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        probes = self.agent.fleet.probes()
        assert inspect.isgenerator(probes)
        probes = list(probes)
        assert len(probes) == 1
        assert probes[0].frame.symbol == 'FRAME_PROBE'
        attribute_test(probes[0], probe_data['data'][1])

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list_siphon_drones(self, respx_mock):
        drone_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_siphon_drones.json'),
                encoding='utf8'
            )
        )

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=drone_data)
        )
        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        siphon_drones = self.agent.fleet.siphon_drones()
        assert inspect.isgenerator(siphon_drones)
        siphon_drones = list(siphon_drones)
        assert len(siphon_drones) == 2
        for j_drone, drone in zip(drone_data['data'], siphon_drones):
            assert drone == snisp.fleet.Ship(self.agent, j_drone)
            attribute_test(drone, j_drone)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list_mining_drones(self, respx_mock):
        drone_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_mining_drones.json'),
                encoding='utf8'
            )
        )

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=drone_data)
        )
        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        mining_drones = self.agent.fleet.mining_drones()
        assert inspect.isgenerator(mining_drones)
        mining_drones = list(mining_drones)
        assert len(mining_drones) == 2
        for j_drone, drone in zip(drone_data['data'], mining_drones):
            assert drone == snisp.fleet.Ship(self.agent, j_drone)
            attribute_test(drone, j_drone)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list_freighters(self, respx_mock):
        freighter_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_freighters.json'),
                encoding='utf8'
            )
        )

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=freighter_data)
        )
        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        freighters = self.agent.fleet.freighters()
        assert inspect.isgenerator(freighters)
        freighters = list(freighters)
        assert len(freighters) == 1
        attribute_test(freighters[0], freighter_data['data'][0])

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list_shuttles(self, respx_mock):
        shuttle_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_shuttles.json'),
                encoding='utf8'
            )
        )

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=shuttle_data)
        )
        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        shuttles = self.agent.fleet.shuttles()
        assert inspect.isgenerator(shuttles)
        shuttles = list(shuttles)
        assert len(shuttles) == 2
        sentinel = object()
        for j_ship, r_ship in itertools.zip_longest(
            shuttle_data['data'], self.agent.fleet, fillvalue=sentinel
        ):
            assert j_ship is not sentinel
            assert r_ship is not sentinel
            assert j_ship == r_ship.to_dict()
            ship = snisp.fleet.Ship(self.agent, j_ship)
            assert ship == r_ship
            attribute_test(ship, r_ship.to_dict())
            attribute_test(ship, j_ship)


class TestFleetShip:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_ship_info(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship == snisp.fleet.Ship(self.agent, ship_data['data'])
        attribute_test(ship, ship_data['data'])

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_markets(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        market = snisp.markets.Markets(ship, ship.location)
        assert ship.markets.ship == ship
        assert ship.markets.location == market.location
        assert str(ship.markets) == str(market)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_shipyards(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        shipyard = snisp.shipyards.Shipyards(ship, ship.location)
        assert ship.shipyards.ship == ship
        assert ship.shipyards.location == shipyard.location
        assert str(ship.shipyards) == str(shipyard)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_refresh(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship == ship.refresh()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_refine(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['modules'].append(
            {'symbol': 'MODULE_MINERAL_PROCESSOR_I'}
        )
        refine_data = json.load(
            open(os.path.join(DATA_DIR, 'refine.json'), encoding='utf8')
        )
        refine_side_effect = RefineSideEffect(data=refine_data, ship=ship_data)
        refine_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/refine')
        refine_route.side_effect = refine_side_effect

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        # Check failed attempts don't cause errors
        with refine_side_effect as tmp:
            tmp.data['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'
            tmp.data['data']['cargo']['inventory'][0]['units'] = 10
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refine('IRON')
            assert ship.cargo.inventory[0].symbol == 'IRON_ORE'
            assert ship.cargo.inventory[0].units == 10
            assert len(ship.cargo.inventory) == 1

        with refine_side_effect as tmp:
            tmp.ship['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'
            tmp.ship['data']['cargo']['inventory'][0]['units'] = 40
            tmp.data['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'
            tmp.data['data']['cargo']['inventory'][0]['units'] = 40
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refine('IRON')
            assert ship.cargo.inventory[0].symbol == 'IRON_ORE'
            assert ship.cargo.inventory[0].units == 10
            assert ship.cargo.inventory[1].symbol == 'IRON'
            assert ship.cargo.inventory[1].units == 1

        # 4237: ShipInvalidRefineryGoodError,
        with pytest.raises(snisp.exceptions.ShipInvalidRefineryGoodError):
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refine('INVALID')

        # 4239: ShipMissingRefineryError,
        with refine_side_effect as tmp:
            tmp.ship['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'
            tmp.ship['data']['cargo']['inventory'][0]['units'] = 40
            tmp.ship['data']['modules'] = []
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ShipMissingRefineryError
            ):
                ship.refine('IRON')

        with refine_side_effect as tmp:
            tmp.ship['data']['cargo']['inventory'][0]['units'] = 10
            tmp.ship['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refine('IRON')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_refuel(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['fuel']['current'] = 0
        ship_data['data']['fuel']['capacity'] = 400
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        refuel_data = json.load(
            open(os.path.join(DATA_DIR, 'refuel.json'), encoding='utf8')
        )
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )
        refuel_side_effect = RefuelSideEffect(
            data=refuel_data, ship=ship_data, waypoint=waypoint_data
        )
        refuel_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/refuel')
        refuel_route.side_effect = refuel_side_effect

        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = refuel_side_effect.ship_route

        with refuel_side_effect as tmp:
            tmp.data['data']['fuel']['current'] = 0
            tmp.data['data']['fuel']['capacity'] = 400
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refuel()
            assert ship.fuel.current == 400
            assert ship.fuel.capacity == 400

        # From cargo
        with refuel_side_effect as tmp:
            tmp.data['data']['fuel']['current'] = 100
            fuel_cargo = {'symbol': 'FUEL', 'units': 300}
            tmp.ship['data']['cargo']['inventory'] = []
            tmp.ship['data']['cargo']['inventory'].append(fuel_cargo)
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refuel(from_cargo=True)
            assert ship.fuel.current == 400
            assert ship.fuel.capacity == 400
            assert ship.cargo.inventory == []

        with refuel_side_effect as tmp:
            tmp.data['data']['fuel']['current'] = 100
            fuel_cargo = {'symbol': 'FUEL', 'units': 400}
            tmp.ship['data']['cargo']['inventory'] = []
            tmp.ship['data']['cargo']['inventory'].append(fuel_cargo)
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refuel(from_cargo=True)
            assert ship.fuel.current == 400
            assert ship.fuel.capacity == 400
            assert ship.cargo.inventory[0].to_dict() == {
                'symbol': 'FUEL', 'units': 100
            }

        with refuel_side_effect as tmp:
            tmp.data['data']['fuel']['current'] = 0
            fuel_cargo = {'symbol': 'FUEL', 'units': 300}
            tmp.ship['data']['cargo']['inventory'] = []
            tmp.ship['data']['cargo']['inventory'].append(fuel_cargo)
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refuel(from_cargo=True)
            assert ship.fuel.current == 300
            assert ship.fuel.capacity == 400
            assert ship.cargo.inventory == []

        # 4218: ShipCargoMissingError,
        with refuel_side_effect as tmp:
            with pytest.raises(snisp.exceptions.ShipCargoMissingError):
                ship = self.agent.fleet('TEST_SHIP_SYMBOL')
                ship.refuel(from_cargo=True)

        # 4225: ShipRefuelDockedError,

        # 4226: ShipRefuelInvalidWaypointError,
        with refuel_side_effect as tmp:
            tmp.waypoint['data']['type'] = 'INVALID'
            with pytest.raises(
                snisp.exceptions.ShipRefuelInvalidWaypointError
            ):
                ship = self.agent.fleet('TEST_SHIP_SYMBOL')
                ship.refuel()

        # Specify units
        with refuel_side_effect as tmp:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.refuel(units=10)
            assert ship.fuel.current == 10

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fleet_list(self, respx_mock):
        fleet_data = json.load(
            open(os.path.join(DATA_DIR, 'fleet_list.json'), encoding='utf8')
        )

        respx_mock.get(
                '/my/ships', params={'page': 1, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json=fleet_data)
        )
        respx_mock.get(
                '/my/ships', params={'page': 2, 'limit': 20}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        sentinel = object()
        for j_ship, r_ship in itertools.zip_longest(
            fleet_data['data'], self.agent.fleet, fillvalue=sentinel
        ):
            assert j_ship is not sentinel
            assert r_ship is not sentinel
            assert j_ship == r_ship.to_dict()
            ship = snisp.fleet.Ship(self.agent, j_ship)
            assert ship == r_ship
            attribute_test(ship, r_ship.to_dict())
            attribute_test(ship, j_ship)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_repr(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert repr(ship) == f'Ship({ship_data["data"]!r})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_navigate(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_data['data']['nav']['waypointSymbol'] = 'STARTED'
        ship_data['data']['fuel']['current'] = 100
        ship_data['data']['fuel']['capacity'] = 400
        ship_data['data']['fuel']['consumed']['amount'] = 0
        ship_data['data']['fuel']['consumed']['timestamp'] = 0
        nav_data = json.load(
            open(os.path.join(DATA_DIR, 'navigate.json'), encoding='utf8')
        )
        nav_data['data']['fuel']['current'] = 1
        nav_data['data']['fuel']['consumed']['amount'] = 99
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['symbol'] = 'DEST-SYSTEM-WAYPOINT'
        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])

        navigate_side_effect = NavigateSideEffect(
            data=nav_data, ship=ship_data
        )
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = navigate_side_effect.ship_side_effect
        navigate_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/navigate')
        navigate_route.side_effect = navigate_side_effect

        with navigate_side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.navigate(waypoint)
            assert ship.fuel.current == 1
            assert ship.fuel.consumed.amount == 99
            assert ship.nav.waypoint_symbol == 'DEST-SYSTEM-WAYPOINT'

        with pytest.raises(Exception):
            waypoint_data['data']['symbol'] = 'INVALID'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.navigate(waypoint)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_autopilot(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-STARTED'
        ship_data['data']['fuel']['current'] = 100
        ship_data['data']['fuel']['capacity'] = 400
        ship_data['data']['fuel']['consumed']['amount'] = 0
        ship_data['data']['fuel']['consumed']['timestamp'] = 0
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect
        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        refuel_data = json.load(
              open(os.path.join(DATA_DIR, 'refuel.json'), encoding='utf8')
        )
        nav_data = json.load(
            open(os.path.join(DATA_DIR, 'navigate.json'), encoding='utf8')
        )
        nav_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        nav_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-DESTINATION'
        navigate_side_effect = AutoPilotSideEffect(
            data=nav_data,
            ship=ship_data,
            orbit=orbit_data,
            refuel=refuel_data,
            dock=dock_data,
        )
        navigate_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/navigate')
        navigate_route.side_effect = navigate_side_effect

        orbit_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit')
        orbit_route.side_effect = navigate_side_effect.orbit_side_effect

        flight_mode_route = respx_mock.patch('/my/ships/TEST_SHIP_SYMBOL/nav')
        flight_mode_route.side_effect = navigate_side_effect.update_flight_mode

        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['symbol'] = 'TEST-SYSTEM-DESTINATION'
        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])

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

        refuel_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/refuel')
        refuel_route.side_effect = navigate_side_effect.refuel_side_effect

        dock_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock')
        dock_route.side_effect = navigate_side_effect.dock_side_effect

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

        # regular
        with navigate_side_effect as nav_tmp:
            nav_tmp.data['data']['fuel']['current'] = 1
            nav_tmp.data['data']['fuel']['consumed']['amount'] = 99
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            attribute_test(ship, ship_data['data'])
            ship.autopilot(waypoint)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # regular but already drifting
        with navigate_side_effect as nav_tmp:
            nav_tmp.ship['data']['nav']['flightMode'] = 'DRIFT'
            nav_tmp.data['data']['fuel']['current'] = 1
            nav_tmp.data['data']['fuel']['consumed']['amount'] = 99
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            attribute_test(ship, ship_data['data'])
            ship.autopilot(waypoint)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # regular but already drifting w/ callback
        with navigate_side_effect as nav_tmp:
            nav_tmp.ship['data']['nav']['flightMode'] = 'DRIFT'
            nav_tmp.data['data']['fuel']['current'] = 1
            nav_tmp.data['data']['fuel']['consumed']['amount'] = 99
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            attribute_test(ship, ship_data['data'])
            ship.autopilot(waypoint, done_callback=print)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # regular w/ callback
        with navigate_side_effect as nav_tmp:
            nav_tmp.data['data']['fuel']['current'] = 1
            nav_tmp.data['data']['fuel']['consumed']['amount'] = 99
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            attribute_test(ship, ship_data['data'])
            ship.autopilot(waypoint, done_callback=print)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # same location as dest
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            ship_tmp.data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-DESTINATION'  # noqa: E501
            nav_tmp.data['data']['fuel']['current'] = 1
            nav_tmp.data['data']['fuel']['consumed']['amount'] = 99
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # starting waypoint is closest fuel
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            ship_tmp.data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-CLOSESTFUEL'  # noqa: E501
            nav_tmp.ship['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-CLOSESTFUEL'  # noqa: E501
            nav_tmp.data['data']['fuel']['current'] = 1
            nav_tmp.data['data']['fuel']['consumed']['amount'] = 99
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # starting waypoint is closest fuel and already drifting
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            ship_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            ship_tmp.data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-FARTHESTFUEL'  # noqa: E501
            nav_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            nav_tmp.ship['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-FARTHESTFUEL'  # noqa: E501
            nav_tmp.data['data']['fuel']['current'] = 1
            nav_tmp.data['data']['fuel']['consumed']['amount'] = 99
            nav_tmp.always_fail = True
            with pytest.raises(
                snisp.exceptions.NavigateInsufficientFuelError
            ):
                ship = self.agent.fleet('TEST_SHIP_SYMBOL')
                ship.autopilot(waypoint)

        # Double-check at the end if this is still need. Useda as a template
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            nav_tmp.max_fails = 3
            ship_tmp.data['data']['fuel']['current'] = 300
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # Everything from here on is "working"
        # but reliant on max_fail counting, which is kind of lame

        # Fail until you navigate to fuel
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            # Stop refueling attempts
            nav_tmp.ship['data']['nav']['route']['destination']['type'] = 'IGNORE'  # noqa: E501
            nav_tmp.max_fails = 3
            ship_tmp.data['data']['fuel']['current'] = 300
            nav_tmp.data['data']['fuel']['current'] = 300
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # Fail until you navigate to fuel w/ callback
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            # Stop refueling attempts
            nav_tmp.ship['data']['nav']['route']['destination']['type'] = 'IGNORE'  # noqa: E501
            nav_tmp.max_fails = 3
            ship_tmp.data['data']['fuel']['current'] = 300
            nav_tmp.data['data']['fuel']['current'] = 300
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint, done_callback=print)
            assert ship.nav.waypoint_symbol == 'TEST-SYSTEM-DESTINATION'

        # Failed to IndexError, Can't refuel
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            # Stop refueling attempts
            nav_tmp.ship['data']['nav']['route']['destination']['type'] = 'INVALID'  # noqa: E501
            nav_tmp.max_fails = 10
            ship_tmp.data['data']['fuel']['current'] = 300
            nav_tmp.data['data']['fuel']['current'] = 300
            with pytest.raises(
                snisp.exceptions.NavigateInsufficientFuelError
            ):
                ship = self.agent.fleet('TEST_SHIP_SYMBOL')
                ship.autopilot(waypoint)

        # 423, IndexError but can make it
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            nav_tmp.max_fails = 6
            ship_tmp.data['data']['fuel']['current'] = 300
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint)

        # 423, IndexError but can make it w/ callback
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            nav_tmp.max_fails = 6
            ship_tmp.data['data']['fuel']['current'] = 300
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint, done_callback=print)

        # Greater than last_successful_fueling but can still make it
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            nav_tmp.max_fails = 3
            nav_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            ship_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            ship_tmp.data['data']['fuel']['current'] = 300
            ship_tmp.data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-NEXTCLOSESTFUEL'  # noqa: E501
            nav_tmp.ship['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-NEXTCLOSESTFUEL'  # noqa: E501
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint)

        # Greater than last_successful_fueling
        # but can still make it w/ callback
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            nav_tmp.max_fails = 3
            nav_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            ship_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            ship_tmp.data['data']['fuel']['current'] = 300
            ship_tmp.data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-NEXTCLOSESTFUEL'  # noqa: E501
            nav_tmp.ship['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-NEXTCLOSESTFUEL'  # noqa: E501
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.autopilot(waypoint, done_callback=print)

        # At closest fuel, already drifting
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            nav_tmp.max_fails = 3
            nav_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            ship_tmp.data['data']['nav']['flightMode'] = 'DRIFT'
            ship_tmp.data['data']['fuel']['current'] = 300
            ship_tmp.data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-CLOSESTFUEL'  # noqa: E501
            nav_tmp.ship['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-CLOSESTFUEL'  # noqa: E501
            with pytest.raises(
                snisp.exceptions.NavigateInsufficientFuelError
            ):
                ship = self.agent.fleet('TEST_SHIP_SYMBOL')
                ship.autopilot(waypoint)

        # No close fuel. SOL, buddy
        with navigate_side_effect as nav_tmp, ship_side_effect as ship_tmp:
            nav_tmp.max_fails = 10
            ship_tmp.data['data']['fuel']['current'] = 300
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.NavigateInsufficientFuelError
            ):
                ship = self.agent.fleet('TEST_SHIP_SYMBOL')
                ship.autopilot(waypoint)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_arrival(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        then = datetime.now(timezone.utc) + timedelta(minutes=1)
        ship_data['data']['nav']['status'] = 'IN_TRANSIT'
        ship_data['data']['nav']['route']['arrival'] = str(then)
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert 59 <= ship.arrival < 60

        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.arrival == 0

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_location(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        location = snisp.systems.Location(self.agent, ship_data['data'])
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.location == location
        assert ship.location.sector == 'TEST'
        assert ship.location.system == 'TEST-SYSTEM'
        assert ship.location.waypoint == 'TEST-SYSTEM-WAYPOINT'

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['headquarters'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        location = snisp.systems.Location(self.agent, ship_data['data'])
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.location.sector == 'TEST'
        assert ship.location.system == 'TEST-SYSTEM'
        assert ship.location.waypoint == 'TEST-SYSTEM-WAYPOINT'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_waypoints(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        location = snisp.systems.Location(self.agent, ship_data['data'])
        waypoints = snisp.waypoints.Waypoints(self.agent, location)
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert str(ship.waypoints) == str(waypoints)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_systems(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        system = snisp.systems.System(self.agent)
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert str(ship.system) == str(system)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_at_market(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        # Waypoint
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['symbol'] = 'TOTALLY-DIFFERENT-WAYPOINT'
        waypoint_data['data']['traits'][0]['symbol'] = 'MARKETPLACE'
        waypoint_side_effect = GenericSideEffect(waypoint_data)
        waypoint_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT'
        )
        waypoint_route.side_effect = waypoint_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with waypoint_side_effect as tmp:
            tmp.data['data']['traits'][0]['symbol'] = 'INVALID'
            assert not ship.at_market

        with ship_side_effect as tmp:
            tmp.data['data']['nav']['status'] = 'IN_TRANSIT'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with waypoint_side_effect as tmp:
                tmp.data['data']['traits'][0]['symbol'] = 'INVALID'
                assert not ship.at_market

        # Navigate
        navigate_data = json.load(
            open(os.path.join(DATA_DIR, 'navigate.json'), encoding='utf8')
        )
        navigate_data['data']['nav']['status'] = 'IN_TRANSIT'
        navigate_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        navigate_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/navigate').mock(
            return_value=httpx.Response(200, json=navigate_data)
        )

        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        ship.navigate(waypoint)
        assert ship.nav.status == 'IN_TRANSIT'
        ship.orbit()
        assert ship.at_market

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_at_shipyard(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        # Waypoint
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['systemSymbol'] = 'TEST-SYSTEM'
        waypoint_data['data']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        waypoint_side_effect = GenericSideEffect(waypoint_data)
        waypoint_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT'
        )
        waypoint_route.side_effect = waypoint_side_effect

        # Navigate
        navigate_data = json.load(
            open(os.path.join(DATA_DIR, 'navigate.json'), encoding='utf8')
        )
        navigate_data['data']['nav']['status'] = 'IN_TRANSIT'
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/navigate').mock(
            return_value=httpx.Response(200, json=navigate_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert not ship.at_shipyard

        with ship_side_effect as tmp:
            tmp.data['data']['nav']['status'] = 'IN_TRANSIT'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            assert not ship.at_shipyard

        with waypoint_side_effect as tmp:
            tmp.data['data']['symbol'] = 'OTHER-SYSTEM-WAYPOINT'
            tmp.data['data']['traits'][0]['symbol'] = 'SHIPYARD'
            waypoint = snisp.waypoints.Waypoint(self.agent, tmp.data['data'])
            ship.navigate(waypoint)
            # The call to `orbit` never happens for some reason as
            # the nav.status gets changed in the process? Maybe something
            # with the deorators
            # Regardless, status will stay as IN_TRANSIT if not called
            ship.orbit()
            assert ship.at_shipyard

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_can_mine(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'mining_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.can_mine

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_can_siphon(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'siphon_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.can_siphon

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_can_survey(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.can_survey

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_can_refine_gas(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'siphon_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.can_refine_gas

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_can_refine_ore(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'mining_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.can_refine_ore

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cannot_mine(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'siphon_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert not ship.can_mine

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cannot_survey(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'siphon_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert not ship.can_survey

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cannot_siphon(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'mining_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert not ship.can_siphon

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cannot_refine_gas(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'mining_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert not ship.can_refine_gas

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_cannot_refine_ore(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'siphon_drone.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert not ship.can_refine_ore

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_closest(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        close_waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        close_waypoint = snisp.waypoints.Waypoint(
            self.agent, close_waypoint_data['data']
        )
        far_waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        far_waypoint_data['data']['x'] = 100
        far_waypoint_data['data']['y'] = 100
        far_waypoint = snisp.waypoints.Waypoint(
            self.agent, far_waypoint_data['data']
        )
        closest = ship.closest([far_waypoint, close_waypoint])
        assert closest is close_waypoint
        assert ship.closest([]) is None

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_closest_fuel(self, respx_mock):
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
        closest_fuel = ship.closest_fuel()
        assert closest_fuel.to_dict() == fuel_stations_data['data'][0]
        assert closest_fuel.to_dict() != fuel_stations_data['data'][1]

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_farthest(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        close_waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        close_waypoint = snisp.waypoints.Waypoint(
            self.agent, close_waypoint_data['data']
        )
        far_waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        far_waypoint_data['data']['x'] = 100
        far_waypoint_data['data']['y'] = 100
        far_waypoint = snisp.waypoints.Waypoint(
            self.agent, far_waypoint_data['data']
        )
        farthest = ship.farthest([far_waypoint, close_waypoint])
        assert farthest is far_waypoint
        assert ship.farthest([]) is None

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_dock(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.nav.status != 'DOCKED'
        ship.dock()
        assert ship.nav.status == 'DOCKED'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_update_flight_mode(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'DOCKED'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        nav_data = json.load(
            open(os.path.join(DATA_DIR, 'update_nav.json'), encoding='utf8')
        )
        flight_mode_side_effect = FlightModeSideEffect(nav_data)
        navigate_route = respx_mock.patch('/my/ships/TEST_SHIP_SYMBOL/nav')
        navigate_route.side_effect = flight_mode_side_effect

        with flight_mode_side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            assert ship.nav.flight_mode == 'CRUISE'
            ship.update_flight_mode('STEALTH')
            assert ship.nav.flight_mode == 'STEALTH'
            assert ship.nav.flight_mode != 'CRUISE'

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            ship.update_flight_mode('INVALID')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_orbit(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'DOCKED'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        assert ship.nav.status != 'IN_ORBIT'
        ship.orbit()
        assert ship.nav.status == 'IN_ORBIT'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_siphon(self, respx_mock):
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['type'] = 'GAS_GIANT'
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'DOCKED'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        siphon_data = json.load(
            open(os.path.join(DATA_DIR, 'siphon.json'), encoding='utf8')
        )
        side_effect = SiphonSideEffect(
                data=siphon_data, ship=ship_data, waypoint=waypoint_data
            )
        siphon_route = respx_mock.post(
            '/my/ships/TEST_SHIP_SYMBOL/siphon'
        )
        siphon_route.side_effect = side_effect

        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )

        # Check siphon in cargo
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        siphon = ship.siphon()
        assert siphon.symbol == ship.cargo.inventory[0].symbol
        assert siphon.units == ship.cargo.inventory[0].units

        # Check siphon till full
        with side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            for _ in range(ship.cargo.capacity):
                ship.siphon()
            assert ship.cargo.units == ship.cargo.capacity

        # Check cooldown is transferred
        # Cooldown is caught in the retry decorator, so don't tempt it
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['cooldown']['totalSeconds'] = 40
            tmp.data['data']['cooldown']['remainingSeconds'] = 39
            ship.siphon()
            assert ship.cooldown.totalSeconds == 40
            assert ship.cooldown.remainingSeconds == 39

        # 4258: ShipMissingGasSiphonsError,
        with side_effect as tmp:
            tmp.ship['data']['mounts'] = []
            with pytest.raises(
                snisp.exceptions.ShipMissingGasSiphonsError
            ):
                ship.siphon()

        # Check can't siphon if already full
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['cargo']['units'] = 40
            with pytest.raises(
                snisp.exceptions.ShipCargoExceedsLimitError
            ):
                ship.siphon()

        # Check can't siphon at non-gas giant waypoint
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.waypoint['data']['type'] = 'STATION'
            with pytest.raises(
                snisp.exceptions.ShipSiphonInvalidWaypointError
            ):
                ship.siphon()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_extract(self, respx_mock):
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['type'] = 'ASTEROID'
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'DOCKED'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        extraction_data = json.load(
            open(os.path.join(DATA_DIR, 'extraction.json'), encoding='utf8')
        )
        side_effect = ExtractionSideEffect(
            data=extraction_data, ship=ship_data, waypoint=waypoint_data
        )
        extraction_route = respx_mock.post(
            '/my/ships/TEST_SHIP_SYMBOL/extract'
        )
        extraction_route.side_effect = side_effect

        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )

        # Check extraction in cargo
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        extraction = ship.extract()
        assert extraction.symbol == ship.cargo.inventory[0].symbol
        assert extraction.units == ship.cargo.inventory[0].units

        # Check extract till full
        with side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            for _ in range(ship.cargo.capacity):
                ship.extract()
            assert ship.cargo.units == ship.cargo.capacity

        # Check cooldown is transferred
        # Cooldown is caught in the retry decorator, so don't tempt it
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['cooldown']['totalSeconds'] = 40
            tmp.data['data']['cooldown']['remainingSeconds'] = 39
            ship.extract()
            assert ship.cooldown.totalSeconds == 40
            assert ship.cooldown.remainingSeconds == 39

        # Check can't extract if already full
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['cargo']['units'] = 40
            with pytest.raises(
                snisp.exceptions.ShipCargoExceedsLimitError
            ):
                ship.extract()

        # Check can't extract at non-asteroid waypoint
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.waypoint['data']['type'] = 'STATION'
            with pytest.raises(
                snisp.exceptions.ShipExtractInvalidWaypointError
            ):
                ship.extract()

        # 4243: ShipMissingMiningLasersError,
        with side_effect as tmp:
            tmp.ship['data']['mounts'] = []
            with pytest.raises(
                snisp.exceptions.ShipMissingMiningLasersError
            ):
                ship.extract()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_scan(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = side_effect
        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )
        scan_data = json.load(
            open(os.path.join(DATA_DIR, 'scan_ships.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/scan/ships').mock(
            return_value=httpx.Response(200, json=scan_data)
        )

        with side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            assert snisp.utils.ilen(ship.scan()) == 2
            scans = list(ship.scan())
            assert scans[0].symbol == 'TEST-SCAN-SHIP-01'
            assert scans[1].symbol == 'TEST-SCAN-SHIP-02'
            assert ship.cooldown.total_seconds == 60
            assert ship.cooldown.remaining_seconds == 59

        # Cooldown is caught in the decorator
        # 4000: CooldownConflictError,

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_extract_with_survey(self, respx_mock):
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['type'] = 'ASTEROID'
        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])

        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'DOCKED'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        extraction_data = json.load(
            open(os.path.join(DATA_DIR, 'extraction.json'), encoding='utf8')
        )
        extract_side_effect = ExtractionSideEffect(
            data=extraction_data, ship=ship_data, waypoint=waypoint_data
        )
        extraction_route = respx_mock.post(
            '/my/ships/TEST_SHIP_SYMBOL/extract/survey'
        )
        extraction_route.side_effect = extract_side_effect

        survey_data = json.load(
            open(os.path.join(DATA_DIR, 'survey.json'), encoding='utf8')
        )
        expires = str(datetime.now(timezone.utc) + timedelta(hours=1))
        for survey in survey_data['data']['surveys']:
            survey['expiration'] = expires
        survey_side_effect = GenericSideEffect(survey_data)
        survey_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/survey')
        survey_route.side_effect = survey_side_effect

        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )
        navigate_data = json.load(
            open(os.path.join(DATA_DIR, 'navigate.json'), encoding='utf8')
        )
        navigate_data['data']['nav']['status'] = 'IN_TRANSIT'
        navigate_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        navigate_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        navigate_data['data']['nav']['route']['destination']['type'] = \
            'ASTEROID'
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/navigate').mock(
            return_value=httpx.Response(200, json=navigate_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        ship.navigate(waypoint)
        survey = ship.waypoints.survey()

        # Extraction
        extraction = ship.extract_with_survey(survey)
        assert extraction.symbol == ship.cargo.inventory[0].symbol
        assert extraction.units == ship.cargo.inventory[0].units

        # Expired survey
        with survey_side_effect as tmp:
            expires = str(datetime.now(timezone.utc) - timedelta(hours=1))
            for survey in tmp.data['data']['surveys']:
                survey['expiration'] = expires
            with pytest.raises(
                snisp.exceptions.ShipSurveyExpirationError
            ):
                ship.extract_with_survey(
                    snisp.waypoints.Survey(self.agent, tmp.data['data'])
                )

        # Cooldown
        # Cooldown is caught in the retry decorator, so don't tempt it
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        ship.navigate(waypoint)
        survey = ship.waypoints.survey()
        with extract_side_effect as tmp:
            tmp.data['data']['cooldown']['totalSeconds'] = 40
            tmp.data['data']['cooldown']['remainingSeconds'] = 39
            ship.extract_with_survey(survey)
            assert ship.cooldown.totalSeconds == 40
            assert ship.cooldown.remainingSeconds == 39

        # Check only one survey was sent
        with pytest.raises(snisp.exceptions.ShipSurveyVerificationError):
            ship.extract_with_survey([survey, survey])

        # Check at Asteroid
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with extract_side_effect as tmp:
            tmp.waypoint['data']['type'] = 'STATION'
            with pytest.raises(
                snisp.exceptions.ShipExtractInvalidWaypointError
            ):
                ship.extract_with_survey(survey)

        # Check extract till full
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with extract_side_effect:
            for _ in range(ship.cargo.capacity):
                ship.extract_with_survey(survey)
            assert ship.cargo.units == ship.cargo.capacity

        # Check can't extract if already full
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with extract_side_effect as tmp:
            tmp.data['data']['cargo']['units'] = 40
            with pytest.raises(
                snisp.exceptions.ShipCargoExceedsLimitError
            ):
                ship.extract_with_survey(survey)

        # Malformed surveys
        with pytest.raises(snisp.exceptions.ShipSurveyVerificationError):
            ship.extract_with_survey(None)
        with pytest.raises(snisp.exceptions.ShipSurveyVerificationError):
            bad_survey = survey.to_dict()
            del bad_survey['surveys'][0]['symbol']
            ship.extract_with_survey(
                snisp.waypoints.Survey(self.agent, bad_survey)
            )

        # 4258: ShipMissingMiningLasersError,
        with extract_side_effect as tmp:
            tmp.ship['data']['mounts'] = []
            with pytest.raises(
                snisp.exceptions.ShipMissingMiningLasersError
            ):
                ship.extract_with_survey(survey)

        # 4224: ShipSurveyExhaustedError
        with extract_side_effect as tmp:
            bad_survey = survey.to_dict()
            for survey in bad_survey['surveys']:
                survey['deposits'] = []
            with pytest.raises(
                snisp.exceptions.ShipSurveyExhaustedError
            ):
                ship.extract_with_survey(
                    snisp.waypoints.Survey(self.agent, bad_survey)
                )

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_updated_mounts(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        mount_data = json.load(
            open(os.path.join(DATA_DIR, 'mount.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL/mounts').mock(
            return_value=httpx.Response(200, json=mount_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        mounts = ship.updated_mounts()
        assert mounts == snisp.fleet.Mounts(self.agent, mount_data['data'])

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_remove_mount(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        mount_data = json.load(
            open(os.path.join(DATA_DIR, 'mount.json'), encoding='utf8')
        )
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )
        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['traits'][0]['symbol'] = 'SHIPYARD'
        mount_side_effect = MountsSideEffect(
            data=mount_data,
            waypoint=waypoint_data,
            agent=agent_data,
        )
        mount_route = respx_mock.post(
            '/my/ships/TEST_SHIP_SYMBOL/mounts/remove'
        )
        mount_route.side_effect = mount_side_effect.remove

        with mount_side_effect as tmp:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.remove_mount('MOUNT_GAS_SIPHON_II')
            assert len(ship.mounts) == 1
            assert not any(
                i.symbol == 'MOUNT_GAS_SIPHON_II' for i in ship.mounts
            )

        # 4248: ShipMountInsufficientCreditsError,
        # Check credits
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with mount_side_effect as tmp:
            tmp.agent['data']['credits'] = 0
            with pytest.raises(
                snisp.exceptions.ShipMountInsufficientCreditsError
            ):
                ship.remove_mount('MOUNT_GAS_SIPHON_II')

        # 4247: ShipMissingMountError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with mount_side_effect as tmp:
            del tmp.data['data']['mounts'][1]
            with pytest.raises(snisp.exceptions.ShipMissingMountError):
                ship.remove_mount('MOUNT_GAS_SIPHON_II')

        # 4251: ShipMissingMountsError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with mount_side_effect as tmp:
            tmp.data['data']['mounts'] = []
            with pytest.raises(snisp.exceptions.ShipMissingMountsError):
                ship.remove_mount('MOUNT_GAS_SIPHON_II')

        # 4246: ShipMountNoShipyardError, (not at shipyard)
        # Check at shipyard
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with mount_side_effect as tmp:
            tmp.waypoint['data']['traits'][0]['symbol'] = 'INVALID'
            with pytest.raises(snisp.exceptions.ShipMountNoShipyardError):
                ship.remove_mount('MOUNT_GAS_SIPHON_II')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_install_mount(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['mounts'] = []

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['traits'][0]['symbol'] = 'SHIPYARD'
        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])
        nav_data = json.load(
            open(os.path.join(DATA_DIR, 'navigate.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/navigate').mock(
            return_value=httpx.Response(200, json=nav_data)
        )
        mount_data = json.load(
            open(os.path.join(DATA_DIR, 'mount.json'), encoding='utf8')
        )
        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        mount_side_effect = MountsSideEffect(
            data=mount_data,
            waypoint=waypoint_data,
            agent=agent_data,
        )
        mount_route = respx_mock.post(
            '/my/ships/TEST_SHIP_SYMBOL/mounts/install'
        )
        mount_route.side_effect = mount_side_effect.install

        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )
        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        ship.navigate(waypoint)
        ship.install_mount('MOUNT_GAS_SIPHON_II')
        for ship_mount in ship.mounts:
            for data_mount in mount_data['data']['mounts']:
                if ship_mount.symbol == data_mount['symbol']:
                    assert ship_mount.to_dict() == data_mount

        # Can only purchase valid Mounts
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        ship.navigate(waypoint)
        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            ship.install_mount('INVALID_MOUNT')

        # 4248: ShipMountInsufficientCreditsError,
        # Check credits
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        ship.navigate(waypoint)
        with mount_side_effect as tmp:
            tmp.agent['data']['credits'] = 0
            with pytest.raises(
                snisp.exceptions.ShipMountInsufficientCreditsError
            ):
                ship.install_mount('MOUNT_GAS_SIPHON_II')

        # 4246: ShipMountNoShipyardError, (not at shipyard)
        # Check at shipyard
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with mount_side_effect as tmp:
            tmp.waypoint['data']['traits'][0]['symbol'] = 'INVALID'
            with pytest.raises(snisp.exceptions.ShipMountNoShipyardError):
                ship.install_mount('MOUNT_GAS_SIPHON_II')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_autopurchase(self, respx_mock):
        trade_symbol = 'PRECIOUS_STONES'

        market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        market_side_effect = MarketSideEffect(market_data)
        market_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        )
        market_route.side_effect = market_side_effect
        trade_volume = next(
            t['tradeVolume']
            for t in market_data['data']['tradeGoods']
            if t['type'] == 'EXPORT' and t['symbol'] == trade_symbol
        )
        amount_to_purchase = 40
        purchase_data = json.load(
            open(os.path.join(DATA_DIR, 'purchase.json'), encoding='utf8')
        )
        price_per_unit = purchase_data['data']['transaction']['pricePerUnit']
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        dock_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        dock_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )
        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        p_side_effect = PurchaseSideEffect(
            market_data=market_data,
            agent_data=agent_data,
            purchase_data=purchase_data,
            trade_symbol=trade_symbol,
            price_per_unit=price_per_unit,
            trade_volume=trade_volume,
        )
        agent_route = respx_mock.get('/my/agent')
        agent_route.side_effect = p_side_effect.agent

        purchase_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/purchase')
        purchase_route.side_effect = p_side_effect.purchase

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            ship.autopurchase('INVALID_TYPE', 69)

        # Purchase as much as buffer allows
        with p_side_effect:
            transactions = ship.autopurchase(
                trade_symbol, max_units=amount_to_purchase, buffer=9_500
            )
            assert ship.cargo.units == 5
            assert ship.cargo.inventory[0].symbol == trade_symbol
            assert ship.cargo.inventory[0].units == 5
            for index, transaction in enumerate(transactions[::-1]):
                assert self.agent.recent_transactions[index] == transaction

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        # Purchase up to cargo limit
        with p_side_effect:
            transactions = ship.autopurchase(
                trade_symbol, max_units=amount_to_purchase, buffer=0
            )
            assert ship.cargo.units == amount_to_purchase
            assert ship.cargo.inventory[0].symbol == trade_symbol
            assert ship.cargo.inventory[0].units == amount_to_purchase
            for index, transaction in enumerate(transactions[::-1]):
                assert self.agent.recent_transactions[index] == transaction

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        # Purchase up to cargo limit by default
        with p_side_effect:
            transactions = ship.autopurchase(
                trade_symbol, max_units=0, buffer=0
            )
            assert ship.cargo.units == ship.cargo.capacity
            assert ship.cargo.inventory[0].symbol == trade_symbol
            assert ship.cargo.inventory[0].units == ship.cargo.capacity
            for index, transaction in enumerate(transactions[::-1]):
                assert self.agent.recent_transactions[index] == transaction

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        # Bad market
        with market_side_effect as tmp:
            tmp.fail = True
            transactions = ship.autopurchase(
                trade_symbol, max_units=0, buffer=0
            )
            assert len(transactions) == 0

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        # No trade volume
        with market_side_effect as tmp:
            tmp.data['data']['tradeGoods'] = []
            transactions = ship.autopurchase(
                trade_symbol, max_units=0, buffer=0
            )
            assert len(transactions) == 0

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        # No unit_price
        with market_side_effect as tmp:
            tmp.data['data']['tradeGoods'] = [
                {
                    'type': 'EXPORT',
                    'symbol': trade_symbol,
                    'purchasePrice': None,
                    'tradeVolume': 999,
                }
            ]
            transactions = ship.autopurchase(
                trade_symbol, max_units=0, buffer=0
            )
            assert len(transactions) == 0

        # No buy_units
        with market_side_effect as market_tmp, ship_side_effect as ship_tmp:
            ship_tmp.data['data']['cargo']['current'] = 400
            ship_tmp.data['data']['cargo']['units'] = 400
            ship_tmp.data['data']['cargo']['capacity'] = 400
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.autopurchase(trade_symbol, buffer=0)
            assert len(transactions) == 0

        # Purchase up to credit limit
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with p_side_effect as tmp_p:
            tmp_p.agent_data['data']['credits'] = amount_to_purchase * \
                    price_per_unit
            transactions = ship.autopurchase(
                trade_symbol, max_units=amount_to_purchase, buffer=0
            )
            assert ship.cargo.units == amount_to_purchase
            assert ship.cargo.inventory[0].symbol == trade_symbol
            assert ship.cargo.inventory[0].units == amount_to_purchase
            for index, transaction in enumerate(transactions[::-1]):
                assert self.agent.recent_transactions[index] == transaction
            assert ship.agent.data.credits == 0

        # Purchase up to buffer_limit
        with (
            p_side_effect as tmp_p,
            ship_side_effect as ship_tmp,
            market_side_effect as market_tmp,
        ):
            p_side_effect.trade_volume = 40
            market_tmp.data['data']['tradeGoods'] = [
                {
                    'type': 'EXPORT',
                    'symbol': trade_symbol,
                    'purchasePrice': price_per_unit,
                    'tradeVolume': 100,
                }
            ]
            ship_tmp.data['data']['cargo']['capacity'] = 1_000
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            tmp_p.agent_data['data']['credits'] = amount_to_purchase * \
                price_per_unit + price_per_unit
            transactions = ship.autopurchase(
                trade_symbol,
                max_units=amount_to_purchase,
                buffer=500,
            )
            # Hardcoded because I'm lazy and so are you
            assert ship.cargo.units == 36
            assert ship.cargo.inventory[0].symbol == trade_symbol
            assert ship.cargo.inventory[0].units == 36
            for index, transaction in enumerate(transactions[::-1]):
                assert self.agent.recent_transactions[index] == transaction
            assert ship.agent.data.credits == 500

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_jettison(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['cargo']['units'] = 10
        ship_data['data']['cargo']['inventory'][0]['units'] = 10
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        side_effect = JettisonSideEffect(ship_data)
        jettison_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/jettison')
        jettison_route.side_effect = side_effect

        # Jettison all
        with side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.jettison('PRECIOUS_STONES', 10)
            assert ship.cargo.units == 0
            assert ship.cargo.inventory == []

        # Jettison a poriton
        with side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            ship.jettison('PRECIOUS_STONES', 5)
            assert ship.cargo.units == 5
            assert ship.cargo.inventory[0].units == 5
            assert ship.cargo.inventory[0].symbol == 'PRECIOUS_STONES'

        # Jettison cargo not in ship
        with side_effect as tmp:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            tmp.data['data']['cargo']['inventory'][0]['symbol'] = 'INVALID'
            with pytest.raises(snisp.exceptions.ShipCargoMissingError):
                ship.jettison('PRECIOUS_STONES', 5)

        # Jettison more than what's in cargo
        with side_effect:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.ShipCargoUnitCountError):
                ship.jettison('PRECIOUS_STONES', 100)
            assert ship.cargo.units == 10
            assert ship.cargo.inventory[0].units == 10
            assert ship.cargo.inventory[0].symbol == 'PRECIOUS_STONES'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_warp(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_data['data']['nav']['waypointSymbol'] = 'SECTOR-SYSTEM-WAYPOINT'

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint = snisp.waypoints.Waypoint(
           self.agent, waypoint_data['data']
        )
        side_effect = WarpSideEffect(data=ship_data, waypoint=waypoint_data)
        warp_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/warp')
        warp_route.side_effect = side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['modules'].append({'symbol': 'WARP_DRIVE_I'})
            tmp.waypoint['data']['symbol'] = 'JUMP-DEST-TEST'
            tmp_waypoint = snisp.waypoints.Waypoint(
                self.agent, tmp.waypoint['data']
            )
            ship.warp(tmp_waypoint)

        # 4235: WarpInsideSystemError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['modules'].append({'symbol': 'WARP_DRIVE_I'})
            tmp.data['data']['nav']['waypointSymbol'] = 'SECTOR-SYSTEM-WAYPOINT'  # noqa: E501
            tmp.waypoint['data']['symbol'] = 'SECTOR-SYSTEM-WAYPOINT'
            tmp_waypoint = snisp.waypoints.Waypoint(
                self.agent, tmp.waypoint['data']
            )
            with pytest.raises(snisp.exceptions.WarpInsideSystemError):
                ship.warp(tmp_waypoint)

        # 4241: ShipMissingWarpDriveError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with pytest.raises(snisp.exceptions.ShipMissingWarpDriveError):
            ship.warp(waypoint)

        # 4201: NavigateInvalidDestinationError
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.waypoint['data']['symbol'] = 'SECTOR-SYSTEM-INVALID'
            tmp_waypoint = snisp.waypoints.Waypoint(
                self.agent, tmp.waypoint['data']
            )
            with pytest.raises(
                snisp.exceptions.NavigateInvalidDestinationError
            ):
                ship.warp(tmp_waypoint)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_jump(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_data['data']['nav']['waypointSymbol'] = 'SECTOR-SYSTEM-WAYPOINT'

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])
        side_effect = JumpSideEffect(data=ship_data, waypoint=waypoint_data)
        jump_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/jump')
        jump_route.side_effect = side_effect

        with side_effect as tmp:
            tmp.waypoint['data']['symbol'] = 'JUMP-DEST-TEST'
            tmp.waypoint['data']['isUnderConstruction'] = False
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            tmp_waypoint = snisp.waypoints.Waypoint(
                self.agent, tmp.waypoint['data']
            )
            ship.jump(tmp_waypoint)

        # 4207: ShipJumpNoSystemError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.waypoint['data']['symbol'] = 'SECTOR-INVALID-WAYPOINT'
            tmp.waypoint['data']['isUnderConstruction'] = False
            tmp_waypoint = snisp.waypoints.Waypoint(
                self.agent, tmp.waypoint['data']
            )
            with pytest.raises(snisp.exceptions.ShipJumpNoSystemError):
                ship.jump(tmp_waypoint)

        # 4208: ShipJumpSameSystemError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['nav']['waypointSymbol'] = 'SECTOR-SYSTEM-WAYPOINT'  # noqa: E501
            tmp.waypoint['data']['symbol'] = 'SECTOR-SYSTEM-WAYPOINT'
            tmp.waypoint['data']['isUnderConstruction'] = False
            tmp_waypoint = snisp.waypoints.Waypoint(
                self.agent, tmp.waypoint['data']
            )
            with pytest.raises(snisp.exceptions.ShipJumpSameSystemError):
                ship.jump(tmp_waypoint)

        '''
        # Not sure how to check for these conditions to be met
        # 4210: ShipJumpMissingModuleError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        # 4211: ShipJumpNoValidWaypointError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        # 4212: ShipJumpMissingAntimatterError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        # 4229: ShipJumpFromGateToGateError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        '''

        # 4254: ShipJumpInvalidOriginError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['nav']['route']['destination']['type'] = 'INVALID'
            with pytest.raises(
                snisp.exceptions.ShipJumpInvalidOriginError
            ):
                ship.jump(waypoint)

        # 4255: ShipJumpInvalidWaypointError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.waypoint['data']['symbol'] = 'RANDOM-TEST-INVALID'
            tmp.waypoint['data']['isUnderConstruction'] = False
            tmp_waypoint = snisp.waypoints.Waypoint(
                self.agent, tmp.waypoint['data']
            )
            with pytest.raises(
                snisp.exceptions.ShipJumpInvalidWaypointError
            ):
                ship.jump(tmp_waypoint)

        # 4256: ShipJumpOriginUnderConstructionError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['nav']['route']['destination']['type'] = 'UNDER_CONSTRUCTION'  # noqa: E501
            with pytest.raises(
                snisp.exceptions.ShipJumpOriginUnderConstructionError
            ):
                ship.jump(waypoint)

        # 4262: ShipJumpDestinationUnderConstructionError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            with pytest.raises(
                snisp.exceptions.ShipJumpDestinationUnderConstructionError
            ):
                ship.jump(waypoint)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_negotiate_contract(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )

        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        contract_data = json.load(
            open(os.path.join(DATA_DIR, 'contract.json'), encoding='utf8')
        )
        side_effect = NegotiateContractSideEffect(contract_data)
        contract_route = respx_mock.post(
            '/my/ships/TEST_SHIP_SYMBOL/negotiate/contract'
        )
        contract_route.side_effect = side_effect
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        contract = ship.negotiate_contract()
        assert contract.accepted
        assert not contract.fulfilled

        # 4501: AcceptContractConflictError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['contract']['accepted'] = True
            with pytest.raises(
                snisp.exceptions.AcceptContractConflictError
            ):
                ship.negotiate_contract()

        '''
        # 4506: ContractNotAuthorizedError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        # 4500: AcceptContractNotAuthorizedError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        '''

        # 4511: ExistingContractError,
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with side_effect as tmp:
            tmp.data['data']['existing'] = True
            with pytest.raises(snisp.exceptions.ExistingContractError):
                ship.negotiate_contract()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_purchase(self, respx_mock):
        trade_symbol = 'PRECIOUS_STONES'
        market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        trade_volume = next(
            t['tradeVolume']
            for t in market_data['data']['tradeGoods']
            if t['type'] == 'EXPORT' and t['symbol'] == trade_symbol
        )
        purchase_data = json.load(
            open(os.path.join(DATA_DIR, 'purchase.json'), encoding='utf8')
        )
        price_per_unit = purchase_data['data']['transaction']['pricePerUnit']
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )
        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        p_side_effect = PurchaseSideEffect(
            market_data=market_data,
            agent_data=agent_data,
            purchase_data=purchase_data,
            trade_symbol=trade_symbol,
            price_per_unit=price_per_unit,
            trade_volume=trade_volume,
        )
        purchase_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/purchase')
        purchase_route.side_effect = p_side_effect.purchase

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        # Only valid trade_symbols
        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            ship.purchase('INVALID_TYPE', 69)

        # Max units is no greater than trade_volume
        with pytest.raises(snisp.exceptions.MarketTradeUnitLimitError):
            ship.purchase(trade_symbol, 999)

        # Cannot purchase ==0
        with pytest.raises(snisp.exceptions.MarketTradeNoPurchaseError):
            ship.purchase(trade_symbol, 0)

        # Cannot purchase =>0
        with pytest.raises(snisp.exceptions.MarketTradeUnitLimitError):
            ship.purchase(trade_symbol, -1)

        # Only purchase as much as you can afford
        with p_side_effect as tmp_p:
            with pytest.raises(
                snisp.exceptions.MarketInsufficientCredits
            ):
                tmp_p.agent_data['data']['credits'] = 0
                ship.purchase(trade_symbol, 1)

        # Cannot purchase while not at a market
        with p_side_effect as tmp_p:
            with pytest.raises(snisp.exceptions.MarketNotFoundError):
                tmp_p.agent_data['data']['headquarters'] = 'INVALID'
                ship.purchase(trade_symbol, 1)

        # Cannot purchase more than can hold
        with p_side_effect as tmp_p:
            with pytest.raises(
                snisp.exceptions.ShipCargoExceedsLimitError
            ):
                tmp_p.purchase_data['data']['cargo']['capacity'] = 0
                ship.purchase(trade_symbol, 1)

        # Cannot purchase what's not sold at market
        with pytest.raises(snisp.exceptions.MarketTradeNotSoldError):
            ship.purchase('EXOTIC_MATTER', 999)

        # Valid purchase
        transaction = ship.purchase(trade_symbol, trade_volume)
        assert transaction.agent == self.agent
        assert transaction._data == transaction.to_dict()
        assert ship.cargo.units == trade_volume
        assert ship.cargo.inventory[0].symbol == trade_symbol
        assert ship.cargo.inventory[0].units == trade_volume
        assert self.agent.recent_transactions[0] == transaction

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_sell(self, respx_mock):
        trade_symbol = 'PRECIOUS_STONES'
        market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        trade_volume = next(
            t['tradeVolume']
            for t in market_data['data']['tradeGoods']
            if t['type'] == 'EXPORT' and t['symbol'] == trade_symbol
        )
        sell_data = json.load(
            open(os.path.join(DATA_DIR, 'sell.json'), encoding='utf8')
        )
        price_per_unit = sell_data['data']['transaction']['pricePerUnit']
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )
        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        side_effect = SellSideEffect(
            market_data=market_data,
            agent_data=agent_data,
            sell_data=sell_data,
            trade_symbol=trade_symbol,
            price_per_unit=price_per_unit,
            trade_volume=trade_volume,
        )
        agent_route = respx_mock.get('/my/agent')
        agent_route.side_effect = side_effect.agent

        sell_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/sell')
        sell_route.side_effect = side_effect.sell

        # 4601: MarketTradeNoPurchaseError,
        # 4603: MarketNotFoundError,
        # 4604: MarketTradeUnitLimitError,

        with side_effect as tmp:
            # Valid sell
            starting_cash = self.agent.data.credits
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transaction = ship.sell(trade_symbol, trade_volume)
            assert ship.cargo.units == 0
            assert ship.cargo.inventory == []
            assert self.agent.recent_transactions[0] == transaction
            assert self.agent.data.credits == starting_cash + trade_volume * price_per_unit  # noqa: E501

        # Only valid trade_symbols
        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            ship.sell('INVALID_TYPE', 69)

        # Max units is no greater than trade_volume
        with pytest.raises(snisp.exceptions.MarketTradeUnitLimitError):
            ship.sell(trade_symbol, 999)

        # Cannot sell ==0
        with pytest.raises(snisp.exceptions.MarketTradeNoPurchaseError):
            ship.sell(trade_symbol, 0)

        # Cannot sell =>0
        with pytest.raises(snisp.exceptions.MarketTradeUnitLimitError):
            ship.sell(trade_symbol, -1)

        # Cannot sell while not at a market
        with side_effect as tmp:
            with pytest.raises(snisp.exceptions.MarketNotFoundError):
                tmp.agent_data['data']['headquarters'] = 'INVALID'
                ship.sell(trade_symbol, 1)

        # Cannot sell what's not sold at market
        with pytest.raises(snisp.exceptions.MarketTradeNotSoldError):
            ship.sell('EXOTIC_MATTER', 999)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_sell_all(self, respx_mock):
        trade_symbol = 'PRECIOUS_STONES'
        market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        trade_volume = next(
            t['tradeVolume']
            for t in market_data['data']['tradeGoods']
            if t['type'] == 'EXPORT' and t['symbol'] == trade_symbol
        )
        market_side_effect = MarketSideEffect(market_data)
        market_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
        )
        market_route.side_effect = market_side_effect
        sell_data = json.load(
            open(os.path.join(DATA_DIR, 'sell.json'), encoding='utf8')
        )
        price_per_unit = sell_data['data']['transaction']['pricePerUnit']
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )
        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        side_effect = SellSideEffect(
            market_data=market_data,
            agent_data=agent_data,
            sell_data=sell_data,
            trade_symbol=trade_symbol,
            price_per_unit=price_per_unit,
            trade_volume=trade_volume,
        )
        agent_route = respx_mock.get('/my/agent')
        agent_route.side_effect = side_effect.agent

        sell_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/sell')
        sell_route.side_effect = side_effect.sell

        # Valid sell
        with side_effect as tmp:
            starting_cash = self.agent.data.credits
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_all(trade_symbol)
            assert ship.cargo.units == 0
            assert ship.cargo.inventory == []
            assert self.agent.recent_transactions[0] == transactions[0]
            assert self.agent.data.credits == starting_cash + trade_volume * price_per_unit  # noqa: E501

        # Trade symbol not in cargo
        with side_effect as tmp:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_all('INVALID')
            assert transactions == []

        # No ship at market
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with market_side_effect as tmp:
            tmp.fail = True
            transactions = ship.sell_all(trade_symbol)
            assert transactions == []

        # No trade volume
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        with market_side_effect as tmp:
            for item in tmp.data['data']['tradeGoods']:
                item['tradeVolume'] = None
            transactions = ship.sell_all(trade_symbol)
            assert transactions == []

        # Piece-by-piece
        with side_effect as tmp, ship_side_effect as ship_tmp:
            ship_tmp.data['data']['cargo']['inventory'][0]['symbol'] = trade_symbol  # noqa: E501
            ship_tmp.data['data']['cargo']['inventory'][0]['units'] = 10
            tmp.sell_data['data']['cargo']['inventory'][0]['symbol'] = trade_symbol  # noqa: E501
            tmp.sell_data['data']['cargo']['inventory'][0]['units'] = 10
            tmp.sell_data['data']['cargo']['units'] = 10
            ship_tmp.data['data']['cargo']['units'] = 10
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_all(trade_symbol)
            assert ship.cargo.units == 0
            assert len(transactions) == 10

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_sell_off_cargo(self, respx_mock):
        trade_symbol = 'PRECIOUS_STONES'
        market_data = json.load(
            open(os.path.join(DATA_DIR, 'market_data.json'), encoding='utf8')
        )
        trade_volume = next(
            t['tradeVolume']
            for t in market_data['data']['tradeGoods']
            if t['type'] == 'IMPORT' and t['symbol'] == trade_symbol
        )
        market_side_effect = MarketSideEffect(market_data)
        market_route = respx_mock.route(
            # '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT/market'
            M(path__regex=r'/systems/TEST-SYSTEM/waypoints/.*/market')
        )
        market_route.side_effect = market_side_effect
        sell_data = json.load(
            open(os.path.join(DATA_DIR, 'sell.json'), encoding='utf8')
        )
        price_per_unit = sell_data['data']['transaction']['pricePerUnit']
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
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

        jettison_side_effect = JettisonSideEffect(ship_data)
        jettison_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/jettison')
        jettison_route.side_effect = jettison_side_effect
        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        refuel_data = json.load(
              open(os.path.join(DATA_DIR, 'refuel.json'), encoding='utf8')
        )
        nav_data = json.load(
            open(os.path.join(DATA_DIR, 'navigate.json'), encoding='utf8')
        )
        nav_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        nav_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-DESTINATION'
        navigate_side_effect = AutoPilotSideEffect(
            data=nav_data,
            ship=ship_data,
            orbit=orbit_data,
            refuel=refuel_data,
            dock=dock_data,
        )
        navigate_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/navigate')
        navigate_route.side_effect = navigate_side_effect

        dock_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock')
        dock_route.side_effect = navigate_side_effect.dock_side_effect

        orbit_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit')
        orbit_route.side_effect = navigate_side_effect.orbit_side_effect

        agent_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        side_effect = SellSideEffect(
            market_data=market_data,
            agent_data=agent_data,
            sell_data=sell_data,
            trade_symbol=trade_symbol,
            price_per_unit=price_per_unit,
            trade_volume=trade_volume,
        )
        agent_route = respx_mock.get('/my/agent')
        agent_route.side_effect = side_effect.agent

        sell_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/sell')
        sell_route.side_effect = side_effect.sell

        # Sell off everything
        # Valid sell
        with side_effect:
            starting_cash = self.agent.data.credits
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_off_cargo()
            assert ship.cargo.units == 0
            assert ship.cargo.inventory == []
            assert self.agent.recent_transactions[0] == transactions[0]
            assert self.agent.data.credits == starting_cash + trade_volume * price_per_unit  # noqa: E501

        # Sell some, jettison others
        with ship_side_effect as ship_tmp, jettison_side_effect as jet_tmp:
            ship_tmp.data['data']['cargo']['units'] += 1
            ship_tmp.data['data']['cargo']['inventory'].append(
                {
                    'symbol': 'INVALID',
                    'name': 'INVALID',
                    'description': 'INVALID',
                    'units': 1
                }
            )
            jet_tmp.data['data']['cargo'] = ship_tmp.data['data']['cargo']
            starting_cash = self.agent.data.credits
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_off_cargo()
            assert ship.cargo.inventory == []
            assert self.agent.recent_transactions[0] == transactions[0]
            assert self.agent.data.credits == starting_cash + trade_volume * price_per_unit  # noqa: E501

        # All jettison, no sell
        with ship_side_effect as ship_tmp, jettison_side_effect as jet_tmp:
            ship_tmp.data['data']['cargo']['units'] = 1
            ship_tmp.data['data']['cargo']['inventory'][0] = {
                'symbol': 'INVALID',
                'name': 'INVALID',
                'description': 'INVALID',
                'units': 1
            }
            jet_tmp.data['data']['cargo'] = ship_tmp.data['data']['cargo']
            starting_cash = self.agent.data.credits
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_off_cargo()
            transaction_count = len(self.agent.recent_transactions)
            assert ship.cargo.units == 0
            assert len(self.agent.recent_transactions) == transaction_count
            assert self.agent.data.credits == starting_cash

        # Filter for trade_symbol; jettison
        with ship_side_effect as ship_tmp, jettison_side_effect as jet_tmp:
            ship_tmp.data['data']['cargo']['units'] += 1
            ship_tmp.data['data']['cargo']['inventory'].append(
                {
                    'symbol': 'INVALID',
                    'name': 'INVALID',
                    'description': 'INVALID',
                    'units': 1
                }
            )
            jet_tmp.data['data']['cargo'] = ship_tmp.data['data']['cargo']
            starting_cash = self.agent.data.credits
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_off_cargo(trade_symbol)
            assert self.agent.recent_transactions[0] == transactions[0]
            assert self.agent.data.credits == starting_cash + trade_volume * price_per_unit  # noqa: E501
            assert not any(
                i.symbol == 'INVALID' for i in ship.cargo.inventory
            )
            assert not any(i.symbol == trade_symbol for i in transactions)

        # Not all was sold; jettisoning (fake scenario)
        with ship_side_effect as ship_tmp, market_side_effect as market_tmp:
            ship_tmp.data['data']['cargo']['units'] = 1
            ship_tmp.data['data']['cargo']['inventory'][0]['units'] = 1
            market_tmp.data['data']['tradeGoods'] = []
            starting_cash = self.agent.data.credits
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            transactions = ship.sell_off_cargo(trade_symbol)
            assert ship.cargo.units == 0
            assert ship.cargo.inventory == []
            assert transactions == []

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_transfer(self, respx_mock):
        trade_symbol = 'IRON_ORE'
        transfer_data = json.load(
            open(os.path.join(DATA_DIR, 'transfer.json'), encoding='utf8')
        )
        transfer_data['data']['cargo']['capacity'] = 40
        transfer_data['data']['cargo']['inventory'] = []
        from_ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        from_ship_data['data']['symbol'] = 'FROM_TEST_SHIP_SYMBOL'
        to_ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        to_ship_data['data']['symbol'] = 'TO_TEST_SHIP_SYMBOL'

        side_effect = TransferSideEffect(
            data=transfer_data, from_ship=from_ship_data, to_ship=to_ship_data
        )
        transfer_route = respx_mock.post(
            '/my/ships/FROM_TEST_SHIP_SYMBOL/transfer'
        )
        transfer_route.side_effect = side_effect

        to_ship_route = respx_mock.get('/my/ships/TO_TEST_SHIP_SYMBOL')
        to_ship_route.side_effect = side_effect.get_to_ship

        from_ship_route = respx_mock.get('/my/ships/FROM_TEST_SHIP_SYMBOL')
        from_ship_route.side_effect = side_effect.get_from_ship

        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['units'] = 30
            tmp.from_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 30}
            ]
            tmp.to_ship['data']['cargo']['units'] = 0
            tmp.to_ship['data']['cargo']['inventory'] = []
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            from_ship.transfer(to_ship, symbol=trade_symbol, units=30)
            assert from_ship.cargo.inventory == []
            assert to_ship.cargo.inventory[0].units == 30
            assert to_ship.cargo.inventory[0].symbol == trade_symbol

        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['units'] = 40
            tmp.from_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 30}
            ]
            tmp.to_ship['data']['cargo']['units'] = 0
            tmp.to_ship['data']['cargo']['inventory'] = []
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            from_ship.transfer(to_ship, symbol=trade_symbol, units=30)
            assert from_ship.cargo.units == 10
            assert to_ship.cargo.inventory[0].units == 30
            assert to_ship.cargo.inventory[0].symbol == trade_symbol

        # Transfer w/ existing trade_symbol cargo in the dest ship
        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['units'] = 40
            tmp.from_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 30}
            ]
            tmp.to_ship['data']['cargo']['units'] = 10
            tmp.to_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 10}
            ]
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            from_ship.transfer(to_ship, symbol=trade_symbol, units=30)
            assert from_ship.cargo.units == 10
            assert to_ship.cargo.inventory[0].units == 40
            assert to_ship.cargo.inventory[0].symbol == trade_symbol

        # Transfer w/ existing cargo in the dest ship
        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['units'] = 40
            tmp.from_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 30}
            ]
            tmp.to_ship['data']['cargo']['units'] = 10
            tmp.to_ship['data']['cargo']['inventory'] = [
                {'symbol': 'INVALID', 'units': 10}
            ]
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            from_ship.transfer(to_ship, symbol=trade_symbol, units=30)
            assert from_ship.cargo.units == 10
            assert to_ship.cargo.inventory[0].units == 10
            assert to_ship.cargo.inventory[0].symbol == 'INVALID'
            assert to_ship.cargo.inventory[1].units == 30
            assert to_ship.cargo.inventory[1].symbol == trade_symbol

        # 4219: ShipCargoUnitCountError
        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['units'] = 1
            tmp.from_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 1}
            ]
            tmp.to_ship['data']['cargo']['units'] = 0
            tmp.to_ship['data']['cargo']['inventory'] = []
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.ShipCargoUnitCountError):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # 4231: ShipTransferShipNotFound,
        with side_effect as tmp:
            tmp.to_ship['data']['symbol'] = 'NOT_FOUND'
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.ShipTransferShipNotFound):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # 4232: ShipTransferAgentConflict,
        with side_effect as tmp:
            tmp.to_ship['data']['symbol'] = 'INVALID_AGENT'
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ShipTransferAgentConflict
            ):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # 4233: ShipTransferSameShipConflict,
        with side_effect as tmp:
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ShipTransferSameShipConflict
            ):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # 4234: ShipTransferLocationConflict,
        with side_effect as tmp:
            tmp.to_ship['data']['nav']['waypointSymbol'] = 'BOONIES'
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ShipTransferLocationConflict
            ):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # 4218: ShipCargoMissingError,
        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['inventory'] = []
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.ShipCargoMissingError):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # 4228: ShipCargoFullError,
        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['units'] = 30
            tmp.from_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 30}
            ]
            tmp.to_ship['data']['cargo']['units'] = 40
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.ShipCargoFullError):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # 4219: ShipCargoUnitCountError,
        with side_effect as tmp:
            tmp.from_ship['data']['cargo']['units'] = 30
            tmp.from_ship['data']['cargo']['inventory'] = [
                {'symbol': trade_symbol, 'units': 30}
            ]
            tmp.to_ship['data']['cargo']['units'] = 11
            from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
            to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
            with pytest.raises(snisp.exceptions.ShipCargoUnitCountError):
                from_ship.transfer(to_ship, symbol=trade_symbol, units=30)

        # Invalid symbol
        from_ship = self.agent.fleet('FROM_TEST_SHIP_SYMBOL')
        to_ship = self.agent.fleet('TO_TEST_SHIP_SYMBOL')
        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            from_ship.transfer(to_ship, symbol='INVALID', units=30)


class PurchaseSideEffect:

    def __init__(
        self,
        *,
        agent_data,
        market_data,
        purchase_data,
        trade_symbol,
        price_per_unit,
        trade_volume,
    ):
        self.orig_purchase_data = purchase_data
        self.orig_agent_data = agent_data
        self.market_data = market_data
        self.purchase_data = copy.deepcopy(self.orig_purchase_data)
        self.agent_data = copy.deepcopy(self.orig_agent_data)
        self.trade_symbol = trade_symbol
        self.price_per_unit = price_per_unit
        self.trade_volume = trade_volume

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def purchase(self, request, route):
        if self.agent_data['data']['headquarters'] == 'INVALID':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4603}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        if not any(
            True
            for t in self.market_data['data']['tradeGoods']
            if t['type'] == 'EXPORT' and t['symbol'] == payload['symbol']
        ):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4602}}}
            )
        units = int(payload.get('units'))
        if units > self.trade_volume:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4604}}}
            )
        if units == 0:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4601}}}
            )
        if units < 0:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4604}}}
            )
        cash = self.agent_data['data']['credits'] - self.price_per_unit * units
        if cash < 0:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4600}}}
            )
        self.purchase_data['data']['agent']['credits'] = cash
        self.purchase_data['data']['cargo']['units'] += units
        cargo = self.purchase_data['data']['cargo']
        if cargo['units'] > cargo['capacity']:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4217}}}
            )
        for i in self.purchase_data['data']['cargo']['inventory']:
            if i['symbol'] == self.trade_symbol:
                i['units'] += units
        self.purchase_data['data']['transaction']['timestamp'] = str(
            datetime.now(timezone.utc)
        )
        self.agent_data['data']['credits'] = cash
        return httpx.Response(200, json=self.purchase_data)

    def agent(self, request, route):
        return httpx.Response(200, json=self.agent_data)

    def reset(self):
        self.purchase_data = copy.deepcopy(self.orig_purchase_data)
        self.agent_data = copy.deepcopy(self.orig_agent_data)


class SiphonSideEffect:

    def __init__(self, *, data, ship, waypoint):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.data['data']['cargo']['units'] = 0
        self.data['data']['cargo']['inventory'][0]['units'] = 0
        self.data['data']['siphon']['yield']['units'] = 1
        self.orig_waypoint = waypoint
        self.waypoint = copy.deepcopy(self.orig_waypoint)
        self.orig_ship = ship
        self.ship = copy.deepcopy(self.orig_ship)

    def __call__(self, request, route):
        if self.waypoint['data']['type'] != 'GAS_GIANT':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4259}}}
            )
        has_mount = next(
            (
                i for i in self.ship['data']['mounts']
                if i['symbol'].startswith('MOUNT_GAS_SIPHON_')
            ), None
        )
        if not has_mount:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4258}}}
            )
        units = self.data['data']['cargo']['units']
        capacity = self.data['data']['cargo']['capacity']
        if units == capacity:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4217}}}
            )
        self.data['data']['cargo']['units'] += 1
        self.data['data']['cargo']['inventory'][0]['units'] += 1
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.waypoint = copy.deepcopy(self.orig_waypoint)
        self.ship = copy.deepcopy(self.orig_ship)
        self.data = copy.deepcopy(self.orig_data)
        self.data['data']['cargo']['units'] = 0
        self.data['data']['cargo']['inventory'][0]['units'] = 0
        self.data['data']['siphon']['yield']['units'] = 1


class ExtractionSideEffect:

    def __init__(self, *, data, ship, waypoint):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.data['data']['cargo']['units'] = 0
        self.data['data']['cargo']['inventory'][0]['units'] = 0
        self.data['data']['extraction']['yield']['units'] = 1
        self.orig_waypoint = waypoint
        self.waypoint = copy.deepcopy(self.orig_waypoint)
        self.orig_ship = ship
        self.ship = copy.deepcopy(self.orig_ship)

    def __call__(self, request, route):
        if not self.waypoint['data']['type'].startswith('ASTEROID'):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4205}}}
            )
        has_mount = next(
            (
                i for i in self.ship['data']['mounts']
                if i['symbol'].startswith('MOUNT_MINING_LASER_')
            ), None
        )
        if not has_mount:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4243}}}
            )
        if content := request.content:
            payload = json.loads(content.decode('utf8'))
            default_keys = [
                'signature',
                'symbol',
                'deposits',
                'expiration',
                'size',
            ]
            for survey in payload['surveys']:
                for key in default_keys:
                    if key not in survey:
                        return httpx.Response(
                            400, json={'error': {'data': {'code': 4220}}}
                        )
            now = datetime.now(timezone.utc)
            expires = datetime.fromisoformat(
                payload['surveys'][0]['expiration']
            )
            if now > expires:
                return httpx.Response(
                    400, json={'error': {'data': {'code': 4221}}}
                )
            if not any(i['deposits'] for i in payload['surveys']):
                return httpx.Response(
                    400, json={'error': {'data': {'code': 4224}}}
                )
        units = self.data['data']['cargo']['units']
        capacity = self.data['data']['cargo']['capacity']
        if units == capacity:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4217}}}
            )
        self.data['data']['cargo']['units'] += 1
        self.data['data']['cargo']['inventory'][0]['units'] += 1
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.waypoint = copy.deepcopy(self.orig_waypoint)
        self.ship = copy.deepcopy(self.orig_ship)
        self.data = copy.deepcopy(self.orig_data)
        self.data['data']['cargo']['units'] = 0
        self.data['data']['cargo']['inventory'][0]['units'] = 0
        self.data['data']['extraction']['yield']['units'] = 1


class MountsSideEffect:

    def __init__(self, *, data, agent, waypoint):
        self.orig_agent = agent
        self.orig_data = data
        self.orig_waypoint = waypoint
        self.waypoint = copy.deepcopy(self.orig_waypoint)
        self.data = copy.deepcopy(self.orig_data)
        self.agent = copy.deepcopy(self.orig_agent)

    def install(self, request, route):
        if not any(
            i['symbol'] == 'SHIPYARD' for i in self.waypoint['data']['traits']
        ):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4246}}}
            )
        if self.agent['data']['credits'] <= 0:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4248}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        self.data['data']['mounts'] = [
            m for m in self.data['data']['mounts']
            if m['symbol'] != payload['symbol']
        ]
        return httpx.Response(200, json=self.data)

    def remove(self, request, route):
        if not any(
            i['symbol'] == 'SHIPYARD' for i in self.waypoint['data']['traits']
        ):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4246}}}
            )
        if self.agent['data']['credits'] <= 0:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4248}}}
            )
        mounts = self.data['data'].get('mounts')
        if not mounts:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4251}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        mount_index = next(
            (
                i for i, v in enumerate(mounts)
                if v['symbol'] == payload['symbol']
            ), None
        )
        if not mount_index:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4247}}}
            )
        del mounts[mount_index]
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.waypoint = copy.deepcopy(self.orig_waypoint)
        self.data = copy.deepcopy(self.orig_data)
        self.agent = copy.deepcopy(self.orig_agent)


class JettisonSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        payload = json.loads(request.content.decode('utf8'))
        units = int(payload['units'])
        symbol = payload['symbol']
        if units > self.data['data']['cargo']['units']:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4219}}}
            )
        if not any(
            i['symbol'] == symbol
            for i in self.data['data']['cargo']['inventory']
        ):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4218}}}
            )
        self.data['data']['cargo']['units'] -= units
        self.data['data']['cargo']['inventory'][0]['units'] -= units
        if self.data['data']['cargo']['inventory'][0]['units'] == 0:
            self.data['data']['cargo']['inventory'] = []
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)


class WarpSideEffect:

    def __init__(self, *, data, waypoint):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_waypoint = waypoint
        self.waypoint = copy.deepcopy(self.orig_waypoint)

    def __call__(self, request, route):
        payload = json.loads(request.content.decode('utf8'))
        dst_symbol = payload['waypointSymbol']
        dst_sector, dst_system, dst_waypoint = dst_symbol.split('-')
        if dst_waypoint == 'INVALID':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4201}}}
            )
        if not any(
            i['symbol'].startswith('WARP_DRIVE')
            for i in self.data['data']['modules']
        ):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4241}}}
            )
        src_symbol = self.data['data']['nav']['waypointSymbol']
        src_sector, src_system, src_waypoint = src_symbol.split('-')
        if dst_system == src_system:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4235}}}
            )
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.waypoint = copy.deepcopy(self.orig_waypoint)


class NegotiateContractSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        if self.data['data']['contract']['accepted']:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4501}}}
            )
        if self.data['data'].get('existing'):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4511}}}
            )
        self.data['data']['contract']['accepted'] = True
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)


class RefuelSideEffect:

    def __init__(self, *, data, ship, waypoint):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_ship = ship
        self.ship = copy.deepcopy(self.orig_ship)
        self.orig_waypoint = waypoint
        self.waypoint = copy.deepcopy(self.orig_waypoint)

    def __call__(self, request, route):
        if self.waypoint['data']['type'] == 'INVALID':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4226}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        units = int(payload.get('units',  0))
        capacity = self.data['data']['fuel']['capacity']
        current = self.data['data']['fuel']['current']
        delta = capacity - current
        if units == 0:
            units = delta
        if payload['fromCargo']:
            fuel_inventory = next(
                (
                    (i, v['units'])
                    for i, v in enumerate(
                        self.ship['data']['cargo']['inventory']
                    )
                    if v['symbol'] == 'FUEL'
                ), None
            )
            if not fuel_inventory:
                return httpx.Response(
                    400, json={'error': {'data': {'code': 4218}}}
                )
            fuel_index, cargo_units = fuel_inventory
            if units > cargo_units:
                units = cargo_units
            units = units if units <= delta else units - delta
            if units == cargo_units:
                del self.ship['data']['cargo']['inventory'][fuel_index]
        self.data['data']['fuel']['current'] += units
        self.data['data']['transaction']['units'] = units
        price = self.data['data']['transaction']['pricePerUnit']
        self.data['data']['transaction']['totalPrice'] = price * units
        return httpx.Response(200, json=self.data)

    def ship_route(self, request, route):
        return httpx.Response(200, json=self.ship)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.ship = copy.deepcopy(self.orig_ship)
        self.waypoint = copy.deepcopy(self.orig_waypoint)


class RefineSideEffect:

    def __init__(self, *, data, ship):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_ship = ship
        self.ship = copy.deepcopy(self.orig_ship)

    def __call__(self, request, route):
        payload = json.loads(request.content.decode('utf8'))
        produce = payload.get('produce', '').upper()
        item = next(
            (
                i for i in self.ship['data']['cargo']['inventory']
                if i['symbol'].rstrip('_ORE') == produce
            ), None
        )
        if not item:
            return httpx.Response(200, json=self.data)
        if item['units'] < 30:
            return httpx.Response(200, json=self.data)
        can_refine = any(
            m['symbol'].upper().startswith('MODULE_MINERAL_PROCESSOR_')
            for m in self.ship['data']['modules']
        )
        if not can_refine:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4239}}}
            )
        self.data['data']['cargo']['inventory'][0]['units'] -= 30
        output = {'symbol': 'IRON', 'units': 1}
        self.data['data']['cargo']['inventory'].append(output)
        self.data['data']['consumed'][0]['units'] = 30
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.ship = copy.deepcopy(self.orig_ship)


class SellSideEffect:

    def __init__(
        self,
        *,
        agent_data,
        market_data,
        sell_data,
        trade_symbol,
        price_per_unit,
        trade_volume,
    ):
        self.orig_purchase_data = sell_data
        self.orig_agent_data = agent_data
        self.market_data = market_data
        self.sell_data = copy.deepcopy(self.orig_purchase_data)
        self.agent_data = copy.deepcopy(self.orig_agent_data)
        self.trade_symbol = trade_symbol
        self.price_per_unit = price_per_unit
        self.trade_volume = trade_volume

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def sell(self, request, route):
        if self.agent_data['data']['headquarters'] == 'INVALID':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4603}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        if not any(
            True
            for t in self.market_data['data']['tradeGoods']
            if t['type'] == 'IMPORT' and t['symbol'] == payload['symbol']
        ):
            return httpx.Response(
                400, json={'error': {'data': {'code': 4602}}}
            )
        units = int(payload.get('units'))
        if units > self.trade_volume:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4604}}}
            )
        if units == 0:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4601}}}
            )
        if units < 0:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4604}}}
            )
        cash = self.agent_data['data']['credits'] + self.price_per_unit * units
        self.sell_data['data']['agent']['credits'] = cash
        self.sell_data['data']['cargo']['units'] -= units
        out_inventory = []
        for item in self.sell_data['data']['cargo']['inventory']:
            if item['symbol'] == self.trade_symbol:
                item['units'] -= units
                if item['units'] > 0:
                    out_inventory.append(item)
        self.sell_data['data']['cargo']['inventory'] = out_inventory
        self.sell_data['data']['transaction']['timestamp'] = str(
            datetime.now(timezone.utc)
        )
        self.agent_data['data']['credits'] = cash
        return httpx.Response(200, json=self.sell_data)

    def agent(self, request, route):
        return httpx.Response(200, json=self.agent_data)

    def reset(self):
        self.sell_data = copy.deepcopy(self.orig_purchase_data)
        self.agent_data = copy.deepcopy(self.orig_agent_data)


class TransferSideEffect:

    def __init__(self, *, data, from_ship, to_ship):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_from_ship = from_ship
        self.orig_to_ship = to_ship
        self.from_ship = copy.deepcopy(self.orig_from_ship)
        self.to_ship = copy.deepcopy(self.orig_to_ship)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def __call__(self, request, route):
        if self.to_ship['data']['cargo']['units'] == self.to_ship['data']['cargo']['capacity']:  # noqa: E501
            return httpx.Response(
                400, json={'error': {'data': {'code': 4228}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        symbol = payload['tradeSymbol']
        units = int(payload['units'])
        receive_ship_symbol = payload['shipSymbol']
        if receive_ship_symbol == 'NOT_FOUND':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4231}}}
            )
        if receive_ship_symbol == 'INVALID_AGENT':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4232}}}
            )
        if self.from_ship['data']['symbol'] == receive_ship_symbol:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4233}}}
            )
        from_loc = self.from_ship['data']['nav']['waypointSymbol']
        to_loc = self.to_ship['data']['nav']['waypointSymbol']
        if from_loc != to_loc:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4234}}}
            )
        from_item = next(
            (
                i for i in self.from_ship['data']['cargo']['inventory']
                if i['symbol'] == symbol
            ), None
        )
        if from_item is None:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4218}}}
            )
        if from_item['units'] < units:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4219}}}
            )
        to_item = next(
            (
                i for i in self.to_ship['data']['cargo']['inventory']
                if i['symbol'] == symbol
                ), {'symbol': symbol, 'units': 0}
        )
        to_item['units'] += units
        self.to_ship['data']['cargo']['units'] += units
        if self.to_ship['data']['cargo']['units'] > self.to_ship['data']['cargo']['capacity']:  # noqa: E501
            return httpx.Response(
                400, json={'error': {'data': {'code': 4219}}}
            )
        self.from_ship['data']['cargo']['units'] -= units
        from_item['units'] -= units
        if from_item['units'] == 0:
            self.from_ship['data']['cargo']['inventory'] = [
                i for i in self.from_ship['data']['cargo']['inventory']
                if i['symbol'] != symbol
            ]
        self.data['data']['cargo']['units'] = self.from_ship['data']['cargo']['units']  # noqa: E501
        self.data['data']['cargo']['inventory'] = self.from_ship['data']['cargo']['inventory']  # noqa: E501
        return httpx.Response(200, json=self.data)

    def get_from_ship(self, request, route):
        return httpx.Response(200, json=self.from_ship)

    def get_to_ship(self, request, route):
        return httpx.Response(200, json=self.to_ship)

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.from_ship = copy.deepcopy(self.orig_from_ship)
        self.to_ship = copy.deepcopy(self.orig_to_ship)


class JumpSideEffect:

    def __init__(self, *, data, waypoint):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_waypoint = waypoint
        self.waypoint = copy.deepcopy(self.orig_waypoint)

    def __call__(self, request, route):
        if self.data['data']['nav']['route']['destination']['type'] == 'INVALID':  # noqa: E501
            # aka, attempting a jump while not a a jump gate
            return httpx.Response(
                400, json={'error': {'data': {'code': 4254}}}
            )
        if self.data['data']['nav']['route']['destination']['type'] == 'UNDER_CONSTRUCTION':  # noqa: E501
            # aka, attempting to jump from a gate under construction
            return httpx.Response(
                400, json={'error': {'data': {'code': 4256}}}
            )
        if self.waypoint['data']['isUnderConstruction']:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4262}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        dst_symbol = payload['waypointSymbol']
        dst_sector, dst_system, dst_waypoint = dst_symbol.split('-')
        if dst_system == 'INVALID':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4207}}}
            )
        if dst_waypoint == 'INVALID':
            return httpx.Response(
                400, json={'error': {'data': {'code': 4255}}}
            )
        src_symbol = self.data['data']['nav']['waypointSymbol']
        src_sector, src_system, src_waypoint = src_symbol.split('-')
        if dst_system == src_system:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4208}}}
            )
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.waypoint = copy.deepcopy(self.orig_waypoint)


class NavigateSideEffect:

    def __init__(self, *, data, ship):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_ship = ship
        self.ship = copy.deepcopy(self.orig_ship)

    def __call__(self, request, route):
        payload = json.loads(request.content.decode('utf8'))
        dest = payload['waypointSymbol']
        if dest == 'INVALID':
            return httpx.Response(400)
        system = '-'.join(dest.split('-')[:2])
        self.data['data']['nav']['systemSymbol'] = system
        self.data['data']['nav']['waypointSymbol'] = dest
        fuel = self.data['data']['fuel']
        self.ship['data']['fuel']['current'] = fuel['current']
        self.ship['data']['fuel']['consumed']['amount'] = fuel['consumed']['amount']  # noqa: E501
        self.ship['data']['fuel']['consumed']['timestamp'] = fuel['consumed']['timestamp']  # noqa: E501
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def ship_side_effect(self, request, route):
        return httpx.Response(200, json=self.ship)

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.ship = copy.deepcopy(self.orig_ship)


class AutoPilotSideEffect:

    def __init__(self, *, data, ship, orbit, refuel, dock):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_ship = ship
        self.ship = copy.deepcopy(self.orig_ship)
        self.orig_orbit = orbit
        self.orbit = copy.deepcopy(self.orig_orbit)
        self.orig_dock = dock
        self.dock = copy.deepcopy(self.orig_dock)
        self.orig_refuel = refuel
        self.refuel = copy.deepcopy(self.orig_refuel)
        self.always_fail = False
        self.num_fails = 0
        self.max_fails = -1

    def __call__(self, request, route):
        if self.always_fail:
            return httpx.Response(400)
        payload = json.loads(request.content.decode('utf8'))
        dest = payload['waypointSymbol']
        system = '-'.join(dest.split('-')[:2])
        if dest == 'TEST-SYSTEM-DESTINATION':
            if self.max_fails >= 0:
                if self.num_fails >= self.max_fails:
                    self.ship['data']['fuel']['current'] -= 100
                    if self.ship['data']['fuel']['current'] == 0:
                        self.ship['data']['fuel']['current'] = 1
                    self.ship['data']['nav']['systemSymbol'] = system
                    self.ship['data']['nav']['waypointSymbol'] = dest
                    return httpx.Response(200, json=self.data)
                return httpx.Response(400)
            elif self.ship['data']['nav']['flightMode'] == 'DRIFT':
                self.ship['data']['fuel']['current'] -= 100
                if self.ship['data']['fuel']['current'] == 0:
                    self.ship['data']['fuel']['current'] = 1
                self.ship['data']['nav']['systemSymbol'] = system
                self.ship['data']['nav']['waypointSymbol'] = dest
                return httpx.Response(200, json=self.data)
            return httpx.Response(400)
        if self.max_fails >= 0:
            self.num_fails += 1
            if self.num_fails <= self.max_fails:
                return httpx.Response(400)
        self.ship['data']['nav']['systemSymbol'] = system
        self.ship['data']['nav']['waypointSymbol'] = dest
        self.data['data']['nav']['waypointSymbol'] = dest
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def update_flight_mode(self, request, route):
        # Double check it isn't dup'ing the waypiont symbol here
        payload = json.loads(request.content.decode('utf8'))
        self.ship['data']['nav']['flightMode'] = payload['flightMode']
        self.data['data']['nav']['flightMode'] = payload['flightMode']
        updated_nav = {'data': self.ship['data']['nav']}
        return httpx.Response(200, json=updated_nav)

    def dock_side_effect(self, request, route):
        flight_mode = self.ship['data']['nav']['flightMode']
        system = self.ship['data']['nav']['systemSymbol']
        waypoint = self.ship['data']['nav']['waypointSymbol']
        self.dock['data']['nav']['systemSymbol'] = system
        self.dock['data']['nav']['waypointSymbol'] = waypoint
        self.dock['data']['nav']['flightMode'] = flight_mode
        return httpx.Response(200, json=self.dock)

    def orbit_side_effect(self, request, route):
        flight_mode = self.ship['data']['nav']['flightMode']
        system = self.ship['data']['nav']['systemSymbol']
        waypoint = self.ship['data']['nav']['waypointSymbol']
        self.orbit['data']['nav']['systemSymbol'] = system
        self.orbit['data']['nav']['waypointSymbol'] = waypoint
        self.orbit['data']['nav']['flightMode'] = flight_mode
        return httpx.Response(200, json=self.orbit)

    def refuel_side_effect(self, request, route):
        if self.ship['data']['nav']['route']['destination']['type'] == 'INVALID':  # noqa: E501
            return httpx.Response(
                400, json={'error': {'data': {'code': 4226}}}
            )
        if self.ship['data']['nav']['route']['destination']['type'] == 'IGNORE':  # noqa: E501
            return httpx.Response(200, json=self.refuel)
        payload = json.loads(request.content.decode('utf8'))
        units = int(payload.get('units',  0))
        capacity = self.refuel['data']['fuel']['capacity']
        current = self.refuel['data']['fuel']['current']
        delta = capacity - current
        if units == 0:
            units = delta
        self.refuel['data']['fuel']['current'] += units
        self.refuel['data']['transaction']['units'] = units
        price = self.refuel['data']['transaction']['pricePerUnit']
        self.refuel['data']['transaction']['totalPrice'] = price * units
        return httpx.Response(200, json=self.refuel)

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.ship = copy.deepcopy(self.orig_ship)
        self.orbit = copy.deepcopy(self.orig_orbit)
        self.dock = copy.deepcopy(self.orig_dock)
        self.refuel = copy.deepcopy(self.orig_refuel)
        self.always_fail = False
        self.num_fails = 0
        self.max_fails = -1


class FlightModeSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        payload = json.loads(request.content.decode('utf8'))
        self.data['data']['flightMode'] = payload['flightMode']
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)


class MarketSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.fail = False

    def __call__(self, request, route):
        if self.fail:
            return httpx.Response(404, json={'data': {'code': 404}})
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.fail = False
