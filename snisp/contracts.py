import logging

from datetime import datetime, timezone

from snisp import utils
from snisp.decorators import docked, retry, transit


logger = logging.getLogger(__name__)


class Contracts:

    def __init__(self, agent):
        self.agent = agent

    def __iter__(self):
        page = 1
        response = self.get_page(page=page)
        while data := response.json()['data']:
            page += 1
            for contract in data:
                yield Contract(self.agent, contract)
            response = self.get_page(page=page)

    @retry()
    def __call__(self, contract_id):
        response = self.agent.client.get(f'/my/contracts/{contract_id}')
        return Contract(self.agent, response.json()['data'])

    @property
    def current(self):
        for contract in self:
            pass
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
        expiration = datetime.fromisoformat(self.terms.deadline)
        return datetime.now(timezone.utc) >= expiration

    @property
    def extractable(self):
        for term in self.terms.deliver:
            if term.units_required - term.units_fulfilled > 0:
                if term.trade_symbol in utils.MINABLE_SYMBOLS:
                    return True
        return False

    @property
    def siphonable(self):
        for term in self.terms.deliver:
            if term.units_required - term.units_fulfilled > 0:
                if term.trade_symbol in utils.SIPHONABLE_SYMBOLS:
                    return True
        return False

    @retry()
    def accept(self):
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
        response = self.agent.client.get(f'/my/contracts/{self.id}')
        return Contract(self.agent, response.json()['data'])
