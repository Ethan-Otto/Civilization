"""Grid class for managing the 2D tile map."""

from typing import Optional, Iterator
from .tile import Tile, TerrainType


class Grid:
    """Manages the 2D tile grid."""

    def __init__(self, width: int, height: int):
        """Initialize an empty grid.

        Args:
            width: Number of tiles wide
            height: Number of tiles tall
        """
        self.width = width
        self.height = height
        self._tiles: list[list[Tile]] = []
        self._initialize_tiles()

    def _initialize_tiles(self) -> None:
        """Create the initial grid of tiles."""
        self._tiles = [
            [Tile(x=x, y=y) for x in range(self.width)]
            for y in range(self.height)
        ]

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get a tile at the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            The tile at (x, y) or None if out of bounds
        """
        if not self.is_valid_position(x, y):
            return None
        return self._tiles[y][x]

    def set_tile(self, x: int, y: int, tile: Tile) -> bool:
        """Set a tile at the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            tile: The tile to place

        Returns:
            True if successful, False if out of bounds
        """
        if not self.is_valid_position(x, y):
            return False
        self._tiles[y][x] = tile
        return True

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if coordinates are within the grid bounds.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if position is valid
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def get_neighbors(self, tile: Tile, include_diagonals: bool = False) -> list[Tile]:
        """Get all neighboring tiles.

        Args:
            tile: The center tile
            include_diagonals: Whether to include diagonal neighbors

        Returns:
            List of neighboring tiles
        """
        neighbors = []

        # Cardinal directions
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        if include_diagonals:
            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

        for dx, dy in directions:
            neighbor = self.get_tile(tile.x + dx, tile.y + dy)
            if neighbor is not None:
                neighbors.append(neighbor)

        return neighbors

    def get_tiles_in_range(self, center_x: int, center_y: int, radius: int) -> list[Tile]:
        """Get all tiles within a certain range of a position.

        Uses Manhattan distance for range calculation.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Maximum distance from center

        Returns:
            List of tiles within range
        """
        tiles = []
        for y in range(max(0, center_y - radius), min(self.height, center_y + radius + 1)):
            for x in range(max(0, center_x - radius), min(self.width, center_x + radius + 1)):
                distance = abs(x - center_x) + abs(y - center_y)
                if distance <= radius:
                    tile = self.get_tile(x, y)
                    if tile is not None:
                        tiles.append(tile)
        return tiles

    def get_tiles_at_range(self, center_x: int, center_y: int, radius: int) -> list[Tile]:
        """Get all tiles exactly at a certain range from a position.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Exact distance from center

        Returns:
            List of tiles at exact range
        """
        tiles = []
        for y in range(max(0, center_y - radius), min(self.height, center_y + radius + 1)):
            for x in range(max(0, center_x - radius), min(self.width, center_x + radius + 1)):
                distance = abs(x - center_x) + abs(y - center_y)
                if distance == radius:
                    tile = self.get_tile(x, y)
                    if tile is not None:
                        tiles.append(tile)
        return tiles

    def find_tiles_by_terrain(self, terrain: TerrainType) -> list[Tile]:
        """Find all tiles with a specific terrain type.

        Args:
            terrain: The terrain type to find

        Returns:
            List of matching tiles
        """
        return [tile for tile in self.all_tiles() if tile.terrain == terrain]

    def find_passable_tiles(self) -> list[Tile]:
        """Find all passable tiles.

        Returns:
            List of passable tiles
        """
        return [tile for tile in self.all_tiles() if tile.is_passable]

    def all_tiles(self) -> Iterator[Tile]:
        """Iterate over all tiles in the grid.

        Yields:
            Each tile in row-major order
        """
        for row in self._tiles:
            for tile in row:
                yield tile

    def get_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Manhattan distance between two positions.

        Args:
            x1, y1: First position
            x2, y2: Second position

        Returns:
            Manhattan distance
        """
        return abs(x2 - x1) + abs(y2 - y1)

    def __repr__(self) -> str:
        return f"Grid({self.width}x{self.height})"
