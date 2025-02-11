import atexit
import collections
import logging
import os
import threading

from snisp import database, utils
from snisp.client import SpaceClient, load_user
from snisp.contracts import Contracts
from snisp.factions import Factions
from snisp.fleet import Fleet
from snisp.systems import Systems


logger = logging.getLogger(__name__)


class Agent:

    """Agent represents your Player in SpaceTraders"""

    def __init__(self, *, symbol='', faction='', email='', token=''):
        database.setup()
        self.lock = threading.RLock()
        self._systems = None
        user_data = load_user(
            symbol=symbol, faction=faction, email=email, token=token
        )
        self._email = user_data.email
        self._symbol = user_data.symbol
        self._faction = user_data.faction
        self._token = user_data.token
        self._client = SpaceClient(token=self.token)
        atexit.register(self.client.cleanup)
        self.contracts = Contracts(self)
        self.fleet = Fleet(self)
        self.factions = Factions(self)
        self.dead_ships = dict()
        self.recent_transactions = collections.deque(maxlen=100)

    def __repr__(self):  # pragma: no cover
        cls = self.__class__.__name__
        output = f'{cls}(symbol={self.symbol!r}, faction={self.faction!r}'
        if self.email:
            return output + f', email={self.email!r})'
        else:
            return output + ')'

    def __del__(self):  # pragma: no cover
        try:
            self.client.close()
        except Exception:
            pass

    @property
    def client(self):
        """Property that returns the modified HTTPX Client"""
        return self._client

    @property
    def data(self):
        """Your Agent's current data

        Returns:
            PlayerData
        """
        response = self.client.get('/my/agent')
        return PlayerData(self, response.json()['data'])

    @property
    def email(self):
        return self._email

    @property
    def faction(self):
        return self._faction

    @property
    def symbol(self):
        return self._symbol

    @property
    def systems(self):
        if self._systems is None:
            self._systems = Systems(self)
        return self._systems

    @property
    def token(self):
        return self._token


class PlayerData(utils.AbstractJSONItem):

    """Your Agent's current data"""

    def __init__(self, agent, ship_data):
        self.agent = agent
        self._data = ship_data


def reset():  # pragma: no cover
    """Removes the user_config.json file if it exists"""
    config_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'data', 'user_config.json')
    )
    if os.path.isfile(config_file):
        try:
            os.remove(config_file)
        except Exception as e:
            raise Exception(
                f'Attempted to reset {config_file} but received {e!r}'
            )
