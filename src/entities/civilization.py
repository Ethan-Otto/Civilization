"""Civilization class representing a player or AI faction."""

from dataclasses import dataclass, field
from typing import Optional

from src.map.tile import ResourceType
from src.core.settings import STARTING_RESOURCES


@dataclass
class Civilization:
    """Represents a civilization (player or AI)."""

    name: str
    color_key: str  # Key into COLORS dict
    is_ai: bool = False
    ai_personality: Optional[str] = None  # "AGGRESSIVE" or "BALANCED" for AI

    # Resources
    resources: dict[ResourceType, int] = field(default_factory=dict)

    # Research
    researched_techs: set[str] = field(default_factory=set)
    current_research: Optional[str] = None
    research_progress: int = 0

    # Units and cities (references, managed externally)
    unit_ids: list[str] = field(default_factory=list)
    city_ids: list[str] = field(default_factory=list)

    # State
    is_eliminated: bool = False

    def __post_init__(self):
        """Initialize resources if not provided."""
        if not self.resources:
            self.resources = {
                ResourceType.FOOD: STARTING_RESOURCES["FOOD"],
                ResourceType.WOOD: STARTING_RESOURCES["WOOD"],
                ResourceType.STONE: STARTING_RESOURCES["STONE"],
                ResourceType.GOLD: STARTING_RESOURCES["GOLD"],
            }

    def get_resource(self, resource_type: ResourceType) -> int:
        """Get amount of a resource.

        Args:
            resource_type: Resource to query

        Returns:
            Amount of resource
        """
        return self.resources.get(resource_type, 0)

    def add_resource(self, resource_type: ResourceType, amount: int) -> None:
        """Add resources.

        Args:
            resource_type: Resource to add
            amount: Amount to add
        """
        current = self.resources.get(resource_type, 0)
        self.resources[resource_type] = current + amount

    def spend_resource(self, resource_type: ResourceType, amount: int) -> bool:
        """Spend resources if available.

        Args:
            resource_type: Resource to spend
            amount: Amount to spend

        Returns:
            True if resources were spent, False if insufficient
        """
        current = self.resources.get(resource_type, 0)
        if current < amount:
            return False
        self.resources[resource_type] = current - amount
        return True

    def can_afford(self, costs: dict[ResourceType, int]) -> bool:
        """Check if can afford a cost.

        Args:
            costs: Dictionary of resource costs

        Returns:
            True if can afford all costs
        """
        for resource_type, amount in costs.items():
            if self.get_resource(resource_type) < amount:
                return False
        return True

    def spend_costs(self, costs: dict[ResourceType, int]) -> bool:
        """Spend multiple resource costs.

        Args:
            costs: Dictionary of resource costs

        Returns:
            True if spent successfully
        """
        if not self.can_afford(costs):
            return False

        for resource_type, amount in costs.items():
            self.spend_resource(resource_type, amount)
        return True

    def has_tech(self, tech_id: str) -> bool:
        """Check if a technology has been researched.

        Args:
            tech_id: Technology ID to check

        Returns:
            True if tech is researched
        """
        return tech_id in self.researched_techs

    def research_complete(self, tech_id: str) -> None:
        """Mark a technology as researched.

        Args:
            tech_id: Technology ID to complete
        """
        self.researched_techs.add(tech_id)
        self.current_research = None
        self.research_progress = 0

    def start_research(self, tech_id: str) -> None:
        """Start researching a technology.

        Args:
            tech_id: Technology ID to research
        """
        self.current_research = tech_id
        self.research_progress = 0

    def add_research_progress(self, amount: int) -> None:
        """Add research progress.

        Args:
            amount: Amount of research points to add
        """
        self.research_progress += amount

    def add_unit(self, unit_id: str) -> None:
        """Register a unit to this civilization.

        Args:
            unit_id: Unit ID to add
        """
        if unit_id not in self.unit_ids:
            self.unit_ids.append(unit_id)

    def remove_unit(self, unit_id: str) -> None:
        """Remove a unit from this civilization.

        Args:
            unit_id: Unit ID to remove
        """
        if unit_id in self.unit_ids:
            self.unit_ids.remove(unit_id)

    def add_city(self, city_id: str) -> None:
        """Register a city to this civilization.

        Args:
            city_id: City ID to add
        """
        if city_id not in self.city_ids:
            self.city_ids.append(city_id)

    def remove_city(self, city_id: str) -> None:
        """Remove a city from this civilization.

        Args:
            city_id: City ID to remove
        """
        if city_id in self.city_ids:
            self.city_ids.remove(city_id)

    @property
    def unit_count(self) -> int:
        """Get number of units."""
        return len(self.unit_ids)

    @property
    def city_count(self) -> int:
        """Get number of cities."""
        return len(self.city_ids)

    def check_elimination(self) -> bool:
        """Check if civilization has been eliminated.

        Returns:
            True if eliminated (no cities and no units)
        """
        if self.unit_count == 0 and self.city_count == 0:
            self.is_eliminated = True
        return self.is_eliminated

    def __repr__(self) -> str:
        return f"Civilization({self.name}, AI={self.is_ai})"
