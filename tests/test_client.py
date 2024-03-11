import httpx
import pytest

import snisp


class TestSpaceClient:

    token = snisp.client.load_user(symbol='testing', faction='testing')
    client = snisp.client.SpaceClient(token=token)

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_init(self, respx_mock):
        assert str(self.client.base_url) == 'https://api.spacetraders.io/v2/'

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_closing(self, respx_mock):
        client = snisp.client.SpaceClient(token=self.token)
        assert not client.is_closed

        client = snisp.client.SpaceClient(token=self.token)
        assert not client.is_closed
        client.cleanup()
        assert client.is_closed

        client = snisp.client.SpaceClient(token=self.token)
        assert not client.is_closed
        client.__del__()  # Not great. Just used to shut up pytest
        assert client.is_closed

        client = snisp.client.SpaceClient(token=self.token)
        assert not client.is_closed
        snisp.client.cleanup_client(client)
        assert client.is_closed
        snisp.client.cleanup_client('fake_client')

    @pytest.mark.respx(base_url='https://api.spacetraders.io/v2')
    def test_unused_options(self, respx_mock):
        # Now with real fake tests!
        # (this actually exposed what would have been a bug in
        # one of the unused paths) :/
        respx_mock.delete('').mock(
            httpx.Response(200, json={'data': 'delete'})
        )
        response = self.client.delete('/')
        assert response.json()['data'] == 'delete'
        respx_mock.options('').mock(
            httpx.Response(200, json={'data': 'options'})
        )
        response = self.client.options('')
        assert response.json()['data'] == 'options'
        respx_mock.put('/').mock(
            httpx.Response(200, json={'data': 'put'})
        )
        response = self.client.put('')
        assert response.json()['data'] == 'put'
