# Snakes in Space!
## A Python library for the SpaceTraders game

You can find additional information, guides, support, and API documentation about SpaceTraders on their website here: https://spacetraders.io/.


The SpaceTraders team will not be able to assist you with any issues regarding SnakesInSpace. Please open a ticket here if you experience any reproducible issues with the Library.

## Installation and Requirements

The minimum Python version supported is currently Python 3.9.

SnakesInSpace will require `httpx` to play and `pytest` if you want to run the tests yourself.

You can install SnakesInSpace from PyPi as well

```
% pip install SnakesInSpace
```



## Quick Example

* Get or Create your Agent
* Get your COMMAND ship, which comes with extraction mounts
* Find the closest Asteroid
* Navigate your ship to the Asteroid
* Extract until your ship's cargo is full while also jettisoning any ICE_WATER

```python3
from snisp.agent import Agent

>>> agent = Agent(symbol='your_symbol_here', faction='COSMIC', email='optional@exmaple.com')
>>> ship = next(iter(agent.fleet))
>>> asteroid = ship.closest(ship.waypoints.asteroids())
>>> ship.autopilot(asteroid)  # Autopilot blocks until at destination
>>> while ship.cargo.units < ship.cargo.capacity:
...     extraction = ship.extract()  # ship.extract will handle Cooldowns automatically
...     if extraction.symbol == 'ICE_WATER':
...         ship.jettison(extraction.symbol, exctraction.units)
>>> ship.cargo.units == ship.cargo.capacity
True
```



<details>
<summary>Agent</summary>

The `Agent` represents your Player in SpaceTraders.

```python3
from snisp.agent import Agent

>>> agent = Agent(symbol='your_symbol_here', faction='COSMIC', email='optional@exmaple.com')
>>> agent.symbol
'your_symbol_here'
>>> agent.token
'AGENT_TOKEN_STRING'
```

Your `symbol` is your callsign in SpaceTraders. The `email` field is entirely optional.

If you already know your `token`, you can also access your `Agent` directly by
```python3
>>> agent = Agent(symbol='your_symbol_here', token='your_spacetraders_token')
>>> agent.symbol
'your_symbol_here'
>>> agent.token
'your_spacetraders_token'
```

SpaceTraders is still in the Alpha phase so expect a full system restart every 2-3 weeks. If a restart occurs, you will have to manually reset your local config and attempt to log in again.

```python3
from snisp import agent

>>> agent = agent.Agent(symbol='your_symbol_here', faction='COSMIC', email='optional@exmaple.com')
>>> agent.data
snisp.exceptions.ClientError: Message: Failed to parse token. Token version does not match the server. Server resets happen on a weekly to bi-weekly frequency during alpha. After a reset, you should re-register your agent. Expected: v2.2.0, Actual: v2.1.5 | Code: 401 | Data: {'expected': 'v2.2.0', 'actual': 'v2.1.5'}
>>> snisp.agent.reset()
>>> agent = agent.Agent(symbol='your_symbol_here', faction='COSMIC', email='optional@exmaple.com')
>>> agent.data
PlayerData({'accountId': 'AGENT_TOKEN_ID', 'symbol': 'YOUR_SYMBOL_HERE', 'headquarters': 'X1-CC27-A1', 'credits': 100000, 'startingFaction': 'COSMIC', 'shipCount': 2})
```

It is up to the user to handle resetting their own account and managing their tokens across devices.


The default `Faction` is "COSMIC," which is guaranteed to work. The complete list of Factions is 
`AEGIS`, `ANCIENTS`, `ASTRO`, `COBALT`, `CORSAIRS`, `COSMIC`, `CULT`, `DOMINION`, `ECHO`, `ETHEREAL`, `GALACTIC`, `LORDS`, `OBSIDIAN`, `OMEGA`, `QUANTUM`, `SHADOW`, `SOLITARY`, `UNITED`, and `VOID`. Not all `Factions` may be supported at this time by SpaceTraders. If in doubt, use "COSMIC."


**Accessing Your Agent**

You can access your Agent from any SnakesInSpace object.

From your ship,

```python3
>>> ship = agent.fleet('SHIP_SYMBOL')
>>> ship.agent
Agent(symbol='your_symbol_here', faction='COSMIC', email='optional@exmaple.com')
```

from a waypoint,

```python3
>>> ship = agent.fleet('SHIP_SYMBOL')
>>> waypoint = next(iter(ship.waypoints))
>>> waypoint.agent
Agent(symbol='your_symbol_here', faction='COSMIC', email='optional@exmaple.com')
```

and so on.

Each `Agent` will have its own lock accessible at `agent.lock`. The lock is used internally but can also be used by the user. The lock type is a reentrant lock (`threading.RLock`).
</details>

<details>
<summary>Contracts</summary>
Every new `Agent` starts with an open `Contract`. `Contract`s can be a great way to jump-start a new game.

Your `Contracts` will be accessible via your `Agent`. For instance, to get the current `Contract`, simply call

```python3
>>> contract = agent.contracts.current
>>> contract
Contract({'id': 'CONTRACT_ID', 'factionSymbol': 'COSMIC', 'type': 'PROCUREMENT', 'terms': {'deadline': '2024-08-24T14:15:22Z', 'payment': {'onAccepted': 151237, 'onFulfilled': 388895}, 'deliver': [{'tradeSymbol': 'IRON_ORE', 'destinationSymbol': 'X1-BD70-A1', 'unitsRequired': 60, 'unitsFulfilled': 0}]}, 'accepted': False, 'fulfilled': False, 'expiration': '2024-08-24T14:15:22Z', 'deadlineToAccept': '2024-08-24T14:15:22Z'})
```

According to your current `Contract`, you need to deliver 60 units of "IRON_ORE" to a `Waypoint` at "X1-BD70-A1." Before you can deliver items to a `Contract`, you will first need to accept it. According to,

```python3
>>> contract.accepted
False
```

the `Contract` has not been accepted. To accept the `Contract`, accept it via the `Contract.accept` method like

```python3
>>> contract.accept()
>>> contract.accepted
True
```
The `Contract.accept` method is idempotent, so you can call it as many times as you want.

If you have "IRON_ORE" in your `ship`'s cargo and you're already at the `contract.terms.deliver[0].destination_symbol`, you can deliver the resources by using the `contract.deliver` method, as shown below

```python3
>>> ship = agent.fleet('SHIP_SYMBOL')  # The ship at destinationSymbol
>>> ship.cargo.inventory  # This ship has 10 units of IRON_ORE in it's cargo
[Inventory({'symbol': 'IRON_ORE', 'name': 'Iron Ore', 'description': 'DESCRIPTION', 'units': 10})]
>>> contract.deliver(ship, 'IRON_ORE')  # or contract.deliver(ship, 'IRON_ORE', max_units=10)
>>> contract
Contract({'id': 'CONTRACT_ID', 'factionSymbol': 'COSMIC', 'type': 'PROCUREMENT', 'terms': {'deadline': '2024-08-24T14:15:22Z', 'payment': {'onAccepted': 151237, 'onFulfilled': 388895}, 'deliver': [{'tradeSymbol': 'IRON_ORE', 'destinationSymbol': 'X1-BD70-A1', 'unitsRequired': 60, 'unitsFulfilled': 10}]}, 'accepted': True, 'fulfilled': False, 'expiration': '2024-08-24T14:15:22Z', 'deadlineToAccept': '2024-08-24T14:15:22Z'})
>>> ship.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
```

A `contract` will automatically update to show you delivered the 10 units of "IRON_ORE" from your ship to the `contract`. Your `ship`'s cargo will be updated automatically as well.

The `max_units` kwarg is entirely optional. If not specified, the `deliver` method will automatically deliver either the maximum units of `trade_symbol` in the `ship`'s cargo or the maximum remaining required units of `trade_symbol` for the `contract`.

Warnings will be logged if you attempt to `deliver` items to a contract that has either had all the remaining units fulfilled or if there are no units of `trade_symbol` in the `ship`'s cargo.

Once you've delivered all of the necessary units to the `contract`'s `Waypoint`, you can fulfill it by calling the `contract.fulfill` method, like

```python3
>>> contract.fuflill()
>>> contract.fulfilled
True
```

`fulfill` works like `accept` in that it is idempotent.


A `contract` instance is not thread safe and may become stale if ships in other threads `deliver` items. To get a fresh instance of the `contract`, you can always call

```python3
>>> contract = contract.refresh()
```

which will return a new `contract` object.


**New Contracts**

Once you've fulfilled a `contract`, you can move on to the next one.

Begin by navigating any ship to a `Waypoint` with a `Faction` and then calling `ship.negotiate_contract()`. The new `contract` will not be accepted by default, so you will have to call `contract.accept()` before you can begin delivering items to it.

The quickest way to get a new `contract` is reproduced below for convenience:

```python3
>>> ship = agent.fleet('SHIP_SYMBOL')
>>> wp_with_faction = (i for i in ship.waypoints if i.faction.symbol)
>>> wp = ship.closest(wp_with_faction)
>>> ship.autopilot(wp)
>>> contract = ship.negotiate_contract()
>>> contract.accept()
```

`ship.autopilot` and `ship.closest` will be covered in the **Fleet** section.


**Exceptions**

`ContractNotAcceptedError` will be raised if you attempt to `deliver` items to a `contract` that has not been accepted.

`ContractFulfilledError` will be raised if you attempt to `deliver` items to a `contract` that has already been fulfilled.

`ContractDeadlineError` will be raised if you attempt to `deliver` items to a `contract` that has already expired.

For additional Errors, see the "Contract Error Codes" found in `snisp.exceptions`.


**Helper Properties**

A `contract` has a few helper properties.

```python3
>>> contract.expired  # Boolean for if the contract has already expired
>>> contract.extractable  # Boolean for if items not yet fulfilled in the contract have tradeSymbols that can be extracted from an Asteroid
>>> contract.siphonable  # Boolean for if items not yet fulfilled in the contract have tradeSymbols that can be siphoned from a Gas Giant
```
</details>

<details>
<summary>Fleet</summary>

By default, a new Agent will receive a command `ship` and a `probe`. As you continue to play and purchase additional `ships`, `probes`, and `drones`, your fleet will be easily managable from your `agent.fleet`.

```python3
# Iterate over the whole fleet for all available ships
>>> whole_fleet = list(agent.fleet)

# Get a ship by symbol
>>> ship = agent.fleet('SHIP_SYMBOL')

# Get the first ship, which will be the default COMMAND ship
>>> ship = next(iter(agent.fleet))

# Get all available Drones
>>> drones = list(agent.fleet.drones())

# Get all available Mining Drones
>>> mining_drones = list(agent.fleet.mining_drones())

# Get all available Siphon Drones
>>> siphon_drones = list(agent.fleet.siphon_drones())

# Get all available Probes
>>> probes = list(agent.fleet.probes())

# Get all available Shuttles
>>> shuttles = list(agent.fleet.shuttles())

# Get all available Ships, excluding probes and drones
>>> ships = list(agent.fleet.ships())
```

It's important to remember that `fleet` itself, `drones`, `mining_drones`, `siphon_drones`, `probes`, `ships`, and `shuttles` are iterables. This can cause issues if you assign a variable to an initialized iterable and attempt to iterate over it more than once.


```python3
>>> probes = agent.fleet.probes()
>>> _ = list(probes)  # Default, the single starting probe
>>> list(probes)
[]  # "probes" iterable has been exhausted
```

This is intentional as there may have been additional probes purchased between the two calls.

A nice side effect of this is that any additional ships purchased between when iterating over `agent.fleet` starts and finishes will be returned. For example,

```python3
>>> for ship in agent.fleet:
...     do_something(ship)  # operation that takes a long time
...     # Additional ship was purchased in a another thread
...     # The new ship will be called to `do_something`
```

As always, you can avoid this side effect by building the list of ships ahead of time with `ships = list(agent.fleet)`.


### Ship

A `ship` returned by `agent.fleet` will be a `snisp.fleet.Ship` instance. 

```python3
>>> ship = next(iter(agent.fleet))  # Starting ship. This will be the default COMMAND ship
>>> ship.registration.role
'COMMAND'
>>> ship.symbol
'YOUR_SYMBOL_HERE-1'
```

Like all SnakesInSpace objects, it will be created from the JSON data returned by the SpaceTraders API. For instance, below is the example data for `GET https://api.spacetraders.io/v2/my/ships/{shipSymbol}` as returned by the SpaceTraders API:

```json
{
  "data": {
    "symbol": "YOUR_SYMBOL_HERE-1",
    "registration": {
      "name": "string",
      "factionSymbol": "string",
      "role": "COMMAND"
    },
    "nav": {
      "systemSymbol": "string",
      "waypointSymbol": "string",
      "route": {
        "destination": {
          "symbol": "string",
          "type": "PLANET",
          "systemSymbol": "string",
          "x": 0,
          "y": 0
        },
        "origin": {
          "symbol": "string",
          "type": "PLANET",
          "systemSymbol": "string",
          "x": 0,
          "y": 0
        },
        "departureTime": "2024-08-24T14:15:22Z",
        "arrival": "2024-08-24T14:15:22Z"
      },
      "status": "IN_TRANSIT",
      "flightMode": "CRUISE"
    },
    "crew": {
      "current": 0,
      "required": 0,
      "capacity": 0,
      "rotation": "STRICT",
      "morale": 0,
      "wages": 0
    },
    "frame": {
      "symbol": "FRAME_PROBE",
      "name": "string",
      "description": "string",
      "condition": 0,
      "moduleSlots": 0,
      "mountingPoints": 0,
      "fuelCapacity": 0,
      "requirements": {
        "power": 0,
        "crew": 0,
        "slots": 0
      }
    },
    "reactor": {
      "symbol": "REACTOR_SOLAR_I",
      "name": "string",
      "description": "string",
      "condition": 0,
      "powerOutput": 1,
      "requirements": {
        "power": 0,
        "crew": 0,
        "slots": 0
      }
    },
    "engine": {
      "symbol": "ENGINE_IMPULSE_DRIVE_I",
      "name": "string",
      "description": "string",
      "condition": 0,
      "speed": 1,
      "requirements": {
        "power": 0,
        "crew": 0,
        "slots": 0
      }
    },
    "cooldown": {
      "shipSymbol": "string",
      "totalSeconds": 0,
      "remainingSeconds": 0,
      "expiration": "2024-08-24T14:15:22Z"
    },
    "modules": [
      {
        "symbol": "MODULE_MINERAL_PROCESSOR_I",
        "capacity": 0,
        "range": 0,
        "name": "string",
        "description": "string",
        "requirements": {
          "power": 0,
          "crew": 0,
          "slots": 0
        }
      }
    ],
    "mounts": [
      {
        "symbol": "MOUNT_GAS_SIPHON_I",
        "name": "string",
        "description": "string",
        "strength": 0,
        "deposits": [
          "QUARTZ_SAND"
        ],
        "requirements": {
          "power": 0,
          "crew": 0,
          "slots": 0
        }
      }
    ],
    "cargo": {
      "capacity": 0,
      "units": 0,
      "inventory": [
        {
          "symbol": "PRECIOUS_STONES",
          "name": "string",
          "description": "string",
          "units": 1
        }
      ]
    },
    "fuel": {
      "current": 300,
      "capacity": 400,
      "consumed": {
        "amount": 100,
        "timestamp": "2024-08-24T14:15:22Z"
      }
    }
  }
}
```

This data, like all objects returned by `agent`, `fleet`, `waypoints`, `markets`, and `systems`, will be directly accessible to their respective object via dot-lookups. For convenience, the "data" in the JSON data is skipped to make accessing more convenient.

Need to check the current fuel level?

```python3
>>> ship.fuel.current
300
```

Need to check the current status of a `ship`'s flight mode?

```python3
>>> ship.nav.flight_mode
'CRUISE'
```

For convenience, you can access attributes via their original camelCase, e.g., flightMode, or via snake_case, e.g., flight_mode. For instance, the previous lookup could also be done instead as


```python3
>>> ship.nav.flightMode
'CRUISE'
```

The `.to_dict()` helper function can translate the data into a Python dictionary for convenience, too. This is especially handy for pretty-printing.

```python3
>>> ship.fuel.to_dict()
{'current': 300, 'capacity': 400, 'consumed': {'amount': 100, 'timestamp': '2024-08-24T14:15:22Z'}}
```

Each dict key will represent a dot-lookup attribute.

```python3
>>> ship.fuel.consumed.amount
100
```

which is equivalent to


```python3
>>> ship.to_dict()['fuel']['consumed']['amount']
100
```


Like all objects created by SnakesInSpace, they are not inherentely thread safe. If a seperate thread updates the `ship` associated with the `ship`'s `ship.symbol`, the reference may become stale. To return a new, up-to-date instance of a `ship`, call

```python3
>>> ship = ship.refresh()
>>> ship.refresh().cargo  # Can be done in-place, too
```

**Navigation**

Moving a ship between `Waypoints` is the most important aspect of the game and much care has been taken to make it as simple as possible.


*Navigate*

The default `ship.navigate` method accepts a `Waypoint` as an arg and a boolean `raise_error` kwarg. The `Waypoint` can be any `Waypoint` type that is found in the same System as the ship. The optional kwarg, `raise_error`, tells the function if it should raise an error if any exceptions occur or suppress and return the error. By default, `raise_error` is `True`.

The `raise_error` kwarg can be ignored by most users.

A typical `navigate` scenario would be to vist the closest `Waypoint`.

```python3
>>> ship = next(iter(agent.fleet))
>>> waypoint = ship.closest(ship.waypoints)
>>> waypoint.symbol
X1-BD70-J64
>>> waypoint.type
ASTEROID
>>> ship.navigate(waypoint)
```

If the `navigate` request is succesful, control will be returned back to the caller immediately and you can begin processing requests for other `ships` in the same thread.


*Autopilot*

A convenience method, `ship.autopilot`, was created to take the guesswork out of navigating, refueling, and controlling flight modes that is inherit to `ship.navigate`. Any situation in which a `ship` can use `ship.navigate`, it could more easily use `ship.autopilot`

```python3
>>> ship = next(iter(agent.fleet))
>>> waypoint = ship.closest(ship.waypoints)
>>> waypoint.symbol
X1-BD70-J64
>>> waypoint.type
ASTEROID
>>> ship.autopilot(waypoint)  # Blocks until at destination
>>> ship.nav.waypoint_symbol  # Current location
X1-BD70-J64
>>> ship.nav.route.destination.symbol  # Last navigation's destination symbol
X1-BD70-J64
>>> ship.nav.route.destination.type  # Last navigation's destination type
ASTEROID
```

Now, with `ship.autopilot`, the library will attempt to `navigate` to the `Waypoint`, but, if it fails due to distance or lack of fuel, `autopilot` will automatically control refuelling and updating flight modes accordingly to get you to the `Waypoint` as quickly as possible.

There are a few caveats with this approach, namely, by design, `autopilot` will block so control will not be returned to the thread until the `ship` reaches the `Waypoint`; and, there is always an off-chance the call to `navigate` from within `autopilot` will use exactly the correct amount of fuel to get you to the destination.

For the former, all calls to `ship.autopilot` should be done via a thread if blocking is an issue.

For the latter, if a `ship` does become "dead" in the water in that it cannot refuel itself at the destination, the `ship` will be added to the `agent`'s `agent.dead_ships` dictionary and skipped on all subsequent `agent.fleet` iterations. It is possible to `navigate` another `ship` to the dead `ship`'s location to manually `transfer` fuel, but that is up to the user.

`ship.autopilot` does accept a `done_callback` kwarg. The callback, so long as it is `callable()`, will be executed before returning control back to the thread. This is convenient if you, say, want to navigate to a `Waypoint` and make an extraction before waiting for the next thread loop.

```python3
>>> ship = next(iter(agent.fleet))
>>> asteroid = ship.closest(ship.waypoints.asteroids())
>>> ship.autopilot(asteroid, done_callback=ship.extract)
```

By default, `ship.autopilot` will attempt to `refuel` at every navigation stage, as well as before returning control back to the thread.


*Navigating with Probes*

In the current iteration, `Probes` in SpaceTraders do not require fuel.

```python3
>>> probe = next(iter(agent.fleet.probes()))
>>> probe.fuel
Fuel({'current': 0, 'capacity': 0, 'consumed': {'amount': 0, 'timestamp': '2024-03-03T16:18:13.155Z'}})
```

Due to this, you can just yeet them without regard by calling `.navigate` and fire-and-forgetting it.

```python3
>>> for probe in agent.fleet.probes():
...     if probe.nav.status != 'IN_TRANSIT:
...         if probe.nav.flight_mode != 'CRUISE':
...             probe.update_flight_mode('CRUISE')
...         probe.navigate(AnyWaypointInTheSystem)
```

You do not need to use `.autopilot` in this situation.


*Changing Flight Modes*

You can manually change flight modes by calling `ship.update_flight_mode` with 'DRIFT', 'STEALTH', 'CRUISE',  or 'BURN'. Note that `ship.autopilot` will change your flight mode to `CRUISE` by default.


*Refuel*

As mentioned previously, if you stick with `ship.autopilot`, you will not need to manually refuel. If you wish to refuel on your own, you can always call `ship.refuel` when located at a `Waypoint` that exports or exchanges FUEL.

For convenience, the `ship` object has a `closest_fuel` method that can find the closest available `Waypoint` that sells fuel.

```python3
>>> ship = next(iter(agent.fleet))
>>> fuel_station = ship.closest_fuel()
>>> ship.navigate(fuel_station)
>>> ship.refuel()
```

You can also refuel from fuel found in the `ship.cargo` by calling
```python3
>>> ship = next(iter(agent.fleet))
>>> ship.refuel(from_cargo=True)
```

This can be helpful for refueling dead ships.

Refuel also has an `ignore_errors` kwarg that accepts a boolean. If `True`, any exception raised while refueling will be suppressed and the exception will be returned instead. This is convenient for attempting to refuel at every `Waypoint` because why not.


*Jump*

Each System has at least one `JumpGate` that allows the `ship` to navigate between Systems. To use a `JumpGate`, the gate will need to be fully constructed and the `ship` will need to be located at the `Waypoint`.

```python3
>>> ship = next(iter(agent.fleet))
>>> jump_gate = next(iter(ship.waypoints.jump_gates()))
>>> jump_gate.is_under_construction
False
>>> ship.autpilot(jump_gate)
>>> next_system = jump_gate.data.connections[0]  # .connections will contain a list with all of the connected systems
>>> ship.jump(next_system)
```


*Warp*

A `ship` with the `Warp Drive` Mount installed can also `warp` to other Systems.

```python3
>>> ship = next(iter(agent.fleet))
>>> next_system = next(i for i in ship.agent.systems if i.symbol != ship.nav.system_symbol)
>>> ship.warp(next_system)
```


**Market Actions**


*Purchase*

"Traders" is in the name of the game so purchasing items at `Markets` is an integral function.

Purchasing items is as simple as navigating to the `Market` and purchasing as much as you can afford.

```python3
>>> ship = next(iter(agent.fleet))
>>> ship.cargo.inventory
[]
>>> market = ship.closest(ship.markets.exports('GOLD'))
>>> ship.autopilot(market)
>>> transaction = ship.purchase('GOLD', 40)
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD', 'name': 'Gold', 'description': 'DESCRIPTION', 'units': 40})]
```

*Autopurchase*

There are some caveats to `purchase`, such as, having the necessary credits, the `Market` selling the good in the required number of units, etc., that are handled for you with `ship.autopurchase`.

`ship.autopurchase` accepts the good symbol to purchase as the first arg and then optional kwargs of `max_units` and `buffer`, with defaults of 0 and 200_000, respectively.

If `max_units` > 0, at most `max_units` will be purchased. Otherwise, `ship.autopurchase` will purchase as many units of the goods as you can either hold or afford.

The `buffer` will be your credits buffer. The default 200_000 limit means you will be able to purchase up to `max_units` so long as your current `agent.data.credits` - `buffer` >= purchase price. To remove the `buffer`, just pass a 0.

Another benefit of `ship.autopurchase` is it handles the maximum units per transaction that the `Market` will allow.

```python3
>>> agent.data.credits
1_000_000
>>> ship = next(iter(agent.fleet))
>>> ship.cargo.inventory
[]
>>> market = ship.closest(ship.markets.exports('GOLD'))
>>> ship.autopilot(market)
>>> transactions = ship.autopurchase('GOLD')
>>> for transaction in transactions:
...     print(transaction.units)
20
20
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD', 'name': 'Gold', 'description': 'DESCRIPTION', 'units': 40})]
>>> agent.data.credits
800_000
```

limited by a buffer

```python3
>>> agent.data.credits
300_000
>>> ship = next(iter(agent.fleet))
>>> ship.cargo.inventory
[]
>>> market = ship.closest(ship.markets.exports('GOLD'))
>>> ship.autopilot(market)
>>> transactions = ship.autopurchase('GOLD', buffer=200_000)  # Default buffer
>>> for transaction in transactions:
...     print(transaction.units)
20
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD', 'name': 'Gold', 'description': 'DESCRIPTION', 'units': 20})]
>>> agent.data.credits
200_000
```

As you can see, `ship.autopurchase` absolves you of tracking units per transaction, `credits` and `cargo.capacity`.

Each attempt to make a purchase in `autopurchase` will be done under the `agent.lock` to gaurantee there are no race conditions with regards to your credit buffer when multiple threads are attempting purchases.


*Sell, Sell All, Sell off Cargo*

Once you've extracted or purchased items you wish to sell, you can do so with three different methods: `ship.sell`, `ship.sell_all`, and `ship.sell_off_cargo`.

The basic `ship.sell` works as

```python3
>>> agent.data.credits
100_000
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 35})]
>>> market = ship.closest(ship.markets.imports('GOLD_ORE'))
>>> ship.autopilot(market)
>>> transaction = ship.sell('GOLD_ORE', 20)
>>> transaction.units
20
>>> transaction.trade_symbol
GOLD_ORE
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 15})]
>> agent.data.credits
100_500
```

Attempting to sell items not found in your `ship.cargo` or more than the number of units in the `ship.cargo` will lead to exceptions.

Your `ship` will need to be located at a `Market` that imports the good.

To sell all items of a good in your `ship.cargo`, you can use the `ship.sell_all` method

```python3
>>> agent.data.credits
100_000
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 35})]
>>> market = ship.closest(ship.markets.imports('GOLD_ORE'))
>>> ship.autopilot(market)
>>> transactions = ship.sell_all('GOLD_ORE')
>>> for transaction in transactions:
...     print(transaction.units)
20
15
>>> ship.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
>> agent.data.credits
100_750
```

The `ship.sell_all` method will perform the necessary number of `ship.sell`'s until all units of the good in your `ship.cargo` have been sold. You can see from the returned `transactions` the `Market` the `ship` was located at accepted at most 20 units per transaction. The number of units per transaction will differ from `Market` to `Market` and from trade good to trade good within a single `Market`.

`ship.sell_all` handles trade volume automatically and is the preferred means of selling goods.

As always, your `ship` will still need to be located at a `Market` that imports the good.

Sometimes you just want to clear out your `ship.cargo` without jettisoning everything and losing the potential credits. To do this, call `ship.sell_off_cargo`

```python3
>>> agent.data.credits
100_000
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 35}), Inventory({'symbol': 'IRON_ORE', 'name': 'Iron Ore', 'description': 'DESCRIPTION', 'units': 5})
>>> transactions = ship.sell_off_cargo()
>>> for transaction in transactions:
...     print(transaction.symbol, transaction.units)
('GOLD_ORE', 20)
('GOLD_ORE', 15)
('IRON_ORE', 5)
>>> ship.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
>> agent.data.credits
100_850
```

If you only want to sell off all of your `GOLD_ORE`, you could call `ship.sell_off_cargo("GOLD_ORE")` to leave your `IRON_ORE` safe in your `ship.cargo`.

The `ship.sell_off_cargo` method is convenient because it will automatically navigate to the closest `Market` which imports each good. Note, this entails the method will block until all navigation has completed.



**Ship Actions**

A `ship` has a number of actions it can perform, depending on the installed Mounts and Modules.

*Survey*

If the ship is located at a `Waypoint` that supports `survey` and the `ship.can_survey`, a survey can be performed via

```python3
>>> survey = ship.waypoints.survey()
```

A single call to `survey` will return multiple "surveys." For example, the "surveys" in the previous `survey` can be found at

```python3
>>> survey.surveys
[{'signature': 'string', 'symbol': 'string', 'deposits': [{'symbol': 'string'}], 'expiration': '2024-08-24T14:15:22Z', 'size': 'SMALL'}]
```

When using a `survey` with a `extract_with_survey`, you will only pass one of the `survey.surveys` to the method. 

A `ship` will enter a cooldown period after performing a survey. The cooldown will prevent the ship from performing various tasks until the cooldown period has completed. SnakesInSpace handles this automaticaly for you, so you can attempt another survey and SnakesInSpace will block until the cooldown period has passed before making the request.

All actions that require a cooldown period to pass will be handled automatically.


*Extraction*

If the ship is located at a `Waypoint` that supports `extraction` and the `ship.can_mine`, exctraction can be done via

```python3
>>> ship.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
>>> extraction = ship.extract()
>>> extraction.symbol
GOLD_ORE
>>> extraction.units
4
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 4})]
```


*Extraction with Survey*

To get the best extraction results, you can make an extraction with a survey by calling `exctract_with_survey` while passing a `survey` from a `survey.surveys` to the method. The `survey` in question can be created by any ship.


```python3
>>> ship.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
>>> survey = ship.waypoints.survey()
>>> survey.surveys[0]
Survey({'signature': 'X1-CC27-CB5A-F0AB4D', 'symbol': 'X1-CC27-CB5A', 'deposits': [{'symbol': 'ALUMINUM_ORE'}, {'symbol': 'QUARTZ_SAND'}, {'symbol': 'COPPER_ORE'}, {'symbol': 'IRON_ORE'}, {'symbol': 'COPPER_ORE'}], 'expiration': '2024-03-10T23:47:07.218Z', 'size': 'SMALL'}) 
>>> extraction = ship.extract_with_survey(survey[0])  # Will block until cooldown from survey has finished
>>> extraction.symbol
COPPER_ORE
>>> extraction.units
8
>>> ship.cargo.inventory
[Inventory({'symbol': 'COPPER_ORE', 'name': 'Copper Ore', 'description': 'DESCRIPTION', 'units': 8})]
```

The `Survey` class has a helper method, `.best`, that accepts a `survey` object which was returned by `ship.survey()`. `.best` will return the "best" `survey` in `survey.surveys`.  If you're looking for specific deposits, you can pass the the deposit symbols to `.best` so only `surveys` which contain all of the deposit symbols will be returned or `None` if none of the deposit symbols are found in a `survey.surveys`.


```python3
>>> survey = ship.waypoints.survey()
>>> survey.best()
Survey({'signature': 'X1-CC27-CB5A-F0AB4D', 'symbol': 'X1-CC27-CB5A', 'deposits': [{'symbol': 'ALUMINUM_ORE'}, {'symbol': 'QUARTZ_SAND'}, {'symbol': 'COPPER_ORE'}, {'symbol': 'IRON_ORE'}, {'symbol': 'COPPER_ORE'}], 'expiration': '2024-03-10T23:47:07.218Z', 'size': 'LARGE'}) 
>>> survey.best('QUARTZ_SAND', 'GOLD_ORE')  # No GOLD_ORE found in any of the survey.surveys
None
>>> survey.best('QUARTZ_SAND', 'IRON_ORE')
Survey({'signature': 'X1-CC27-CB5A-F0AB4D', 'symbol': 'X1-CC27-CB5A', 'deposits': [{'symbol': 'ALUMINUM_ORE'}, {'symbol': 'QUARTZ_SAND'}, {'symbol': 'COPPER_ORE'}, {'symbol': 'IRON_ORE'}, {'symbol': 'COPPER_ORE'}], 'expiration': '2024-03-10T23:47:07.218Z', 'size': 'LARGE'}) 
```


Attempting to `extract_with_survey` with a `survey` that has already expired will raise a `snisp.exceptions.ShipSurveyExpirationError` error.

Attempting to `extract_with_survey` with an invalid `survey` will raise a `snisp.exceptions.ShipSurveyVerificationError` error.

To see all `Survey` related errors, see `snisp.exceptions`.


*Siphon*

If the ship is located at a Waypoint that supports `siphon` and the `ship.can_siphon`, siphoning can be done via

```python3
>>> ship.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
>>> siphon = ship.siphon()
>>> siphon.symbol
LIQUID_HYDROGEN
>>> siphon.units
4
>>> ship.cargo.inventory
[Inventory({'symbol': 'LIQUID_HYDROGEN', 'name': 'Liquid Hydrogen', 'description': 'DESCRIPTION', 'units': 4})]
```


*Jettison*

You can jettison unwanted items in your `ship.cargo` by calling `ship.jettison`

```python3
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 4})]
>>> ship.jettison('GOLD_ORE', units=2)
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 2})]
```


*Refine*

If there are at least 30 units of an Ore in your `ship.cargo.inventory` and the `ship.can_refine`, you can refine the 30 units of Ore into 1 refined unit through `ship.refine`.

```python3
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 35})]
>>> ship.refine('GOLD')
>>> ship.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 5}), Inventory({'symbol': 'GOLD', 'name': 'Gold', 'description': 'DESCRIPTION', 'units': 1})]
```


*Scan*

You can scan for nearby ships in the current System with `ship.scan`

```python3
>>> nearby_ships = list(ship.scan())
```

SpaceTraders does not make it explicit who the owner of a scanned ship is, so SnakesInSpace currently assumes scanned ships are owned by the Agent. Attempting to perform actions on a ship you do not own will lead to undefined consequences.


*Chart*

You can create a `Chart` of an uncharted `Waypoint` that a `ship` is located at by calling `.chart`

```python3
>>> ship.waypoints.chart()
```

If the `Waypoint` was already charted, a Warning will be logged but no Exception will be raised.

There is a convenience function, `is_uncharted`, in `snisp.waypoints` for checking if a `Waypoint` is uncharted.

```python3
from snisp.waypoints import is_uncharted

>>> waypoint = ship.waypoints.get()  # Get the current Waypoint at the ship's location
>>> if is_uncharted(waypoint):
...     ship.waypoints.chart()
```


*Transfer*

You can transfer cargo beteween two `ship`s via `ship.transfer`

```python3
>>> ship_from = agent.fleet('FROM_SHIP')
>>> ship_to = agent.fleet('TO_SHIP')
>>> ship_from.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 35}), Inventory({'symbol': 'IRON_ORE', 'name': 'Iron Ore', 'description': 'DESCRIPTION', 'units': 5})
>>> ship_to.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
>>> ship_from.transfer(ship_to, symbol='GOLD_ORE', units=35)
>>> ship_from.cargo.inventory
[Inventory({'symbol': 'IRON_ORE', 'name': 'Iron Ore', 'description': 'DESCRIPTION', 'units': 5})
>>> ship_to.cargo.inventory
[Inventory({'symbol': 'GOLD_ORE', 'name': 'Gold Ore', 'description': 'DESCRIPTION', 'units': 35})]
```

Exceptions will be raised if you attempt to transfer goods not found in the "from" ship or if there are unit mismatches in either ship.


*Orbit, Dock*

Almost every action will require the `ship` to either be `IN_ORBIT` or `DOCKED` before it can be executed. You can check the status of the `ship` with `ship.nav.status`. To ensure you have the most up-to-date version, you can always do `ship.refresh().nav.status`.

The library will take care of all calls to `ship.orbit()` and `ship.dock()`, so this is not something a user has to worry about.


*Closest, Farthest*

As you've seen sprinkled throughout the guide, the `ship` object does have helper methods of `ship.closest` and `ship.farthest`. Each method will accept any number of iterables and return either the closest or farthest `Waypoint` to the `ship`'s current location.


```python3
>>> ship = next(iter(agent.fleet))
>>> closest_asteroid = ship.closest(
...     ship.waypoints.asteroid_bases(),
...     ship.waypoints.asteroids(),
...     ship.waypoints.enginereed_asteroids(),
...     ship.waypoints.asteroids_fields()
... )
>>> ship.autopilot(closest_asteroid)
```

You can also do `ship.farthest` if you want?


**Waypoints, Markets, Shipyards**

The respective `Waypoints`, `Markets`, and `Shipyards` in the `ship`'s current System are directly accesible via

```python3
>>> ship.waypoints
>>> ship.markets
>>> ship.shipyards
```

See their respective sections for for additional information.


**Exceptions**

There are too many `agent.fleet` and `ship` related exceptions to cover here. Please check `snisp.exceptions` for an exhaustive list of exceptions.


**Helper Properties**

Below are some helper properties for things like arrival times, current location, and capabilities.

```python3
>>> ship.arrival  # Seconds to arriving at destination or 0
>>> ship.location  # The ships current Location object
>>> ship.at_market  # Boolean for if the ship is currently DOCKED or IN_ORBIT at a Market
>>> ship.at_shipyard  # Boolean for if the ship is currently DOCKED or IN_ORBIT at a Shipyard
>>> ship.can_mine  # Boolean for if the ship has a Mining Mount
>>> ship.can_siphon  # Boolean for if the ship has a Siphoning Mount
>>> ship.can_refine_gas  # Boolean for if the ship can refine gas onboard
>>> ship.can_refine_ore  # Boolean for if the ship can refine ore onboard
>>> ship.can_survey  # Boolean for if the ship has a Surveying Mount
```
</details>

<details>
<summary>Waypoints</summary>

In SpaceTraders, `Waypoints` are the fundamental location points within a System. All `Markets`, `Shipyards`, `Asteroids`, etc., are necessarily and suffiecient to being a `Waypoint`.

You can see all `Waypoints` in a `ship`'s System by iterating over `ship.waypoint` directly.

```python3
>>> ship = next(iter(agent.fleet))
>>> waypoints = list(ship.waypoints)
```

Each `Waypoint` `type`has a convenience method for quick and convenient iteration.

For instance, to find all `Asteroids`, 

```python3
>>> ship = next(iter(agent.fleet))
>>> asteroids = list(ship.waypoints.asteroids())
>>> all(asteroid.type == 'ASTEROID' for asteroid in asteroids)
True
>>> asteroids == [waypoint for waypoint in ship.waypoints if waypoint.type == 'ASTEROID']
True
```

all `JumpGates`,
```python3
>>> ship = next(iter(agent.fleet))
>>> jump_gates = list(ship.waypoints.jump_gates())
>>> all(jump_gate.type == 'JUMP_GATE' for jump_gate in jump_gates)
True
>>> jump_gates == [waypoint for waypoint in ship.waypoints if waypoint.type == 'JUMP_GATE']
True
```

and so on.

Some `Waypoints` have unique traits that provide additional information about itself. You can filter for these traits by using the `traits` kwarg in the respective `ship.waypoints` methods.

```python3
>>> ship = next(iter(agent.fleet))
>>> asteroids = list(ship.waypoints.asteroids())
>>> sorted({i.symbol for w in asteroids for i in w.traits})
['COMMON_METAL_DEPOSITS', 'DEEP_CRATERS', 'EXPLOSIVE_GASES', 'HOLLOWED_INTERIOR', 'MICRO_GRAVITY_ANOMALIES', 'MINERAL_DEPOSITS', 'PRECIOUS_METAL_DEPOSITS', 'RADIOACTIVE', 'RARE_METAL_DEPOSITS', 'SHALLOW_CRATERS', 'UNSTABLE_COMPOSITION']
>>> radioactive_asteroids = list(ship.waypoints.asteroids(traits='RADIOACTIVE'))
>>> radioactive_asteroids == [w for w in ship.waypoints.asteroids() for i in w.traits if i.symbol == 'RADIOACTIVE']
True
```

You can use `traits` and `types` while calling `ship.waypoints` (`__call__`) directly as well. Internally, this is how SnakesInSpace finds `Markets`.

```python3
>>> ship = next(iter(agent.fleet))
>>> market_waypoints = list(ship.waypoints(traits='MARKETPLACE'))
>>> markets = list(ship.markets)
>>> len(market_waypoints) == len(markets)
True
>>> {i.symbol for i in market_waypoints} == {i.symbol for i in markets}
True
>>> sorted({market.type for market in markets})
['ASTEROID_BASE', 'ENGINEERED_ASTEROID', 'FUEL_STATION', 'JUMP_GATE', 'MOON', 'ORBITAL_STATION', 'PLANET']
```

For convenience, the `Waypoint` types methods are: 
`artificial_gravity_wells`, `asteroid_bases`, `asteroid_fields`, `asteroids`, `debris_fields`, `engineered_asteroids`, `gas_giants`, `gravity_wells`, `jump_gates`, `moons`, `nebulas`, `orbital_stations`, `planets`, and `shipyards`.

Also, for convenience, there is a `construction_sites` method for iterating over all `Waypoints` that are currently under construction. A `Waypoint` under construction will not have a specific type but will report if it's under construction by `waypiont.is_under_construction`.
</details>


<details>
<summary>Markets</summary>

A `Market` is a `Waypoint` type that imports, exports, or exchanges goods. Not all `Waypoints` are `Markets` but all `Markets` are `Waypoints`.

You can see all of the `Markets` in the System in which a `ship` is located by iterating over the `ship`'s `Markets`

```python3
>>> ship = next(iter(agent.fleet))
>>> markets = list(ship.markets)
```

A `Market` object can be created from a `Waypoint` or `waypoint.symbol`, if the `Waypoint` is also a `Market`. This can be convenient when jumping around between object types.

```python3
>>> ship = next(iter(agent.fleet))
>>> market = ship.markets(waypoint_symbol='MARKET_WAYPOINT_SYMBOL')
>>> market_as_a_waypoint = ship.waypoints(waypoint_symbol='MARKET_WAYPOINT_SYMBOL')
>>> market = ship.markets(waypoint=market_as_a_waypoint)
```

which can be converted back to a `Waypoint` like so

```python3
>>> waypoint = ship.waypoints(waypoint=market)
```

This is helpful if you're iterating over `Asteroid`s and an `Asteroid` is also a `Market`, for instance.

You can find which `Markets` import, exchange, or export specific goods via their respective iterable methods.

```python3
>>> ship = next(iter(agent.fleet))
>>> iron_importers = list(ship.markets.imports('IRON')
>>> iron_exports = list(ship.markets.exports('IRON')
>>> iron_exchanges = list(ship.markets.exchanges('IRON')
```


**Market Data**

The most important feature of a `Market` is to report the current purchase price and sell price of goods. To access the data, you *must* have a `ship` or `probe` located at the waypoint. In a typical game, the first thing you do is purchase enough cheap `probes` to park at every `Market`.

With a `ship` or `probe` located at a `Market`, you can begin tracking the live prices and transactions two ways.

Either by calling `ship.markets()` directly,

```python3
>>> ship = next(iter(agent.fleet))
>>> markets_data = [ship.markets() for ship in agent.fleet if ship.at_market]
```

or by calling the `.data` property of a `Market` obect


```python3
>>> ship = next(iter(agent.fleet))
>>> markets_data = [market.data for market in ship.markets]
```

Note how the first version, using `ship.markets()`, checked if a `ship` was located at the `Market` before getting the `Market`'s data. This is unnecessary as calling either `ship.markets()` or `market.data` will return the default `Market` data if no `ship` or `probe` is located at the `Market` `Waypoint`.

The default `Market` data will contain what the `Market` exports, imports, or exchanges but will not contain recent transactions, trade volumes, or prices.

Once you've parked enough `probe`s at enough `Markets`, you can begin trading on arbitrage and making credits to buy more `probe`s, etc. There are some helper functions located in the `snisp.markets` file but I'll leave that exercise to the reader.


**Fuel Stations**

It is worth pointing out there is a `Markets.fuel_stations` method that is meant to be a convenient lookup for `Markets` that export or exchange FUEL. For instance, you can find the closest `Market` that allows refueling by calling

```python3
>>> ship = next(iter(agent.fleet))
>>> closest_fuel = ship.closet(ship.markets.fuel_stations())
>>> ship.navigate(closest_fuel)
>>> ship.refuel()
```

The `fuel_stations` method will take a considerable amount of time to run initially but all subsequent calls in the same session will cached. The internal SnakesInSpace cache is covered more in depth later on.
</details>

<details>
<summary>Shipyards</summary>
Like `Markets`, all `Shipyards` are `Waypoints` but not all `Waypoints` are `Shipyards`. All `Shipyards` are `Markets` but not all `Markets` are `Shipyards`.

You can find all `Shipyards` in a `ship`s System by iterating over the `ship.shipyards`

```python3
>>> ship = next(iter(agent.fleet))
>>> shipyards = list(ship.shipyards)
```

Like a `Market`, a `Shipyard` with a `ship` or `probe` located at it can reveal additional information by calling `.data`.

```python3
>>> ship = next(iter(agent.fleet))
>>> shipyard = next(iter(ship.shipyards))  # Assumes a Ship or Drone is located at the Waypoint
>>> shipyard.data  # the good stuff
```

To purchase additional `Ships`, `Probes`, `Drones`, and `Shuttles`, call the `.purchase` method on the `Shipyard` object with an acceptable `ship_type`. You can see all available `ship_type`s in `snisp.utils.SHIP_TYPES`.


```python3
>>> ship = next(iter(agent.fleet))
>>> shipyard = ship.closest(ship.shipyards)
>>> ship.autopilot(shipyard)
>>> snisp.utils.ilen(agent.fleet)
2
>>> probe = ship.purchase('SHIP_PROBE')
>>> snisp.utils.ilen(agent.fleet)
3
```

If you attempt to purchase a `ship` at a `Shipyard` that does not have any `Probes` or `Ships` located at it, a `snisp.exceptions.NoShipAtLocationError` will be raised. If you attempt to purchase a `ship_type` that is not sold at the `Shipyard`, an Exception will be raised.

The `Shipyards` class does support `autopurchase`, like in `Markets`. This is a convenience method to purchase additional `Ships` by type. `autopurchase` requires a `ship_type` kwarg and can also take optional kwargs of `max_units` and `buffer`, with defaults of 1 and 300,000, respectively. The `buffer` works like the buffer in `ship.autopurchase` in that you will be able to purchase up to `max_units` so long as your current `agent.data.credits` - `buffer` >= purchase price. To remove the `buffer`, just pass a 0.

```python3
>>> ship = next(iter(agent.fleet))
>>> snisp.utils.ilen(agent.fleet)
2
>>> transactions = ship.shipyards.autopurchase(ship_type='SHIP_PROBE', max_units=5)
>>> for ship in transactions:
...     print(ship.frame.symbol)
FRAME_PROBE
FRAME_PROBE
>>> snisp.utils.ilen(agent.fleet)
4
```

You can see in the above example the user could only afford two `Probes` before hitting the buffer limit.

`ship.shipyards.autopurchase` does come with a caveat, namely, it relies on a `ship` or `probe` being at the `Shipyard` `Waypoint` in order to be able to access the `Shipyard`'s `Market` data to get available ships and ship price. This means if you don't have any `probes` or `ships` at a `Shipyard` that sells `SHIP_PROBES` and you call `ship.shipyards.autopurchase(ship_type="SHIP_PROBE")`, nothing will happen.

As a convenience, you can see the available `ship`s in a `Shipyard` by calling the `.available_ships` method. The method accepts an optional `ship_type` if you wanted to check if the `Shipyard` sold `Probes`, for instance.

```python3
>>> ship = next(iter(agent.fleet))
>>> shipyard = next(iter(ship.shipyards))  # Assumes a Ship or Drone is located at the Waypoint
>>> all_available_ships = list(shipyard.available_ships())
>>> available_probes = list(shipyard.available_ships('SHIP_PROBE))
```

SpaceTraders does not limit the supply of ships available for purchase in a `Shipyard`. As long as one ship of a `ship_type` is available, you can purchase as many as your credits will allow.

The `ship` objects returned by `.available_ships` do have a convenience method of `purchase`, which works  like `Shipyard.purchase` except the `ship_type` is the `ship`s type by default. Meaning, if the type of the `ship` returned by `.available_ships` is a `probe` and you call `.purchase()` on it, a `probe` will be purchased. This can be handy for manually iterating over the `ship`s being sold at the `Shipyard` and purchasing them on demand.

```python3
>>> ship = next(iter(agent.fleet))
>>> shipyard = next(iter(ship.shipyards))  # Assumes a Ship or Drone is located at the Waypoint
>>> for ship in shipyard.available_ships():
...     if ship.purchase_price < 10_000:
...         ship.purchase()
```
</details>

<details>
<summary>Construction Sites</summary>

Select `Waypoints` will need construction materials delivered to them before they'll function correctly. Currently, all `JumpGate`s  in new Systems will need to be completed before you'll be able to use them to `jump` between Systems.

You can see the required materials by calling `.data` on the `ConstructionSite`.

```python3
>>> ship = next(iter(agent.fleet))
>>> construction_sites = list(ship.waypoints.construction_sites())
>>> all(construction_site.is_under_construction for construction_site in construction_sites)
True
>>> construction_sites[0].data
ConstructionSiteData({'symbol': 'X1-CC27-I56', 'materials': [{'tradeSymbol': 'FAB_MATS', 'required': 4000, 'fulfilled': 0}, {'tradeSymbol': 'ADVANCED_CIRCUITRY', 'required': 1200, 'fulfilled': 0}, {'tradeSymbol': 'QUANTUM_STABILIZERS', 'required': 1, 'fulfilled': 1}], 'isComplete': False, 'systemSymbol': 'X1-CC27'})
>>> jump_gate = ship.waypoints.get(waypoint_symbol=construction_site.symbol)
>>> jump_gate
JumpGate({'systemSymbol': 'X1-CC27', 'symbol': 'X1-CC27-I56', 'type': 'JUMP_GATE', 'x': -335, 'y': 298, 'orbitals': [], 'traits': [{'symbol': 'MARKETPLACE', 'name': 'Marketplace', 'description': 'A thriving center of commerce where traders from across the galaxy gather to buy, sell, and exchange goods.'}], 'modifiers': [], 'chart': {'submittedBy': 'COSMIC', 'submittedOn': '2024-03-10T02:51:05.063Z'}, 'faction': {'symbol': 'COSMIC'}, 'isUnderConstruction': True})
>>> jump_gate.is_under_construction
True
>>> jump_gate.symbol == construction_sites[0].symbol
True
```

This particular `JumpGate` won't become functional until 4,000 Units of `FAB_MATS` and 1,200 Units of `ADVANCED_CIRCUITRY` has been delivered to it.

You can supply materials to a `ConstructionSite` in much the same way as you can deliver materials to a `Contract`. Diffferences being, a `ConstructionSite` uses `.supply` instead of `.deliver` and a `ConstructionSite` requires kwargs of `ship`, `trade_symbol`, and `units`.

```python3
>>> ship = next(iter(agent.fleet))
>>> construction_site = next(iter(ship.waypoints.construction_sites()))
>>> construction_site.data
ConstructionSiteData({'symbol': 'X1-CC27-I56', 'materials': [{'tradeSymbol': 'FAB_MATS', 'required': 4000, 'fulfilled': 0}, {'tradeSymbol': 'ADVANCED_CIRCUITRY', 'required': 1200, 'fulfilled': 0}, {'tradeSymbol': 'QUANTUM_STABILIZERS', 'required': 1, 'fulfilled': 1}], 'isComplete': False, 'systemSymbol': 'X1-CC27'})
>>> ship.autopilot(construction_site)
>>> ship.cargo.inventory
[Inventory({'symbol': 'FAB_MATS', 'name': 'Fab Mats', 'description': 'DESCRIPTION', 'units': 40})]
>>> construction_site.supply(ship=ship, trade_symbol='FAB_MATS', units=40)
>>> construction_site.data
ConstructionSiteData({'symbol': 'X1-CC27-I56', 'materials': [{'tradeSymbol': 'FAB_MATS', 'required': 4000, 'fulfilled': 40}, {'tradeSymbol': 'ADVANCED_CIRCUITRY', 'required': 1200, 'fulfilled': 0}, {'tradeSymbol': 'QUANTUM_STABILIZERS', 'required': 1, 'fulfilled': 1}], 'isComplete': False, 'systemSymbol': 'X1-CC27'})
>>> ship.cargo
Cargo({'capacity': 40, 'units': 0, 'inventory': []})
```

Once all of the materials have been supplied to the `ConstructionSite`, it will no longer be returned by `ship.waypoints.construction_sites()` as it is no longer `.is_under_construction`.
</details>

<details>
<summary>Systems</summary>

`Systems` in SpaceTraders are connected by `JumpGates` and by `Ships` that can `warp` between them.

You can see all of the `Systems` in the current SpaceTraders system by iterating over the `agent`'s `.systems`

```python3
>>> agent = Agent(symbol='your_symbol_here', faction='COSMIC', email='optional@exmaple.com')
>>> systems = list(agent.systems)
```

...but I wouldn't do it. There are *a lot* of `Systems` in SpaceTraders. A lot.

Each `ship` will contain the `system` the `ship` is located in it's respective `.system` property. You can scan for nearby `Systems` with `ship.systems.scan()` method.

```python3
>>> ship = next(iter(agent.fleet))
>>> scans = list(ship.system.scan())
>>> scans[0]
StarSystem({'symbol': 'X1-HD87', 'sectorSymbol': 'X1', 'type': 'ORANGE_STAR', 'x': -22731, 'y': -8129, 'distance': 300}), StarSystem({'symbol': 'X1-MR62', 'sectorSymbol': 'X1', 'type': 'BLUE_STAR', 'x': -23151, 'y': -8498, 'distance': 761})
```
</details>

<details>
<summary>Threads and Blocking</summary>
As mentioned previously, the Library will take care of all calls to `.dock`, `.orbit`, as well as handeling Cooldowns and making sure no actions are peformed while the `ship` is in transit. The convenience of this does come at a cost: Blocking.

If you start one action in a thread and attempt to perform another action on that `ship` in another thread, the Library will automatically block until the previous action has completed.


```python3
>>> from threading import Thread
>>> ship = next(iter(agent.fleet))
>>> waypoint = ship.farthest(ship.waypoints)
>>> t = Thread(target=ship.autopilot, args=(waypoint,))
>>> t.start()
>>> ship.dock()
```
The call to `ship.dock()` will block until the `ship` has reached the `waypoint`, which, depending on how far away the `waypoint` is from the starting location, may be seconds, minutes, or hours.

To avoid unnecessary blocking, make sure to perform any `ship` action in its own thread. To expand on the original example at the top of this page, you could combine the navigation, extraction, and selling into one function that can be passed off to a thread.

```python3
>>> def extract_all(ship, asteroid):
...     while True:
...         ship.autopilot(asteroid)
...         while ship.cargo.units < ship.cargo.capacity:
...             if extraction.units == 0:
...                 # Asteroid has been stripped
...                 return
...             if extraction.symbol == 'ICE_WATER':
...                 ship.jettison(extraction.symbol, exctraction.units)
...         ship.sell_off_cargo()
>>>
>>> command_ship = next(iter(agent.fleet))
>>> for asteroid in command_ship.waypoints.asteroids():
...     threads = []
...     for ship in agent.fleet.ships():
...         if ship.can_mine:
...             t = Thread(target=extract_all, args=(ship, asteroid))
...             t.start()
...             threads.append(t)
...     for thread in threads:
...         thread.join()
>>>
```

This is a simple and inefficent example but it shows how well each `ship` can mantain itself. Each thread will have its own `ship` which will

* Navigate to the `asteroid`
* Extract until the `ship`'s `ship.cargo` is full
* Sell whatever has been extracted at the closest `markets`
* Navigate back to the `asteroid`
* Repeat until the `asteroid` has been depeleted, upon which it will exit the loop and return to be joined and continue on to the next `asteroid`

Congratulations, you just stripped all of the `asteroids` in a `system` in less than 20 LOC.
</details>

<details>
<summary>Ratelimiting</summary>
SpaceTraders, a FREE game, allows two requests per second per IP with additional "bursts." The SnakesInSpace Library will automatically restrict you to two request per second per active instance. Meaning, if you run multiple clients in multiple terminals, you may run in to issues with SpaceTraders rate-limiting your IP. The SnakesInSpace rate-limiter will automatically handle these overages on your behalf, but, given this is a FREE resource, please take care to only run one to two clients at a time.
</details>

<details>
<summary>Cache</summary>
SnakesInSpace uses a rudimentary cache with a SQLite database to try and prevent any unnecessary calls to the SpaceTraders API. The current database will be located at SnakesInSpace/snisps/data/cache.db.

The cache will be reset on every login.

The cache can be ignored for now by the end user.
</details>

<details>
<summary>Tests</summary>
You can run `pytest` in the current working directory for `which SnakesInSpace` is located.
</details>
