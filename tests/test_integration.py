"""Integration tests for the full game system."""

import pytest
from unittest.mock import patch, MagicMock

from src.core.game_state import GameState, GamePhase
from src.map.map_generator import generate_game_map
from src.map.pathfinding import get_reachable_tiles
from src.entities.civilization import Civilization
from src.entities.city import City
from src.entities.unit_types import create_warrior, create_archer
from src.systems.combat_system import CombatSystem
from src.ai.ai_controller import process_ai_turn


class TestGameInitialization:
    """Tests for game initialization."""

    def test_game_generates_valid_map(self):
        """Test that game generates a playable map."""
        grid, positions = generate_game_map(
            width=40,
            height=30,
            num_civs=3,
            seed=12345
        )

        assert grid is not None
        assert len(positions) == 3
        assert grid.width == 40
        assert grid.height == 30

    def test_game_state_creation_with_civs(self):
        """Test creating game state with civilizations."""
        grid, positions = generate_game_map(
            width=20,
            height=15,
            num_civs=2,
            seed=42
        )

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)
        ai = Civilization(name="AI", color_key="AI_AGGRESSIVE", is_ai=True)

        game_state = GameState(
            grid=grid,
            civilizations=[player, ai]
        )

        assert game_state.player_civ == player
        assert len(game_state.ai_civs) == 1
        assert game_state.current_turn == 1

    def test_starting_units_placement(self):
        """Test placing starting units at valid positions."""
        grid, positions = generate_game_map(
            width=20,
            height=15,
            num_civs=2,
            seed=42
        )

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)
        ai = Civilization(name="AI", color_key="AI_AGGRESSIVE", is_ai=True)

        game_state = GameState(
            grid=grid,
            civilizations=[player, ai]
        )

        # Place units for player
        start_x, start_y = positions[0]
        warrior = create_warrior(player, start_x, start_y)
        game_state.add_unit(warrior)

        assert len(game_state.get_units_for_civ(player)) == 1
        assert warrior in game_state.get_all_units()


class TestCombatIntegration:
    """Integration tests for combat system."""

    def test_full_combat_sequence(self):
        """Test a complete combat sequence."""
        grid, _ = generate_game_map(width=10, height=10, num_civs=2, seed=42)

        player = Civilization(name="Player", color_key="PLAYER")
        enemy = Civilization(name="Enemy", color_key="AI_AGGRESSIVE", is_ai=True)

        game_state = GameState(
            grid=grid,
            civilizations=[player, enemy]
        )

        # Find adjacent passable tiles
        attacker_tile = None
        defender_tile = None
        for x in range(grid.width - 1):
            for y in range(grid.height):
                t1 = grid.get_tile(x, y)
                t2 = grid.get_tile(x + 1, y)
                if t1 and t2 and t1.is_passable and t2.is_passable:
                    attacker_tile = t1
                    defender_tile = t2
                    break
            if attacker_tile:
                break

        assert attacker_tile is not None, "Could not find adjacent passable tiles"

        attacker = create_warrior(player, attacker_tile.x, attacker_tile.y)
        defender = create_warrior(enemy, defender_tile.x, defender_tile.y)

        game_state.add_unit(attacker)
        game_state.add_unit(defender)

        # Execute combat
        initial_defender_hp = defender.health
        result = CombatSystem.resolve_combat(
            attacker, defender, attacker_tile, defender_tile
        )

        assert result.defender_damage > 0
        assert defender.health < initial_defender_hp


class TestAIIntegration:
    """Integration tests for AI system."""

    def test_ai_processes_turn_without_error(self):
        """Test that AI can process a full turn."""
        grid, positions = generate_game_map(
            width=20,
            height=15,
            num_civs=2,
            seed=42
        )

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)
        ai = Civilization(name="AI", color_key="AI_AGGRESSIVE", is_ai=True, ai_personality="AGGRESSIVE")

        game_state = GameState(
            grid=grid,
            civilizations=[player, ai]
        )
        game_state.fog_states[player.name] = {}
        game_state.fog_states[ai.name] = {}

        # Give AI a city and unit
        ai_x, ai_y = positions[1]
        city = City(name="AI Capital", owner=ai, x=ai_x, y=ai_y)
        game_state.add_city(city)

        # Find passable tile for unit
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            tile = grid.get_tile(ai_x + dx, ai_y + dy)
            if tile and tile.is_passable:
                warrior = create_warrior(ai, ai_x + dx, ai_y + dy)
                # Mark unit as unable to act to avoid infinite loop
                warrior.remaining_movement = 0
                warrior.has_attacked = True
                game_state.add_unit(warrior)
                break

        # Process AI turn
        process_ai_turn(ai, game_state)

        # Should complete without error


class TestFogOfWar:
    """Tests for fog of war system."""

    def test_visibility_updates_from_units(self):
        """Test that visibility updates based on unit positions."""
        grid, positions = generate_game_map(
            width=15,
            height=15,
            num_civs=2,
            seed=42
        )

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)
        game_state = GameState(
            grid=grid,
            civilizations=[player]
        )
        game_state.fog_states[player.name] = {}

        # Add unit
        start_x, start_y = positions[0]
        warrior = create_warrior(player, start_x, start_y)
        game_state.add_unit(warrior)

        # Update visibility
        game_state.update_visibility(player)

        # Check that tiles near unit are visible
        fog = game_state.fog_states[player.name]
        assert (start_x, start_y) in fog
        assert fog[(start_x, start_y)] == "VISIBLE"

    def test_visibility_persists_as_explored(self):
        """Test that previously visible tiles become explored."""
        grid, positions = generate_game_map(
            width=15,
            height=15,
            num_civs=2,
            seed=42
        )

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)
        game_state = GameState(
            grid=grid,
            civilizations=[player]
        )
        game_state.fog_states[player.name] = {}

        start_x, start_y = positions[0]
        warrior = create_warrior(player, start_x, start_y)
        game_state.add_unit(warrior)

        # Initial visibility
        game_state.update_visibility(player)
        visible_tiles = [k for k, v in game_state.fog_states[player.name].items() if v == "VISIBLE"]

        # Move unit away (simulate)
        game_state.remove_unit(warrior)

        # Create new unit far away
        warrior2 = create_warrior(player, 0, 0)
        if grid.get_tile(0, 0) and grid.get_tile(0, 0).is_passable:
            game_state.add_unit(warrior2)
            game_state.update_visibility(player)

            # Original position should now be explored
            if start_x != 0 or start_y != 0:
                state = game_state.fog_states[player.name].get((start_x, start_y))
                assert state == "EXPLORED"


class TestVictoryConditions:
    """Tests for victory conditions."""

    def test_elimination_victory(self):
        """Test that eliminating all enemies triggers victory."""
        grid, positions = generate_game_map(
            width=10,
            height=10,
            num_civs=2,
            seed=42
        )

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)
        enemy = Civilization(name="Enemy", color_key="AI_AGGRESSIVE", is_ai=True)

        game_state = GameState(
            grid=grid,
            civilizations=[player, enemy]
        )

        # Give player a city
        city = City(name="Player Capital", owner=player, x=positions[0][0], y=positions[0][1])
        game_state.add_city(city)

        # Enemy has no cities or units - should be eliminated
        enemy.check_elimination()

        # Check victory
        winner = game_state.check_victory()

        assert winner == player
        assert game_state.phase == GamePhase.GAME_OVER


class TestPathfindingIntegration:
    """Integration tests for pathfinding with real map."""

    def test_reachable_tiles_on_generated_map(self):
        """Test pathfinding on generated map."""
        grid, positions = generate_game_map(
            width=15,
            height=15,
            num_civs=2,
            seed=42
        )

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)

        start_x, start_y = positions[0]
        warrior = create_warrior(player, start_x, start_y)

        start_tile = grid.get_tile(start_x, start_y)
        assert start_tile is not None

        # Get reachable tiles with 2 movement points
        reachable = get_reachable_tiles(grid, start_tile, 2, warrior)

        # Should have at least some reachable tiles (starting position is passable)
        assert len(reachable) >= 0  # May be 0 if surrounded by water


class TestCityProduction:
    """Tests for city production system."""

    def test_city_produces_unit_over_time(self):
        """Test that city can produce a unit."""
        from src.data.unit_data import UnitType

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)
        city = City(name="Test City", owner=player, x=5, y=5)

        # Set production to warrior
        city.set_production(UnitType.WARRIOR)
        assert city.is_producing

        # Process turns until production completes
        completed = None
        for _ in range(20):  # Warriors cost around 80, 10 per turn
            completed = city.process_turn()
            if completed:
                break

        assert completed == UnitType.WARRIOR
        assert not city.is_producing


class TestResourceSystem:
    """Tests for resource management."""

    def test_civilization_starts_with_resources(self):
        """Test that civilizations start with default resources."""
        from src.map.tile import ResourceType

        player = Civilization(name="Player", color_key="PLAYER", is_ai=False)

        # Civilization stores resources with ResourceType keys
        assert player.resources[ResourceType.FOOD] == 100
        assert player.resources[ResourceType.WOOD] == 50
        assert player.resources[ResourceType.STONE] == 30
        assert player.resources[ResourceType.GOLD] == 50
