"""Turn management system."""

from typing import TYPE_CHECKING, Callable, Optional
from enum import Enum, auto

if TYPE_CHECKING:
    from src.core.game_state import GameState
    from src.entities.civilization import Civilization


class TurnPhase(Enum):
    """Phases within a turn."""
    START_TURN = auto()      # Gather resources, apply effects
    MOVEMENT = auto()        # Move units
    COMBAT = auto()          # Resolve combat
    PRODUCTION = auto()      # Build units, research tech
    END_TURN = auto()        # Cleanup


class TurnManager:
    """Manages the turn cycle for all civilizations."""

    def __init__(self, game_state: 'GameState'):
        """Initialize turn manager.

        Args:
            game_state: Reference to game state
        """
        self.game_state = game_state
        self.current_phase = TurnPhase.START_TURN

        # Callbacks for AI turns
        self._ai_turn_callback: Optional[Callable[['Civilization'], None]] = None

    def set_ai_callback(self, callback: Callable[['Civilization'], None]) -> None:
        """Set callback for processing AI turns.

        Args:
            callback: Function that takes a Civilization and processes its turn
        """
        self._ai_turn_callback = callback

    def start_turn(self, civ: 'Civilization') -> None:
        """Begin a civilization's turn.

        - Gather resources
        - Reset unit movement
        - Apply per-turn effects

        Args:
            civ: Civilization starting their turn
        """
        self.current_phase = TurnPhase.START_TURN

        # Reset all units for this civ
        for unit in self.game_state.get_units_for_civ(civ):
            unit.reset_turn()

        # Heal cities
        for city in self.game_state.get_cities_for_civ(civ):
            city.heal()

        # Gather resources from cities
        self._gather_resources(civ)

        # Process research progress
        self._process_research(civ)

        # Update fog of war
        self.game_state.update_visibility(civ)

        self.current_phase = TurnPhase.MOVEMENT

    def _gather_resources(self, civ: 'Civilization') -> None:
        """Gather resources for a civilization.

        Args:
            civ: Civilization to gather for
        """
        from src.map.tile import ResourceType
        from src.data.resource_data import BASE_CITY_INCOME, RESOURCE_YIELDS

        cities = self.game_state.get_cities_for_civ(civ)

        for city in cities:
            # Base city income
            for resource_type, amount in BASE_CITY_INCOME.items():
                civ.add_resource(resource_type, amount)

            # Income from worked tiles (tiles within 2 range of city with resources)
            worked_tiles = self.game_state.grid.get_tiles_in_range(city.x, city.y, 2)
            for tile in worked_tiles:
                if tile.resource and tile.owner == civ:
                    yield_amount = RESOURCE_YIELDS.get(tile.resource, 0)
                    civ.add_resource(tile.resource, yield_amount)

    def _process_research(self, civ: 'Civilization') -> None:
        """Process research progress.

        Args:
            civ: Civilization to process
        """
        if civ.current_research is None:
            return

        # Add research points (base 5 per turn)
        research_per_turn = 5

        # Writing tech bonus
        if civ.has_tech("writing"):
            research_per_turn = int(research_per_turn * 1.5)

        civ.add_research_progress(research_per_turn)

    def end_turn(self, civ: 'Civilization') -> None:
        """End a civilization's turn.

        Args:
            civ: Civilization ending their turn
        """
        self.current_phase = TurnPhase.END_TURN

        # Process city production
        self._process_production(civ)

        # Check for victory conditions
        self.game_state.check_victory()

        # Advance to next player
        self.game_state.advance_turn()

        # If next player is AI, process their turn
        next_civ = self.game_state.current_player
        if next_civ.is_ai and self._ai_turn_callback:
            self.process_ai_turn(next_civ)

    def _process_production(self, civ: 'Civilization') -> None:
        """Process city production.

        Args:
            civ: Civilization to process
        """
        from src.entities.unit_types import create_unit

        cities = self.game_state.get_cities_for_civ(civ)

        for city in cities:
            if not city.is_producing:
                continue

            # Add production (base 10 per turn)
            production_per_turn = 10

            # Mathematics tech bonus
            if civ.has_tech("mathematics"):
                production_per_turn = int(production_per_turn * 1.25)

            completed_unit_type = city.add_production(production_per_turn)

            if completed_unit_type:
                # Create the unit adjacent to the city
                spawn_tile = self._find_spawn_tile(city)
                if spawn_tile:
                    unit = create_unit(
                        completed_unit_type,
                        civ,
                        spawn_tile.x,
                        spawn_tile.y
                    )
                    self.game_state.add_unit(unit)

    def _find_spawn_tile(self, city) -> Optional:
        """Find a tile to spawn a new unit near a city.

        Args:
            city: City producing the unit

        Returns:
            Tile to spawn on, or None
        """
        # Check adjacent tiles
        for tile in self.game_state.grid.get_neighbors(
            self.game_state.grid.get_tile(city.x, city.y)
        ):
            if tile.is_passable and not tile.has_unit():
                return tile
        return None

    def process_ai_turn(self, civ: 'Civilization') -> None:
        """Process an AI civilization's turn.

        Args:
            civ: AI civilization to process
        """
        if civ.is_eliminated:
            self.end_turn(civ)
            return

        self.start_turn(civ)

        # Call AI callback if set
        if self._ai_turn_callback:
            self._ai_turn_callback(civ)

        self.end_turn(civ)

    def process_all_ai_turns(self) -> None:
        """Process turns for all AI civs until back to player."""
        while self.game_state.current_player.is_ai:
            civ = self.game_state.current_player
            self.process_ai_turn(civ)

            # Check if game is over
            if self.game_state.winner:
                break
