"""Base unit class for all game units."""

import uuid
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from src.data.unit_data import UnitType, UnitStats, CombatType, get_unit_stats

if TYPE_CHECKING:
    from src.entities.civilization import Civilization
    from src.map.tile import Tile


@dataclass
class Unit:
    """Represents a game unit."""

    unit_type: UnitType
    owner: 'Civilization'
    x: int
    y: int

    # Derived from stats but can be modified
    health: int = field(init=False)
    remaining_movement: int = field(init=False)
    has_attacked: bool = field(default=False)

    # Unique identifier
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Initialize derived attributes from unit stats."""
        stats = self.stats
        self.health = stats.max_health
        self.remaining_movement = stats.movement

    @property
    def stats(self) -> UnitStats:
        """Get the stats for this unit type."""
        return get_unit_stats(self.unit_type)

    @property
    def name(self) -> str:
        """Get the unit name."""
        return self.stats.name

    @property
    def max_health(self) -> int:
        """Get maximum health."""
        return self.stats.max_health

    @property
    def attack(self) -> int:
        """Get attack value."""
        return self.stats.attack

    @property
    def defense(self) -> int:
        """Get defense value."""
        return self.stats.defense

    @property
    def range(self) -> int:
        """Get attack range."""
        return self.stats.range

    @property
    def movement(self) -> int:
        """Get movement points per turn."""
        return self.stats.movement

    @property
    def combat_type(self) -> CombatType:
        """Get combat type (melee/ranged)."""
        return self.stats.combat_type

    @property
    def is_melee(self) -> bool:
        """Check if unit is melee."""
        return self.combat_type == CombatType.MELEE

    @property
    def is_ranged(self) -> bool:
        """Check if unit is ranged."""
        return self.combat_type == CombatType.RANGED

    @property
    def position(self) -> tuple[int, int]:
        """Get unit position."""
        return (self.x, self.y)

    @property
    def is_alive(self) -> bool:
        """Check if unit is alive."""
        return self.health > 0

    @property
    def health_ratio(self) -> float:
        """Get health as a ratio (0.0 to 1.0)."""
        return self.health / self.max_health

    @property
    def can_move(self) -> bool:
        """Check if unit can still move this turn."""
        return self.remaining_movement > 0

    @property
    def can_attack(self) -> bool:
        """Check if unit can attack this turn."""
        return not self.has_attacked and self.is_alive

    def take_damage(self, amount: int) -> None:
        """Apply damage to the unit.

        Args:
            amount: Damage to apply
        """
        self.health = max(0, self.health - amount)

    def heal(self, amount: int) -> None:
        """Heal the unit.

        Args:
            amount: Amount to heal
        """
        self.health = min(self.max_health, self.health + amount)

    def move_to(self, x: int, y: int, cost: int) -> bool:
        """Move the unit to a new position.

        Args:
            x: New X coordinate
            y: New Y coordinate
            cost: Movement cost

        Returns:
            True if move was successful
        """
        if cost > self.remaining_movement:
            return False

        self.x = x
        self.y = y
        self.remaining_movement -= cost
        return True

    def attack_target(self) -> None:
        """Mark that this unit has attacked."""
        self.has_attacked = True

    def reset_turn(self) -> None:
        """Reset unit for a new turn."""
        self.remaining_movement = self.movement
        self.has_attacked = False

        # Heal if fortified (not moved and didn't attack)
        # For now, simple heal when not acting
        if self.health < self.max_health:
            self.heal(5)  # Heal 5 HP per turn if damaged

    def can_attack_at_range(self, distance: int) -> bool:
        """Check if unit can attack at a given distance.

        Args:
            distance: Manhattan distance to target

        Returns:
            True if can attack at this range
        """
        if self.is_melee:
            return distance == 1
        else:
            return 1 <= distance <= self.range

    def get_damage_modifier(self) -> float:
        """Get damage modifier based on current health.

        Damaged units deal less damage.

        Returns:
            Damage multiplier (0.0 to 1.0)
        """
        # Units at full health deal full damage
        # Units at 50% health deal 75% damage
        # Units at 10% health deal 55% damage
        return 0.5 + (self.health_ratio * 0.5)

    def __repr__(self) -> str:
        return f"Unit({self.name}, HP={self.health}/{self.max_health}, pos=({self.x}, {self.y}))"
