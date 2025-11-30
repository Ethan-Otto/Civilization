"""Tactical AI for unit-level decisions."""

from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
from enum import Enum, auto

from src.map.pathfinding import find_path, get_reachable_tiles, get_tiles_in_attack_range
from src.ai.utility_functions import calculate_attack_utility, calculate_movement_utility, calculate_retreat_utility
from src.systems.combat_system import CombatSystem

if TYPE_CHECKING:
    from src.core.game_state import GameState
    from src.entities.unit import Unit
    from src.map.tile import Tile


class ActionType(Enum):
    """Types of tactical actions."""
    ATTACK = auto()
    MOVE = auto()
    RETREAT = auto()
    FORTIFY = auto()


@dataclass
class TacticalAction:
    """A tactical action for a unit."""
    action_type: ActionType
    target_tile: Optional['Tile'] = None
    target_unit: Optional['Unit'] = None
    utility: float = 0.0


class TacticalAI:
    """Handles tactical decisions for individual units."""

    def __init__(self, personality_weights: dict[str, float]):
        """Initialize tactical AI.

        Args:
            personality_weights: AI personality weights
        """
        self.personality_weights = personality_weights

    def decide_action(self, unit: 'Unit', game_state: 'GameState') -> TacticalAction:
        """Decide the best action for a unit.

        Args:
            unit: Unit to decide for
            game_state: Current game state

        Returns:
            Best tactical action
        """
        possible_actions = []

        # Check if should retreat
        retreat_utility = calculate_retreat_utility(unit, game_state)
        if retreat_utility > 0.5:
            retreat_action = self._get_retreat_action(unit, game_state)
            if retreat_action:
                possible_actions.append(retreat_action)

        # Check for attack opportunities
        if unit.can_attack:
            attack_actions = self._get_attack_actions(unit, game_state)
            possible_actions.extend(attack_actions)

        # Check for movement opportunities
        if unit.can_move:
            move_actions = self._get_move_actions(unit, game_state)
            possible_actions.extend(move_actions)

        # Fortify as default
        possible_actions.append(TacticalAction(
            action_type=ActionType.FORTIFY,
            utility=0.1
        ))

        # Select highest utility action
        if not possible_actions:
            return TacticalAction(action_type=ActionType.FORTIFY)

        return max(possible_actions, key=lambda a: a.utility)

    def _get_attack_actions(self, unit: 'Unit', game_state: 'GameState') -> list[TacticalAction]:
        """Get possible attack actions.

        Args:
            unit: Attacking unit
            game_state: Current game state

        Returns:
            List of attack actions
        """
        actions = []

        # Get tiles in attack range
        attackable_tiles = get_tiles_in_attack_range(game_state.grid, unit)

        for tile in attackable_tiles:
            if tile.unit and tile.unit.owner != unit.owner:
                # Enemy unit found
                utility = calculate_attack_utility(
                    unit, tile.unit, tile, self.personality_weights
                )
                actions.append(TacticalAction(
                    action_type=ActionType.ATTACK,
                    target_tile=tile,
                    target_unit=tile.unit,
                    utility=utility
                ))

        return actions

    def _get_move_actions(self, unit: 'Unit', game_state: 'GameState') -> list[TacticalAction]:
        """Get possible movement actions.

        Args:
            unit: Moving unit
            game_state: Current game state

        Returns:
            List of move actions
        """
        actions = []

        start_tile = game_state.grid.get_tile(unit.x, unit.y)
        if not start_tile:
            return actions

        reachable = get_reachable_tiles(
            game_state.grid, start_tile, unit.remaining_movement, unit
        )

        for tile, cost in reachable.items():
            if tile.has_unit():
                continue  # Can't move onto occupied tile

            utility = calculate_movement_utility(
                unit, tile, game_state, self.personality_weights
            )
            actions.append(TacticalAction(
                action_type=ActionType.MOVE,
                target_tile=tile,
                utility=utility
            ))

        return actions

    def _get_retreat_action(self, unit: 'Unit', game_state: 'GameState') -> Optional[TacticalAction]:
        """Get retreat action toward nearest friendly city.

        Args:
            unit: Unit to retreat
            game_state: Current game state

        Returns:
            Retreat action or None
        """
        friendly_cities = game_state.get_cities_for_civ(unit.owner)
        if not friendly_cities:
            return None

        # Find nearest friendly city
        unit_tile = game_state.grid.get_tile(unit.x, unit.y)
        if not unit_tile:
            return None

        nearest_city = min(
            friendly_cities,
            key=lambda c: abs(c.x - unit.x) + abs(c.y - unit.y)
        )

        city_tile = game_state.grid.get_tile(nearest_city.x, nearest_city.y)
        if not city_tile:
            return None

        # Find path to city
        path = find_path(game_state.grid, unit_tile, city_tile, unit)
        if not path:
            return None

        # Move as far as we can toward city
        reachable = get_reachable_tiles(
            game_state.grid, unit_tile, unit.remaining_movement, unit
        )

        best_tile = None
        best_distance = float('inf')

        for tile in reachable:
            if tile.has_unit():
                continue
            dist = abs(tile.x - nearest_city.x) + abs(tile.y - nearest_city.y)
            if dist < best_distance:
                best_distance = dist
                best_tile = tile

        if best_tile:
            return TacticalAction(
                action_type=ActionType.RETREAT,
                target_tile=best_tile,
                utility=calculate_retreat_utility(unit, game_state) * 2.0
            )

        return None

    def execute_action(self, action: TacticalAction, unit: 'Unit', game_state: 'GameState') -> bool:
        """Execute a tactical action.

        Args:
            action: Action to execute
            unit: Unit performing action
            game_state: Current game state

        Returns:
            True if action was successful
        """
        if action.action_type == ActionType.ATTACK:
            return self._execute_attack(action, unit, game_state)
        elif action.action_type in (ActionType.MOVE, ActionType.RETREAT):
            return self._execute_move(action, unit, game_state)
        elif action.action_type == ActionType.FORTIFY:
            return True  # Fortify just means do nothing

        return False

    def _execute_attack(self, action: TacticalAction, unit: 'Unit', game_state: 'GameState') -> bool:
        """Execute an attack action.

        Args:
            action: Attack action
            unit: Attacking unit
            game_state: Current game state

        Returns:
            True if successful
        """
        if not action.target_unit or not action.target_tile:
            return False

        attacker_tile = game_state.grid.get_tile(unit.x, unit.y)
        if not attacker_tile:
            return False

        result = CombatSystem.resolve_combat(
            unit, action.target_unit, attacker_tile, action.target_tile
        )

        # Remove dead units
        if result.defender_killed:
            game_state.remove_unit(action.target_unit)

        if result.attacker_killed:
            game_state.remove_unit(unit)

        return True

    def _execute_move(self, action: TacticalAction, unit: 'Unit', game_state: 'GameState') -> bool:
        """Execute a move action.

        Args:
            action: Move action
            unit: Moving unit
            game_state: Current game state

        Returns:
            True if successful
        """
        if not action.target_tile:
            return False

        cost = action.target_tile.movement_cost
        return game_state.move_unit(unit, action.target_tile.x, action.target_tile.y, int(cost))
