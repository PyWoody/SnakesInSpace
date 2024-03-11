import httpx
import inspect
import json
import os
import pytest

import snisp

from . import DATA_DIR


class TestSystems:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    def test_repr(self, respx_mock):
        assert repr(self.agent.systems) == f'Systems({self.agent!r})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_list_systems(self, respx_mock):
        systems_data = json.load(
            open(os.path.join(DATA_DIR, 'systems.json'), encoding='utf8')
        )
        respx_mock.get('/systems', params={'page': 1}).mock(
            return_value=httpx.Response(200, json=systems_data)
        )
        respx_mock.get('/systems', params={'page': 2}).mock(
                return_value=httpx.Response(200, json={'data': []})
        )

        systems = list(self.agent.systems)
        assert len(systems) == 2
        assert systems[0].symbol == 'TEST-SYSTEM'
        assert systems[0].sectorSymbol == 'TEST'
        assert systems[1].factions[0].symbol == 'ANCIENTS'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_find(self, respx_mock):
        systems_data = json.load(
            open(os.path.join(DATA_DIR, 'systems.json'), encoding='utf8')
        )
        respx_mock.get('/systems', params={'page': 1}).mock(
            return_value=httpx.Response(200, json=systems_data)
        )
        respx_mock.get('/systems', params={'page': 2}).mock(
                return_value=httpx.Response(200, json={'data': []})
        )

        system = self.agent.systems.find(type='NEUTRON_STAR')
        assert system.type == 'NEUTRON_STAR'
        assert system.symbol == 'TEST-SYSTEM'
        assert system.sectorSymbol == 'TEST'
        assert system.factions[0].symbol == 'COSMIC'

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            self.agent.systems.find(type='INVALID')

        assert not self.agent.systems.find(type='UNSTABLE')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_find_all(self, respx_mock):
        systems_data = json.load(
            open(os.path.join(DATA_DIR, 'systems.json'), encoding='utf8')
        )
        respx_mock.get('/systems', params={'page': 1}).mock(
            return_value=httpx.Response(200, json=systems_data)
        )
        respx_mock.get('/systems', params={'page': 2}).mock(
                return_value=httpx.Response(200, json={'data': []})
        )

        systems = list(self.agent.systems.find_all(type='BLACK_HOLE'))
        assert systems[0].type == 'BLACK_HOLE'
        assert systems[0].symbol == 'TEST-SYSTEM'
        assert systems[0].sectorSymbol == 'TEST'
        assert systems[0].factions[0].symbol == 'ANCIENTS'

        with pytest.raises(snisp.exceptions.SpaceAttributeError):
            next(self.agent.systems.find_all(type='INVALID'))


class TestSystem:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    def test_repr(self, respx_mock):
        system = snisp.systems.System(self.agent)
        assert repr(system) == f'System({self.agent!r})'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_call(self, respx_mock):
        system_data = json.load(
            open(os.path.join(DATA_DIR, 'system.json'), encoding='utf8')
        )
        respx_mock.get('/systems/TEST-SYSTEM').mock(
            return_value=httpx.Response(200, json=system_data)
        )

        system = snisp.systems.System(self.agent)
        system = system('TEST-SYSTEM')

        assert system.to_dict() == system_data['data']
        assert system.type == 'NEUTRON_STAR'
        assert system.symbol == 'TEST-SYSTEM'
        assert system.sectorSymbol == 'TEST'
        assert system.factions[0].symbol == 'COSMIC'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_scan(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        respx_mock.get('/my/ships/TEST_SHIP_SYMBOL').mock(
            return_value=httpx.Response(200, json=ship_data)
        )
        scan_data = json.load(
            open(os.path.join(DATA_DIR, 'system_scan.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/scan/systems').mock(
            return_value=httpx.Response(200, json=scan_data)
        )
        orbit_data = json.load(
            open(os.path.join(DATA_DIR, 'orbit.json'), encoding='utf8')
        )
        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/orbit').mock(
            return_value=httpx.Response(200, json=orbit_data)
        )

        ship = self.agent.fleet('TEST_SHIP_SYMBOL')
        scans = ship.system.scan()
        assert inspect.isgenerator(scans)
        scans = list(scans)
        assert ship.cooldown.total_seconds == 60
        assert ship.cooldown.remaining_seconds == 59
        assert len(scans) == 1
        for scan, scan_json in zip(scans, scan_data['data']['systems']):
            assert scan.to_dict() == scan_json
