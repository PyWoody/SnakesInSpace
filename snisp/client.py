import httpx
import json
import logging
import os

from collections import namedtuple
from datetime import datetime, timezone
from httpx import HTTPError

from snisp.exceptions import ClientError, SpaceUserError
from snisp.decorators import CachedRateLimiter


logger = logging.getLogger(__name__)
cached_rate_limiter = CachedRateLimiter()


UserData = namedtuple('UserData', ('symbol', 'faction', 'email', 'token'))


def cleanup_client(client):
    try:
        client.close()
    except Exception:
        pass


class SpaceClient(httpx.Client):

    def __init__(self, headers=None, token=None):
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        self.testing = False
        if token is not None:
            headers['Authorization'] = f'Bearer {token}'
            if token == 'TESTING_TOKEN':
                self.testing = True
        super().__init__(
            headers=headers, base_url='https://api.spacetraders.io/v2'
        )

    def __del__(self):
        cleanup_client(self)

    def cleanup(self):
        cleanup_client(self)

    @cached_rate_limiter
    def delete(self, *args, **kwargs):
        response = super().delete(*args, **kwargs)
        raise_for_status(response)
        return response

    @cached_rate_limiter
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        raise_for_status(response)
        return response

    @cached_rate_limiter
    def options(self, *args, **kwargs):
        response = super().options(*args, **kwargs)
        raise_for_status(response)
        return response

    @cached_rate_limiter
    def patch(self, *args, **kwargs):
        response = super().patch(*args, **kwargs)
        raise_for_status(response)
        return response

    @cached_rate_limiter
    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)
        raise_for_status(response)
        return response

    @cached_rate_limiter
    def put(self, *args, **kwargs):
        response = super().put(*args, **kwargs)
        raise_for_status(response)
        return response


def raise_for_status(response):  # pragma: no cover
    try:
        if isinstance(response, dict):
            # Assumes it's a cached response. Not great
            return
        response.raise_for_status()
    except HTTPError as e:
        logger.debug(f'FAILED RESPONSE: {response!r}')
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            raise e
        if err := data.get('error'):
            msg = ' | '.join(
                f'{k.capitalize()}: {v}' for k, v in err.items()
            )
            err_data = err.get('data', err)
            if not err_data.get('code'):
                if code := err.get('code'):
                    err_data['code'] = code
            raise ClientError(msg, err_data)
        raise ClientError(str(e), data.get('data', data))


def load_user(
    *, symbol='', faction='', email='', token=''
):  # pragma: no cover
    symbol = symbol.upper().strip() if symbol else ''
    faction = faction.upper().strip() if faction else ''
    token = token.strip() if token else ''
    if symbol == 'TESTING' and faction == 'TESTING':
        return UserData(
            token='TESTING_TOKEN',
            symbol='TESTING',
            faction='TESTING',
            email='TESTING',
        )
    config_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'data', 'user_config.json')
    )
    last_login = str(datetime.now(timezone.utc))
    if os.path.isfile(config_file):
        user_data = json.load(open(config_file, 'r', encoding='utf8'))
        if not symbol or not token:
            if user := max(
                user_data.get('users', []),
                key=lambda x: datetime.fromisoformat(x['last_login'])
            ):
                user['last_login'] = last_login
                with open(config_file, 'w', encoding='utf8') as f:
                    json.dump(user_data, f, sort_keys=True, indent=2)
                return UserData(
                    token=user['token'],
                    symbol=user['symbol'],
                    faction=user['faction'],
                    email=user['email'],
                )
        for user in user_data.get('users', []):
            if user['symbol'].upper() == symbol or user['token'] == token:
                if faction and user['faction'] != faction:
                    raise SpaceUserError(
                        f'{user} already exists with a Faction of '
                        f'{user["faction"]!r}. {faction!r} is not compatible.'
                    )
                if email and user['email'] != email:
                    raise SpaceUserError(
                        f'{user} already exists but is associated with an'
                        f'email address of {user["email"]!r}.'
                    )
                user['last_login'] = last_login
                with open(config_file, 'w', encoding='utf8') as f:
                    json.dump(user_data, f, sort_keys=True, indent=2)
                return UserData(
                    token=user['token'],
                    symbol=user['symbol'],
                    faction=user['faction'],
                    email=user['email'],
                )
    else:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        user_data = dict()
    if token:
        user_data.setdefault('users', []).append(
            {
                'symbol': symbol,
                'faction': faction,
                'token': token,
                'email': email,
                'last_login': last_login,
            }
        )
        with open(config_file, 'w', encoding='utf8') as f:
            json.dump(user_data, f, sort_keys=True, indent=2)
        return UserData(
            token=token,
            symbol=symbol,
            faction=faction,
            email=email,
        )
    if not symbol or not faction:
        raise SpaceUserError(
            '"symbol" and "faction" are required to create an account.'
        )
    try:
        session = SpaceClient(headers={})
        payload = {'symbol': symbol, 'faction': faction}
        if email is not None:
            payload['email'] = email
        response = session.post('/register', data=payload)
        token = response.json()['data']['token']
    except Exception as e:
        raise e
    finally:
        session.close()
    user_data.setdefault('users', []).append(
        {
            'symbol': symbol,
            'faction': faction,
            'token': token,
            'email': email,
            'last_login': last_login,
        }
    )
    with open(config_file, 'w', encoding='utf8') as f:
        json.dump(user_data, f, sort_keys=True, indent=2)
    return UserData(
        token=token,
        symbol=symbol,
        faction=faction,
        email=email,
    )
