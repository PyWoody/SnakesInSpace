import itertools
import logging

from collections import namedtuple

from snisp import cache, utils
from snisp.exceptions import ClientError
from snisp.decorators import retry
from snisp.waypoints import Waypoints
from snisp.systems import Location


logger = logging.getLogger(__name__)

MarketDataRecord = namedtuple(
    'MarketDataRecord',
    [
        'distance',
        'trade_symbol',
        'import_market',
        'export_market',
        'import_waypoint',
        'export_waypoint',
    ]
)


class Markets:

    """Markets in the Ship's current Location"""

    # TODO: using __call__ for the actual market data is kind of confusing
    #       when used by a ship, e.g., ship.markets()
    #       Need to think of a better scheme/name

    def __init__(self, ship, location):
        self.ship = ship
        self.agent = ship.agent
        self.location = location

    def __repr__(self):
        cls = self.__class__.__name__
        return f'{cls}({self.agent!r}, {self.location!r})'

    def __iter__(self):
        """
        Iterates over the Waypoint's in the Ship's current location
        yielding Markets

        Yields:
            Market
        """
        _waypoint = Waypoints(self.agent, self.location)
        for waypoint in _waypoint(traits='MARKETPLACE'):
            yield Market(self.agent, waypoint.to_dict())

    @retry()
    def __call__(
        self, *, waypoint=None, waypoint_symbol=None
    ):
        """
        Retrieves a Market. Can be useful when going from
        Waypoint --> Market.

        If no kwarg is passed, the current Market data will be returned, which
        is equivalent to MarketData

        Kwargs:
            waypoint: A Waypoint or Waypoint sublcass
            waypoint_symbol: The string of a Waypoint that is a Market

        Returns:
            MarketData
        """
        if waypoint is not None:
            system_symbol = waypoint.system_symbol
            waypoint_symbol = waypoint.symbol
        elif waypoint_symbol is not None:
            system_symbol = '-'.join(waypoint_symbol.split('-')[:2])
        else:
            waypoint_symbol = self.location.waypoint
            system_symbol = self.location.system
        try:
            response = self.agent.client.get(
                f'/systems/{system_symbol}/waypoints/{waypoint_symbol}/market'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 404:
                    logger.warning(
                        f'Market at {waypoint_symbol} does not exist'
                    )
                    return MarketData(self.agent, {})
                elif data.get('code') == 4001:
                    logger.warning(
                        f'Waypoint at {waypoint_symbol} has not been charted.'
                    )
                    return MarketData(self.agent, {})
            raise e
        data = response.json()['data']
        data['location'] = Location(
            self.agent, {'headquarters': waypoint_symbol}
        )
        if not data.get('tradeGoods'):
            data['tradeGoods'] = []
        return MarketData(self.agent, data)

    def cheapest(self, trade_symbol):
        """
        Searches Markets in the Ship's system to return the Market
        with the cheapest Purchase Price for the trade symbol

        A Ship or Probe must be at the Market to get the current
        Sell Price. Otherwise, the closest Market that offers the trade
        symbol will be returned

        Args:
            trade_symbol: The symbol of the good to search

        Returns:
            Market if a Market that sells trade_symbol is found; else None
        """
        trade_symbol = trade_symbol.upper().strip()
        best_market = None
        best_price = None
        for market in self:
            market_data = market.data
            goods = itertools.chain(
                market_data.imports, market_data.exports, market_data.exchange
            )
            for good in goods:
                if good.symbol == trade_symbol:
                    purchase_price = next(
                        (
                            i.purchase_price
                            for i in market.data.trade_goods
                            if i.symbol == good.symbol
                        ), None
                    )
                    if best_market is None:
                        best_market = market
                        best_price = purchase_price
                    elif purchase_price:
                        # A market w/o a ship located at it will report that
                        # it sells the good but won't have the sell price
                        if not best_price or purchase_price < best_price:
                            best_market = market
                            best_price = purchase_price
        return best_market

    def cheapest_import(self, trade_symbol):
        """
        Searches Markets in the Ship's system to return the Market
        importing the trade symbol with the cheapest Sell Price

        A Ship or Probe must be at the Market to get the current
        Sell Price. Otherwise, the closest Market that imports the trade
        symbol will be returned

        Args:
            trade_symbol: The symbol of the good to search

        Returns:
            Market if a Market that imports trade_symbol is found; else None
        """
        if imports := list(self.search(imports=trade_symbol)):
            try:
                imports = sorted(
                    imports, key=lambda x: import_sort_key(x[1], trade_symbol)
                )
                best = import_sort_key(imports[0][1], trade_symbol)
                filtered = filter(
                    lambda x: import_sort_key(x[1], trade_symbol) == best,
                    imports
                )
                return min(filtered, key=lambda x: self.ship.distance(x[0]))
            except TypeError:
                return min(imports, key=lambda x: self.ship.distance(x[0]))

    def most_expensive_import(self, trade_symbol):
        """
        Searches Markets in the Ship's system to return the Market
        importing the trade symbol with the highest Sell Price

        A Ship or Probe must be at the Market to get the current
        Sell Price. Otherwise, the closest Market that imports the trade
        symbol will be returned

        Args:
            trade_symbol: The symbol of the good to search

        Returns:
            Market if a Market that imports trade_symbol is found; else None
        """
        if imports := list(self.search(imports=trade_symbol)):
            try:
                imports = sorted(
                    imports,
                    key=lambda x: x and import_sort_key(x[1], trade_symbol),
                    reverse=True,
                )
                best = import_sort_key(imports[0][1], trade_symbol)
                filtered = filter(
                    lambda x: import_sort_key(x[1], trade_symbol) == best,
                    imports
                )
                return min(filtered, key=lambda x: self.ship.distance(x[0]))
            except TypeError:
                return min(imports, key=lambda x: self.ship.distance(x[0]))

    def cheapest_export(self, trade_symbol):
        """
        Searches Markets in the Ship's system to return the Market
        exporting the trade symbol with the cheapest Purchase Price

        A Ship or Probe must be at the Market to get the current
        Sell Price. Otherwise, the closest Market that exports the trade
        symbol will be returned

        Args:
            trade_symbol: The symbol of the good to search

        Returns:
            Market if a Market that expports trade_symbol is found; else None
        """
        if exports := list(self.search(exports=trade_symbol)):
            try:
                exports = sorted(
                    exports, key=lambda x: export_sort_key(x[1], trade_symbol)
                )
                best = export_sort_key(exports[0][1], trade_symbol)
                filtered = filter(
                    lambda x: export_sort_key(x[1], trade_symbol) == best,
                    exports
                )
                return min(filtered, key=lambda x: self.ship.distance(x[0]))
            except TypeError:
                return min(exports, key=lambda x: self.ship.distance(x[0]))

    def cheapest_exchange(self, trade_symbol):
        """
        Searches Markets in the Ship's system to return the Market
        exchanging the trade symbol with the cheapest Purchase Price

        A Ship or Probe must be at the Market to get the current
        Sell Price. Otherwise, the closest Market that exchanges the trade
        symbol will be returned

        Args:
            trade_symbol: The symbol of the good to search

        Returns:
            Market if a Market that exchanges trade_symbol is found; else None
        """
        if exchanges := list(self.search(exchanges=trade_symbol)):
            try:
                exchanges = sorted(
                    exchanges,
                    key=lambda x: exchange_sort_key(x[1], trade_symbol)
                )
                best = exchange_sort_key(exchanges[0][1], trade_symbol)
                filtered = filter(
                    lambda x: exchange_sort_key(x[1], trade_symbol) == best,
                    exchanges
                )
                return min(filtered, key=lambda x: self.ship.distance(x[0]))
            except TypeError:
                return min(exchanges, key=lambda x: self.ship.distance(x[0]))

    def cheapest_export_or_exchange(self, trade_symbol):
        """
        Searches Markets in the Ship's system to return the Market
        exporting or exchanging the trade symbol with the
        cheapest Purchase Price

        A Ship or Probe must be at the Market to get the current
        Sell Price. Otherwise, the closest Market that exports or exchanges
        the trade symbol will be returned

        Args:
            trade_symbol: The symbol of the good to search

        Returns:
            Market if a Market that exports or exchanges trade_symbol is
            found; else None
        """
        markets = []
        for market in self:
            market_data = self(waypoint=market)
            if trade_symbol in {i.symbol for i in market_data.exports}:
                markets.append((market, market_data))
            elif trade_symbol in {i.symbol for i in market_data.exchange}:
                markets.append((market, market_data))
        if markets:
            try:
                markets = sorted(
                    markets,
                    key=lambda x: export_or_exchange_sort_key(
                        x[1], trade_symbol
                    )
                )
                best = export_or_exchange_sort_key(markets[0][1], trade_symbol)
                filtered = filter(
                    lambda x: export_or_exchange_sort_key(
                        x[1], trade_symbol
                    ) == best,
                    markets
                )
                return min(filtered, key=lambda x: self.ship.distance(x[0]))
            except TypeError:
                return min(markets, key=lambda x: self.ship.distance(x[0]))

    def most_expensive_export(self, trade_symbol):
        """
        Searches Markets in the Ship's system to return the Market
        exporting the trade symbol with the most expensive Purchase Price

        A Ship or Probe must be at the Market to get the current
        Sell Price. Otherwise, the closest Market that exports the trade
        symbol will be returned

        Args:
            trade_symbol: The symbol of the good to search

        Returns:
            Market if a Market that imports trade_symbol is found; else None
        """
        if exports := list(self.search(exports=trade_symbol)):
            try:
                exports = sorted(
                    exports,
                    key=lambda x: export_sort_key(x[1], trade_symbol),
                    reverse=True,
                )
                best = export_sort_key(exports[0][1], trade_symbol)
                filtered = filter(
                    lambda x: export_sort_key(x[1], trade_symbol) == best,
                    exports
                )
                return min(filtered, key=lambda x: self.ship.distance(x[0]))
            except TypeError:
                return min(exports, key=lambda x: self.ship.distance(x[0]))

    def search(self, imports=None, exports=None, exchanges=None):
        """
        Searches for Markets in the current System. Multiple arguments
        will be ANDs

        Kwargs:
            imports: Find a Market that imports trade symbol
            exports: Find a Market that exports trade symbol
            exchanges: Find a Market that exchanges trade symbol

        Yields:
            A tuple of (Market, MarketData)
        """
        if imports is not None:
            imports = imports.upper().strip()
        if exports is not None:
            exports = exports.upper().strip()
        if exchanges is not None:
            exchanges = exchanges.upper().strip()
        for market in self:
            market_data = self(waypoint=market)
            market_imports = {i.symbol for i in market_data.imports}
            if not imports or imports in market_imports:
                market_exports = {i.symbol for i in market_data.exports}
                if not exports or exports in market_exports:
                    market_exchanges = {
                        i.symbol for i in market_data.exchange
                    }
                    if not exchanges or exchanges in market_exchanges:
                        yield market, market_data

    def shipyard_market_data(self, ship_type):
        """
        Returns a tuple of the Shipyard, ShipyardShip of the cheapest
        ShipyardShip of type ship type

        Args:
            ship_type: Ship type to search. See snisp.utils.SHIP_TYPES
                       for all supported ship types

        Returns:
            A tuple of (Shipyard, ShipyardShip) if ship_type is found; else,
            a tuple of (None, None)
        """
        # Reminder: Available ships will yield nothing if no probes
        #           are at the waypoint
        output = (
            (i, s) for i in self.ship.waypoints.shipyards()
            for s in i.available_ships(ship_type=ship_type)
        )
        try:
            return min(output, key=lambda x: x[1].purchase_price)
        except ValueError:
            return None, None

    def sells(self, trade_symbol):
        """
        Finds Markets in the current System that sell the trade symbol

        Args:
            trade_symbol: The symbol of the good to find

        Yields:
            Market
        """
        trade_symbol = trade_symbol.strip().upper()
        for market in self:
            market_data = market.data
            if any(i.symbol == trade_symbol for i in market_data.imports):
                yield market
            elif any(i.symbol == trade_symbol for i in market_data.exports):
                yield market
            elif any(i.symbol == trade_symbol for i in market_data.exchange):
                yield market

    def imports(self, trade_symbol):
        """
        Finds Markets in the current System that import the trade symbol

        Args:
            trade_symbol: The symbol of the good to find

        Yields:
            Market
        """
        trade_symbol = trade_symbol.strip().upper()
        for market in self:
            if imports := market.data.imports:
                for _import in imports:
                    if _import.symbol == trade_symbol:
                        yield market

    def exports(self, trade_symbol):
        """
        Finds Markets in the current System that export the trade symbol

        Args:
            trade_symbol: The symbol of the good to find

        Yields:
            Market
        """
        trade_symbol = trade_symbol.strip().upper()
        for market in self:
            if exports := market.data.exports:
                for export in exports:
                    if export.symbol == trade_symbol:
                        yield market

    def exchanges(self, trade_symbol):
        """
        Finds Markets in the current System that exchange the trade symbol

        Args:
            trade_symbol: The symbol of the good to find

        Yields:
            Market
        """
        trade_symbol = trade_symbol.strip().upper()
        for market in self:
            if exchanges := market.data.exchange:
                for exchange in exchanges:
                    if exchange.symbol == trade_symbol:
                        yield market

    def fuel_stations(self, *, system_symbol=None, traits=None):
        """
        Finds all Waypoints in the system that allow refueling

        NOTE: Since this is an expensive and time consuming call that requires
        a considerable amount of network calls, the results will be cached.

        Returns:
            Waypoints: List of Waypoints that accept refueling
        """
        with self.agent.lock:
            if not self.agent.client.testing:
                if fuel_stations := cache.get_fuel_stations(self.location):
                    return fuel_stations
            fuel_stations = []
            fs_waypoints = Waypoints(self.agent, self.location)
            fuel_station_symbols = set()
            for fuel_station in itertools.chain(
                fs_waypoints(
                    system_symbol=system_symbol,
                    types='FUEL_STATION',
                    traits=traits,
                ),
                (i[0] for i in self.search(exports='FUEL')),
                (i[0] for i in self.search(exchanges='FUEL')),
            ):
                if fuel_station.symbol not in fuel_station_symbols:
                    fuel_stations.append(fuel_station)
                    fuel_station_symbols.add(fuel_station.symbol)
            if not self.agent.client.testing:
                cache.insert_fuel_stations(self.location, fuel_stations)
        return fuel_stations


class Market(utils.AbstractJSONItem):

    def __init__(self, agent, market):
        self.agent = agent
        self._data = market

    @property
    def data(self):
        """
        Returns the MarketData for the Market

        Equivalent to calling markets() on an existing Market

        If a Ship or Probe is located at the Market, the live MarketData
        will be returned, including recent transactions, sell prices, and
        purchase prices

        Returns:
            MarketData
        """
        # REMINDER: This is the same data returned by Markets.__call__
        try:
            response = self.agent.client.get(
                f'/systems/{self.location.system}/waypoints'
                f'/{self.symbol}/market'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'Market at {self.location!r} has not been charted.'
                    )
                    return MarketData(self.agent, {})
            raise e
        data = response.json()['data']
        data['location'] = self.location
        if not data.get('tradeGoods'):
            data['tradeGoods'] = []
        return MarketData(self.agent, data)

    @property
    def location(self):
        """Returns the Market's Location"""
        return Location(self.agent, {'headquarters': self.symbol})


class MarketData(utils.AbstractJSONItem):

    """
    Convenience class. Equivalent to Market but useful for comparing Market
    to Market.data as Market will not have the supplemental data that
    MarketData contains

    >>> ship = next(iter(agent.fleet))
    >>> market = next(iter(ship.markets))
    >>> market.trade_goods  # Does not exist. Returns None
    >>> market.data.trade_goods  # or, market().trade_goods
    []
    """

    def __init__(self, agent, data):
        self.agent = agent
        self._data = data

    @property
    def data(self):
        """
        Returns the MarketData for the Market

        Equivalent to calling markets() on an existing Market

        If a Ship or Probe is located at the Market, the live MarketData
        will be returned, including recent transactions, sell prices, and
        purchase prices

        Returns:
            MarketData
        """
        # REMINDER: This is the same data returned by Markets.__call__
        try:
            response = self.agent.client.get(
                f'/systems/{self.location.system}/waypoints'
                f'/{self.symbol}/market'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'Market at {self.location!r} has not been charted.'
                    )
                    return MarketData(self.agent, {})
            raise e
        data = response.json()['data']
        data['location'] = self.location
        if not data.get('tradeGoods'):
            data['tradeGoods'] = []
        return MarketData(self.agent, data)

    @property
    def location(self):
        """Returns the Market's Location"""
        return Location(self.agent, {'headquarters': self.symbol})


def best_market_pairs(ship, market_data, price_delta=0):
    """
    Returns a sorted list of the best market pairs


    Args:
        ship: A ship in the System to search
        market_data: An iterable of MarketDatas to search

    Kwargs:
        price_delta: Minimum delta between the Purchase and Sell prices
                     Default is 0

    Returns:
        MarketDataRecord: Sorted list of MarketDataRecords if matches are
        found; else, an empty list
    """
    market_pairs = {}
    for market in market_data:
        for good in market.trade_goods:
            market_pairs.setdefault(good.symbol, []).append((market, good))
    output = []
    cache = {}

    for trade_symbol, markets in market_pairs.items():
        e_market, e_good = min(markets, key=lambda x: x[1].purchase_price)
        i_market, i_good = max(markets, key=lambda x: x[1].sell_price)
        if i_good.sell_price - e_good.purchase_price < price_delta:
            continue
        i_wp = cache.get(
            (
                i_market.location.system,
                i_market.location.waypoint
            )
        )
        if not i_wp:
            i_wp = ship.waypoints.get(
                system_symbol=i_market.location.system,
                waypoint_symbol=i_market.location.waypoint,
            )
            cache[
                (
                    i_market.location.system,
                    i_market.location.waypoint
                )
            ] = i_wp
        e_wp = cache.get(
            (
                e_market.location.system,
                e_market.location.waypoint
            )
        )
        if not e_wp:
            e_wp = ship.waypoints.get(
                system_symbol=e_market.location.system,
                waypoint_symbol=e_market.location.waypoint,
            )
            cache[
                (
                    e_market.location.system,
                    e_market.location.waypoint
                )
            ] = e_wp
        output.append(
            MarketDataRecord(
                distance=utils.calculate_waypoint_distance(i_wp, e_wp),
                trade_symbol=trade_symbol,
                import_market=i_market,
                export_market=e_market,
                import_waypoint=i_wp,
                export_waypoint=e_wp,
            )
        )
    return sorted(output, key=market_delta_sort_key, reverse=True)


def market_delta_sort_key(market_record):
    """
    Returns the difference between the Sell Price and Purchase Price
    for the trade goods associated with the market_record.trade_symbol

    Args:
        market_record: A MarketDataRecord
    """
    for i_good in market_record.import_market.trade_goods:
        if i_good.symbol == market_record.trade_symbol:
            for e_good in market_record.export_market.trade_goods:
                if e_good.symbol == market_record.trade_symbol:
                    return i_good.sell_price - e_good.purchase_price


def import_sort_key(market_data, trade_symbol):
    """
    Args:
        market_data: The Market's MarketData
        trade_symbol: Symbol of the good to check

    Returns:
        purchase_price: Returns sell price of the trade good if it imports
                        the trade_symbol
    """
    if market_data.trade_goods:
        for good in market_data.trade_goods:
            if good.type == 'IMPORT' and good.symbol == trade_symbol:
                return good.sell_price


def export_sort_key(market_data, trade_symbol):
    """
    Args:
        market_data: The Market's MarketData
        trade_symbol: Symbol of the good to check

    Returns:
        purchase_price: Returns purchase price of the trade good if it exports
                        the trade_symbol
    """
    if market_data.trade_goods:
        for good in market_data.trade_goods:
            if good.type == 'EXPORT' and good.symbol == trade_symbol:
                return good.purchase_price


def exchange_sort_key(market_data, trade_symbol):
    """
    Args:
        market_data: The Market's MarketData
        trade_symbol: Symbol of the good to check

    Returns:
        purchase_price: Returns purchase price of the trade good
                        if it exchanges the trade_symbol
    """
    if market_data.trade_goods:
        for good in market_data.trade_goods:
            if good.type == 'EXCHANGE' and good.symbol == trade_symbol:
                return good.purchase_price


def export_or_exchange_sort_key(market_data, trade_symbol):
    """
    Args:
        market_data: The Market's MarketData
        trade_symbol: Symbol of the good to check

    Returns:
        purchase_price: Returns purchase price of the trade good if it exports
                        or exchanges the trade_symbol
    """
    if market_data.trade_goods:
        for good in market_data.trade_goods:
            if good.symbol == trade_symbol:
                if good.type == 'EXPORT' or good.type == 'EXCHANGE':
                    return good.purchase_price


def has_import(market_data, trade_symbol):
    """
    Args:
        market_data: The Market's MarketData
        trade_symbol: Symbol of the good to check

    Returns:
        bool: True if market imports trade symbol; else, False
    """
    return trade_symbol in {i.symbol for i in market_data.imports}


def has_export(market_data, trade_symbol):
    """
    Args:
        market_data: The Market's MarketData
        trade_symbol: Symbol of the good to check

    Returns:
        bool: True if market exports trade symbol; else, False
    """
    return trade_symbol in {i.symbol for i in market_data.exports}


def has_exchange(market_data, trade_symbol):
    """
    Args:
        market_data: The Market's MarketData
        trade_symbol: Symbol of the good to check

    Returns:
        bool: True if market exchanges trade symbol; else, False
    """
    return trade_symbol in {i.symbol for i in market_data.exchange}
