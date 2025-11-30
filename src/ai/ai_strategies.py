"""Strategic AI for civilization-level decisions."""

from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum, auto

from src.ai.utility_functions import calculate_production_utility, calculate_research_utility
from src.data.unit_data import get_available_units
from src.data.tech_data import get_available_techs

if TYPE_CHECKING:
    from src.core.game_state import GameState
    from src.entities.civilization import Civilization
    from src.entities.city import City


class StrategicGoal(Enum):
    """High-level strategic goals."""
    BUILD_MILITARY = auto()
    EXPAND_TERRITORY = auto()
    DEVELOP_ECONOMY = auto()
    RESEARCH_TECH = auto()
    DEFEND = auto()


@dataclass
class StrategicAssessment:
    """Assessment of current strategic situation."""
    military_strength: float  # 0-1 relative strength
    economic_strength: float  # 0-1 relative strength
    threat_level: float  # 0-1 how threatened
    expansion_potential: float  # 0-1 room to expand
    recommended_goal: StrategicGoal


class StrategicAI:
    """Handles strategic decisions for a civilization."""

    def __init__(self, personality_weights: dict[str, float]):
        """Initialize strategic AI.

        Args:
            personality_weights: AI personality weights
        """
        self.personality_weights = personality_weights

    def assess_situation(self, civ: 'Civilization', game_state: 'GameState') -> StrategicAssessment:
        """Assess the current strategic situation.

        Args:
            civ: Civilization to assess for
            game_state: Current game state

        Returns:
            Strategic assessment
        """
        military = self._assess_military(civ, game_state)
        economic = self._assess_economy(civ, game_state)
        threat = self._assess_threats(civ, game_state)
        expansion = self._assess_expansion(civ, game_state)

        # Determine recommended goal based on situation and personality
        goal = self._determine_goal(military, economic, threat, expansion)

        return StrategicAssessment(
            military_strength=military,
            economic_strength=economic,
            threat_level=threat,
            expansion_potential=expansion,
            recommended_goal=goal
        )

    def _assess_military(self, civ: 'Civilization', game_state: 'GameState') -> float:
        """Assess military strength relative to enemies.

        Args:
            civ: Civilization to assess
            game_state: Current game state

        Returns:
            Military strength ratio (0-1)
        """
        our_units = game_state.get_units_for_civ(civ)
        our_strength = sum(u.attack + u.defense for u in our_units)

        enemy_strength = 0
        for enemy_civ in game_state.active_civs:
            if enemy_civ != civ:
                enemy_units = game_state.get_units_for_civ(enemy_civ)
                enemy_strength += sum(u.attack + u.defense for u in enemy_units)

        if enemy_strength == 0:
            return 1.0
        if our_strength == 0:
            return 0.0

        return min(1.0, our_strength / (our_strength + enemy_strength) * 2)

    def _assess_economy(self, civ: 'Civilization', game_state: 'GameState') -> float:
        """Assess economic strength.

        Args:
            civ: Civilization to assess
            game_state: Current game state

        Returns:
            Economic strength (0-1)
        """
        from src.map.tile import ResourceType

        total_resources = sum(civ.resources.values())
        city_count = len(game_state.get_cities_for_civ(civ))

        # More cities and resources = stronger economy
        base_score = (city_count * 100 + total_resources) / 500
        return min(1.0, base_score)

    def _assess_threats(self, civ: 'Civilization', game_state: 'GameState') -> float:
        """Assess threat level from enemies.

        Args:
            civ: Civilization to assess
            game_state: Current game state

        Returns:
            Threat level (0-1)
        """
        our_cities = game_state.get_cities_for_civ(civ)
        if not our_cities:
            return 1.0  # No cities = max threat

        threat = 0.0

        for enemy_civ in game_state.active_civs:
            if enemy_civ == civ:
                continue

            enemy_units = game_state.get_units_for_civ(enemy_civ)
            for unit in enemy_units:
                # Check distance to our cities
                for city in our_cities:
                    dist = abs(unit.x - city.x) + abs(unit.y - city.y)
                    if dist < 5:
                        threat += (5 - dist) * 0.1

        return min(1.0, threat)

    def _assess_expansion(self, civ: 'Civilization', game_state: 'GameState') -> float:
        """Assess potential for expansion.

        Args:
            civ: Civilization to assess
            game_state: Current game state

        Returns:
            Expansion potential (0-1)
        """
        # Simple measure: count unclaimed passable tiles near our territory
        our_cities = game_state.get_cities_for_civ(civ)
        if not our_cities:
            return 0.5  # Neutral

        unclaimed_near = 0
        for city in our_cities:
            nearby = game_state.grid.get_tiles_in_range(city.x, city.y, 5)
            for tile in nearby:
                if tile.is_passable and tile.owner is None:
                    unclaimed_near += 1

        return min(1.0, unclaimed_near / 50)

    def _determine_goal(self, military: float, economic: float,
                        threat: float, expansion: float) -> StrategicGoal:
        """Determine the best strategic goal.

        Args:
            military: Military strength
            economic: Economic strength
            threat: Threat level
            expansion: Expansion potential

        Returns:
            Recommended strategic goal
        """
        military_weight = self.personality_weights.get("military_weight", 1.0)
        expansion_weight = self.personality_weights.get("expansion_weight", 1.0)
        economy_weight = self.personality_weights.get("economy_weight", 1.0)
        research_weight = self.personality_weights.get("research_weight", 1.0)

        # High threat = defend or build military
        if threat > 0.6:
            if military < 0.4:
                return StrategicGoal.BUILD_MILITARY
            return StrategicGoal.DEFEND

        # Score each goal
        scores = {
            StrategicGoal.BUILD_MILITARY: (1 - military) * military_weight,
            StrategicGoal.EXPAND_TERRITORY: expansion * expansion_weight,
            StrategicGoal.DEVELOP_ECONOMY: (1 - economic) * economy_weight,
            StrategicGoal.RESEARCH_TECH: 0.5 * research_weight,
        }

        return max(scores, key=scores.get)

    def decide_production(self, city: 'City', civ: 'Civilization',
                          game_state: 'GameState') -> None:
        """Decide what a city should produce.

        Args:
            city: City to decide for
            civ: Owning civilization
            game_state: Current game state
        """
        if city.is_producing:
            return  # Already producing something

        available_units = get_available_units(civ.researched_techs)
        if not available_units:
            return

        best_unit = None
        best_utility = -1

        for unit_type in available_units:
            utility = calculate_production_utility(
                city, unit_type, game_state, civ, self.personality_weights
            )
            if utility > best_utility:
                best_utility = utility
                best_unit = unit_type

        if best_unit:
            city.set_production(best_unit)

    def decide_research(self, civ: 'Civilization', game_state: 'GameState') -> None:
        """Decide what technology to research.

        Args:
            civ: Civilization researching
            game_state: Current game state
        """
        if civ.current_research:
            return  # Already researching

        available_techs = get_available_techs(civ.researched_techs)
        if not available_techs:
            return

        best_tech = None
        best_utility = -1

        for tech in available_techs:
            utility = calculate_research_utility(
                tech.id, civ, self.personality_weights
            )
            if utility > best_utility:
                best_utility = utility
                best_tech = tech

        if best_tech:
            civ.start_research(best_tech.id)
