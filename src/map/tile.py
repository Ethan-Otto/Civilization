"""Tile class and terrain types."""

from enum import Enum, auto
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from src.entities.unit import Unit
    from src.entities.city import City
    from src.entities.civilization import Civilization


class TerrainType(Enum):
    """Types of terrain on the map."""
    GRASS = auto()
    FOREST = auto()
    MOUNTAIN = auto()
    WATER = auto()
    DESERT = auto()
    HILLS = auto()


class ResourceType(Enum):
    """Types of resources that can be found on tiles."""
    FOOD = auto()
    WOOD = auto()
    STONE = auto()
    GOLD = auto()


# Terrain properties lookup
TERRAIN_PROPERTIES = {
    TerrainType.GRASS: {"movement_cost": 1, "defense_bonus": 0.0, "passable": True},
    TerrainType.FOREST: {"movement_cost": 2, "defense_bonus": 0.25, "passable": True},
    TerrainType.MOUNTAIN: {"movement_cost": float('inf'), "defense_bonus": 0.50, "passable": False},
    TerrainType.WATER: {"movement_cost": float('inf'), "defense_bonus": 0.0, "passable": False},
    TerrainType.DESERT: {"movement_cost": 1, "defense_bonus": 0.0, "passable": True},
    TerrainType.HILLS: {"movement_cost": 2, "defense_bonus": 0.25, "passable": True},
}

# Which resources can spawn on which terrain
TERRAIN_RESOURCES = {
    TerrainType.GRASS: [ResourceType.FOOD, ResourceType.GOLD],
    TerrainType.FOREST: [ResourceType.WOOD],
    TerrainType.MOUNTAIN: [],  # Mountains spawn stone on adjacent hills
    TerrainType.WATER: [],
    TerrainType.DESERT: [ResourceType.GOLD],
    TerrainType.HILLS: [ResourceType.STONE],
}


@dataclass(eq=False)
class Tile:
    """Represents a single map tile."""

    x: int
    y: int
    terrain: TerrainType = TerrainType.GRASS
    resource: Optional[ResourceType] = None
    unit: Optional['Unit'] = field(default=None, repr=False)
    city: Optional['City'] = field(default=None, repr=False)
    owner: Optional['Civilization'] = field(default=None, repr=False)

    def __eq__(self, other: object) -> bool:
        """Tiles are equal if they have the same position."""
        if not isinstance(other, Tile):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        """Hash based on position."""
        return hash((self.x, self.y))

    @property
    def movement_cost(self) -> float:
        """Get the movement cost to enter this tile."""
        return TERRAIN_PROPERTIES[self.terrain]["movement_cost"]

    @property
    def defense_bonus(self) -> float:
        """Get the defense bonus this tile provides."""
        return TERRAIN_PROPERTIES[self.terrain]["defense_bonus"]

    @property
    def is_passable(self) -> bool:
        """Check if units can move through this tile."""
        return TERRAIN_PROPERTIES[self.terrain]["passable"]

    @property
    def position(self) -> tuple[int, int]:
        """Get the tile's position as a tuple."""
        return (self.x, self.y)

    def has_unit(self) -> bool:
        """Check if there's a unit on this tile."""
        return self.unit is not None

    def has_city(self) -> bool:
        """Check if there's a city on this tile."""
        return self.city is not None

    def has_resource(self) -> bool:
        """Check if there's a resource on this tile."""
        return self.resource is not None

    def is_occupied(self) -> bool:
        """Check if the tile is occupied by a unit or city."""
        return self.has_unit() or self.has_city()

    def can_enter(self, unit: Optional['Unit'] = None) -> bool:
        """Check if a unit can enter this tile."""
        if not self.is_passable:
            return False
        if self.has_unit():
            # Can't enter if there's already a unit (unless it's an enemy for attack)
            if unit is not None and self.unit.owner != unit.owner:
                return True  # Can attack
            return False
        return True
