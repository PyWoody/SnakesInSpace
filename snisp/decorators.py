import functools
import httpx
import itertools
import logging
import threading
import time

import snisp

from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class CachedRateLimiter:

    def __init__(self):
        self.lock = threading.Lock()
        self.last_request = datetime.now(timezone.utc)

    def __call__(self, func):

        functools.wraps(func)

        def inner(*args, **kwargs):
            if args[0].testing:
                return func(*args, **kwargs)
            is_get = True if func.__name__ == 'get' else False
            with self.lock:
                if is_get:
                    if cache := snisp.cache.lookup(*args, **kwargs):
                        return cache
                # ignoring bursts
                delta = datetime.now(timezone.utc) - self.last_request
                if not delta.seconds:
                    second = pow(10, -6) * delta.microseconds
                    if second < .5:
                        time.sleep(.5 - second)
                try:
                    response = func(*args, **kwargs)
                    if is_get:
                        snisp.cache.insert(response, *args, **kwargs)
                    return response
                finally:
                    self.last_request = datetime.now(timezone.utc)
        return inner


def cooldown(func):

    functools.wraps(func)

    def inner(*args, **kwargs):
        for ship in itertools.chain(args, kwargs.values()):
            if isinstance(ship, snisp.fleet.Ship):
                if expires := ship.cooldown.expiration:
                    expires = datetime.fromisoformat(expires)
                    delta = expires - datetime.now(timezone.utc)
                    if delta.days >= 0:  # pragma: no cover aka impatient
                        time.sleep(delta.seconds)
        return func(*args, **kwargs)
    return inner


def docked(func):

    functools.wraps(func)

    def inner(*args, **kwargs):
        for ship in itertools.chain(args, kwargs.values()):
            if isinstance(ship, snisp.fleet.Ship):
                if ship.nav.status != 'DOCKED':
                    ship.dock()
        return func(*args, **kwargs)
    return inner


def in_orbit(func):

    functools.wraps(func)

    def inner(*args, **kwargs):
        for ship in itertools.chain(args, kwargs.values()):
            if isinstance(ship, snisp.fleet.Ship):
                if ship.nav.status != 'IN_ORBIT':
                    ship.orbit()
        return func(*args, **kwargs)
    return inner


def retry(jitter=.2, max_retries=5):

    def wrapper(func):

        functools.wraps(func)

        def inner(*args, **kwargs):
            ship = args[0]
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except httpx.HTTPError as e:
                    logger.warning(
                        f'Attempt: {attempt}/{max_retries}. '
                        f'Received {e!r}.'
                    )
                    if not ship.agent.client.testing:  # pragma: no cover
                        time.sleep(jitter * attempt)
                    last_exception = e
                except snisp.exceptions.ClientError as e:
                    logger.warning(
                        f'Attempt: {attempt}/{max_retries}. '
                        f'Received: {e!r}.'
                    )
                    if data := e.data:
                        if cooldown := data.get(
                            'cooldown'
                        ):  # pragma: no cover
                            if wait := cooldown.get('remainingSeconds'):
                                if not ship.agent.client.testing:
                                    time.sleep(float(wait))
                        elif wait := max(
                            [
                                data.get('secondsToArrival', 0),
                                data.get('retryAfter', 0),
                                data.get('remainingSeconds', 0),
                            ]
                        ):  # pragma: no cover
                            if not ship.agent.client.testing:
                                time.sleep(float(wait))
                        elif code := data.get('code'):
                            if err := snisp.exceptions.error_codes.get(
                                int(code)
                            ):
                                raise err(str(e))
                    last_exception = e
            raise last_exception
        return inner
    return wrapper


def transit(func):

    functools.wraps(func)

    def inner(*args, **kwargs):
        for ship in itertools.chain(args, kwargs.values()):
            if isinstance(ship, snisp.fleet.Ship):
                if ship.nav.status == 'IN_TRANSIT':
                    if arrives_in := ship.arrival:  # pragma: no cover
                        time.sleep(arrives_in)
                    ship.arrived_at_destination()
        return func(*args, **kwargs)
    return inner
