"""City class for settlements."""

import uuid
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from src.data.unit_data import UnitType, get_unit_stats
from src.map.tile import ResourceType
from src.core.settings import CITY_VISION_RANGE

if TYPE_CHECKING:
    from src.entities.civilization import Civilization


@dataclass
class City:
    """Represents a city/settlement."""

    name: str
    owner: 'Civilization'
    x: int
    y: int

    # Production
    current_production: Optional[UnitType] = None
    production_progress: int = 0

    # Defense
    health: int = 200
    max_health: int = 200
    defense_bonus: float = 0.0  # From walls tech

    # Unique identifier
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def position(self) -> tuple[int, int]:
        """Get city position."""
        return (self.x, self.y)

    @property
    def vision_range(self) -> int:
        """Get city vision range."""
        return CITY_VISION_RANGE

    @property
    def is_producing(self) -> bool:
        """Check if city is producing something."""
        return self.current_production is not None

    def set_production(self, unit_type: UnitType) -> None:
        """Set what the city is producing.

        Args:
            unit_type: Unit type to produce
        """
        self.current_production = unit_type
        self.production_progress = 0

    def add_production(self, amount: int) -> Optional[UnitType]:
        """Add production points and check for completion.

        Args:
            amount: Production points to add

        Returns:
            UnitType if production completed, None otherwise
        """
        if self.current_production is None:
            return None

        self.production_progress += amount
        stats = get_unit_stats(self.current_production)

        # Calculate production cost (sum of resource costs, simplified)
        total_cost = sum(stats.cost.values())

        if self.production_progress >= total_cost:
            completed = self.current_production
            self.current_production = None
            self.production_progress = 0
            return completed

        return None

    def get_production_remaining(self) -> int:
        """Get remaining production needed.

        Returns:
            Production points needed
        """
        if self.current_production is None:
            return 0

        stats = get_unit_stats(self.current_production)
        total_cost = sum(stats.cost.values())
        return max(0, total_cost - self.production_progress)

    def take_damage(self, amount: int) -> None:
        """Apply damage to the city.

        Args:
            amount: Damage to apply
        """
        # Apply defense bonus
        actual_damage = int(amount * (1 - self.defense_bonus))
        self.health = max(0, self.health - actual_damage)

    def heal(self, amount: int = 10) -> None:
        """Heal the city.

        Args:
            amount: Amount to heal (default 10 per turn)
        """
        self.health = min(self.max_health, self.health + amount)

    @property
    def is_destroyed(self) -> bool:
        """Check if city is destroyed."""
        return self.health <= 0

    def apply_tech_bonus(self, tech_id: str) -> None:
        """Apply bonuses from researched technology.

        Args:
            tech_id: Technology that was researched
        """
        if tech_id == "masonry":
            self.defense_bonus = 0.25  # Walls provide 25% damage reduction

    def process_turn(self) -> Optional[UnitType]:
        """Process a turn for this city.

        Adds production and heals if damaged.

        Returns:
            UnitType if a unit was produced, None otherwise
        """
        # Heal city if damaged
        if self.health < self.max_health:
            self.heal(10)

        # Add production (base production of 10 per turn)
        completed = self.add_production(10)
        return completed

    def __repr__(self) -> str:
        return f"City({self.name}, HP={self.health}/{self.max_health}, pos=({self.x}, {self.y}))"
