"""Game constants and configuration."""

# Window settings
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Civilization"
FPS = 60

# Tile settings
TILE_SIZE = 32
MAP_WIDTH = 40
MAP_HEIGHT = 30

# Colors (RGB)
COLORS = {
    # Terrain colors
    "GRASS": (34, 139, 34),
    "FOREST": (0, 100, 0),
    "MOUNTAIN": (139, 137, 137),
    "WATER": (65, 105, 225),
    "DESERT": (238, 214, 175),
    "HILLS": (139, 119, 101),

    # UI colors
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "GRAY": (128, 128, 128),
    "DARK_GRAY": (64, 64, 64),

    # Fog of war
    "FOG_UNEXPLORED": (20, 20, 20),
    "FOG_EXPLORED": (80, 80, 80),

    # Civilization colors
    "PLAYER": (0, 0, 255),
    "AI_AGGRESSIVE": (255, 0, 0),
    "AI_BALANCED": (0, 255, 0),

    # Resource colors
    "FOOD": (255, 215, 0),
    "WOOD": (139, 69, 19),
    "STONE": (169, 169, 169),
    "GOLD": (255, 223, 0),

    # UI elements
    "HUD_BG": (40, 40, 40),
    "BUTTON": (70, 70, 70),
    "BUTTON_HOVER": (100, 100, 100),
    "SELECTED": (255, 255, 0),
}

# Terrain movement costs
TERRAIN_MOVEMENT_COST = {
    "GRASS": 1,
    "FOREST": 2,
    "MOUNTAIN": float('inf'),  # Impassable
    "WATER": float('inf'),     # Impassable
    "DESERT": 1,
    "HILLS": 2,
}

# Terrain defense bonuses (percentage damage reduction)
TERRAIN_DEFENSE_BONUS = {
    "GRASS": 0.0,
    "FOREST": 0.25,
    "MOUNTAIN": 0.50,
    "WATER": 0.0,
    "DESERT": 0.0,
    "HILLS": 0.25,
}

# Starting resources
STARTING_RESOURCES = {
    "FOOD": 100,
    "WOOD": 50,
    "STONE": 30,
    "GOLD": 50,
}

# Vision ranges
UNIT_VISION_RANGE = 2
CITY_VISION_RANGE = 3

# AI personalities
AI_PERSONALITIES = {
    "AGGRESSIVE": {
        "military_weight": 1.5,
        "expansion_weight": 0.8,
        "economy_weight": 0.7,
        "research_weight": 0.6,
    },
    "BALANCED": {
        "military_weight": 1.0,
        "expansion_weight": 1.0,
        "economy_weight": 1.0,
        "research_weight": 1.0,
    },
}

# Camera settings
CAMERA_SCROLL_SPEED = 10
CAMERA_EDGE_SCROLL_MARGIN = 50
