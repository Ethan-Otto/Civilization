"""Input handler for processing user input."""

import pygame
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from src.core.settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE

if TYPE_CHECKING:
    from src.ui.camera import Camera
    from src.core.game_state import GameState


class InputAction(Enum):
    """Types of input actions."""
    QUIT = auto()
    END_TURN = auto()
    SELECT_TILE = auto()
    MOVE_UNIT = auto()
    ATTACK = auto()
    DESELECT = auto()
    CAMERA_SCROLL = auto()
    CYCLE_UNIT = auto()


@dataclass
class InputEvent:
    """Represents a processed input event."""
    action: InputAction
    world_x: Optional[int] = None
    world_y: Optional[int] = None
    data: dict = field(default_factory=dict)


class InputHandler:
    """Handles all user input and translates to game actions."""

    def __init__(self, camera: 'Camera'):
        """Initialize input handler.

        Args:
            camera: Game camera for coordinate conversion
        """
        self.camera = camera

        # UI element positions for click detection
        self.end_turn_button_rect = pygame.Rect(
            WINDOW_WIDTH - 120,
            WINDOW_HEIGHT - 60,
            100, 40
        )

        # HUD height for determining map clicks
        self.hud_top_height = 40
        self.hud_bottom_height = 80

    def process_events(self, game_state: 'GameState') -> list[InputEvent]:
        """Process all pending pygame events.

        Args:
            game_state: Current game state

        Returns:
            List of input events
        """
        events = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append(InputEvent(action=InputAction.QUIT))

            elif event.type == pygame.KEYDOWN:
                key_event = self._handle_keydown(event, game_state)
                if key_event:
                    events.append(key_event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_event = self._handle_mousedown(event, game_state)
                if mouse_event:
                    events.append(mouse_event)

        return events

    def _handle_keydown(self, event: pygame.event.Event,
                        game_state: 'GameState') -> Optional[InputEvent]:
        """Handle keyboard input.

        Args:
            event: Pygame key event
            game_state: Current game state

        Returns:
            Input event or None
        """
        if event.key == pygame.K_ESCAPE:
            return InputEvent(action=InputAction.QUIT)

        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            return InputEvent(action=InputAction.END_TURN)

        elif event.key == pygame.K_TAB:
            return InputEvent(action=InputAction.CYCLE_UNIT)

        return None

    def _handle_mousedown(self, event: pygame.event.Event,
                          game_state: 'GameState') -> Optional[InputEvent]:
        """Handle mouse click events.

        Args:
            event: Pygame mouse event
            game_state: Current game state

        Returns:
            Input event or None
        """
        mouse_x, mouse_y = event.pos

        if event.button == 1:  # Left click
            # Check UI buttons first
            if self.end_turn_button_rect.collidepoint(mouse_x, mouse_y):
                return InputEvent(action=InputAction.END_TURN)

            # Check if clicking on map (not on HUD)
            if self._is_map_click(mouse_y):
                world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                return self._determine_map_action(world_x, world_y, game_state)

        elif event.button == 3:  # Right click
            # Check if clicking on map
            if self._is_map_click(mouse_y):
                world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)

                # Right click with selected unit = move/attack
                if game_state.selected_unit:
                    return self._determine_unit_action(world_x, world_y, game_state)
                else:
                    return InputEvent(action=InputAction.DESELECT)

        return None

    def _is_map_click(self, screen_y: int) -> bool:
        """Check if click is on the map area.

        Args:
            screen_y: Y coordinate of click

        Returns:
            True if click is on map
        """
        return self.hud_top_height < screen_y < WINDOW_HEIGHT - self.hud_bottom_height

    def _determine_map_action(self, world_x: int, world_y: int,
                              game_state: 'GameState') -> Optional[InputEvent]:
        """Determine action for a left click on the map.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            game_state: Current game state

        Returns:
            Input event
        """
        tile = game_state.grid.get_tile(world_x, world_y)
        if tile is None:
            return None

        # Check if clicking on a unit
        if tile.unit:
            # If it's our unit, select it
            if tile.unit.owner == game_state.player_civ:
                return InputEvent(
                    action=InputAction.SELECT_TILE,
                    world_x=world_x,
                    world_y=world_y,
                    data={"unit": tile.unit}
                )
            # If it's enemy and we have selected unit, attack
            elif game_state.selected_unit:
                return InputEvent(
                    action=InputAction.ATTACK,
                    world_x=world_x,
                    world_y=world_y,
                    data={"target": tile.unit}
                )

        # If we have a selected unit, try to move
        if game_state.selected_unit:
            return InputEvent(
                action=InputAction.MOVE_UNIT,
                world_x=world_x,
                world_y=world_y
            )

        # Otherwise just select the tile
        return InputEvent(
            action=InputAction.SELECT_TILE,
            world_x=world_x,
            world_y=world_y
        )

    def _determine_unit_action(self, world_x: int, world_y: int,
                               game_state: 'GameState') -> Optional[InputEvent]:
        """Determine action for right click with selected unit.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            game_state: Current game state

        Returns:
            Input event
        """
        tile = game_state.grid.get_tile(world_x, world_y)
        if tile is None:
            return None

        selected = game_state.selected_unit

        # Check if target tile has enemy unit
        if tile.unit and tile.unit.owner != selected.owner:
            return InputEvent(
                action=InputAction.ATTACK,
                world_x=world_x,
                world_y=world_y,
                data={"target": tile.unit}
            )

        # Otherwise try to move
        return InputEvent(
            action=InputAction.MOVE_UNIT,
            world_x=world_x,
            world_y=world_y
        )

    def handle_continuous_input(self) -> None:
        """Handle continuous input like camera scrolling.

        This should be called each frame.
        """
        # Handle keyboard camera scrolling
        keys = pygame.key.get_pressed()
        keys_dict = {
            pygame.K_LEFT: keys[pygame.K_LEFT],
            pygame.K_RIGHT: keys[pygame.K_RIGHT],
            pygame.K_UP: keys[pygame.K_UP],
            pygame.K_DOWN: keys[pygame.K_DOWN],
            pygame.K_a: keys[pygame.K_a],
            pygame.K_d: keys[pygame.K_d],
            pygame.K_w: keys[pygame.K_w],
            pygame.K_s: keys[pygame.K_s],
        }
        self.camera.handle_key_scroll(keys_dict)

        # Handle edge scrolling
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if self._is_map_click(mouse_y):
            self.camera.handle_edge_scroll(mouse_x, mouse_y)

    def update_button_rects(self, end_turn_rect: pygame.Rect) -> None:
        """Update UI button rectangles for hit detection.

        Args:
            end_turn_rect: Rectangle of the end turn button
        """
        self.end_turn_button_rect = end_turn_rect
