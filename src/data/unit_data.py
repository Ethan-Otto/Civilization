"""Unit type definitions and stats."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict

from src.map.tile import ResourceType


class UnitType(Enum):
    """Types of units in the game."""
    WARRIOR = auto()
    ARCHER = auto()
    SPEARMAN = auto()
    HORSEMAN = auto()
    CATAPULT = auto()
    SWORDSMAN = auto()
    CROSSBOWMAN = auto()


class CombatType(Enum):
    """Combat classification of units."""
    MELEE = auto()
    RANGED = auto()


@dataclass(frozen=True)
class UnitStats:
    """Stats definition for a unit type."""
    name: str
    unit_type: UnitType
    combat_type: CombatType
    max_health: int
    attack: int
    defense: int
    range: int  # 1 for melee, 2+ for ranged
    movement: int
    cost: Dict[ResourceType, int]
    tech_requirement: str | None  # Tech ID required to build, None for starting units


# Unit definitions based on plan
UNIT_STATS: Dict[UnitType, UnitStats] = {
    UnitType.WARRIOR: UnitStats(
        name="Warrior",
        unit_type=UnitType.WARRIOR,
        combat_type=CombatType.MELEE,
        max_health=100,
        attack=15,
        defense=10,
        range=1,
        movement=2,
        cost={ResourceType.FOOD: 50},
        tech_requirement=None,  # Available from start
    ),
    UnitType.ARCHER: UnitStats(
        name="Archer",
        unit_type=UnitType.ARCHER,
        combat_type=CombatType.RANGED,
        max_health=60,
        attack=12,
        defense=5,
        range=2,
        movement=2,
        cost={ResourceType.FOOD: 40, ResourceType.WOOD: 20},
        tech_requirement="archery",
    ),
    UnitType.SPEARMAN: UnitStats(
        name="Spearman",
        unit_type=UnitType.SPEARMAN,
        combat_type=CombatType.MELEE,
        max_health=80,
        attack=12,
        defense=15,
        range=1,
        movement=2,
        cost={ResourceType.FOOD: 45},
        tech_requirement="bronze_working",
    ),
    UnitType.HORSEMAN: UnitStats(
        name="Horseman",
        unit_type=UnitType.HORSEMAN,
        combat_type=CombatType.MELEE,
        max_health=90,
        attack=18,
        defense=8,
        range=1,
        movement=4,
        cost={ResourceType.FOOD: 60, ResourceType.GOLD: 30},
        tech_requirement="horseback_riding",
    ),
    UnitType.CATAPULT: UnitStats(
        name="Catapult",
        unit_type=UnitType.CATAPULT,
        combat_type=CombatType.RANGED,
        max_health=50,
        attack=25,
        defense=3,
        range=3,
        movement=1,
        cost={ResourceType.WOOD: 80, ResourceType.STONE: 40},
        tech_requirement="engineering",
    ),
    UnitType.SWORDSMAN: UnitStats(
        name="Swordsman",
        unit_type=UnitType.SWORDSMAN,
        combat_type=CombatType.MELEE,
        max_health=120,
        attack=20,
        defense=12,
        range=1,
        movement=2,
        cost={ResourceType.FOOD: 70, ResourceType.GOLD: 30},
        tech_requirement="iron_working",
    ),
    UnitType.CROSSBOWMAN: UnitStats(
        name="Crossbowman",
        unit_type=UnitType.CROSSBOWMAN,
        combat_type=CombatType.RANGED,
        max_health=70,
        attack=18,
        defense=8,
        range=2,
        movement=2,
        cost={ResourceType.FOOD: 50, ResourceType.WOOD: 40},
        tech_requirement="machinery",
    ),
}


def get_unit_stats(unit_type: UnitType) -> UnitStats:
    """Get stats for a unit type.

    Args:
        unit_type: The unit type to get stats for

    Returns:
        UnitStats for the unit type
    """
    return UNIT_STATS[unit_type]


def get_available_units(researched_techs: set[str]) -> list[UnitType]:
    """Get list of unit types that can be built with current tech.

    Args:
        researched_techs: Set of researched technology IDs

    Returns:
        List of buildable unit types
    """
    available = []
    for unit_type, stats in UNIT_STATS.items():
        if stats.tech_requirement is None or stats.tech_requirement in researched_techs:
            available.append(unit_type)
    return available
