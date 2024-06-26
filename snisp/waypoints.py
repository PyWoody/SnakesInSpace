import functools
import logging

from collections import Counter

from snisp import cache, database, exceptions, utils, systems
from snisp.decorators import cooldown, docked, in_orbit, retry, transit
from snisp.exceptions import ClientError
from snisp.shipyards import Shipyard


logger = logging.getLogger(__name__)


class Waypoints:

    def __init__(self, agent, location):
        self.agent = agent
        self.location = location

    def __repr__(self):
        cls = self.__class__.__name__
        return f'{cls}({self.agent!r}, {self.location!r})'

    def __iter__(self):
        """
        Iterates over all of the Waypoint's in the Ship's current location

        Yields:
            Waypoint or a subclass of Waypoint
        """
        page = 1
        response = self.get_page(page=page)
        while data := response.json()['data']:
            for waypoint in data:
                cls = class_factory(waypoint['type'])
                yield cls(self.agent, waypoint)
            page += 1
            response = self.get_page(page=page)

    def __call__(
        self,
        *,
        system_symbol=None,
        traits=None,
        types=None,
        filters=None,
        page=1,
    ):
        """
        Iterates over Waypoints while yield only the ones that match the
        filters

        Kwargs:
            system_symbol: Symbol of the System to search. If not specified,
                           the System in the current self.location will be used
                           Default is None.
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None
            types: Single type to filter on. See snisp.utils.WAYPOINT_TYPES
                   for all types
                   Default is None
            filters: A dictionary of top-level items to filter the Waypoints.
                     The key, value pairs in the Waypoint's waypoint.to_dict()
                     data is compared against the filters
                     e.g., a filter of {'orbitals': []} would return only
                     Waypoints that don't have any orbitals
                     Default is None

        Yields:
            Waypoint or a subclass of Waypoint
        """
        filters = dict(filters) if filters is not None else {}
        filters = {utils.camel_case(k): v for k, v in filters.items()}
        response = self.get_page(
            system_symbol=system_symbol,
            traits=traits,
            types=types,
            page=page,
        )
        while data := response.json()['data']:
            for waypoint in data:
                if all(
                    False for k, v in filters.items()
                    if waypoint.get(k) != v
                ):
                    cls = class_factory(waypoint['type'])
                    yield cls(self.agent, waypoint)
            page += 1
            response = self.get_page(
                system_symbol=system_symbol,
                traits=traits,
                types=types,
                page=page,
            )

    @retry()
    def get_page(self, *, page=1, system_symbol=None, traits=None, types=None):
        params = {'page': int(page)}
        if types is not None:
            types = types.strip().upper()
            if types not in utils.WAYPOINT_TYPES:
                raise exceptions.SpaceAttributeError(
                    f'{types} is not an acceptable Waypoint type. '
                    'See snisp.utils.WAYPOINT_TYPES for acceptable types.'
                )
            params['type'] = types
        if traits is not None:
            traits = traits.strip().upper()
            if traits not in utils.WAYPOINT_TRAITS:
                raise exceptions.SpaceAttributeError(
                    f'{traits} is not an acceptable Waypoint trait. '
                    'See snisp.utils.WAYPOINT_TRAITS for acceptable traits.'
                )
            params['traits'] = traits
        if system_symbol is None:
            system_symbol = self.location.system
        return self.agent.client.get(
            f'/systems/{system_symbol}/waypoints', params=params
        )

    @retry()
    def get(self, *, waypoint=None, system_symbol=None, waypoint_symbol=None):
        """
        Gets a Waypoint or Waypoint subclass.

        Convenient for converting a something back to a Waypoint
        or Waypoint subclass

        >>> ship = next(iter(agent.fleet))
        >>> market = next(iter(ship.markets))
        >>> type(market)
        <class 'snisp.markets.Market'>
        >>> waypoint = ship.waypoints.get(waypoint=market)
        >>> type(waypoint)
        <class 'snisp.waypoints.EngineeredAsteroid'>

        Kwargs:
            waypoint: Waypoint or Waypoint subclass. Default is None
            system_symbol: Symbol of a System to use. Default is None
            waypoint_symbol: Symbol of a Waypoint to use. Default is None

        Returns:
            Waypoint or Waypoint subclass
        """
        if waypoint is not None:
            system_symbol = waypoint.system_symbol
            waypoint_symbol = waypoint.symbol
        else:
            if system_symbol is None:
                system_symbol = self.location.system
            if waypoint_symbol is None:
                waypoint_symbol = self.location.waypoint
        response = self.agent.client.get(
            f'/systems/{system_symbol}/waypoints/{waypoint_symbol}'
        )
        data = response.json()['data']
        cls = class_factory(data['type'])
        return cls(self.agent, data)

    @retry()
    def refresh(self, waypoint):
        """Returns a new Waypoint class or subclass object of the
        current Waypoint

        Returns:
            A new Waypoint or Waypoint subclass instance from self
        """
        response = self.agent.client.get(
            f'/systems/{waypoint.system_symbol}/waypoints/{waypoint.symbol}'
        )
        data = response.json()['data']
        data['systemSymbol'] = waypoint.system_symbol
        data['symbol'] = waypoint.symbol
        cls = class_factory(data['type'])
        return cls(self.agent, data)

    @retry()
    def search(
        self, *, traits=None, types=None, system_symbol=None, filters=None,
    ):
        """Convenience method. Equivalent to __call__

        Kwargs:
            system_symbol: Symbol of the System to search. If not specified,
                           the System in the current self.location will be used
                           Default is None.
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None
            types: Single type to filter on. See snisp.utils.WAYPOINT_TYPES
                   for all types
                   Default is None
            filters: A dictionary of top-level items to filter the Waypoints.
                     The key, value pairs in the Waypoint's waypoint.to_dict()
                     data is compared against the filters
                     e.g., a filter of {'orbitals': []} would return only
                     Waypoints that don't have any orbitals
                     Default is None

        Yields:
            Waypoint or Waypoint subclass
        """
        yield from self(
            system_symbol=system_symbol,
            traits=traits,
            types=types,
            filters=filters,
        )

    @retry()
    @transit
    def chart(self, ship):
        """
        Charts the Waypoint at the ship's current location

        Args:
            ship: Ship to use. All snisp.fleet.Ship objects will have this
                  automatically monkey-patched in.
        Blocks:
            True: Won't be executed until Ship reaches destination

        Returns:
            Chart
        """
        try:
            response = self.agent.client.post(
                f'/my/ships/{ship.symbol}/chart'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4230:
                    logger.warning(
                        f'Waypoint at {ship.symbol} has already been charted'
                    )
                    return Chart(self.agent, {})
            raise e
        with self.agent.lock:
            cache.reset_fuel_stations(ship.location)
            database.reset_system(ship.location.system)
        logger.info(
            f'{ship.registration.role}: {ship.symbol} | '
            f'Charted {ship.nav.waypoint_symbol}'
        )
        return Chart(self.agent, response.json()['data'])

    @retry()
    @transit
    @cooldown
    @in_orbit
    def scan(self, ship):
        """
        Scans the Waypoints in the ship's current System

        Args:
            ship: Ship to use. All snisp.fleet.Ship objects will have this
                  automatically monkey-patched in.
        Blocks:
            True: Won't be executed until Ship reaches destination and/or
                  the cooldown period has passed

        Yields:
            Waypoint or Waypoint subclasses
        """
        response = self.agent.client.post(
            f'/my/ships/{ship.symbol}/scan/waypoints'
        )
        data = response.json()['data']
        ship.update_data_item('cooldown', data['cooldown'])
        for waypoint in data['waypoints']:
            cls = class_factory(waypoint['type'])
            yield cls(self.agent, waypoint)

    def surveys(self):
        surveyed_wps = set()
        for ship in self.agent.fleet:
            if ship.nav.waypoint_symbol in surveyed_wps:
                continue
            if ship.nav.route.destination.type in utils.SURVEYABLE_WAYPOINTS:
                if ship.can_survey and ship.nav.status == 'IN_ORBIT':
                    try:
                        yield ship.waypoints.survey()
                    except Exception as e:
                        logger.warning(e)
                    else:
                        surveyed_wps.add(ship.nav.waypoint_symbol)

    @retry()
    @transit
    @cooldown
    @in_orbit
    def survey(self, ship):
        """
        Surveys the Waypoint at the ship's current location

        Args:
            ship: Ship to use. All snisp.fleet.Ship objects will have this
                  automatically monkey-patched in.
        Blocks:
            True: Won't be executed until Ship reaches destination and/or
                  the cooldown period has passed

        Returns:
            Survey
        """
        if ship.nav.route.destination.type not in utils.SURVEYABLE_WAYPOINTS:
            raise exceptions.ShipSurveyWaypointTypeError(
                f'{ship.nav.route.destination.type} is not an '
                'acceptable Waypoint type for surveying. '
                'See snisp.utils.SURVEYABLE_WAYPOINTS for acceptable types.'
            )
        response = self.agent.client.post(f'/my/ships/{ship.symbol}/survey')
        data = response.json()['data']
        ship.update_data_item('cooldown', data['cooldown'])
        logger.info(
            f'{ship.registration.role}: {ship.symbol} | '
            f'Surveyed {ship.nav.waypoint_symbol}'
        )
        return Survey(self.agent, data)

    def construction_sites(self, *, system_symbol=None):
        """
        Convenience method for finding ConstructionSites

        Kwargs:
            system_symbol: System to search. Default is None for current System

        Yields:
            ConstructionSite
        """
        for waypoint in self(
            system_symbol=system_symbol
        ):
            if waypoint.is_under_construction:
                yield ConstructionSite.get(self.agent, waypoint)

    def shipyards(self, *, system_symbol=None):
        """
        Convenience method for finding Shipyards

        Kwargs:
            system_symbol: System to search. Default is None for current System

        Yields:
            Shipyard
        """
        for shipyard in self(system_symbol=system_symbol, traits='SHIPYARD'):
            yield Shipyard(self.agent, shipyard.to_dict())

    def planets(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Planets

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            Planet
        """
        for planet in self(
            system_symbol=system_symbol, types='PLANET', traits=traits
        ):
            yield Planet(self.agent, planet.to_dict())

    def gas_giants(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Gas Giants

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            GasGiant
        """
        for gas_giant in self(
            system_symbol=system_symbol, types='GAS_GIANT', traits=traits
        ):
            yield GasGiant(self.agent, gas_giant.to_dict())

    def moons(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Moons

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            Moon
        """
        for moon in self(
            system_symbol=system_symbol, types='MOON', traits=traits
        ):
            yield Moon(self.agent, moon.to_dict())

    def orbital_stations(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Orbital Stations

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            OrbitalStation
        """
        for orbital_station in self(
            system_symbol=system_symbol, types='ORBITAL_STATION', traits=traits
        ):
            yield OrbitalStation(self.agent, orbital_station.to_dict())

    def jump_gates(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Jump Gates

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            JumpGate
        """
        for jump_gate in self(
            system_symbol=system_symbol, types='JUMP_GATE', traits=traits
        ):
            yield JumpGate(self.agent, jump_gate.to_dict())

    def asteroid_fields(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Asteroid Fields

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            AsteroidField
        """
        for asteroid_field in self(
            system_symbol=system_symbol, types='ASTEROID_FIELD', traits=traits
        ):
            yield AsteroidField(self.agent, asteroid_field.to_dict())

    def asteroids(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Asteroids

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            Asteroid
        """
        for asteroid in self(
            system_symbol=system_symbol, types='ASTEROID', traits=traits
        ):
            yield Asteroid(self.agent, asteroid.to_dict())

    def engineered_asteroids(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Engineered Asteroids

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            EngineeredAsteroid
        """
        for engineered_asteroid in self(
            system_symbol=system_symbol,
            types='ENGINEERED_ASTEROID',
            traits=traits
        ):
            yield EngineeredAsteroid(self.agent, engineered_asteroid.to_dict())

    def asteroid_bases(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Asteroid Bases

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            AsteroidBase
        """
        for asteroid_base in self(
            system_symbol=system_symbol, types='ASTEROID_BASE', traits=traits
        ):
            yield AsteroidBase(self.agent, asteroid_base.to_dict())

    def nebulas(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Nebulas

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            Nebula
        """
        for nebula in self(
            system_symbol=system_symbol, types='NEBULA', traits=traits
        ):
            yield Nebula(self.agent, nebula.to_dict())

    def debris_fields(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Debris Fields

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            DebrisField
        """
        for debris_field in self(
            system_symbol=system_symbol, types='DEBRIS_FIELD', traits=traits
        ):
            yield DebrisField(self.agent, debris_field.to_dict())

    def gravity_wells(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Gravity Wells

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            GravityWell
        """
        for gravity_well in self(
            system_symbol=system_symbol, types='GRAVITY_WELL', traits=traits
        ):
            yield GravityWell(self.agent, gravity_well.to_dict())

    def artificial_gravity_wells(self, *, system_symbol=None, traits=None):
        """
        Convenience method for finding Artificial Gravity Wells

        Kwargs:
            system_symbol: System to search. Default is None for current System
            traits: Single trait to filter on. See snisp.utils.WAYPOINT_TRAITS
                    for all traits
                    Default is None

        Yields:
            ArtificialGravityWell
        """
        for artificial_gravity_well in self(
            system_symbol=system_symbol,
            types='ARTIFICIAL_GRAVITY_WELL',
            traits=traits
        ):
            yield ArtificialGravityWell(
                self.agent, artificial_gravity_well.to_dict()
            )


class Waypoint(utils.AbstractJSONItem):

    def __init__(self, agent, waypoint):
        self.agent = agent
        self._data = waypoint

    @property
    def data(self):
        response = self.agent.client.get(
            f'/systems/{self.system_symbol}/waypoints/{self.waypoint_symbol}'
        )
        return WaypointData(self.agent, response.json()['data'])

    @property
    def location(self):
        """Property for the Waypoints Location

        Returns:
            snisp.system.Location: Waypoints Location
        """
        return systems.Location(self.agent, self.to_dict())


class WaypointData(utils.AbstractJSONItem):

    def __init__(self, agent, data):
        self.agent = agent
        self._data = data


class Chart(utils.AbstractJSONItem):

    def __init__(self, agent, waypoint):
        self.agent = agent
        self._data = waypoint


class Survey(utils.AbstractJSONItem):

    def __init__(self, agent, waypoint):
        self.agent = agent
        self._data = waypoint

    def best(self, *trade_symbols):
        if not trade_symbols:
            trade_symbols = {
                d.symbol for s in self.surveys for d in s.deposits
            }
        else:
            trade_symbols = {i for i in trade_symbols}
        # TODO: If this is used elsewhere, make it an enum
        survey_sizes = {
            'SMALL': 0,
            'MODERATE': 1,
            'LARGE': 2,
        }
        counter = Counter()
        sig_to_survey = {i.signature: i for i in self.surveys}
        for survey in self.surveys:
            for deposit in survey.deposits:
                if deposit.symbol in trade_symbols:
                    counter[survey.signature] += 1
        best_survey = None
        prev_count = None
        for survey_sig, count in counter.most_common():
            survey = sig_to_survey[survey_sig]
            if prev_count is not None and count < prev_count:
                break
            if best_survey is None:
                best_survey = survey
            elif survey_sizes[survey.size] > survey_sizes[best_survey.size]:
                best_survey = survey
            prev_count = count
        return best_survey


class ConstructionSite(utils.AbstractJSONItem):

    def __init__(self, agent, waypoint):
        self.agent = agent
        self._data = waypoint

    @classmethod
    @retry()
    def get(cls, agent, waypoint):
        """
        Class method that creates a ConstructionSite instance from a Waypiont
        Useful for when going from JumpGate Waypoint type to
        a ConstrutionSite type, for instance

        Args:
            agent: Your Agent
            waypoint: The Waypoint to generate the ConstructionSite from

        Returns:
            ConstructionSite
        """
        try:
            response = agent.client.get(
                f'/systems/{waypoint.system_symbol}/'
                f'waypoints/{waypoint.symbol}/construction'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'ConstructionSite at {waypoint!r} '
                        'has not been charted.'
                    )
                    return cls(agent, {})
            raise e
        data = response.json()['data']
        data['systemSymbol'] = waypoint.system_symbol
        data['symbol'] = waypoint.symbol
        return cls(agent, data)

    @retry()
    def refresh(self):
        """
        Returns a new ConstructionSite class object of the
        current ConstructionSite and its current status

        Returns:
            A new ConstructionSite instance from self
        """
        try:
            response = self.agent.client.get(
                f'/systems/{self.system_symbol}/waypoints/'
                f'{self.symbol}/construction'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'ConstructionSite at {self.location!r} '
                        'has not been charted.'
                    )
                    return ConstructionSite(self.agent, {})
            raise e
        data = response.json()['data']
        data['systemSymbol'] = self.system_symbol
        data['symbol'] = self.symbol
        return ConstructionSite(self.agent, data)

    @retry()
    @transit
    @docked
    def supply(
        self,
        *,
        ship,
        trade_symbol,
        units,
    ):
        """
        Supply construction materials to a Waypoint under construction

        Kwargs:
            ship: Ship that contains the construciton materials
                  and is at the Waypoint
            trade_symbol: Symbol of the good to supply
            units: Number of units of the good to supply

        Blocks:
            True: Won't be executed until Ship reaches destination
        """
        units = int(units)
        payload = {
            'shipSymbol': ship.symbol,
            'tradeSymbol': trade_symbol,
            'units': units,
        }
        response = self.agent.client.post(
            f'/systems/{self.system_symbol}/waypoints/{self.symbol}'
            '/construction/supply',
            json=payload
        )
        data = response.json()['data']
        self.update_data_item('materials', data['construction']['materials'])
        self.update_data_item('isComplete', data['construction']['isComplete'])
        ship.update_data_item('cargo', data['cargo'])
        logger.info(
            f'{ship.registration.role}: {ship.symbol} | '
            f'Supplied {units:,} units of '
            f'{trade_symbol} to {self.symbol}'
        )
        return data


# NOTE: These can be convient for isinstance checking


class Planet(utils.AbstractJSONItem):

    def __init__(self, agent, planet):
        self.agent = agent
        self._data = planet


class GasGiant(utils.AbstractJSONItem):

    def __init__(self, agent, gas_giant):
        self.agent = agent
        self._data = gas_giant


class Moon(utils.AbstractJSONItem):

    def __init__(self, agent, moon):
        self.agent = agent
        self._data = moon


class OrbitalStation(utils.AbstractJSONItem):

    def __init__(self, agent, orbital_station):
        self.agent = agent
        self._data = orbital_station


class JumpGate(utils.AbstractJSONItem):

    def __init__(self, agent, jump_gate):
        self.agent = agent
        self._data = jump_gate

    @property
    def data(self):
        try:
            response = self.agent.client.get(
                f'/systems/{self.system_symbol}/waypoints/'
                f'{self.symbol}/jump-gate'
            )
        except ClientError as e:
            if data := e.data:
                if data.get('code') == 4001:
                    logger.warning(
                        f'JumpGate at {self.location!r} has not been charted.'
                    )
                    return JumpGateData(self.agent, {})
            raise e
        return JumpGateData(self.agent, response.json()['data'])


class JumpGateData(utils.AbstractJSONItem):

    def __init__(self, agent, jump_gate):
        self.agent = agent
        self._data = jump_gate


class AsteroidField(utils.AbstractJSONItem):

    def __init__(self, agent, asteroid_field):
        self.agent = agent
        self._data = asteroid_field


class Asteroid(utils.AbstractJSONItem):

    def __init__(self, agent, asteroid):
        self.agent = agent
        self._data = asteroid


class EngineeredAsteroid(utils.AbstractJSONItem):

    def __init__(self, agent, engineered_asteroid):
        self.agent = agent
        self._data = engineered_asteroid


class AsteroidBase(utils.AbstractJSONItem):

    def __init__(self, agent, asteroid_base):
        self.agent = agent
        self._data = asteroid_base


class Nebula(utils.AbstractJSONItem):

    def __init__(self, agent, nebula):
        self.agent = agent
        self._data = nebula


class DebrisField(utils.AbstractJSONItem):

    def __init__(self, agent, debris_field):
        self.agent = agent
        self._data = debris_field


class GravityWell(utils.AbstractJSONItem):

    def __init__(self, agent, gravity_well):
        self.agent = agent
        self._data = gravity_well


class ArtificialGravityWell(utils.AbstractJSONItem):

    def __init__(self, agent, artificial_gravity_well):
        self.agent = agent
        self._data = artificial_gravity_well


class FuelStation(utils.AbstractJSONItem):

    def __init__(self, agent, fuel_station):
        self.agent = agent
        self._data = fuel_station


def is_uncharted(waypoint):
    return any(
        trait.symbol.upper() == 'UNCHARTED' for trait in waypoint.traits
    )


def best_asteroid(ship, trade_symbol=None, *, contract=None):
    trade_symbols = set()
    if trade_symbol is not None:
        trade_symbols.add(trade_symbol.strip().upper())
    if contract is not None:
        for item in contract.terms.deliver:
            if item.units_required - item.units_fulfilled > 0:
                trade_symbols.add(item.trade_symbol)
    if not trade_symbols:
        trade_symbols = utils.MINABLE_SYMBOLS.union(utils.REFINABLE_SYMBOLS)
    small_surveys = set()
    moderate_surveys = set()
    large_surveys = set()
    for survey_item in ship.waypoints.surveys():
        for survey in survey_item.surveys:
            if any(i.symbol in trade_symbols for i in survey.deposits):
                if survey.size == 'SMALL':
                    small_surveys.add(survey.symbol)
                elif survey.size == 'MODERATE':
                    moderate_surveys.add(survey.symbol)
                elif survey.size == 'LARGE':
                    large_surveys.add(survey.symbol)
    if large_surveys:
        large_waypoints = (
            ship.waypoints.get(waypoint_symbol=i) for i in large_surveys
        )
        return min(large_waypoints, key=lambda x: ship.distance(x))
    if moderate_surveys:
        moderate_waypoints = (
            ship.waypoints.get(waypoint_symbol=i) for i in moderate_surveys
        )
        return min(moderate_waypoints, key=lambda x: ship.distance(x))
    if small_surveys:
        small_waypoints = (
            ship.waypoints.get(waypoint_symbol=i) for i in small_surveys
        )
        return min(small_waypoints, key=lambda x: ship.distance(x))


@functools.lru_cache
def class_factory(cls_name):
    cls_name = utils.camel_case(cls_name.capitalize().rstrip('s'))
    try:
        return globals()[cls_name]
    except KeyError:
        return type(cls_name, (utils.BaseItem,), {})
