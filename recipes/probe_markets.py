import threading
import time

from snisp.agent import Agent


"""
This recipe will run until all of the Markets in your Command Ship's System
have a Probe DOCKED or IN_ORBIT at each Market.

The recipe can be run in it's own thread and it requires no monitoring,
which is ideal for running as a sub-script for a larger game.

Each new iteration of agent.fleet.probes() will return the most up-to-date
list of Probes. Meaning, if you purchase additional Probes in a seperate
thread in the time between iterations, the Probes will automatically
show up here.
"""


def main(*, agent_symbol, faction='', email='', token=''):
    # Get your agent
    agent = Agent(
        symbol=agent_symbol, faction=faction, email=email, token=token
    )

    # Fire off a thread
    # The thread will run until either all Markets or probed
    # or the program exits
    t = threading.Thread(target=run, args=(agent,), daemon=True)
    t.start()


def run(agent):
    # Get your command ship
    command_ship = next(iter(agent.fleet))

    # Get all of the Markets in your Command Ship's System
    markets = list(command_ship.markets)

    # Empty set for tracking probed Markets
    markets_with_probes = {}

    # Set of Probes that are at their Market
    probes_at_markets = {}

    while True:
        next_arrival = 60 * 15  # Fifteen minute baseline
        for probe in agent.fleet.probes():
            if probe.symbol in probes_at_markets:
                # Already at a Market
                continue
            if probe.nav.status == 'IN_TRANSIT':
                # Probe may already be in transit to a Market from
                # a previous iteration or function
                if probe.arrival < next_arrival:
                    # Set the timer to reset once this Probe arrives at
                    # it's destination
                    next_arrival = probe.arrival
                continue
            if probe.at_market:
                # The Probe is either at a Market that already has a probe,
                # which means it needs to move on to another Market; or,
                # it's at a Market that does not have a Probe listed at it,
                # which means it's safe to stay and should notify other Probes
                if probe.nav.waypoint_symbol not in markets_with_probes:
                    markets_with_probes.add(probe.nav.waypoint_symbol)
                    # Mark the Probe as at a Market
                    probes_at_markets.add(probe.symbol)
                    continue

            # At this point we know the Probe is not IN_TRANSIT and is not
            # at a Market that already has a Probe at it
            # Next thing to do is find the closest Market to the Probe
            next_market = probe.closest(markets)
            while next_market.symbol in markets_with_probes:
                # Drain the Markets pool of already known Probed Markets
                _ = markets.remove(next_market)
                if not markets:
                    # No remaining Markets! All Markets have been Probed
                    # or have a Probe heading their way
                    return
                next_market = probe.closest(markets)

            # Move the Probe on to the new Market location
            probe.update_flight_mode('CRUISE')
            # .navigate will *not* block if the Probe is not already IN_TRANSIT
            # The check for IN_TRANSIT at the top of the loop confirmed this
            probe.navigate(next_market)

            # Mark the Market as Probed
            markets_with_probes.add(next_market.symbol)

            # Mark the Probe as at a Market
            probes_at_markets.add(probe.symbol)

            # Remove the Market from the list
            _ = markets.remove(next_market)
            if not markets:
                # No remaining Markets! All Markets have been Probed
                # or have a Probe heading their way
                return

        # Wait either the default 15 minutes or when the next Probe is set to
        # arrive at its destination
        time.sleep(next_arrival)
