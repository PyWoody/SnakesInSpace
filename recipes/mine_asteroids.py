import itertools
import queue
import threading
import time

from snisp.agent import Agent


"""
This recipe shows how to more efficiently strip all of the minable Asteroids
in the Agent's current System. By using a Queue of Asteroid Symbols, the recipe
demonstrates how Waypoints can be easily serialized. The shared Queue between
threads is also a more efficient means of extraction, compared to the
default example in the README.

The recipe can be run in it's own thread and it requires no monitoring,
which is ideal for running as a sub-script for a larger game.

Each new iteration of agent.fleet will return the most up-to-date
list of available Ships. Meaning, if you purchase additional Ships
in a seperate thread in the time between iterations and those Ships can_mine,
the Ships will automatically show up here.
"""


def main(*, agent_symbol, faction='', email='', token=''):
    # Get your agent
    agent = Agent(
        symbol=agent_symbol, faction=faction, email=email, token=token
    )

    # Fire off a thread
    # The thread will run until all Asteroids have been stripped
    # or the program exits
    t = threading.Thread(target=run, args=(agent,), daemon=True)
    t.start()


def run(agent):
    # Get your command ship
    command_ship = next(iter(agent.fleet))

    # Get all of the mineable Asteroids Symbols in your Command Ship's System
    # Sets automatically prevent duplicates
    asteroid_symbols = {
        i.symbol for i in
        itertools.chain(
            command_ship.waypoints.asteroids(),
            command_ship.waypoints.engineered_asteroids(),
        )
    }
    # Build a Queue with all of the Symbols
    # You could just build the Queue with the Asteroids directly but one of
    # the intents of this recipe is to show how Waypoints can go from
    # symbol --> Waypoint, which makes serializing data a breeze
    asteroid_queue = queue.Queue()
    for symbol in asteroid_symbols:
        asteroid_queue.put(symbol)

    already_mining_ships = set()

    wait = 60 * 15  # Fifteen minutes between loops
    while not asteroid_queue.empty():
        for ship in agent.fleet:
            if ship.symbol not in already_mining_ships:
                if ship.can_mine:
                    t = threading.Thread(
                        target=extract,
                        args=(ship, asteroid_queue),
                        daemon=True
                    )
                    t.start()
                    already_mining_ships.add(ship.symbol)
        for _ in range(wait):
            time.sleep(1)
            # Check the queue once a second
            if asteroid_queue.empty():
                # All Asteroids are being extracted! Need to break out of the
                # loop and wait until they're completed
                break
    # Block until all currently working threads have had a chance to strip
    # their Asteroids and mark their queue task done
    asteroid_queue.join()


def extract(ship, asteroid_queue):
    try:
        # Attempt to get an Asteroid symbol
        asteroid_symbol = asteroid_queue.get_nowait()
    except queue.Empty:
        # No more asteroids. Exit
        return
    else:
        # Get the Asteroid Waypoint from the Asteroid symbol
        asteroid = ship.waypoints.get(waypoint_symbol=asteroid_symbol)

    while True:
        # Navigate to the Asteroid
        # Autopilot blocks until you're at the destination
        ship.autopilot(asteroid)
        stripped = False
        # Extract until cargo is full
        # ship.extract automatically updates the ship's cargo
        while ship.cargo.units < ship.cargo.capacity:
            extraction = ship.extract()
            if extraction.units == 0:
                # Asteroid is stripped! Nothing else to see here
                stripped = True
                break
        # Sell off whatever is in the Ship's cargo at the closest Markets
        # Jettisons anything that can't be sold
        ship.sell_off_cargo()
        if stripped:
            # Mark the Asteroid as completed
            asteroid_queue.task_done()
            try:
                # Attempt to get the next Asteroid Symbol
                asteroid_symbol = asteroid_queue.get_nowait()
            except queue.Empty:
                # No more asteroids. Exit
                return
            else:
                # Get the Asteroid Waypoint from the Asteroid symbol
                asteroid = ship.waypoints.get(waypoint_symbol=asteroid_symbol)
