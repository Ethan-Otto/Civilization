"""Tests for A* pathfinding using real game data."""

import pytest

from src.map.grid import Grid
from src.map.tile import Tile, TerrainType
from src.map.pathfinding import (
    find_path,
    get_reachable_tiles,
    get_path_cost,
    get_tiles_in_attack_range,
    heuristic,
)
from src.entities.civilization import Civilization
from src.entities.unit_types import create_warrior, create_archer
from src.data.unit_data import UnitType


@pytest.fixture
def simple_grid():
    """Create a simple 10x10 grid with all grass."""
    grid = Grid(10, 10)
    for tile in grid.all_tiles():
        tile.terrain = TerrainType.GRASS
    return grid


@pytest.fixture
def grid_with_obstacles():
    """Create a grid with mountains blocking the middle."""
    grid = Grid(10, 10)
    for tile in grid.all_tiles():
        tile.terrain = TerrainType.GRASS

    # Create a wall of mountains from (5, 2) to (5, 7)
    for y in range(2, 8):
        tile = grid.get_tile(5, y)
        tile.terrain = TerrainType.MOUNTAIN

    return grid


@pytest.fixture
def player_civ():
    """Create a player civilization."""
    return Civilization(name="Player", color_key="PLAYER")


@pytest.fixture
def enemy_civ():
    """Create an enemy civilization."""
    return Civilization(name="Enemy", color_key="AI_AGGRESSIVE", is_ai=True)


class TestHeuristic:
    """Tests for heuristic function."""

    def test_heuristic_same_tile(self, simple_grid):
        """Heuristic should be 0 for same tile."""
        tile = simple_grid.get_tile(5, 5)
        assert heuristic(tile, tile) == 0

    def test_heuristic_adjacent_tiles(self, simple_grid):
        """Heuristic should be 1 for adjacent tiles."""
        tile1 = simple_grid.get_tile(5, 5)
        tile2 = simple_grid.get_tile(5, 6)
        assert heuristic(tile1, tile2) == 1

    def test_heuristic_manhattan_distance(self, simple_grid):
        """Heuristic should calculate Manhattan distance."""
        tile1 = simple_grid.get_tile(0, 0)
        tile2 = simple_grid.get_tile(5, 3)
        assert heuristic(tile1, tile2) == 8  # 5 + 3


class TestFindPath:
    """Tests for A* pathfinding."""

    def test_path_to_same_tile(self, simple_grid):
        """Path to same tile should be empty."""
        start = simple_grid.get_tile(5, 5)
        path = find_path(simple_grid, start, start)
        assert path == []

    def test_path_to_adjacent_tile(self, simple_grid):
        """Path to adjacent tile should have one step."""
        start = simple_grid.get_tile(5, 5)
        goal = simple_grid.get_tile(5, 6)
        path = find_path(simple_grid, start, goal)

        assert len(path) == 1
        assert path[0] == goal

    def test_path_straight_line(self, simple_grid):
        """Path in a straight line should be direct."""
        start = simple_grid.get_tile(0, 5)
        goal = simple_grid.get_tile(5, 5)
        path = find_path(simple_grid, start, goal)

        assert len(path) == 5
        assert path[-1] == goal

    def test_path_around_obstacle(self, grid_with_obstacles):
        """Path should go around obstacles."""
        start = grid_with_obstacles.get_tile(3, 5)
        goal = grid_with_obstacles.get_tile(7, 5)
        path = find_path(grid_with_obstacles, start, goal)

        # Path must exist and go around mountains
        assert len(path) > 0
        assert path[-1] == goal

        # Path should not include any mountain tiles
        for tile in path:
            assert tile.terrain != TerrainType.MOUNTAIN

    def test_no_path_to_impassable(self, simple_grid):
        """Should return empty path when goal is impassable."""
        start = simple_grid.get_tile(5, 5)
        goal = simple_grid.get_tile(7, 7)
        goal.terrain = TerrainType.WATER

        path = find_path(simple_grid, start, goal)
        assert path == []

    def test_path_prefers_low_cost_terrain(self, simple_grid):
        """Path should prefer grass (cost 1) over forest (cost 2)."""
        # Create a forest patch
        for x in range(3, 7):
            simple_grid.get_tile(x, 5).terrain = TerrainType.FOREST

        start = simple_grid.get_tile(2, 5)
        goal = simple_grid.get_tile(8, 5)
        path = find_path(simple_grid, start, goal)

        # Path exists
        assert len(path) > 0
        assert path[-1] == goal

    def test_path_blocked_by_friendly_unit(self, simple_grid, player_civ):
        """Path should not pass through friendly units."""
        start = simple_grid.get_tile(0, 5)
        goal = simple_grid.get_tile(5, 5)

        # Place a friendly unit in the way
        blocking_tile = simple_grid.get_tile(3, 5)
        friendly_unit = create_warrior(player_civ, 3, 5)
        blocking_tile.unit = friendly_unit

        # Create unit for pathfinding context
        unit = create_warrior(player_civ, 0, 5)

        path = find_path(simple_grid, start, goal, unit)

        # Path should exist but go around
        assert len(path) > 0
        assert blocking_tile not in path


class TestGetReachableTiles:
    """Tests for reachable tiles calculation."""

    def test_reachable_from_center(self, simple_grid, player_civ):
        """Should find all tiles reachable within movement."""
        start = simple_grid.get_tile(5, 5)
        unit = create_warrior(player_civ, 5, 5)

        reachable = get_reachable_tiles(simple_grid, start, unit.movement, unit)

        # Warrior has 2 movement, all grass (cost 1)
        # Should reach all tiles within 2 Manhattan distance
        assert len(reachable) > 0

        # All tiles in result should be within movement range
        for tile, cost in reachable.items():
            assert cost <= unit.movement

    def test_reachable_blocked_by_obstacle(self, grid_with_obstacles, player_civ):
        """Reachable tiles should not include impassable terrain."""
        start = grid_with_obstacles.get_tile(3, 5)
        unit = create_warrior(player_civ, 3, 5)

        reachable = get_reachable_tiles(grid_with_obstacles, start, unit.movement, unit)

        # Should not include mountain tiles
        for tile in reachable:
            assert tile.terrain != TerrainType.MOUNTAIN

    def test_reachable_forest_costs_more(self, simple_grid, player_civ):
        """Forest terrain should cost more movement."""
        # Make right side forest
        for x in range(6, 10):
            for y in range(10):
                simple_grid.get_tile(x, y).terrain = TerrainType.FOREST

        start = simple_grid.get_tile(5, 5)
        unit = create_warrior(player_civ, 5, 5)

        reachable = get_reachable_tiles(simple_grid, start, unit.movement, unit)

        # Tiles in forest should have higher cost
        grass_tile = simple_grid.get_tile(4, 5)
        forest_tile = simple_grid.get_tile(6, 5)

        assert grass_tile in reachable
        assert grass_tile not in reachable or reachable.get(grass_tile, 0) < reachable.get(forest_tile, 0)


class TestGetPathCost:
    """Tests for path cost calculation."""

    def test_path_cost_grass(self, simple_grid):
        """Path through grass should cost 1 per tile."""
        path = [
            simple_grid.get_tile(1, 5),
            simple_grid.get_tile(2, 5),
            simple_grid.get_tile(3, 5),
        ]
        assert get_path_cost(path) == 3

    def test_path_cost_forest(self, simple_grid):
        """Path through forest should cost 2 per tile."""
        for tile in simple_grid.all_tiles():
            tile.terrain = TerrainType.FOREST

        path = [
            simple_grid.get_tile(1, 5),
            simple_grid.get_tile(2, 5),
        ]
        assert get_path_cost(path) == 4  # 2 forest tiles * 2 cost


class TestGetTilesInAttackRange:
    """Tests for attack range calculation."""

    def test_melee_attack_range(self, simple_grid, player_civ):
        """Melee units should only attack adjacent tiles."""
        unit = create_warrior(player_civ, 5, 5)
        simple_grid.get_tile(5, 5).unit = unit

        attackable = get_tiles_in_attack_range(simple_grid, unit)

        # Should have 4 adjacent tiles (cardinal directions)
        assert len(attackable) == 4

        # All should be distance 1
        for tile in attackable:
            distance = abs(tile.x - 5) + abs(tile.y - 5)
            assert distance == 1

    def test_ranged_attack_range(self, simple_grid, player_civ):
        """Ranged units should attack at distance."""
        unit = create_archer(player_civ, 5, 5)
        simple_grid.get_tile(5, 5).unit = unit

        attackable = get_tiles_in_attack_range(simple_grid, unit)

        # Archer has range 2, should include tiles at distance 1 and 2
        distances = set()
        for tile in attackable:
            distance = abs(tile.x - 5) + abs(tile.y - 5)
            distances.add(distance)
            assert distance <= 2

        assert 1 in distances
        assert 2 in distances

    def test_attack_range_at_edge(self, simple_grid, player_civ):
        """Attack range should be limited at map edges."""
        unit = create_warrior(player_civ, 0, 0)
        simple_grid.get_tile(0, 0).unit = unit

        attackable = get_tiles_in_attack_range(simple_grid, unit)

        # At corner, only 2 adjacent tiles
        assert len(attackable) == 2
