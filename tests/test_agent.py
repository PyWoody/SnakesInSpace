import httpx
import json
import pytest
import os

import snisp

from . import DATA_DIR, attribute_test


class TestAgent:

    agent = snisp.agent.Agent(symbol='testing', faction='testing')

    def test_agent(self, respx_mock):
        assert self.agent.symbol == 'TESTING'
        assert self.agent.faction == 'TESTING'
        assert self.agent.email == 'TESTING'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_data(self, respx_mock):
        json_data = json.load(
            open(os.path.join(DATA_DIR, 'agent_data.json'), encoding='utf8')
        )
        respx_mock.get('/my/agent').mock(
            return_value=httpx.Response(200, json=json_data)
        )
        response = self.agent.data
        assert response == snisp.agent.PlayerData(
            self.agent, json_data['data']
        )
        attribute_test(response, json_data['data'])
