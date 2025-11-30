"""Central game state management."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto

from src.map.grid import Grid
from src.entities.civilization import Civilization
from src.entities.unit import Unit
from src.entities.city import City


class GamePhase(Enum):
    """Current phase of the game."""
    SETUP = auto()
    PLAYING = auto()
    GAME_OVER = auto()


@dataclass
class GameState:
    """Central container for all game state."""

    # Map
    grid: Grid

    # Civilizations
    civilizations: list[Civilization] = field(default_factory=list)
    current_player_index: int = 0

    # Turn tracking
    current_turn: int = 1

    # Game phase
    phase: GamePhase = GamePhase.SETUP

    # Victory
    winner: Optional[Civilization] = None

    # Entities storage (by ID for easy lookup)
    _units: dict[str, Unit] = field(default_factory=dict)
    _cities: dict[str, City] = field(default_factory=dict)

    # Selected unit for UI
    selected_unit_id: Optional[str] = None

    # Fog of war per civilization
    fog_states: dict[str, dict[tuple[int, int], str]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize fog states for each civ."""
        for civ in self.civilizations:
            self.fog_states[civ.name] = {}

    @property
    def current_player(self) -> Civilization:
        """Get the current player's civilization."""
        return self.civilizations[self.current_player_index]

    @property
    def player_civ(self) -> Civilization:
        """Get the human player's civilization (first non-AI)."""
        for civ in self.civilizations:
            if not civ.is_ai:
                return civ
        return self.civilizations[0]

    @property
    def ai_civs(self) -> list[Civilization]:
        """Get all AI civilizations."""
        return [civ for civ in self.civilizations if civ.is_ai]

    @property
    def active_civs(self) -> list[Civilization]:
        """Get all non-eliminated civilizations."""
        return [civ for civ in self.civilizations if not civ.is_eliminated]

    @property
    def selected_unit(self) -> Optional[Unit]:
        """Get currently selected unit."""
        if self.selected_unit_id is None:
            return None
        return self._units.get(self.selected_unit_id)

    @selected_unit.setter
    def selected_unit(self, unit: Optional[Unit]) -> None:
        """Set selected unit."""
        self.selected_unit_id = unit.id if unit else None

    # Unit management
    def add_unit(self, unit: Unit) -> None:
        """Add a unit to the game.

        Args:
            unit: Unit to add
        """
        self._units[unit.id] = unit
        unit.owner.add_unit(unit.id)

        # Place on tile
        tile = self.grid.get_tile(unit.x, unit.y)
        if tile:
            tile.unit = unit

    def remove_unit(self, unit: Unit) -> None:
        """Remove a unit from the game.

        Args:
            unit: Unit to remove
        """
        # Remove from tile
        tile = self.grid.get_tile(unit.x, unit.y)
        if tile and tile.unit == unit:
            tile.unit = None

        # Remove from owner
        unit.owner.remove_unit(unit.id)

        # Remove from storage
        if unit.id in self._units:
            del self._units[unit.id]

        # Clear selection if this was selected
        if self.selected_unit_id == unit.id:
            self.selected_unit_id = None

    def get_unit(self, unit_id: str) -> Optional[Unit]:
        """Get a unit by ID.

        Args:
            unit_id: Unit ID

        Returns:
            Unit or None
        """
        return self._units.get(unit_id)

    def get_units_for_civ(self, civ: Civilization) -> list[Unit]:
        """Get all units belonging to a civilization.

        Args:
            civ: Civilization to get units for

        Returns:
            List of units
        """
        return [self._units[uid] for uid in civ.unit_ids if uid in self._units]

    def get_all_units(self) -> list[Unit]:
        """Get all units in the game."""
        return list(self._units.values())

    def move_unit(self, unit: Unit, new_x: int, new_y: int, cost: int) -> bool:
        """Move a unit to a new position.

        Args:
            unit: Unit to move
            new_x: New X coordinate
            new_y: New Y coordinate
            cost: Movement cost

        Returns:
            True if move successful
        """
        old_tile = self.grid.get_tile(unit.x, unit.y)
        new_tile = self.grid.get_tile(new_x, new_y)

        if not new_tile or not new_tile.can_enter(unit):
            return False

        if not unit.move_to(new_x, new_y, cost):
            return False

        # Update tile references
        if old_tile:
            old_tile.unit = None
        new_tile.unit = unit

        return True

    # City management
    def add_city(self, city: City) -> None:
        """Add a city to the game.

        Args:
            city: City to add
        """
        self._cities[city.id] = city
        city.owner.add_city(city.id)

        # Place on tile
        tile = self.grid.get_tile(city.x, city.y)
        if tile:
            tile.city = city
            tile.owner = city.owner

    def remove_city(self, city: City) -> None:
        """Remove a city from the game.

        Args:
            city: City to remove
        """
        # Remove from tile
        tile = self.grid.get_tile(city.x, city.y)
        if tile and tile.city == city:
            tile.city = None
            tile.owner = None

        # Remove from owner
        city.owner.remove_city(city.id)

        # Remove from storage
        if city.id in self._cities:
            del self._cities[city.id]

    def get_city(self, city_id: str) -> Optional[City]:
        """Get a city by ID.

        Args:
            city_id: City ID

        Returns:
            City or None
        """
        return self._cities.get(city_id)

    def get_cities_for_civ(self, civ: Civilization) -> list[City]:
        """Get all cities belonging to a civilization.

        Args:
            civ: Civilization to get cities for

        Returns:
            List of cities
        """
        return [self._cities[cid] for cid in civ.city_ids if cid in self._cities]

    def get_all_cities(self) -> list[City]:
        """Get all cities in the game."""
        return list(self._cities.values())

    # Turn management
    def advance_turn(self) -> None:
        """Advance to the next player's turn."""
        self.current_player_index = (self.current_player_index + 1) % len(self.civilizations)

        # If back to first player, increment turn counter
        if self.current_player_index == 0:
            self.current_turn += 1

    def is_player_turn(self) -> bool:
        """Check if it's the human player's turn."""
        return not self.current_player.is_ai

    # Victory checking
    def check_victory(self) -> Optional[Civilization]:
        """Check if any civilization has won.

        Returns:
            Winning civilization or None
        """
        # Check for elimination victory (only one civ left)
        active = self.active_civs
        if len(active) == 1:
            self.winner = active[0]
            self.phase = GamePhase.GAME_OVER
            return self.winner

        # Update elimination status for each civ
        for civ in self.civilizations:
            civ.check_elimination()

        return None

    # Fog of war
    def get_fog_state(self, civ: Civilization, x: int, y: int) -> str:
        """Get fog of war state for a tile.

        Args:
            civ: Civilization to check for
            x: X coordinate
            y: Y coordinate

        Returns:
            "UNEXPLORED", "EXPLORED", or "VISIBLE"
        """
        if civ.name not in self.fog_states:
            return "UNEXPLORED"
        return self.fog_states[civ.name].get((x, y), "UNEXPLORED")

    def update_visibility(self, civ: Civilization) -> None:
        """Update fog of war visibility for a civilization.

        Args:
            civ: Civilization to update visibility for
        """
        if civ.name not in self.fog_states:
            self.fog_states[civ.name] = {}

        fog = self.fog_states[civ.name]

        # Mark all previously visible tiles as explored
        for pos, state in fog.items():
            if state == "VISIBLE":
                fog[pos] = "EXPLORED"

        # Update visibility from units
        for unit in self.get_units_for_civ(civ):
            visible_tiles = self.grid.get_tiles_in_range(unit.x, unit.y, 2)  # Unit vision = 2
            for tile in visible_tiles:
                fog[(tile.x, tile.y)] = "VISIBLE"

        # Update visibility from cities
        for city in self.get_cities_for_civ(civ):
            visible_tiles = self.grid.get_tiles_in_range(city.x, city.y, city.vision_range)
            for tile in visible_tiles:
                fog[(tile.x, tile.y)] = "VISIBLE"

    def get_player_fog_state(self) -> dict[tuple[int, int], str]:
        """Get fog state for the player civilization."""
        return self.fog_states.get(self.player_civ.name, {})
