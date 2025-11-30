"""Camera system for viewport management."""

from src.core.settings import (
    TILE_SIZE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    CAMERA_SCROLL_SPEED,
    CAMERA_EDGE_SCROLL_MARGIN
)


class Camera:
    """Manages the visible portion of the map."""

    def __init__(self, map_width: int, map_height: int):
        """Initialize the camera.

        Args:
            map_width: Width of the map in tiles
            map_height: Height of the map in tiles
        """
        self.x = 0.0  # World X position (top-left of viewport)
        self.y = 0.0  # World Y position (top-left of viewport)

        self.map_width = map_width
        self.map_height = map_height

        # Viewport dimensions in pixels
        self.viewport_width = WINDOW_WIDTH
        self.viewport_height = WINDOW_HEIGHT - 120  # Leave room for HUD

        # Calculate map bounds in pixels
        self.max_x = max(0, map_width * TILE_SIZE - self.viewport_width)
        self.max_y = max(0, map_height * TILE_SIZE - self.viewport_height)

    def move(self, dx: float, dy: float) -> None:
        """Move the camera by a delta amount.

        Args:
            dx: Change in X position
            dy: Change in Y position
        """
        self.x = max(0, min(self.max_x, self.x + dx))
        self.y = max(0, min(self.max_y, self.y + dy))

    def center_on(self, world_x: int, world_y: int) -> None:
        """Center the camera on a world position.

        Args:
            world_x: World X coordinate in tiles
            world_y: World Y coordinate in tiles
        """
        # Convert tile position to pixel position, then center
        pixel_x = world_x * TILE_SIZE
        pixel_y = world_y * TILE_SIZE

        self.x = max(0, min(self.max_x, pixel_x - self.viewport_width // 2))
        self.y = max(0, min(self.max_y, pixel_y - self.viewport_height // 2))

    def world_to_screen(self, world_x: int, world_y: int) -> tuple[int, int]:
        """Convert world tile coordinates to screen pixel coordinates.

        Args:
            world_x: World X coordinate in tiles
            world_y: World Y coordinate in tiles

        Returns:
            Screen pixel coordinates (x, y)
        """
        screen_x = world_x * TILE_SIZE - int(self.x)
        screen_y = world_y * TILE_SIZE - int(self.y)
        return (screen_x, screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        """Convert screen pixel coordinates to world tile coordinates.

        Args:
            screen_x: Screen X coordinate in pixels
            screen_y: Screen Y coordinate in pixels

        Returns:
            World tile coordinates (x, y)
        """
        world_x = int((screen_x + self.x) // TILE_SIZE)
        world_y = int((screen_y + self.y) // TILE_SIZE)
        return (world_x, world_y)

    def is_visible(self, world_x: int, world_y: int) -> bool:
        """Check if a tile is currently visible on screen.

        Args:
            world_x: World X coordinate in tiles
            world_y: World Y coordinate in tiles

        Returns:
            True if the tile is visible
        """
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        return (
            -TILE_SIZE < screen_x < self.viewport_width and
            -TILE_SIZE < screen_y < self.viewport_height
        )

    def get_visible_tile_range(self) -> tuple[int, int, int, int]:
        """Get the range of tiles currently visible.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) tile coordinates
        """
        min_x = max(0, int(self.x // TILE_SIZE))
        min_y = max(0, int(self.y // TILE_SIZE))
        max_x = min(self.map_width, int((self.x + self.viewport_width) // TILE_SIZE) + 1)
        max_y = min(self.map_height, int((self.y + self.viewport_height) // TILE_SIZE) + 1)
        return (min_x, min_y, max_x, max_y)

    def handle_edge_scroll(self, mouse_x: int, mouse_y: int) -> None:
        """Handle camera scrolling when mouse is near screen edges.

        Args:
            mouse_x: Mouse X position
            mouse_y: Mouse Y position
        """
        if mouse_x < CAMERA_EDGE_SCROLL_MARGIN:
            self.move(-CAMERA_SCROLL_SPEED, 0)
        elif mouse_x > self.viewport_width - CAMERA_EDGE_SCROLL_MARGIN:
            self.move(CAMERA_SCROLL_SPEED, 0)

        if mouse_y < CAMERA_EDGE_SCROLL_MARGIN:
            self.move(0, -CAMERA_SCROLL_SPEED)
        elif mouse_y > self.viewport_height - CAMERA_EDGE_SCROLL_MARGIN:
            self.move(0, CAMERA_SCROLL_SPEED)

    def handle_key_scroll(self, keys_pressed: dict) -> None:
        """Handle camera scrolling via keyboard.

        Args:
            keys_pressed: Dictionary of pressed keys
        """
        import pygame

        if keys_pressed.get(pygame.K_LEFT) or keys_pressed.get(pygame.K_a):
            self.move(-CAMERA_SCROLL_SPEED, 0)
        if keys_pressed.get(pygame.K_RIGHT) or keys_pressed.get(pygame.K_d):
            self.move(CAMERA_SCROLL_SPEED, 0)
        if keys_pressed.get(pygame.K_UP) or keys_pressed.get(pygame.K_w):
            self.move(0, -CAMERA_SCROLL_SPEED)
        if keys_pressed.get(pygame.K_DOWN) or keys_pressed.get(pygame.K_s):
            self.move(0, CAMERA_SCROLL_SPEED)
