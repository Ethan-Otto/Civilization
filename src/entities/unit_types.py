"""Factory functions for creating specific unit types."""

from typing import TYPE_CHECKING

from src.data.unit_data import UnitType
from src.entities.unit import Unit

if TYPE_CHECKING:
    from src.entities.civilization import Civilization


def create_unit(unit_type: UnitType, owner: 'Civilization', x: int, y: int) -> Unit:
    """Create a unit of the specified type.

    Args:
        unit_type: Type of unit to create
        owner: Civilization that owns this unit
        x: Starting X position
        y: Starting Y position

    Returns:
        New unit instance
    """
    return Unit(unit_type=unit_type, owner=owner, x=x, y=y)


def create_warrior(owner: 'Civilization', x: int, y: int) -> Unit:
    """Create a Warrior unit."""
    return create_unit(UnitType.WARRIOR, owner, x, y)


def create_archer(owner: 'Civilization', x: int, y: int) -> Unit:
    """Create an Archer unit."""
    return create_unit(UnitType.ARCHER, owner, x, y)


def create_spearman(owner: 'Civilization', x: int, y: int) -> Unit:
    """Create a Spearman unit."""
    return create_unit(UnitType.SPEARMAN, owner, x, y)


def create_horseman(owner: 'Civilization', x: int, y: int) -> Unit:
    """Create a Horseman unit."""
    return create_unit(UnitType.HORSEMAN, owner, x, y)


def create_catapult(owner: 'Civilization', x: int, y: int) -> Unit:
    """Create a Catapult unit."""
    return create_unit(UnitType.CATAPULT, owner, x, y)


def create_swordsman(owner: 'Civilization', x: int, y: int) -> Unit:
    """Create a Swordsman unit."""
    return create_unit(UnitType.SWORDSMAN, owner, x, y)


def create_crossbowman(owner: 'Civilization', x: int, y: int) -> Unit:
    """Create a Crossbowman unit."""
    return create_unit(UnitType.CROSSBOWMAN, owner, x, y)
