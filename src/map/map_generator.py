"""Procedural map generation using smoothed random noise."""

import random
import math
from typing import Optional

from src.map.grid import Grid
from src.map.tile import Tile, TerrainType, ResourceType
from src.data.resource_data import RESOURCE_SPAWN_CHANCES


class MapGenerator:
    """Generates procedural maps using smoothed random values."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the map generator.

        Args:
            seed: Random seed for reproducible generation
        """
        self.seed = seed if seed is not None else random.randint(0, 999999)
        # Use a dedicated Random instance for determinism
        self._rng = random.Random(self.seed)

    def generate_map(self, width: int, height: int) -> Grid:
        """Generate a complete game map.

        Args:
            width: Map width in tiles
            height: Map height in tiles

        Returns:
            A Grid populated with terrain and resources
        """
        grid = Grid(width, height)

        # Generate terrain using smoothed random
        self._generate_terrain(grid)

        # Place resources
        self._place_resources(grid)

        return grid

    def _generate_terrain(self, grid: Grid) -> None:
        """Generate terrain using smoothed random values.

        Args:
            grid: The grid to populate
        """
        width, height = grid.width, grid.height

        # Generate initial random elevation map
        elevation_map = [[0.0 for _ in range(width)] for _ in range(height)]
        moisture_map = [[0.0 for _ in range(width)] for _ in range(height)]

        # Fill with random values
        for y in range(height):
            for x in range(width):
                elevation_map[y][x] = self._rng.random()
                moisture_map[y][x] = self._rng.random()

        # Apply multiple smoothing passes
        for _ in range(3):
            elevation_map = self._smooth_map(elevation_map, width, height)
            moisture_map = self._smooth_map(moisture_map, width, height)

        # Add some variation with a second layer at different scale
        variation_map = [[self._rng.random() for _ in range(width)] for _ in range(height)]
        for _ in range(2):
            variation_map = self._smooth_map(variation_map, width, height)

        # Combine layers
        for y in range(height):
            for x in range(width):
                elevation_map[y][x] = elevation_map[y][x] * 0.7 + variation_map[y][x] * 0.3

        # Apply terrain types based on elevation and moisture
        for tile in grid.all_tiles():
            elevation = elevation_map[tile.y][tile.x]
            moisture = moisture_map[tile.y][tile.x]
            tile.terrain = self._elevation_to_terrain(elevation, moisture)

    def _smooth_map(self, map_data: list[list[float]], width: int, height: int) -> list[list[float]]:
        """Apply a smoothing pass to a 2D map.

        Args:
            map_data: 2D list of values
            width: Map width
            height: Map height

        Returns:
            Smoothed map
        """
        smoothed = [[0.0 for _ in range(width)] for _ in range(height)]

        for y in range(height):
            for x in range(width):
                total = 0.0
                count = 0

                # Sample 3x3 neighborhood
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            # Center has more weight
                            weight = 2 if (dx == 0 and dy == 0) else 1
                            total += map_data[ny][nx] * weight
                            count += weight

                smoothed[y][x] = total / count if count > 0 else 0.0

        return smoothed

    def _elevation_to_terrain(self, elevation: float, moisture: float) -> TerrainType:
        """Convert elevation and moisture values to terrain type.

        Args:
            elevation: Elevation value [0, 1]
            moisture: Moisture value [0, 1]

        Returns:
            Appropriate terrain type
        """
        if elevation < 0.25:
            return TerrainType.WATER
        elif elevation < 0.35:
            return TerrainType.DESERT
        elif elevation < 0.60:
            # Grass or forest based on moisture
            if moisture > 0.55:
                return TerrainType.FOREST
            return TerrainType.GRASS
        elif elevation < 0.75:
            # Hills or forest
            if moisture > 0.5:
                return TerrainType.FOREST
            return TerrainType.HILLS
        else:
            return TerrainType.MOUNTAIN

    def _place_resources(self, grid: Grid) -> None:
        """Place resources on appropriate terrain tiles.

        Args:
            grid: The grid to add resources to
        """
        for tile in grid.all_tiles():
            spawn_chances = RESOURCE_SPAWN_CHANCES.get(tile.terrain, {})

            for resource_type, chance in spawn_chances.items():
                if self._rng.random() < chance:
                    tile.resource = resource_type
                    break  # Only one resource per tile

    def find_starting_positions(self, grid: Grid, num_civs: int,
                                 min_distance: int = 8) -> list[tuple[int, int]]:
        """Find suitable starting positions for civilizations.

        Requirements:
        - On GRASS terrain
        - At least min_distance tiles apart from each other
        - At least 2 resource tiles within 3-tile radius
        - Not surrounded by water on more than 2 sides

        Args:
            grid: The game grid
            num_civs: Number of civilizations to place
            min_distance: Minimum distance between starting positions

        Returns:
            List of (x, y) starting positions
        """
        candidates = []

        # Find all valid candidate tiles
        for tile in grid.all_tiles():
            if self._is_valid_starting_position(tile, grid):
                candidates.append(tile)

        if len(candidates) < num_civs:
            raise ValueError(f"Not enough valid starting positions. Found {len(candidates)}, need {num_civs}")

        # Select positions that are far enough apart
        positions = []
        self._rng.shuffle(candidates)

        for candidate in candidates:
            # Check distance from all existing positions
            valid = True
            for pos in positions:
                distance = grid.get_distance(candidate.x, candidate.y, pos[0], pos[1])
                if distance < min_distance:
                    valid = False
                    break

            if valid:
                positions.append((candidate.x, candidate.y))
                if len(positions) == num_civs:
                    break

        if len(positions) < num_civs:
            raise ValueError(f"Could not find {num_civs} starting positions with min distance {min_distance}")

        return positions

    def _is_valid_starting_position(self, tile: Tile, grid: Grid) -> bool:
        """Check if a tile is a valid starting position.

        Args:
            tile: The tile to check
            grid: The game grid

        Returns:
            True if valid starting position
        """
        # Must be on grass
        if tile.terrain != TerrainType.GRASS:
            return False

        # Count water neighbors
        neighbors = grid.get_neighbors(tile)
        water_count = sum(1 for n in neighbors if n.terrain == TerrainType.WATER)
        if water_count > 2:
            return False

        # Check for resources within 3 tiles
        nearby_tiles = grid.get_tiles_in_range(tile.x, tile.y, 3)
        resource_count = sum(1 for t in nearby_tiles if t.resource is not None)
        if resource_count < 2:
            return False

        return True

    def ensure_playable(self, grid: Grid) -> bool:
        """Verify the map is playable.

        Args:
            grid: The grid to check

        Returns:
            True if map is playable
        """
        # Check that there's enough passable land
        passable_tiles = list(grid.find_passable_tiles())
        total_tiles = grid.width * grid.height
        land_ratio = len(passable_tiles) / total_tiles

        if land_ratio < 0.3:  # At least 30% land
            return False

        # Check that we can find starting positions for 3 civs
        try:
            self.find_starting_positions(grid, 3)
            return True
        except ValueError:
            return False


def generate_game_map(width: int, height: int, num_civs: int = 3,
                      seed: Optional[int] = None,
                      max_attempts: int = 10) -> tuple[Grid, list[tuple[int, int]]]:
    """Generate a complete game map with starting positions.

    Will retry generation if map is not playable.

    Args:
        width: Map width
        height: Map height
        num_civs: Number of civilizations
        seed: Optional random seed
        max_attempts: Maximum generation attempts

    Returns:
        Tuple of (grid, starting_positions)
    """
    base_seed = seed if seed is not None else random.randint(0, 999999)

    for attempt in range(max_attempts):
        generator = MapGenerator(seed=base_seed + attempt)
        grid = generator.generate_map(width, height)

        if generator.ensure_playable(grid):
            positions = generator.find_starting_positions(grid, num_civs)
            return grid, positions

    raise RuntimeError(f"Failed to generate playable map after {max_attempts} attempts")
