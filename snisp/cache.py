import httpx
import logging
import urllib.parse as urlparse

import snisp


logger = logging.getLogger(__name__)


# NOTE: Only waypoints work for now in DB

FUEL_STATIONS = {}


def get_fuel_stations(location):
    # Assumes the calling thread is already under a lock
    # Ideally, it will be the agent's lock
    return FUEL_STATIONS.get(location.system)


def insert_fuel_stations(location, fuel_stations):
    # Assumes the calling thread is already under a lock
    # Ideally, it will be the agent's lock
    FUEL_STATIONS[location.system] = list(fuel_stations)


def lookup(*args, **kwargs):
    # args: (client, url)
    # kwargs: {params}
    url = urlparse.urlsplit(args[1])
    parts = url.path.split('/')
    if parts[-1] == 'market':
        # Markets always need live data
        # Fucks up trade_volume otherwise
        return
    elif parts[-1] == 'waypoints':
        return waypoints_lookup(url, params=kwargs.get('params'))


def insert(response, *args, **kwargs):
    url = urlparse.urlsplit(args[1])
    parts = url.path.split('/')
    if parts[-1] == 'market':
        # Markets always need live data
        # Fucks up trade_volume otherwise
        return
    elif parts[-1] == 'waypoints':
        return waypoints_insert(response, url, params=kwargs.get('params'))


def waypoints_lookup(url, *, params=None):
    parts = url.path.split('/')
    params = params if params is not None else {}
    system = parts[-2]
    page = int(params.get('page', 0))
    page_limit = int(params.get('limit', 20))
    traits = params.get('traits', None)
    types = params.get('type', None)
    if data := snisp.database.get_waypoints(
        system=system,
        page_limit=page_limit,
        page=page,
        traits=traits,
        types=types,
    ):
        request = httpx.Request('GET', url.path, params=params)
        return httpx.Response(200, json=data, request=request)


def waypoints_insert(response, url, params=None):
    parts = url.path.split('/')
    system = parts[-2]
    params = params if params is not None else {}
    page = int(params.get('page', 0))
    page_limit = int(params.get('limit', 20))
    traits = params.get('traits', None)
    types = params.get('type', None)
    snisp.database.insert_waypoints(
        response.json(),
        system=system,
        page_limit=page_limit,
        page=page,
        traits=traits,
        types=types,
    )
