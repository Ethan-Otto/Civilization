"""Renderer for drawing the game world and UI."""

import pygame
from typing import Optional, TYPE_CHECKING

from src.core.settings import TILE_SIZE, COLORS, WINDOW_WIDTH, WINDOW_HEIGHT
from src.map.tile import TerrainType, ResourceType

if TYPE_CHECKING:
    from src.map.grid import Grid
    from src.map.tile import Tile
    from src.ui.camera import Camera
    from src.entities.civilization import Civilization


# Map terrain types to colors
TERRAIN_COLORS = {
    TerrainType.GRASS: COLORS["GRASS"],
    TerrainType.FOREST: COLORS["FOREST"],
    TerrainType.MOUNTAIN: COLORS["MOUNTAIN"],
    TerrainType.WATER: COLORS["WATER"],
    TerrainType.DESERT: COLORS["DESERT"],
    TerrainType.HILLS: COLORS["HILLS"],
}

# Map resource types to colors
RESOURCE_COLORS = {
    ResourceType.FOOD: COLORS["FOOD"],
    ResourceType.WOOD: COLORS["WOOD"],
    ResourceType.STONE: COLORS["STONE"],
    ResourceType.GOLD: COLORS["GOLD"],
}


class Renderer:
    """Handles all game rendering."""

    def __init__(self, screen: pygame.Surface):
        """Initialize the renderer.

        Args:
            screen: Pygame surface to render to
        """
        self.screen = screen
        self.font = None
        self.small_font = None
        self._init_fonts()

    def _init_fonts(self) -> None:
        """Initialize fonts for text rendering."""
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

    def clear(self) -> None:
        """Clear the screen."""
        self.screen.fill(COLORS["BLACK"])

    def render_grid(self, grid: 'Grid', camera: 'Camera',
                    fog_state: Optional[dict] = None) -> None:
        """Render the tile grid.

        Args:
            grid: The game grid to render
            camera: Camera for viewport positioning
            fog_state: Optional fog of war state dict {(x,y): "UNEXPLORED"|"EXPLORED"|"VISIBLE"}
        """
        min_x, min_y, max_x, max_y = camera.get_visible_tile_range()

        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                tile = grid.get_tile(x, y)
                if tile is not None:
                    self._render_tile(tile, camera, fog_state)

    def _render_tile(self, tile: 'Tile', camera: 'Camera',
                     fog_state: Optional[dict] = None) -> None:
        """Render a single tile.

        Args:
            tile: The tile to render
            camera: Camera for position conversion
            fog_state: Optional fog of war state
        """
        screen_x, screen_y = camera.world_to_screen(tile.x, tile.y)
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)

        # Check fog of war state
        fog = None
        if fog_state is not None:
            fog = fog_state.get((tile.x, tile.y), "UNEXPLORED")

        if fog == "UNEXPLORED":
            # Don't render anything for unexplored tiles
            pygame.draw.rect(self.screen, COLORS["FOG_UNEXPLORED"], rect)
            return

        # Render terrain
        color = TERRAIN_COLORS.get(tile.terrain, COLORS["GRASS"])
        pygame.draw.rect(self.screen, color, rect)

        # Render resource indicator if present
        if tile.resource is not None:
            resource_color = RESOURCE_COLORS.get(tile.resource, COLORS["WHITE"])
            resource_rect = pygame.Rect(
                screen_x + TILE_SIZE - 10,
                screen_y + 2,
                8, 8
            )
            pygame.draw.rect(self.screen, resource_color, resource_rect)

        # Apply fog overlay for explored but not visible tiles
        if fog == "EXPLORED":
            fog_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            fog_surface.set_alpha(128)
            fog_surface.fill(COLORS["FOG_EXPLORED"])
            self.screen.blit(fog_surface, (screen_x, screen_y))

        # Draw grid lines
        pygame.draw.rect(self.screen, COLORS["DARK_GRAY"], rect, 1)

    def render_unit(self, unit, camera: 'Camera', selected: bool = False) -> None:
        """Render a unit on the map.

        Args:
            unit: The unit to render
            camera: Camera for position conversion
            selected: Whether this unit is currently selected
        """
        screen_x, screen_y = camera.world_to_screen(unit.x, unit.y)

        # Unit body (colored rectangle based on owner)
        unit_rect = pygame.Rect(
            screen_x + 4,
            screen_y + 4,
            TILE_SIZE - 8,
            TILE_SIZE - 8
        )

        # Get civilization color
        civ_color = COLORS.get(unit.owner.color_key, COLORS["WHITE"]) if unit.owner else COLORS["WHITE"]
        pygame.draw.rect(self.screen, civ_color, unit_rect)

        # Draw unit type indicator (M for melee, R for ranged)
        indicator = "M" if unit.range == 1 else "R"
        text = self.small_font.render(indicator, True, COLORS["WHITE"])
        text_rect = text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2))
        self.screen.blit(text, text_rect)

        # Health bar
        health_ratio = unit.health / unit.max_health
        health_bar_width = TILE_SIZE - 8
        health_bar_rect = pygame.Rect(
            screen_x + 4,
            screen_y + TILE_SIZE - 6,
            int(health_bar_width * health_ratio),
            4
        )
        # Color based on health
        if health_ratio > 0.6:
            health_color = (0, 255, 0)
        elif health_ratio > 0.3:
            health_color = (255, 255, 0)
        else:
            health_color = (255, 0, 0)
        pygame.draw.rect(self.screen, health_color, health_bar_rect)

        # Selection indicator
        if selected:
            select_rect = pygame.Rect(screen_x + 2, screen_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
            pygame.draw.rect(self.screen, COLORS["SELECTED"], select_rect, 2)

    def render_city(self, city, camera: 'Camera') -> None:
        """Render a city on the map.

        Args:
            city: The city to render
            camera: Camera for position conversion
        """
        screen_x, screen_y = camera.world_to_screen(city.x, city.y)

        # City body (larger square)
        city_rect = pygame.Rect(
            screen_x + 2,
            screen_y + 2,
            TILE_SIZE - 4,
            TILE_SIZE - 4
        )

        civ_color = COLORS.get(city.owner.color_key, COLORS["WHITE"]) if city.owner else COLORS["WHITE"]
        pygame.draw.rect(self.screen, civ_color, city_rect)
        pygame.draw.rect(self.screen, COLORS["WHITE"], city_rect, 2)

        # City icon (C)
        text = self.font.render("C", True, COLORS["WHITE"])
        text_rect = text.get_rect(center=(screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2))
        self.screen.blit(text, text_rect)

    def render_hud(self, resources: dict, current_turn: int,
                   current_civ_name: str, selected_unit=None) -> None:
        """Render the heads-up display.

        Args:
            resources: Dictionary of resource counts
            current_turn: Current turn number
            current_civ_name: Name of the current civilization
            selected_unit: Currently selected unit (if any)
        """
        # Top bar background
        top_bar = pygame.Rect(0, 0, WINDOW_WIDTH, 40)
        pygame.draw.rect(self.screen, COLORS["HUD_BG"], top_bar)

        # Turn and civilization info
        turn_text = self.font.render(f"Turn: {current_turn}  |  {current_civ_name}", True, COLORS["WHITE"])
        self.screen.blit(turn_text, (10, 10))

        # Resources
        x_offset = 300
        for resource_name, amount in resources.items():
            resource_text = self.font.render(f"{resource_name}: {amount}", True, COLORS["WHITE"])
            self.screen.blit(resource_text, (x_offset, 10))
            x_offset += 120

        # Bottom bar background
        bottom_bar = pygame.Rect(0, WINDOW_HEIGHT - 80, WINDOW_WIDTH, 80)
        pygame.draw.rect(self.screen, COLORS["HUD_BG"], bottom_bar)

        # Selected unit info
        if selected_unit is not None:
            unit_info = f"{selected_unit.name}  HP: {selected_unit.health}/{selected_unit.max_health}  Moves: {selected_unit.remaining_movement}/{selected_unit.movement}"
            unit_text = self.font.render(unit_info, True, COLORS["WHITE"])
            self.screen.blit(unit_text, (10, WINDOW_HEIGHT - 70))

            # Unit stats
            stats_text = f"ATK: {selected_unit.attack}  DEF: {selected_unit.defense}  Range: {selected_unit.range}"
            stats_render = self.font.render(stats_text, True, COLORS["WHITE"])
            self.screen.blit(stats_render, (10, WINDOW_HEIGHT - 45))

        # End turn button
        self.render_button("End Turn", WINDOW_WIDTH - 120, WINDOW_HEIGHT - 60, 100, 40)

    def render_button(self, text: str, x: int, y: int, width: int, height: int,
                      hover: bool = False) -> pygame.Rect:
        """Render a button.

        Args:
            text: Button text
            x, y: Position
            width, height: Size
            hover: Whether mouse is hovering

        Returns:
            Button rect for hit detection
        """
        rect = pygame.Rect(x, y, width, height)
        color = COLORS["BUTTON_HOVER"] if hover else COLORS["BUTTON"]
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLORS["WHITE"], rect, 2)

        text_surface = self.font.render(text, True, COLORS["WHITE"])
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

        return rect

    def render_text(self, text: str, x: int, y: int,
                    color: tuple = None, centered: bool = False) -> None:
        """Render text on screen.

        Args:
            text: Text to render
            x, y: Position
            color: Text color (default white)
            centered: Whether to center the text at position
        """
        if color is None:
            color = COLORS["WHITE"]

        text_surface = self.font.render(text, True, color)
        if centered:
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, (x, y))
