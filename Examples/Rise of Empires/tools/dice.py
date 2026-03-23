"""
Dice rolling and random generation tools for Rise of Empires.
Usage: python tools/dice.py <command> [args]

Commands:
  roll <n>d<sides>       Roll n dice with given sides (e.g., 2d6)
  terrain                Generate a random terrain type
  resource               Generate a random bonus resource
  event                  Roll for random event (d20)
  event_positive         Roll on positive event table (d8)
  event_disaster         Roll on disaster event table (d6)
  npc_select <count>     Randomly select <count> NPCs from the roster (1-6)
  position <grid_size>   Generate a random grid position (e.g., 5)
"""

import random
import sys


def roll_dice(notation: str) -> dict:
    """Roll dice in NdS format. Returns individual rolls and total."""
    parts = notation.lower().split("d")
    n = int(parts[0]) if parts[0] else 1
    sides = int(parts[1])
    rolls = [random.randint(1, sides) for _ in range(n)]
    return {"rolls": rolls, "total": sum(rolls), "notation": notation}


def random_terrain() -> str:
    """Generate a random terrain type."""
    terrains = ["Plains", "Forest", "Mountain", "Desert", "Coast", "River"]
    roll = random.randint(1, 6)
    return terrains[roll - 1]


def random_resource() -> str:
    """Generate a random bonus resource (or None)."""
    resources = ["None", "None", "Iron", "Horses", "Gems", "Fertile Soil"]
    roll = random.randint(1, 6)
    return resources[roll - 1]


def roll_event() -> dict:
    """Roll d20 for event check."""
    roll = random.randint(1, 20)
    if roll >= 17:
        return {"roll": roll, "result": "positive_event"}
    elif roll == 1:
        return {"roll": roll, "result": "disaster"}
    else:
        return {"roll": roll, "result": "nothing"}


def roll_positive_event() -> dict:
    """Roll on positive event table."""
    events = [
        "Bountiful Harvest",
        "Gold Rush",
        "Cultural Renaissance",
        "Scientific Breakthrough",
        "Trade Caravan",
        "Population Boom",
        "Military Volunteers",
        "Ancient Discovery",
    ]
    roll = random.randint(1, 8)
    return {"roll": roll, "event": events[roll - 1]}


def roll_disaster_event() -> dict:
    """Roll on disaster event table."""
    events = [
        "Famine",
        "Plague",
        "Earthquake",
        "Barbarian Raid",
        "Flood",
        "Rebellion",
    ]
    roll = random.randint(1, 6)
    return {"roll": roll, "event": events[roll - 1]}


def select_npcs(count: int) -> list:
    """Randomly select NPCs from the roster."""
    npcs = [
        "Verdanian Republic",
        "Ironhold Dominion",
        "Celestine Theocracy",
        "Ashenmoor Collective",
        "Sunspire Dynasty",
        "Thornveil Tribes",
    ]
    count = min(count, len(npcs))
    return random.sample(npcs, count)


def random_position(grid_size: int) -> str:
    """Generate a random grid position (e.g., 'C3')."""
    col = chr(ord("A") + random.randint(0, grid_size - 1))
    row = random.randint(1, grid_size)
    return f"{col}{row}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "roll":
        result = roll_dice(sys.argv[2])
        print(f"Rolling {result['notation']}: {result['rolls']} = {result['total']}")

    elif command == "terrain":
        print(f"Terrain: {random_terrain()}")

    elif command == "resource":
        print(f"Resource: {random_resource()}")

    elif command == "event":
        result = roll_event()
        print(f"Event roll (d20): {result['roll']} -> {result['result']}")

    elif command == "event_positive":
        result = roll_positive_event()
        print(f"Positive event (d8): {result['roll']} -> {result['event']}")

    elif command == "event_disaster":
        result = roll_disaster_event()
        print(f"Disaster event (d6): {result['roll']} -> {result['event']}")

    elif command == "npc_select":
        count = int(sys.argv[2])
        npcs = select_npcs(count)
        print(f"Selected NPCs: {', '.join(npcs)}")

    elif command == "position":
        grid_size = int(sys.argv[2])
        print(f"Position: {random_position(grid_size)}")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
