"""Resource definitions and spawn rates."""

from src.map.tile import ResourceType, TerrainType


# Resource spawn chances per terrain type
RESOURCE_SPAWN_CHANCES = {
    TerrainType.GRASS: {
        ResourceType.FOOD: 0.15,  # 15% chance
        ResourceType.GOLD: 0.05,  # 5% chance
    },
    TerrainType.FOREST: {
        ResourceType.WOOD: 0.30,  # 30% chance
    },
    TerrainType.HILLS: {
        ResourceType.STONE: 0.40,  # 40% chance
    },
    TerrainType.DESERT: {
        ResourceType.GOLD: 0.08,  # 8% chance
    },
    TerrainType.MOUNTAIN: {},  # No resources on mountains
    TerrainType.WATER: {},      # No resources on water
}


# Resource yields when gathered
RESOURCE_YIELDS = {
    ResourceType.FOOD: 3,
    ResourceType.WOOD: 4,
    ResourceType.STONE: 3,
    ResourceType.GOLD: 5,
}


# Base resource income per city
BASE_CITY_INCOME = {
    ResourceType.FOOD: 5,
    ResourceType.WOOD: 2,
    ResourceType.STONE: 1,
    ResourceType.GOLD: 3,
}
