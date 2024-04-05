import dateutil
import logging

from datetime import datetime, timezone

from snisp import utils
from snisp.decorators import docked, retry, transit


logger = logging.getLogger(__name__)


class Contracts:

    def __init__(self, agent):
        self.agent = agent
        self.last_contract_page = 1

    def __iter__(self):
        """
        Iterates over the current Agent's Contracts

        Yields:
            Contract
        """
        page = 1
        response = self.get_page(page=page)
        while data := response.json()['data']:
            page += 1
            for contract in data:
                yield Contract(self.agent, contract)
            response = self.get_page(page=page)

    @retry()
    def __call__(self, contract_id):
        """Returns the Contract assoiated with the contract ID

        Args:
            contract_id: The Contract's ID to lookup

        Returns:
            Contract
        """
        response = self.agent.client.get(f'/my/contracts/{contract_id}')
        return Contract(self.agent, response.json()['data'])

    @property
    def current(self):
        """Returns the current Contract"""
        with self.agent.lock:
            response = self.get_page(page=self.last_contract_page)
            while data := response.json()['data']:
                self.last_contract_page += 1
                for _contract in data:
                    contract = Contract(self.agent, _contract)
                response = self.get_page(page=self.last_contract_page)
            self.last_contract_page -= 1
        return contract

    @retry()
    def get_page(self, page=1, limit=20):
        params = {'limit': int(limit), 'page': int(page)}
        return self.agent.client.get('/my/contracts', params=params)


class Contract(utils.AbstractJSONItem):

    def __init__(self, agent, contract):
        self.agent = agent
        self._data = contract

    @property
    def expired(self):
        """Property for if the Contract has already expired

        Returns:
            bool
        """
        expiration = dateutil.parser.parse(self.terms.deadline)
        return datetime.now(timezone.utc) >= expiration

    @property
    def extractable(self):
        """Property for if any remaining items to deliver for the Contract
        can be extracted at an Asteroid

        Returns:
            bool
        """
        for term in self.terms.deliver:
            if term.units_required - term.units_fulfilled > 0:
                if term.trade_symbol in utils.MINABLE_SYMBOLS:
                    return True
        return False

    @property
    def siphonable(self):
        """Property for if any remaining items to deliver for the Contract
        can be siphoned at a Gas Giant

        Returns:
            bool
        """
        for term in self.terms.deliver:
            if term.units_required - term.units_fulfilled > 0:
                if term.trade_symbol in utils.SIPHONABLE_SYMBOLS:
                    return True
        return False

    @retry()
    def accept(self):
        """
        Accepts the Contract. Can be called multiple times without an issue
        """
        if not self.accepted:
            self.agent.client.post(
                f'/my/contracts/{self.id}/accept'
            )
            self.update_data_item('accepted', True)
            logger.info(f'Contract {self.id} accepted')

    @retry()
    @transit
    @docked
    def deliver(self, ship, trade_symbol, max_units=0):
        """
        Deliver items to the Contract.

        Ship must be located at the Contracts respective contract.deliver
        "destination_symbol"

        Args:
            ship: The Ship that contains the items to deliver
            trade_symbol: The symbol of the item to deliver

        Kwargs:
            max_units: Number of units to deliver, if > 1. Otherwise,
                       either the number of remaining units to be delivered
                       or the number of units in the Ship's cargo, whatever
                       is fewer

        Blocks:
            True: Won't be executed until Ship reaches destination
        """
        trade_symbol = trade_symbol.strip().upper()
        cargo_units = next(
            (
                int(i.units) for i in ship.cargo.inventory
                if i.symbol == trade_symbol
            ), None
        )
        if cargo_units is None:
            logger.warning(
                f'{ship.registration.role}: {ship.symbol} | '
                f'Attempted to deliver {trade_symbol} '
                f'to Contract {self.id}. '
                f'No {trade_symbol} units found in cargo'
            )
            return
        contract_units = next(
            (
                i.units_required - i.units_fulfilled
                for i in self.terms.deliver
                if i.trade_symbol == trade_symbol
            ), None
        )
        if contract_units is None:
            logger.warning(
                f'{ship.registration.role}: {ship.symbol} | '
                f'Attempted to deliver {trade_symbol} '
                f'to Contract {self.id}. '
                f'Contract does not required {trade_symbol}'
            )
            return
        max_units = max_units if max_units > 0 else cargo_units
        units = min(contract_units, cargo_units, max_units)
        payload = {
            'shipSymbol': ship.symbol,
            'tradeSymbol': trade_symbol,
            'units': units,
        }
        response = self.agent.client.post(
            f'/my/contracts/{self.id}/deliver', json=payload
        )
        data = response.json()['data']
        self.update_data_item('terms', data['contract']['terms'])
        ship.update_data_item('cargo', data['cargo'])
        logger.info(
            f'{ship.registration.role}: {ship.symbol} | '
            f'Delivered {units:,} units of '
            f'{trade_symbol} to CONTRACT {self.id}'
        )
        return data

    @retry()
    def fulfill(self):
        """
        Fulfills the Contract. Can be called multiple times without an issue
        """
        if not self.fulfilled:
            response = self.agent.client.post(
                f'/my/contracts/{self.id}/fulfill'
            )
            data = response.json()['data']
            self.update_data_item('fulfilled', data['contract']['fulfilled'])
            logger.info(f'Contract {self.id} fulfilled!')
            return data

    @retry()
    def refresh(self):
        """Returns a new Contract class object of the current Contract

        Returns:
            A new Contract instance from self
        """
        response = self.agent.client.get(f'/my/contracts/{self.id}')
        return Contract(self.agent, response.json()['data'])
