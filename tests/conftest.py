"""Pytest fixtures with real game data."""

import pytest

from src.map.grid import Grid
from src.map.map_generator import MapGenerator, generate_game_map
from src.map.tile import TerrainType, ResourceType
from src.core.settings import MAP_WIDTH, MAP_HEIGHT


@pytest.fixture
def map_generator():
    """Create a map generator with a fixed seed for reproducibility."""
    return MapGenerator(seed=12345)


@pytest.fixture
def small_grid():
    """Create a small 10x10 grid for quick tests."""
    return Grid(10, 10)


@pytest.fixture
def standard_grid():
    """Create a standard size grid."""
    return Grid(MAP_WIDTH, MAP_HEIGHT)


@pytest.fixture
def generated_map():
    """Create a fully generated map with terrain and resources."""
    generator = MapGenerator(seed=12345)
    return generator.generate_map(MAP_WIDTH, MAP_HEIGHT)


@pytest.fixture
def game_map_with_positions():
    """Create a game map with starting positions for 3 civs."""
    grid, positions = generate_game_map(MAP_WIDTH, MAP_HEIGHT, num_civs=3, seed=12345)
    return grid, positions


@pytest.fixture
def grass_tile():
    """Create a grass tile at origin."""
    from src.map.tile import Tile
    return Tile(x=0, y=0, terrain=TerrainType.GRASS)


@pytest.fixture
def forest_tile():
    """Create a forest tile."""
    from src.map.tile import Tile
    return Tile(x=1, y=0, terrain=TerrainType.FOREST)


@pytest.fixture
def mountain_tile():
    """Create a mountain tile."""
    from src.map.tile import Tile
    return Tile(x=2, y=0, terrain=TerrainType.MOUNTAIN)


@pytest.fixture
def tile_with_resource():
    """Create a grass tile with food resource."""
    from src.map.tile import Tile
    return Tile(x=0, y=0, terrain=TerrainType.GRASS, resource=ResourceType.FOOD)
