"""Main AI controller for civilizations."""

from typing import TYPE_CHECKING

from src.ai.ai_tactics import TacticalAI, ActionType
from src.ai.ai_strategies import StrategicAI
from src.core.settings import AI_PERSONALITIES

if TYPE_CHECKING:
    from src.core.game_state import GameState
    from src.entities.civilization import Civilization


class AIController:
    """Main controller for AI civilizations."""

    def __init__(self, civ: 'Civilization'):
        """Initialize AI controller.

        Args:
            civ: Civilization this AI controls
        """
        self.civ = civ

        # Get personality weights
        personality = civ.ai_personality or "BALANCED"
        self.personality_weights = AI_PERSONALITIES.get(
            personality,
            AI_PERSONALITIES["BALANCED"]
        )

        # Initialize sub-controllers
        self.tactical_ai = TacticalAI(self.personality_weights)
        self.strategic_ai = StrategicAI(self.personality_weights)

    def take_turn(self, game_state: 'GameState') -> None:
        """Process a complete AI turn.

        Args:
            game_state: Current game state
        """
        if self.civ.is_eliminated:
            return

        # Strategic decisions
        self._make_strategic_decisions(game_state)

        # Tactical decisions for each unit
        self._command_units(game_state)

    def _make_strategic_decisions(self, game_state: 'GameState') -> None:
        """Make strategic-level decisions.

        Args:
            game_state: Current game state
        """
        # Assess situation
        assessment = self.strategic_ai.assess_situation(self.civ, game_state)

        # Decide research
        self.strategic_ai.decide_research(self.civ, game_state)

        # Decide production for each city
        for city in game_state.get_cities_for_civ(self.civ):
            self.strategic_ai.decide_production(city, self.civ, game_state)

    def _command_units(self, game_state: 'GameState') -> None:
        """Command all units for tactical actions.

        Args:
            game_state: Current game state
        """
        units = game_state.get_units_for_civ(self.civ)

        for unit in units:
            if not unit.is_alive:
                continue

            # Keep acting until unit can't do anything useful
            while unit.can_move or unit.can_attack:
                action = self.tactical_ai.decide_action(unit, game_state)

                if action.action_type == ActionType.FORTIFY:
                    break  # Nothing useful to do

                success = self.tactical_ai.execute_action(action, unit, game_state)
                if not success:
                    break  # Action failed, stop trying

                # Check if unit died
                if not unit.is_alive:
                    break


def create_ai_controller(civ: 'Civilization') -> AIController:
    """Create an AI controller for a civilization.

    Args:
        civ: Civilization to create controller for

    Returns:
        New AI controller
    """
    return AIController(civ)


def process_ai_turn(civ: 'Civilization', game_state: 'GameState') -> None:
    """Process a turn for an AI civilization.

    Convenience function for use as a callback.

    Args:
        civ: AI civilization
        game_state: Current game state
    """
    controller = create_ai_controller(civ)
    controller.take_turn(game_state)
