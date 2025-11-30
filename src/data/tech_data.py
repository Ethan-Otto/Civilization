"""Technology definitions."""

from dataclasses import dataclass
from typing import Optional

from src.data.unit_data import UnitType


@dataclass(frozen=True)
class Technology:
    """Definition of a technology."""
    id: str
    name: str
    description: str
    cost: int  # Research points required
    prerequisites: tuple[str, ...]  # Tech IDs required before this
    unlocks_units: tuple[UnitType, ...]  # Units unlocked by this tech
    bonuses: dict[str, float]  # Bonus effects


# Technology definitions from plan
TECHNOLOGIES: dict[str, Technology] = {
    "agriculture": Technology(
        id="agriculture",
        name="Agriculture",
        description="Unlocks farms and increases food production",
        cost=20,
        prerequisites=(),
        unlocks_units=(),
        bonuses={"food_per_city": 2},
    ),
    "mining": Technology(
        id="mining",
        name="Mining",
        description="Unlocks mines and increases stone production",
        cost=25,
        prerequisites=(),
        unlocks_units=(),
        bonuses={"stone_per_city": 1},
    ),
    "archery": Technology(
        id="archery",
        name="Archery",
        description="Unlocks Archer units",
        cost=30,
        prerequisites=(),
        unlocks_units=(UnitType.ARCHER,),
        bonuses={},
    ),
    "writing": Technology(
        id="writing",
        name="Writing",
        description="Increases research speed by 50%",
        cost=35,
        prerequisites=(),
        unlocks_units=(),
        bonuses={"research_bonus": 0.5},
    ),
    "animal_husbandry": Technology(
        id="animal_husbandry",
        name="Animal Husbandry",
        description="Increases food from pastures",
        cost=40,
        prerequisites=("agriculture",),
        unlocks_units=(),
        bonuses={"pasture_food": 1},
    ),
    "bronze_working": Technology(
        id="bronze_working",
        name="Bronze Working",
        description="Unlocks Spearman units",
        cost=45,
        prerequisites=("mining",),
        unlocks_units=(UnitType.SPEARMAN,),
        bonuses={},
    ),
    "masonry": Technology(
        id="masonry",
        name="Masonry",
        description="Unlocks city walls (+25% defense)",
        cost=50,
        prerequisites=("mining",),
        unlocks_units=(),
        bonuses={"city_defense": 0.25},
    ),
    "horseback_riding": Technology(
        id="horseback_riding",
        name="Horseback Riding",
        description="Unlocks Horseman units",
        cost=60,
        prerequisites=("animal_husbandry",),
        unlocks_units=(UnitType.HORSEMAN,),
        bonuses={},
    ),
    "iron_working": Technology(
        id="iron_working",
        name="Iron Working",
        description="Unlocks Swordsman units",
        cost=70,
        prerequisites=("bronze_working",),
        unlocks_units=(UnitType.SWORDSMAN,),
        bonuses={},
    ),
    "mathematics": Technology(
        id="mathematics",
        name="Mathematics",
        description="Increases production by 25%",
        cost=75,
        prerequisites=("writing", "masonry"),
        unlocks_units=(),
        bonuses={"production_bonus": 0.25},
    ),
    "engineering": Technology(
        id="engineering",
        name="Engineering",
        description="Unlocks Catapult units and roads",
        cost=90,
        prerequisites=("mathematics",),
        unlocks_units=(UnitType.CATAPULT,),
        bonuses={"road_movement": 0.5},
    ),
    "machinery": Technology(
        id="machinery",
        name="Machinery",
        description="Unlocks Crossbowman and +1 range for ranged units",
        cost=100,
        prerequisites=("engineering",),
        unlocks_units=(UnitType.CROSSBOWMAN,),
        bonuses={"ranged_bonus_range": 1},
    ),
}


def get_technology(tech_id: str) -> Optional[Technology]:
    """Get a technology by ID.

    Args:
        tech_id: Technology ID

    Returns:
        Technology or None
    """
    return TECHNOLOGIES.get(tech_id)


def get_available_techs(researched: set[str]) -> list[Technology]:
    """Get technologies that can be researched.

    Args:
        researched: Set of already researched tech IDs

    Returns:
        List of researchable technologies
    """
    available = []
    for tech in TECHNOLOGIES.values():
        # Skip already researched
        if tech.id in researched:
            continue

        # Check prerequisites
        if all(prereq in researched for prereq in tech.prerequisites):
            available.append(tech)

    return available


def get_all_techs() -> list[Technology]:
    """Get all technologies."""
    return list(TECHNOLOGIES.values())
