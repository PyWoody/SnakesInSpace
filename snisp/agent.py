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

    def __init__(self, *, symbol='', faction='', email='', token=''):
        database.setup()
        self.lock = threading.RLock()
        self.__systems = None
        user_data = load_user(
            symbol=symbol, faction=faction, email=email, token=token
        )
        self.__email = user_data.email
        self.__symbol = user_data.symbol
        self.__faction = user_data.faction
        self.__token = user_data.token
        self.__client = SpaceClient(token=self.token)
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
        return self.__client

    @property
    def data(self):
        response = self.client.get('/my/agent')
        return PlayerData(self, response.json()['data'])

    @property
    def email(self):
        return self.__email

    @property
    def faction(self):
        return self.__faction

    @property
    def symbol(self):
        return self.__symbol

    @property
    def systems(self):
        if self.__systems is None:
            self.__systems = Systems(self)
        return self.__systems

    @property
    def token(self):
        return self.__token


class PlayerData(utils.AbstractJSONItem):

    def __init__(self, agent, ship_data):
        self.agent = agent
        self._data = ship_data


def reset():  # pragma: no cover
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
