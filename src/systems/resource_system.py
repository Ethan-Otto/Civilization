"""Resource management system."""

from typing import TYPE_CHECKING

from src.map.tile import ResourceType
from src.data.resource_data import BASE_CITY_INCOME, RESOURCE_YIELDS

if TYPE_CHECKING:
    from src.core.game_state import GameState
    from src.entities.civilization import Civilization


class ResourceSystem:
    """Manages resource collection and spending."""

    def __init__(self, game_state: 'GameState'):
        """Initialize resource system.

        Args:
            game_state: Reference to game state
        """
        self.game_state = game_state

    def calculate_income(self, civ: 'Civilization') -> dict[ResourceType, int]:
        """Calculate per-turn income for a civilization.

        Args:
            civ: Civilization to calculate for

        Returns:
            Dictionary of resource income per turn
        """
        income = {rt: 0 for rt in ResourceType}

        cities = self.game_state.get_cities_for_civ(civ)

        for city in cities:
            # Base city income
            for resource_type, amount in BASE_CITY_INCOME.items():
                income[resource_type] += amount

            # Income from worked tiles
            worked_tiles = self.game_state.grid.get_tiles_in_range(city.x, city.y, 2)
            for tile in worked_tiles:
                if tile.resource and tile.owner == civ:
                    yield_amount = RESOURCE_YIELDS.get(tile.resource, 0)
                    income[tile.resource] += yield_amount

        # Apply tech bonuses
        if civ.has_tech("agriculture"):
            income[ResourceType.FOOD] += 2 * len(cities)

        if civ.has_tech("mining"):
            income[ResourceType.STONE] += 1 * len(cities)

        return income

    def calculate_expenses(self, civ: 'Civilization') -> dict[ResourceType, int]:
        """Calculate per-turn expenses for a civilization.

        Unit maintenance: 1 gold per unit after first 3 units.

        Args:
            civ: Civilization to calculate for

        Returns:
            Dictionary of resource expenses per turn
        """
        expenses = {rt: 0 for rt in ResourceType}

        # Unit maintenance
        units = self.game_state.get_units_for_civ(civ)
        maintainable_units = max(0, len(units) - 3)  # First 3 units are free
        expenses[ResourceType.GOLD] = maintainable_units

        return expenses

    def collect_resources(self, civ: 'Civilization') -> None:
        """Collect resources for a civilization's turn.

        Args:
            civ: Civilization to collect for
        """
        income = self.calculate_income(civ)
        expenses = self.calculate_expenses(civ)

        # Add income
        for resource_type, amount in income.items():
            civ.add_resource(resource_type, amount)

        # Subtract expenses
        for resource_type, amount in expenses.items():
            civ.spend_resource(resource_type, amount)

    def get_net_income(self, civ: 'Civilization') -> dict[ResourceType, int]:
        """Get net income (income - expenses) for a civilization.

        Args:
            civ: Civilization to calculate for

        Returns:
            Dictionary of net resource change per turn
        """
        income = self.calculate_income(civ)
        expenses = self.calculate_expenses(civ)

        net = {}
        for resource_type in ResourceType:
            net[resource_type] = income.get(resource_type, 0) - expenses.get(resource_type, 0)

        return net

    def can_build_unit(self, civ: 'Civilization', unit_type) -> bool:
        """Check if a civilization can afford to build a unit.

        Args:
            civ: Civilization to check
            unit_type: Unit type to check

        Returns:
            True if can afford
        """
        from src.data.unit_data import get_unit_stats

        stats = get_unit_stats(unit_type)
        return civ.can_afford(stats.cost)

    def spend_for_unit(self, civ: 'Civilization', unit_type) -> bool:
        """Spend resources to build a unit.

        Args:
            civ: Civilization spending
            unit_type: Unit type being built

        Returns:
            True if successful
        """
        from src.data.unit_data import get_unit_stats

        stats = get_unit_stats(unit_type)
        return civ.spend_costs(stats.cost)
