import copy
import httpx
import json
import os
import pytest

from datetime import datetime, timedelta, timezone

import snisp

from . import DATA_DIR


class TestContracts:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_iter(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        respx_mock.get(
            '/my/contracts', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=contracts_data)
        )
        respx_mock.get(
            '/my/contracts', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        contracts = self.agent.contracts
        contracts = list(contracts)
        assert len(contracts) == 2
        assert contracts[0].fulfilled is True
        assert contracts[1].fulfilled is False

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_call(self, respx_mock):
        contract_data = json.load(
            open(os.path.join(DATA_DIR, 'contract.json'), encoding='utf8')
        )
        contract_data['data']['contract']['id'] = 'CONTRACT-ID'
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contracts_data['data'][-1]['id'] = 'CONTRACT-ID'
        respx_mock.get(
            '/my/contracts', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=contracts_data)
        )
        respx_mock.get(
            '/my/contracts', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )
        respx_mock.get(
            '/my/contracts/CONTRACT-ID'
        ).mock(
            return_value=httpx.Response(
                200, json={'data': contract_data['data']['contract']}
            )
        )

        contract = list(self.agent.contracts)[-1]
        assert not contract.accepted
        assert self.agent.contracts(contract.id) == contract

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_current(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        respx_mock.get(
            '/my/contracts', params={'page': 1}
        ).mock(
            return_value=httpx.Response(200, json=contracts_data)
        )
        respx_mock.get(
            '/my/contracts', params={'page': 2}
        ).mock(
            return_value=httpx.Response(200, json={'data': []})
        )

        contract = list(self.agent.contracts)[-1]
        assert contract == self.agent.contracts.current


class TestContract:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_accept(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contract_side_effect = ContractsSideEffect(contracts_data)
        contract_route = respx_mock.get('/my/contracts')
        contract_route.side_effect = contract_side_effect

        accept_contract_route = respx_mock.post(
            f'/my/contracts/{contracts_data["data"][-1]["id"]}/accept'
        )
        accept_contract_route.side_effect = contract_side_effect.accept

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['accepted'] = False
            assert not self.agent.contracts.current.accepted

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['accepted'] = True
            assert self.agent.contracts.current.accepted

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['accepted'] = False
            contract = self.agent.contracts.current
            contract.accept()
            assert contract.accepted

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_fulfilled(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contract_side_effect = ContractsSideEffect(contracts_data)
        contract_route = respx_mock.get('/my/contracts')
        contract_route.side_effect = contract_side_effect

        accept_contract_route = respx_mock.post(
            f'/my/contracts/{contracts_data["data"][-1]["id"]}/fulfill'
        )
        accept_contract_route.side_effect = contract_side_effect.fulfill

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['fulfilled'] = False
            assert not self.agent.contracts.current.fulfilled

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['fulfilled'] = True
            assert self.agent.contracts.current.fulfilled

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['fulfilled'] = False
            contract = self.agent.contracts.current
            contract.fulfill()
            assert contract.fulfilled

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_expired(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contract_side_effect = ContractsSideEffect(contracts_data)
        contract_route = respx_mock.get('/my/contracts')
        contract_route.side_effect = contract_side_effect

        assert self.agent.contracts.current.expired

        with contract_side_effect as tmp:
            expiration = datetime.now(timezone.utc) + timedelta(hours=1)
            tmp.data['data'][-1]['terms']['deadline'] = str(expiration)
            assert not self.agent.contracts.current.expired

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_refresh(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contract_side_effect = ContractsSideEffect(contracts_data)
        contract_route = respx_mock.get('/my/contracts')
        contract_route.side_effect = contract_side_effect

        respx_mock.get(
            f'/my/contracts/{contracts_data["data"][-1]["id"]}'
        ).mock(
            return_value=httpx.Response(
                200, json={'data': contracts_data['data'][-1]}
            )
        )

        contract = self.agent.contracts.current
        assert contract == contract.refresh()

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'INVALID'  # noqa: E501
            contract = self.agent.contracts.current
            assert contract != contract.refresh()

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_extractable(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contract_side_effect = ContractsSideEffect(contracts_data)
        contract_route = respx_mock.get('/my/contracts')
        contract_route.side_effect = contract_side_effect

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'IRON_ORE'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 0
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100  # noqa: E501
            contract = self.agent.contracts.current
            assert contract.extractable
            assert contract.__dict__['_data']['type'] == contract.type

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'IRON_ORE'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 0
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100  # noqa: E501
            contract = self.agent.contracts.current
            with pytest.raises(AttributeError):
                contract.update_data_item('INVALID', '')
            with pytest.raises(AttributeError):
                contract.extractable = False

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'INVALID'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 0
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100  # noqa: E501
            contract = self.agent.contracts.current
            assert not contract.extractable

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_siphonable(self, respx_mock):
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contract_side_effect = ContractsSideEffect(contracts_data)
        contract_route = respx_mock.get('/my/contracts')
        contract_route.side_effect = contract_side_effect

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'LIQUID_HYDROGEN'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 0
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100  # noqa: E501
            contract = self.agent.contracts.current
            assert contract.siphonable

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'INVALID'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 0
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100  # noqa: E501
            contract = self.agent.contracts.current
            assert not contract.siphonable

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_deliver(self, respx_mock):
        ship_data = json.load(
            open(os.path.join(DATA_DIR, 'ship_info.json'), encoding='utf8')
        )
        contracts_data = json.load(
            open(os.path.join(DATA_DIR, 'contracts.json'), encoding='utf8')
        )
        contract_side_effect = ContractsSideEffect(
            contracts_data, ship_data=ship_data
        )
        contract_route = respx_mock.get('/my/contracts')
        contract_route.side_effect = contract_side_effect
        ship_route = respx_mock.get('/my/ships/TEST_SHIP_SYMBOL')
        ship_route.side_effect = contract_side_effect.ship
        deliver_contract_route = respx_mock.post(
            f'/my/contracts/{contracts_data["data"][-1]["id"]}/deliver'
        )
        deliver_contract_route.side_effect = contract_side_effect.deliver

        dock_data = json.load(
            open(os.path.join(DATA_DIR, 'dock.json'), encoding='utf8')
        )

        respx_mock.post('/my/ships/TEST_SHIP_SYMBOL/dock').mock(
            return_value=httpx.Response(200, json=dock_data)
        )

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'IRON_ORE'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100
            tmp.ship_data['data']['cargo']['units'] = 40
            tmp.ship_data['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'  # noqa: E501
            tmp.ship_data['data']['cargo']['inventory'][0]['units'] = 40
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            contract = self.agent.contracts.current
            contract.deliver(ship, 'IRON_ORE')
            assert contract.terms.deliver[0].units_required == 100
            assert contract.terms.deliver[0].units_fulfilled == 40
            assert ship.cargo.units == 0
            assert ship.cargo.inventory == []

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'INVALID'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100
            tmp.ship_data['data']['cargo']['units'] = 40
            tmp.ship_data['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'  # noqa: E501
            tmp.ship_data['data']['cargo']['inventory'][0]['units'] = 40
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            contract = self.agent.contracts.current
            assert contract.deliver(ship, 'IRON_ORE') is None

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'IRON_ORE'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100
            tmp.ship_data['data']['cargo']['units'] = 40
            tmp.ship_data['data']['cargo']['inventory'][0]['symbol'] = 'INVALID'  # noqa: E501
            tmp.ship_data['data']['cargo']['inventory'][0]['units'] = 40
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            contract = self.agent.contracts.current
            contract.deliver(ship, 'IRON_ORE')
            assert contract.terms.deliver[0].units_required == 100
            assert contract.terms.deliver[0].units_fulfilled == 0
            assert ship.cargo.units == 40

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'IRON_ORE'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 100
            tmp.ship_data['data']['cargo']['units'] = 40
            tmp.ship_data['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'  # noqa: E501
            tmp.ship_data['data']['cargo']['inventory'][0]['units'] = 40
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            contract = self.agent.contracts.current
            contract.deliver(ship, 'IRON_ORE')
            assert contract.terms.deliver[0].units_required == 100
            assert contract.terms.deliver[0].units_fulfilled == 100
            assert ship.cargo.units == 40

        with contract_side_effect as tmp:
            tmp.data['data'][-1]['terms']['deliver'][0]['tradeSymbol'] = 'IRON_ORE'  # noqa: E501
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsRequired'] = 100
            tmp.data['data'][-1]['terms']['deliver'][0]['unitsFulfilled'] = 99
            tmp.ship_data['data']['cargo']['units'] = 40
            tmp.ship_data['data']['cargo']['inventory'][0]['symbol'] = 'IRON_ORE'  # noqa: E501
            tmp.ship_data['data']['cargo']['inventory'][0]['units'] = 40
            ship = self.agent.fleet('TEST_SHIP_SYMBOL')
            contract = self.agent.contracts.current
            contract.deliver(ship, 'IRON_ORE')
            assert contract.terms.deliver[0].units_required == 100
            assert contract.terms.deliver[0].units_fulfilled == 100
            assert ship.cargo.units == 39


class ContractsSideEffect:

    def __init__(self, data, *, ship_data=None):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)
        self.orig_ship_data = ship_data
        self.ship_data = copy.deepcopy(self.orig_ship_data)

    def __enter__(self):
        self.reset()
        return self

    def __call__(self, request, route):
        if int(request.url.params.get('page', 1)) > 1:
            return httpx.Response(200, json={'data': []})
        return httpx.Response(200, json=self.data)

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def accept(self, request, route):
        return httpx.Response(200)

    def fulfill(self, request, route):
        self.data['data'][-1]['fulfilled'] = True
        return httpx.Response(
            200, json={'data': {'contract': self.data['data'][-1]}}
        )

    def ship(self, request, route):
        return httpx.Response(200, json=self.ship_data)

    def deliver(self, request, route):
        payload = json.loads(request.content.decode('utf8'))
        good = payload['tradeSymbol']
        units = int(payload['units'])
        output = []
        for item in self.ship_data['data']['cargo']['inventory']:
            if item['symbol'] == good:
                item['units'] -= units
                if item['units'] > 0:
                    output.append(item)
        self.ship_data['data']['cargo']['units'] -= units
        self.ship_data['data']['cargo']['inventory'] = output
        for item in self.data['data'][-1]['terms']['deliver']:
            if item['tradeSymbol'] == good:
                item['unitsFulfilled'] += units
        return httpx.Response(
            200,
            json={
                'data': {
                    'contract': self.data['data'][-1],
                    'cargo': self.ship_data['data']['cargo'],
                }
            }
        )

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)
        self.ship_data = copy.deepcopy(self.orig_ship_data)
