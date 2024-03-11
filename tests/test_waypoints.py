import copy
import httpx
import inspect
import json
import os
import pytest

from datetime import datetime, timedelta, timezone
from respx.patterns import M

import snisp

from . import DATA_DIR, GenericSideEffect


class TestWaypoints:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    def test_repr(self, respx_mock):
        assert repr(self.agent.factions) == f'Factions({self.agent!r})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_chart(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        chart_data = json.load(
            open(os.path.join(DATA_DIR, 'chart.json'), encoding='utf8')
        )
        chart_side_effect = ChartSideEffect(chart_data)
        chart_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/chart')
        chart_route.side_effect = chart_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        chart = ship.waypoints.chart()
        assert chart.to_dict() == chart_data['data']

        # 4230: WaypointChartedError
        with chart_side_effect as tmp:
            tmp.already_charted = True
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            chart = ship.waypoints.chart()
            assert chart.to_dict() == {}

        # .raised_at
        with chart_side_effect as tmp:
            tmp.fail = True
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            try:
                chart = ship.waypoints.chart()
            except snisp.exceptions.ClientError as e:
                _ = e.raised_at

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_scan(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        scan_data = json.load(
            open(
                os.path.join(DATA_DIR, 'scan_waypoints.json'), encoding='utf8'
            )
        )
        scan_side_effect = GenericSideEffect(scan_data)
        scan_route = respx_mock.post(
            '/my/ships/TEST_SHIP_SYMBOL/scan/waypoints'
        )
        scan_route.side_effect = scan_side_effect
        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        scan = ship.waypoints.scan()
        assert inspect.isgenerator(scan)
        scans = list(scan)
        assert ship.cooldown.total_seconds == 60
        assert ship.cooldown.remaining_seconds == 59
        assert len(scans) == 1
        for scan, scan_json in zip(scans, scan_data['data']['waypoints']):
            assert scan.to_dict() == scan_json

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_best_survey(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_data['data']['nav']['route']['destination']['type'] = 'ASTEROID'
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        survey_data = json.load(
            open(os.path.join(DATA_DIR, 'survey.json'), encoding='utf8')
        )
        expires = str(datetime.now(timezone.utc) + timedelta(hours=1))
        for survey in survey_data['data']['surveys']:
            survey['expiration'] = expires
        survey_side_effect = SurveySideEffect(survey_data)
        survey_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/survey')
        survey_route.side_effect = survey_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        survey = ship.waypoints.survey()
        best = survey.best()
        assert best.size == 'LARGE'

        best = survey.best('INVALID')
        assert not best

        best = survey.best('PRECIOUS_STONES', 'IRON_ORE')
        assert best.size == 'LARGE'
        symbols = {i.symbol for i in best.deposits}
        assert 'IRON_ORE' in symbols

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_survey(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_data['data']['nav']['route']['destination']['type'] = 'ASTEROID'
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect

        survey_data = json.load(
            open(os.path.join(DATA_DIR, 'survey.json'), encoding='utf8')
        )
        expires = str(datetime.now(timezone.utc) + timedelta(hours=1))
        for survey in survey_data['data']['surveys']:
            survey['expiration'] = expires
        survey_side_effect = SurveySideEffect(survey_data)
        survey_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/survey')
        survey_route.side_effect = survey_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        survey = ship.waypoints.survey()
        assert len(survey.surveys) == 3
        assert ship.cooldown.total_seconds == 60
        assert ship.cooldown.remaining_seconds == 59

        # 4240: ShipMissingSurveyorError
        with survey_side_effect as tmp:
            tmp.no_mounts = True
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ShipMissingSurveyorError
            ):
                ship.waypoints.survey()

        # 4222: ShipSurveyWaypointTypeError
        with ship_side_effect as tmp:
            tmp.data['data']['nav']['route']['destination']['type'] = 'PLANET'
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ShipSurveyWaypointTypeError
            ):
                ship.waypoints.survey()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_surveys(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_data['data']['nav']['route']['destination']['type'] = 'ASTEROID'
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_side_effect = GenericSideEffect(ship_data)
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = ship_side_effect
        ships_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_ships.json'),
                encoding='utf8'
            )
        )
        ships_side_effect = ShipsSideEffect(ships_data)
        ships_route = respx_mock.get('/my/ships')
        ships_route.side_effect = ships_side_effect

        survey_data = json.load(
            open(os.path.join(DATA_DIR, 'survey.json'), encoding='utf8')
        )
        expires = str(datetime.now(timezone.utc) + timedelta(hours=1))
        for survey in survey_data['data']['surveys']:
            survey['expiration'] = expires
        survey_side_effect = SurveySideEffect(survey_data)
        survey_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/survey')
        survey_route.side_effect = survey_side_effect

        # Good survey
        with ships_side_effect as tmp:
            tmp.data['data'][0]['symbol'] = 'TEST_SHIP_SYMBOL'
            tmp.data['data'][0]['nav']['systemSymbol'] = 'TEST-SYSTEM'
            tmp.data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            tmp.data['data'][0]['nav']['route']['destination']['type'] = 'ASTEROID'  # noqa: E501
            tmp.data['data'][0]['nav']['status'] = 'IN_ORBIT'
            tmp.data['data'][0]['mounts'][0]['symbol'] = 'MOUNT_SURVEYOR_II'

            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            surveys = ship.waypoints.surveys()
            assert inspect.isgenerator(surveys)
            surveys = list(surveys)
            assert len(surveys) == 1

        # Failed survey
        with ships_side_effect as ship_tmp, survey_side_effect as survey_tmp:
            ship_tmp.data['data'][0]['symbol'] = 'TEST_SHIP_SYMBOL'
            ship_tmp.data['data'][0]['nav']['systemSymbol'] = 'TEST-SYSTEM'
            ship_tmp.data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            ship_tmp.data['data'][0]['nav']['route']['destination']['type'] = 'ASTEROID'  # noqa: E501
            ship_tmp.data['data'][0]['nav']['status'] = 'IN_ORBIT'
            ship_tmp.data['data'][0]['mounts'][0]['symbol'] = 'MOUNT_SURVEYOR_II'  # noqa: E501
            survey_tmp.no_mounts = True

            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            surveys = list(ship.waypoints.surveys())

        # Only one waypoint surveyed
        with ships_side_effect as tmp:
            tmp.data['data'][0]['symbol'] = 'TEST_SHIP_SYMBOL'
            tmp.data['data'][0]['nav']['systemSymbol'] = 'TEST-SYSTEM'
            tmp.data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            tmp.data['data'][0]['nav']['route']['destination']['type'] = 'ASTEROID'  # noqa: E501
            tmp.data['data'][0]['nav']['status'] = 'IN_ORBIT'
            tmp.data['data'][0]['mounts'][0]['symbol'] = 'MOUNT_SURVEYOR_II'
            tmp.data['data'][1]['symbol'] = 'TEST_SHIP_SYMBOL'
            tmp.data['data'][1]['nav']['systemSymbol'] = 'TEST-SYSTEM'
            tmp.data['data'][1]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'  # noqa: E501
            tmp.data['data'][1]['nav']['route']['destination']['type'] = 'ASTEROID'  # noqa: E501
            tmp.data['data'][1]['nav']['status'] = 'IN_ORBIT'
            tmp.data['data'][1]['mounts'][0]['symbol'] = 'MOUNT_SURVEYOR_II'

            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            surveys = ship.waypoints.surveys()
            assert inspect.isgenerator(surveys)
            surveys = list(surveys)
            assert len(surveys) == 1

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_iter(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
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
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        waypoints = list(ship.waypoints)
        assert len(waypoints) == 3

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_call(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
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
        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        waypoints = ship.waypoints()
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints(traits='UNCHARTED')
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints(types='PLANET')
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints(traits='UNCHARTED')
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints(filters={'isUnderConstruction': False})
        assert snisp.utils.ilen(waypoints) == 0
        waypoints = ship.waypoints(filters={'isUnderConstruction': True})
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints(system_symbol='TEST-SYSTEM')
        assert snisp.utils.ilen(waypoints) == 3

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            waypoints = next(ship.waypoints(traits='INVALID'))

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            waypoints = next(ship.waypoints(types='INVALID'))

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_get(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_side_effect = GenericSideEffect(waypoint_data)
        waypoint_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT'
        )
        waypoint_route.side_effect = waypoint_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        waypoint = ship.waypoints.get()

        assert waypoint.to_dict() == waypoint_data['data']
        assert waypoint == ship.waypoints.get(waypoint=waypoint)
        assert waypoint == ship.waypoints.get(system_symbol='TEST-SYSTEM')
        assert waypoint == ship.waypoints.get(
            waypoint_symbol='TEST-SYSTEM-WAYPOINT'
        )
        assert waypoint == ship.waypoints.get(
            system_symbol='TEST-SYSTEM', waypoint_symbol='TEST-SYSTEM-WAYPOINT'
        )
        assert snisp.waypoints.is_uncharted(waypoint)

        with waypoint_side_effect as tmp:
            for trait in tmp.data['data']['traits']:
                if trait['symbol'] == 'UNCHARTED':
                    trait['symbol'] = 'CHARTED'
            waypoint = ship.waypoints.get()
            assert not snisp.waypoints.is_uncharted(waypoint)


class TestWaypoint:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_data(self, respx_mock):
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['waypointSymbol'] = waypoint_data['data']['symbol']  # noqa: E501
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT'
        ).mock(
            return_value=httpx.Response(200, json=waypoint_data)
        )

        waypoint = snisp.waypoints.Waypoint(self.agent, waypoint_data['data'])

        assert waypoint.data.to_dict() == waypoint.to_dict()
        assert waypoint.data.to_dict() == waypoint_data['data']

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_supply_construction_data(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['cargo']['capacity'] = 40
        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )

        supply_data = json.load(
            open(
                os.path.join(DATA_DIR, 'supply_construction_site.json'),
                encoding='utf8'
            )
        )
        construction_data = json.load(
            open(
                os.path.join(DATA_DIR, 'construction_site.json'),
                encoding='utf8'
            )
        )
        construction_data['data']['systemSymbol'] = 'TEST-SYSTEM'
        construction_data['data']['isComplete'] = False
        construction_data['data']['systemSymbol'] = 'TEST-SYSTEM'
        construction_data['data']['materials'][0]['required'] = 40
        construction_data['data']['materials'][0]['fulfilled'] = 10

        supply_data['data']['systemSymbol'] = 'TEST-SYSTEM'
        supply_data['data']['construction']['materials'][0]['required'] = 40
        supply_data['data']['construction']['materials'][0]['fulfilled'] = 10
        supply_data['data']['cargo']['capacity'] = 40

        construction_side_effect = SupplyConstructionSiteSideEffect(
            data=supply_data,
            site_data=construction_data,
            ship_data=ship_data,
        )
        supply_route = respx_mock.post(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-CONSTRUCTION/construction/supply'
        )
        supply_route.side_effect = construction_side_effect

        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = construction_side_effect.ship

        construction_site = snisp.waypoints.ConstructionSite(
            self.agent, construction_data['data']
        )

        # Supply until completed
        with construction_side_effect as tmp:
            tmp.ship_data['data']['cargo']['capacity'] = 40
            tmp.ship_data['data']['cargo']['units'] = 40
            tmp.ship_data['data']['cargo']['inventory'][0] = {
                'symbol': 'PRECIOUS_STONES', 'units': 40
            }
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            while not construction_site.is_complete:
                prev_supply_count = construction_site.materials[0].fulfilled
                prev_cargo_count = ship.cargo.units
                construction_site.supply(
                    ship=ship, trade_symbol='PRECIOUS_STONES', units=5
                )
                assert ship.cargo.units == prev_cargo_count - 5
                assert construction_site.materials[0].fulfilled == prev_supply_count + 5  # noqa: E501
                prev_supply_count = construction_site.materials[0].fulfilled
                prev_cargo_count = ship.cargo.units
            assert construction_site.is_complete
            assert construction_site.materials[0].fulfilled == construction_site.materials[0].required  # noqa: E501
            assert ship.cargo.units == 10

        # 4800: ConstructionMaterialNotRequired
        with construction_side_effect as tmp:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ConstructionMaterialNotRequired
            ):
                construction_site.supply(
                    ship=ship, trade_symbol='INVALID', units=5
                )

        # 4801: ConstructionMaterialFulfilled
        with construction_side_effect as tmp:
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ConstructionMaterialFulfilled
            ):
                construction_site.supply(
                    ship=ship, trade_symbol='PRECIOUS_STONES', units=50
                )

        # 4802: ShipConstructionInvalidLocationError
        with construction_side_effect as tmp:
            tmp.invalid = True
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            with pytest.raises(
                snisp.exceptions.ShipConstructionInvalidLocationError
            ):
                construction_site.supply(
                    ship=ship, trade_symbol='PRECIOUS_STONES', units=50
                )

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_construction_data(self, respx_mock):
        construction_data = json.load(
            open(
                os.path.join(DATA_DIR, 'construction_site.json'),
                encoding='utf8'
            )
        )
        construction_data['data']['systemSymbol'] = 'TEST-SYSTEM'
        respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/'
            'TEST-SYSTEM-CONSTRUCTION/construction'
        ).mock(
            return_value=httpx.Response(200, json=construction_data)
        )

        construction_site = snisp.waypoints.ConstructionSite(
            self.agent, construction_data['data']
        )

        assert construction_site.data.to_dict() == construction_site.to_dict()  # noqa: E501
        assert construction_site.data.to_dict() == construction_data['data']

        construction_site_data = snisp.waypoints.ConstructionSiteData(
            self.agent, construction_data['data']
        )
        assert construction_site_data.refresh().to_dict() == construction_site_data.to_dict()  # noqa: E501
        assert construction_site_data.refresh().to_dict() == construction_data['data']  # noqa: E501

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_refresh(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_side_effect = GenericSideEffect(waypoint_data)
        waypoint_route = respx_mock.get(
            '/systems/TEST-SYSTEM/waypoints/TEST-SYSTEM-WAYPOINT'
        )
        waypoint_route.side_effect = waypoint_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        waypoint = ship.waypoints.get()

        assert waypoint.to_dict() == ship.waypoints.refresh(waypoint).to_dict()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_search(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
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

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        waypoints = ship.waypoints.search()
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints.search(traits='UNCHARTED')
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints.search(types='PLANET')
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints.search(traits='UNCHARTED')
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints.search(
            filters={'isUnderConstruction': False}
        )
        assert snisp.utils.ilen(waypoints) == 0
        waypoints = ship.waypoints.search(
            filters={'isUnderConstruction': True}
        )
        assert snisp.utils.ilen(waypoints) == 3
        waypoints = ship.waypoints.search(system_symbol='TEST-SYSTEM')
        assert snisp.utils.ilen(waypoints) == 3

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            waypoints = next(ship.waypoints.search(traits='INVALID'))

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            waypoints = next(ship.waypoints.search(types='INVALID'))

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_by_types(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        waypoints_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoints.json'), encoding='utf8')
        )
        waypoints_side_effect = WaypointsSideEffect(waypoints_data)
        waypoints_route = respx_mock.get('/systems/TEST-SYSTEM/waypoints')
        waypoints_route.side_effect = waypoints_side_effect

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        with waypoints_side_effect as tmp:
            assert snisp.utils.ilen(
                ship.waypoints.construction_sites()
            ) == 3

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['traits'][0]['symbol'] = 'SHIPYARD'
            assert snisp.utils.ilen(ship.waypoints.shipyards()) == 1

        with waypoints_side_effect as tmp:
            assert snisp.utils.ilen(ship.waypoints.shipyards()) == 0

        with waypoints_side_effect as tmp:
            assert snisp.utils.ilen(ship.waypoints.planets()) == 3

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.planets()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'GAS_GIANT'
            assert snisp.utils.ilen(ship.waypoints.gas_giants()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.gas_giants()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'MOON'
            assert snisp.utils.ilen(ship.waypoints.moons()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.moons()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'ORBITAL_STATION'
            assert snisp.utils.ilen(ship.waypoints.orbital_stations()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.orbital_stations()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'JUMP_GATE'
            respx_mock.get(
                '/systems/TEST-SYSTEM/waypoints/'
                'TEST-SYSTEM-FARTHESTWAYPOINT/jump-gate'
            ).mock(
                return_value=httpx.Response(
                    200, json={'data': tmp.data['data'][-1]}
                )
            )
            assert snisp.utils.ilen(ship.waypoints.jump_gates()) == 1
            jump_gate = next(ship.waypoints.jump_gates())
            assert jump_gate.data.to_dict() == jump_gate.to_dict()

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.jump_gates()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'ASTEROID_FIELD'
            assert snisp.utils.ilen(ship.waypoints.asteroid_fields()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.asteroid_fields()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'ASTEROID'
            assert snisp.utils.ilen(ship.waypoints.asteroids()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.asteroids()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'ENGINEERED_ASTEROID'
            assert snisp.utils.ilen(ship.waypoints.engineered_asteroids()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.engineered_asteroids()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'ASTEROID_BASE'
            assert snisp.utils.ilen(ship.waypoints.asteroid_bases()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.asteroid_bases()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'NEBULA'
            assert snisp.utils.ilen(ship.waypoints.nebulas()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.nebulas()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'DEBRIS_FIELD'
            assert snisp.utils.ilen(ship.waypoints.debris_fields()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.debris_fields()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'GRAVITY_WELL'
            assert snisp.utils.ilen(ship.waypoints.gravity_wells()) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(ship.waypoints.gravity_wells()) == 0

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'ARTIFICIAL_GRAVITY_WELL'
            assert snisp.utils.ilen(
                ship.waypoints.artificial_gravity_wells()
            ) == 1

        with waypoints_side_effect as tmp:
            tmp.data['data'][-1]['type'] = 'FUEL_STATION'
            assert snisp.utils.ilen(
                (i for i in ship.waypoints if i.type == 'FUEL_STATION')
            ) == 1

        with waypoints_side_effect as tmp:
            for wp in tmp.data['data']:
                wp['type'] = 'INVALID'
            assert snisp.utils.ilen(
                ship.waypoints.artificial_gravity_wells()
            ) == 0

    def test_class_factory(self, respx_mock):
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        cls = snisp.waypoints.class_factory('Waypoint')
        waypoint = cls(self.agent, waypoint_data['data'])
        assert waypoint.to_dict() == waypoint_data['data']
        cls = snisp.waypoints.class_factory('FakeWaypointType')
        waypoint = cls(self.agent, waypoint_data['data'])
        assert waypoint.to_dict() == waypoint_data['data']

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_best_asteroid(self, respx_mock):
        ships_data = json.load(
            open(
                os.path.join(DATA_DIR, 'fleet_list_ships.json'),
                encoding='utf8'
            )
        )
        ships_data['data'][0]['symbol'] = 'TEST_SHIP_SYMBOL'
        ships_data['data'][0]['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ships_data['data'][0]['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ships_data['data'][0]['nav']['status'] = 'IN_ORBIT'
        ships_data['data'][0]['nav']['route']['destination']['type'] = 'ASTEROID'  # noqa: E501
        ships_data['data'][0]['mounts'][0]['symbol'] = 'MOUNT_SURVEYOR_II'
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        ship_data['data']['nav']['systemSymbol'] = 'TEST-SYSTEM'
        ship_data['data']['nav']['waypointSymbol'] = 'TEST-SYSTEM-WAYPOINT'
        ship_data['data']['nav']['status'] = 'IN_ORBIT'
        ship_data['data']['nav']['route']['destination']['type'] = 'ASTEROID'
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
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )

        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        survey_data = json.load(
            open(os.path.join(DATA_DIR, 'survey.json'), encoding='utf8')
        )
        waypoint_data = json.load(
            open(os.path.join(DATA_DIR, 'waypoint.json'), encoding='utf8')
        )
        waypoint_data['data']['type'] = 'ASTEROID'

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')

        best_asteroid_side_effect = BestAsteroidSideEffect(
            contracts=contracts_data,
            surveys=survey_data,
            waypoint=waypoint_data,
        )

        waypoint_route = respx_mock.route(
            M(path__regex=r'/systems/TEST-SYSTEM/waypoints/.*')
        )
        waypoint_route.side_effect = best_asteroid_side_effect.waypoint

        contracts_route = respx_mock.get('/my/contracts')
        contracts_route.side_effect = best_asteroid_side_effect.contracts

        survey_route = respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/survey')
        survey_route.side_effect = best_asteroid_side_effect.survey

        asteroid = snisp.waypoints.best_asteroid(ship)
        assert asteroid.type in snisp.utils.SURVEYABLE_WAYPOINTS

        asteroid = snisp.waypoints.best_asteroid(ship, 'IRON_ORE')
        assert asteroid.type in snisp.utils.SURVEYABLE_WAYPOINTS

        assert not snisp.waypoints.best_asteroid(ship, 'INVALID')

        with best_asteroid_side_effect as tmp:
            for survey in tmp.surveys_data['data']['surveys']:
                survey['size'] = 'MODERATE'
            asteroid = snisp.waypoints.best_asteroid(ship)
            assert asteroid.type in snisp.utils.SURVEYABLE_WAYPOINTS

        with best_asteroid_side_effect as tmp:
            for survey in tmp.surveys_data['data']['surveys']:
                survey['size'] = 'SMALL'
            asteroid = snisp.waypoints.best_asteroid(ship)
            assert asteroid.type in snisp.utils.SURVEYABLE_WAYPOINTS

        with best_asteroid_side_effect as tmp:
            tmp.contracts_data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'IRON_ORE'  # noqa: E501
            tmp.contracts_data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 0  # noqa: E501
            tmp.contracts_data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100  # noqa: E501
            contract = self.agent.contracts.current
            assert snisp.waypoints.best_asteroid(ship, contract=contract)


class ChartSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.already_charted = False
        self.fail = False

    def __call__(self, request, route):
        if self.already_charted:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4230}}}
            )
        if self.fail:
            return httpx.Response(400, json={})
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.already_charted = False
        self.fail = False


class SurveySideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.no_mounts = False

    def __call__(self, request, route):
        if self.no_mounts:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4240}}}
            )
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.no_mounts = False


class ShipsSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': []})
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)


class WaypointsSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': []})
        if traits := request.url.params.get('traits'):
            output = []
            for wp in self.data['data']:
                if any(i['symbol'] == traits for i in wp['traits']):
                    output.append(wp)
            self.data['data'] = output
        if types := request.url.params.get('type'):
            output = []
            for wp in self.data['data']:
                if types == wp['type']:
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


class SupplyConstructionSiteSideEffect:

    def __init__(self, *, data, site_data, ship_data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_site_data = site_data
        self.site_data = copy.copy(self.orig_site_data)
        self.orig_ship_data = ship_data
        self.ship_data = copy.deepcopy(self.orig_ship_data)
        self.invalid = False

    def __call__(self, request, route):
        if self.invalid:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4802}}}
            )
        payload = json.loads(request.content.decode('utf8'))
        units = int(payload['units'])
        material = next(
            (
                m for m in self.data['data']['construction']['materials']
                if payload['tradeSymbol'] == m['tradeSymbol']
            ), None
        )
        if material is None:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4800}}}
            )
        if units > material['required']:
            return httpx.Response(
                400, json={'error': {'data': {'code': 4801}}}
            )
        material['fulfilled'] += units
        self.ship_data['data']['cargo']['units'] -= units
        out_inventory = []
        for item in self.ship_data['data']['cargo']['inventory']:
            if item['symbol'] == payload['tradeSymbol']:
                item['units'] -= units
                if item['units'] > 0:
                    out_inventory.append(item)
        if all(
            m['required'] == m['fulfilled']
            for m in self.data['data']['construction']['materials']
        ):
            self.data['data']['construction']['isComplete'] = True
            self.site_data['data']['isComplete'] = True
        self.ship_data['data']['cargo']['inventory'] = out_inventory
        self.data['data']['cargo'] = self.ship_data['data']['cargo']
        return httpx.Response(200, json=self.data)

    def ship(self, request, route):
        return httpx.Response(200, json=self.ship_data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.site_data = copy.copy(self.orig_site_data)
        self.ship_data = copy.deepcopy(self.orig_ship_data)
        self.invalid = False


class BestAsteroidSideEffect:

    def __init__(self, *, contracts, surveys, waypoint):
        self.orig_contracts = contracts
        self.contracts_data = copy.deepcopy(self.orig_contracts)
        self.orig_surveys = surveys
        self.surveys_data = copy.deepcopy(self.orig_surveys)
        self.orig_waypoint = waypoint
        self.waypoint_data = copy.deepcopy(self.orig_waypoint)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def contracts(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': []})
        return httpx.Response(200, json=self.contracts_data)

    def survey(self, request, route):
        return httpx.Response(200, json=self.surveys_data)

    def waypoint(self, request, route):
        return httpx.Response(200, json=self.waypoint_data)

    def reset(self):
        self.contracts_data = copy.deepcopy(self.orig_contracts)
        self.surveys_data = copy.deepcopy(self.orig_surveys)
        self.waypoint_data = copy.deepcopy(self.orig_waypoint)
