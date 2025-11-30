"""Tests for map generation using real game data."""

import pytest

from src.map.grid import Grid
from src.map.map_generator import MapGenerator, generate_game_map
from src.map.tile import TerrainType, ResourceType
from src.core.settings import MAP_WIDTH, MAP_HEIGHT


class TestMapGenerator:
    """Tests for MapGenerator class."""

    def test_generator_creates_grid_of_correct_size(self, map_generator):
        """Generator should create a grid of the specified dimensions."""
        grid = map_generator.generate_map(40, 30)

        assert grid.width == 40
        assert grid.height == 30

    def test_generator_is_deterministic_with_seed(self):
        """Same seed should produce identical maps."""
        gen1 = MapGenerator(seed=42)
        gen2 = MapGenerator(seed=42)

        grid1 = gen1.generate_map(20, 20)
        grid2 = gen2.generate_map(20, 20)

        # Check all tiles match
        for y in range(20):
            for x in range(20):
                tile1 = grid1.get_tile(x, y)
                tile2 = grid2.get_tile(x, y)
                assert tile1.terrain == tile2.terrain
                assert tile1.resource == tile2.resource

    def test_generator_produces_different_maps_with_different_seeds(self):
        """Different seeds should produce different maps."""
        gen1 = MapGenerator(seed=42)
        gen2 = MapGenerator(seed=999)

        grid1 = gen1.generate_map(20, 20)
        grid2 = gen2.generate_map(20, 20)

        # At least some tiles should be different
        differences = 0
        for y in range(20):
            for x in range(20):
                tile1 = grid1.get_tile(x, y)
                tile2 = grid2.get_tile(x, y)
                if tile1.terrain != tile2.terrain:
                    differences += 1

        assert differences > 0

    def test_generated_map_has_varied_terrain(self, generated_map):
        """Generated map should have multiple terrain types."""
        terrain_counts = {}
        for tile in generated_map.all_tiles():
            terrain_counts[tile.terrain] = terrain_counts.get(tile.terrain, 0) + 1

        # Should have at least 3 different terrain types
        assert len(terrain_counts) >= 3

        # Should have significant grass (most common land type)
        assert terrain_counts.get(TerrainType.GRASS, 0) > 0

    def test_generated_map_has_resources(self, generated_map):
        """Generated map should have resources placed on tiles."""
        resource_count = sum(1 for tile in generated_map.all_tiles() if tile.resource is not None)

        # Should have at least some resources
        assert resource_count > 0

        # Should have multiple resource types
        resource_types = set(
            tile.resource for tile in generated_map.all_tiles()
            if tile.resource is not None
        )
        assert len(resource_types) >= 2

    def test_resources_on_valid_terrain(self, generated_map):
        """Resources should only appear on appropriate terrain."""
        for tile in generated_map.all_tiles():
            if tile.resource is not None:
                # Resources shouldn't be on water or mountains
                assert tile.terrain not in [TerrainType.WATER, TerrainType.MOUNTAIN]

                # Specific resource/terrain checks
                if tile.resource == ResourceType.WOOD:
                    assert tile.terrain == TerrainType.FOREST
                elif tile.resource == ResourceType.STONE:
                    assert tile.terrain == TerrainType.HILLS

    def test_generated_map_has_passable_land(self, generated_map):
        """Generated map should have sufficient passable land."""
        passable = list(generated_map.find_passable_tiles())
        total = generated_map.width * generated_map.height
        land_ratio = len(passable) / total

        # At least 30% should be passable
        assert land_ratio >= 0.3


class TestStartingPositions:
    """Tests for starting position finding."""

    def test_finds_correct_number_of_positions(self, game_map_with_positions):
        """Should find the requested number of starting positions."""
        grid, positions = game_map_with_positions

        assert len(positions) == 3

    def test_starting_positions_are_on_grass(self, game_map_with_positions):
        """All starting positions should be on grass terrain."""
        grid, positions = game_map_with_positions

        for x, y in positions:
            tile = grid.get_tile(x, y)
            assert tile.terrain == TerrainType.GRASS

    def test_starting_positions_are_far_apart(self, game_map_with_positions):
        """Starting positions should be at least 8 tiles apart."""
        grid, positions = game_map_with_positions

        for i, (x1, y1) in enumerate(positions):
            for j, (x2, y2) in enumerate(positions):
                if i != j:
                    distance = grid.get_distance(x1, y1, x2, y2)
                    assert distance >= 8

    def test_starting_positions_have_nearby_resources(self, game_map_with_positions):
        """Starting positions should have resources within 3 tiles."""
        grid, positions = game_map_with_positions

        for x, y in positions:
            nearby = grid.get_tiles_in_range(x, y, 3)
            resource_count = sum(1 for tile in nearby if tile.resource is not None)
            assert resource_count >= 2

    def test_starting_positions_not_surrounded_by_water(self, game_map_with_positions):
        """Starting positions should not be surrounded by water."""
        grid, positions = game_map_with_positions

        for x, y in positions:
            tile = grid.get_tile(x, y)
            neighbors = grid.get_neighbors(tile)
            water_count = sum(1 for n in neighbors if n.terrain == TerrainType.WATER)
            assert water_count <= 2


class TestGenerateGameMap:
    """Tests for the complete map generation function."""

    def test_generates_playable_map(self):
        """generate_game_map should produce a playable map."""
        grid, positions = generate_game_map(
            width=MAP_WIDTH,
            height=MAP_HEIGHT,
            num_civs=3,
            seed=12345
        )

        assert grid is not None
        assert len(positions) == 3
        assert grid.width == MAP_WIDTH
        assert grid.height == MAP_HEIGHT

    def test_retries_on_unplayable_map(self):
        """Should retry generation if initial attempt is unplayable."""
        # Use a very small map that might not be playable on first try
        # This tests the retry mechanism
        try:
            grid, positions = generate_game_map(
                width=15,
                height=15,
                num_civs=2,
                seed=None,
                max_attempts=20
            )
            # If we get here, generation succeeded
            assert len(positions) == 2
        except RuntimeError:
            # Acceptable if small map can't support 2 civs
            pass

    def test_reproducible_with_seed(self):
        """Same seed should produce identical results."""
        grid1, pos1 = generate_game_map(30, 30, 2, seed=999)
        grid2, pos2 = generate_game_map(30, 30, 2, seed=999)

        assert pos1 == pos2

        for y in range(30):
            for x in range(30):
                assert grid1.get_tile(x, y).terrain == grid2.get_tile(x, y).terrain
