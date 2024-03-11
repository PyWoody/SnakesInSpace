import copy
import logging
import math
import threading
import traceback

from collections.abc import Iterable


ATTRIBUTE_LOCK = threading.Lock()
logger = logging.getLogger(__name__)


class AbstractJSONItem:

    """Allows for snake or camel case accessing of JSON data
    as class attributes.
    """

    def __dir__(self):
        output = super().__dir__()
        output.extend(
            snake_case(i) for i in self._data.keys()
            if snake_case(i) not in output
        )
        return output

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()!r})'

    def __eq__(self, other):
        return type(other) == type(self) and other.to_dict() == self.to_dict()

    def __len__(self):
        return len(self._data)

    def __getattribute__(self, name):
        # Slow but fight me
        if name == 'agent':
            return super().__getattribute__('agent')
        data_dict = super().__getattribute__('_data')
        if name == '_data':
            return data_dict
        try:
            if name in data_dict.keys():
                value = super().__getattribute__(name)
                if value != data_dict[name]:
                    super().__setattr__(name, data_dict[name])
                return data_dict[name]
            _name = camel_case(name)
            if _name in data_dict.keys():
                value = super().__getattribute__(_name)
                if value != data_dict[_name]:  # pragma: no cover
                    # Probably not possible to get here since update_data_item
                    # also makes a call to __setattr__
                    # buy why not?
                    super().__setattr__(_name, data_dict[_name])
                return data_dict[_name]
            return super().__getattribute__(name)
        except AttributeError:
            if name in data_dict.keys():
                if isinstance(data_dict[name], dict):
                    data = type(
                        camel_case(name.capitalize()).rstrip('s'),
                        (BaseJSONItem,),
                        {}
                    )(data_dict[name])
                    data_dict[name] = data
                    super().__setattr__(name, data)
                    return data
                elif is_list_like(data_dict[name]):
                    class_factory = type(
                        camel_case(name.capitalize()).rstrip('s'),
                        (BaseJSONItem,),
                        {}
                    )
                    data = []
                    for index, item in enumerate(data_dict[name]):
                        if type(item) == str:
                            data.append(item)
                        else:
                            base_item = class_factory(item)
                            data_dict[name][index] = base_item
                            data.append(base_item)
                    super().__setattr__(name, data)
                else:
                    super().__setattr__(name, data_dict[name])
                return data_dict[name]
            name = camel_case(name)
            if name in data_dict.keys():
                if isinstance(data_dict[name], dict):  # pragma: no cover
                    data = type(
                        ''.join([name[0].upper(), name[1:]]).rstrip('s'),
                        (BaseJSONItem,),
                        {}
                    )(data_dict[name])
                    data_dict[name] = data
                    super().__setattr__(name, data)
                    return data
                elif is_list_like(data_dict[name]):
                    class_factory = type(
                        ''.join([name[0].upper(), name[1:]]).rstrip('s'),
                        (BaseJSONItem,),
                        {}
                    )
                    data = []
                    for index, item in enumerate(data_dict[name]):
                        if type(item) == str:  # pragma: no cover
                            data.append(item)
                        else:
                            base_item = class_factory(item)
                            data_dict[name][index] = base_item
                            data.append(base_item)
                    super().__setattr__(name, data)
                else:
                    super().__setattr__(name, data_dict[name])
                return data_dict[name]

    def __setattr__(self, name, value):
        if name == '_data' or name == 'agent':
            return super().__setattr__(name, value)
        raise AttributeError(
            f'{self.__class__.__name__} does not support attribute assignment'
        )

    def to_dict(self):
        output = {}
        for k, v in self._data.items():
            if issubclass(type(v), AbstractJSONItem):
                output[k] = v.to_dict()
            elif is_list_like(v) and not isinstance(v, dict):
                output[k] = []
                for item in v:
                    if issubclass(type(item), AbstractJSONItem):
                        output[k].append(item.to_dict())
                    else:
                        output[k].append(copy.copy(item))
            else:
                output[k] = copy.copy(v)
        return output

    def update_data_item(self, name, value):
        """Updates top-level items found in the `_data` dict.
        Not intended to be used by a user."""
        with ATTRIBUTE_LOCK:
            if name not in self._data.keys():
                raise AttributeError(
                    f'{name!r} not found in {self.__class__.__name__}'
                )
            if isinstance(value, dict):
                value = type(
                    camel_case(name.capitalize()).rstrip('s'),
                    (BaseJSONItem,),
                    {}
                )(value)
            elif is_list_like(value):
                class_factory = type(
                    camel_case(name.capitalize()).rstrip('s'),
                    (BaseJSONItem,),
                    {}
                )
                data = []
                for index, item in enumerate(value):
                    if type(item) == str:  # pragma: no cover
                        data.append(item)
                    else:
                        data.append(class_factory(item))
                value = data
            self._data[name] = value
            super().__setattr__(name, value)


class BaseItem(AbstractJSONItem):

    def __init__(self, agent, data):
        self.agent = agent
        self._data = data


class BaseJSONItem(AbstractJSONItem):

    def __init__(self, data):
        self._data = data


def is_list_like(value):
    if isinstance(value, Iterable):
        if not isinstance(value, str):
            return True
    return False


def snake_case(name):
    if name.startswith('__') and name.endswith('__'):  # pragma: no cover
        return name
    output = ''
    for char in name:
        if char.isupper():
            output += f'_{char.lower()}'
        else:
            output += char
    return output


def camel_case(name):
    if name.startswith('__') and name.endswith('__'):
        return name
    upper_next = False
    output = ''
    for char in name:
        if char == '_':
            upper_next = True
        else:
            if upper_next:
                char = char.upper()
                upper_next = False
            output += char
    return output


# Helpers

def ilen(*iterables, start=0):
    for iterable in iterables:
        for _ in iterable:
            start += 1
    return start


def calculate_distance(ship, dest):
    return math.sqrt(
        pow(ship.nav.route.destination.x - dest.x, 2) +
        pow(ship.nav.route.destination.y - dest.y, 2)
    )


def calculate_waypoint_distance(origin, dest):
    return math.sqrt(pow(origin.x - dest.x, 2) + pow(origin.y - dest.y, 2))


def a_ship_at_location(agent, symbol):
    return any(
        s.nav.waypoint_symbol == symbol
        for s in agent.fleet if s.nav.status != 'IN_TRANSIT'
    )


def thread_exception_hook_logger(err):  # pragma: no cover
    logger.warning(f'ThreadExcetion: {err!r}')
    logger.warning(traceback.extract_tb(err.exc_traceback))


def thread_exception_hook_raiser(err):  # pragma: no cover
    print(traceback.extract_tb(err.exc_traceback))
    raise Exception(err)


# AKA enums

SYSTEMS_TYPES = frozenset(
    [
        'BLACK_HOLE',
        'BLUE_STAR',
        'HYPERGIANT',
        'NEBULA',
        'NEUTRON_STAR',
        'ORANGE_STAR',
        'RED_STAR',
        'UNSTABLE',
        'YOUNG_STAR',
        'WHITE_DWARF',
    ]
)


WAYPOINT_TRAITS = frozenset(
    [
        'ASH_CLOUDS',
        'BARREN',
        'BLACK_MARKET',
        'BREATHABLE_ATMOSPHERE',
        'BUREAUCRATIC',
        'CANYONS',
        'COMMON_METAL_DEPOSITS',
        'CORROSIVE_ATMOSPHERE',
        'CORRUPT',
        'CRUSHING_GRAVITY',
        'DEBRIS_CLUSTER',
        'DEEP_CRATERS',
        'DIVERSE_LIFE',
        'DRY_SEABEDS',
        'EXPLORATION_OUTPOST',
        'EXPLOSIVE_GASES',
        'EXTREME_PRESSURE',
        'EXTREME_TEMPERATURES',
        'FOSSILS',
        'FROZEN',
        'HIGH_TECH',
        'HOLLOWED_INTERIOR',
        'ICE_CRYSTALS',
        'INDUSTRIAL',
        'JOVIAN',
        'JUNGLE',
        'MAGMA_SEAS',
        'MARKETPLACE',
        'MEGA_STRUCTURES',
        'METHANE_POOLS',
        'MICRO_GRAVITY_ANOMALIES',
        'MILITARY_BASE',
        'MINERAL_DEPOSITS',
        'MUTATED_FLORA',
        'OCEAN',
        'OUTPOST',
        'OVERCROWDED',
        'PERPETUAL_DAYLIGHT',
        'PERPETUAL_OVERCAST',
        'PIRATE_BASE',
        'PRECIOUS_METAL_DEPOSITS',
        'RADIOACTIVE',
        'RARE_METAL_DEPOSITS',
        'RESEARCH_FACILITY',
        'ROCKY',
        'SALT_FLATS',
        'SCARCE_LIFE',
        'SCATTERED_SETTLEMENTS',
        'SHALLOW_CRATERS',
        'SHIPYARD',
        'SPRAWLING_CITIES',
        'STRIPPED',
        'STRONG_GRAVITY',
        'STRONG_MAGNETOSPHERE',
        'SUPERVOLCANOES',
        'SURVEILLANCE_OUTPOST',
        'SWAMP',
        'TEMPERATE',
        'TERRAFORMED',
        'THIN_ATMOSPHERE',
        'TOXIC_ATMOSPHERE',
        'TRADING_HUB',
        'UNCHARTED',
        'UNDER_CONSTRUCTION',
        'UNSTABLE_COMPOSITION',
        'VAST_RUINS',
        'VIBRANT_AURORAS',
        'VOLCANIC',
        'WEAK_GRAVITY',
    ]
)


WAYPOINT_TYPES = frozenset(
    [
        'ARTIFICIAL_GRAVITY_WELL',
        'ASTEROID',
        'ASTEROID_BASE',
        'ASTEROID_FIELD',
        'DEBRIS_FIELD',
        'ENGINEERED_ASTEROID',
        'FUEL_STATION',
        'GAS_GIANT',
        'GRAVITY_WELL',
        'JUMP_GATE',
        'MOON',
        'NEBULA',
        'ORBITAL_STATION',
        'PLANET',
    ]
)


SHIP_TYPES = frozenset(
    [
        'SHIP_COMMAND_FRIGATE',
        'SHIP_EXPLORER',
        'SHIP_HEAVY_FREIGHTER',
        'SHIP_INTERCEPTOR',
        'SHIP_LIGHT_HAULER',
        'SHIP_LIGHT_SHUTTLE',
        'SHIP_MINING_DRONE',
        'SHIP_ORE_HOUND',
        'SHIP_PROBE',
        'SHIP_REFINING_FREIGHTER',
        'SHIP_SIPHON_DRONE',
        'SHIP_SURVEYOR',
    ]
)

GOODS_TYPES = frozenset(
    [
        'PRECIOUS_STONES',
        'QUARTZ_SAND',
        'SILICON_CRYSTALS',
        'AMMONIA_ICE',
        'LIQUID_HYDROGEN',
        'LIQUID_NITROGEN',
        'ICE_WATER',
        'EXOTIC_MATTER',
        'ADVANCED_CIRCUITRY',
        'GRAVITON_EMITTERS',
        'IRON',
        'IRON_ORE',
        'COPPER',
        'COPPER_ORE',
        'ALUMINUM',
        'ALUMINUM_ORE',
        'SILVER',
        'SILVER_ORE',
        'GOLD',
        'GOLD_ORE',
        'PLATINUM',
        'PLATINUM_ORE',
        'DIAMONDS',
        'URANITE',
        'URANITE_ORE',
        'MERITIUM',
        'MERITIUM_ORE',
        'HYDROCARBON',
        'ANTIMATTER',
        'FAB_MATS',
        'FERTILIZERS',
        'FABRICS',
        'FOOD',
        'JEWELRY',
        'MACHINERY',
        'FIREARMS',
        'ASSAULT_RIFLES',
        'MILITARY_EQUIPMENT',
        'EXPLOSIVES',
        'LAB_INSTRUMENTS',
        'AMMUNITION',
        'ELECTRONICS',
        'SHIP_PLATING',
        'SHIP_PARTS',
        'EQUIPMENT',
        'FUEL',
        'MEDICINE',
        'DRUGS',
        'CLOTHING',
        'MICROPROCESSORS',
        'PLASTICS',
        'POLYNUCLEOTIDES',
        'BIOCOMPOSITES',
        'QUANTUM_STABILIZERS',
        'NANOBOTS',
        'AI_MAINFRAMES',
        'QUANTUM_DRIVES',
        'ROBOTIC_DRONES',
        'CYBER_IMPLANTS',
        'GENE_THERAPEUTICS',
        'NEURAL_CHIPS',
        'MOOD_REGULATORS',
        'VIRAL_AGENTS',
        'MICRO_FUSION_GENERATORS',
        'SUPERGRAINS',
        'LASER_RIFLES',
        'HOLOGRAPHICS',
        'SHIP_SALVAGE',
        'RELIC_TECH',
        'NOVEL_LIFEFORMS',
        'BOTANICAL_SPECIMENS',
        'CULTURAL_ARTIFACTS',
        'FRAME_PROBE',
        'FRAME_DRONE',
        'FRAME_INTERCEPTOR',
        'FRAME_RACER',
        'FRAME_FIGHTER',
        'FRAME_FRIGATE',
        'FRAME_SHUTTLE',
        'FRAME_EXPLORER',
        'FRAME_MINER',
        'FRAME_LIGHT_FREIGHTER',
        'FRAME_HEAVY_FREIGHTER',
        'FRAME_TRANSPORT',
        'FRAME_DESTROYER',
        'FRAME_CRUISER',
        'FRAME_CARRIER',
        'REACTOR_SOLAR_I',
        'REACTOR_FUSION_I',
        'REACTOR_FISSION_I',
        'REACTOR_CHEMICAL_I',
        'REACTOR_ANTIMATTER_I',
        'ENGINE_IMPULSE_DRIVE_I',
        'ENGINE_ION_DRIVE_I',
        'ENGINE_ION_DRIVE_II',
        'ENGINE_HYPER_DRIVE_I',
        'MODULE_MINERAL_PROCESSOR_I',
        'MODULE_GAS_PROCESSOR_I',
        'MODULE_CARGO_HOLD_I',
        'MODULE_CARGO_HOLD_II',
        'MODULE_CARGO_HOLD_III',
        'MODULE_CREW_QUARTERS_I',
        'MODULE_ENVOY_QUARTERS_I',
        'MODULE_PASSENGER_CABIN_I',
        'MODULE_MICRO_REFINERY_I',
        'MODULE_SCIENCE_LAB_I',
        'MODULE_JUMP_DRIVE_I',
        'MODULE_JUMP_DRIVE_II',
        'MODULE_JUMP_DRIVE_III',
        'MODULE_WARP_DRIVE_I',
        'MODULE_WARP_DRIVE_II',
        'MODULE_WARP_DRIVE_III',
        'MODULE_SHIELD_GENERATOR_I',
        'MODULE_SHIELD_GENERATOR_II',
        'MODULE_ORE_REFINERY_I',
        'MODULE_FUEL_REFINERY_I',
        'MOUNT_GAS_SIPHON_I',
        'MOUNT_GAS_SIPHON_II',
        'MOUNT_GAS_SIPHON_III',
        'MOUNT_SURVEYOR_I',
        'MOUNT_SURVEYOR_II',
        'MOUNT_SURVEYOR_III',
        'MOUNT_SENSOR_ARRAY_I',
        'MOUNT_SENSOR_ARRAY_II',
        'MOUNT_SENSOR_ARRAY_III',
        'MOUNT_MINING_LASER_I',
        'MOUNT_MINING_LASER_II',
        'MOUNT_MINING_LASER_III',
        'MOUNT_LASER_CANNON_I',
        'MOUNT_MISSILE_LAUNCHER_I',
        'MOUNT_TURRET_I',
        'SHIP_PROBE',
        'SHIP_MINING_DRONE',
        'SHIP_SIPHON_DRONE',
        'SHIP_INTERCEPTOR',
        'SHIP_LIGHT_HAULER',
        'SHIP_COMMAND_FRIGATE',
        'SHIP_EXPLORER',
        'SHIP_HEAVY_FREIGHTER',
        'SHIP_LIGHT_SHUTTLE',
        'SHIP_ORE_HOUND',
        'SHIP_REFINING_FREIGHTER',
        'SHIP_SURVEYOR',
    ]
)


FLIGHT_MODES = frozenset(['DRIFT', 'STEALTH', 'CRUISE', 'BURN'])


FACTION_SYMBOL = frozenset(
    [
        'COSMIC',
        'VOID',
        'GALACTIC',
        'QUANTUM',
        'DOMINION',
        'ASTRO',
        'CORSAIRS',
        'OBSIDIAN',
        'AEGIS',
        'UNITED',
        'SOLITARY',
        'COBALT',
        'OMEGA',
        'ECHO',
        'LORDS',
        'CULT',
        'ANCIENTS',
        'SHADOW',
        'ETHEREAL',
    ]
)


SURVEYABLE_WAYPOINTS = frozenset(
    ['ASTEROID', 'ASTEROID_FIELD', 'ENGINEERED_ASTEROID']
)


SIPHONABLE_SYMBOLS = frozenset(
    ['LIQUID_HYDROGEN', 'LIQUID_NITROGEN', 'HYDROCARBON']
)

MINABLE_SYMBOLS = frozenset(
    [
        'ALUMINUM_ORE',
        'AMMONIA_ICE',
        'COPPER_ORE',
        'DIAMONDS',  # NOTE: Not mentioned in docs
        'GOLD_ORE',
        'ICE_WATER',
        'IRON_ORE',
        'PLATINUM_ORE',
        'PRECIOUS_STONES',
        'QUARTZ_SAND',
        'SILICON_CRYSTALS',
        'SILVER_ORE',
        'URANITE_ORE',  # NOTE: Not mentioned in docs
    ]
)

REFINABLE_SYMBOLS = frozenset(
    [
        'ALUMINUM',
        'COPPER',
        'FUEL',
        'GOLD',
        'IRON',
        'MERITIUM',
        'PLATINUM',
        'SILVER',
        'URANITE',
    ]
)


SHIP_MOUNTS = frozenset(
    [
        'MOUNT_GAS_SIPHON_I',
        'MOUNT_GAS_SIPHON_II',
        'MOUNT_GAS_SIPHON_III',
        'MOUNT_SURVEYOR_I',
        'MOUNT_SURVEYOR_II',
        'MOUNT_SURVEYOR_III',
        'MOUNT_SENSOR_ARRAY_I',
        'MOUNT_SENSOR_ARRAY_II',
        'MOUNT_SENSOR_ARRAY_III',
        'MOUNT_MINING_LASER_I',
        'MOUNT_MINING_LASER_II',
        'MOUNT_MINING_LASER_III',
        'MOUNT_LASER_CANNON_I',
        'MOUNT_MISSILE_LAUNCHER_I',
        'MOUNT_TURRET_I',
    ]
)
