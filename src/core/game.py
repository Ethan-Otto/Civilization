"""Main game class and game loop."""

import pygame
from typing import Optional

from src.core.settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS,
    MAP_WIDTH, MAP_HEIGHT, COLORS
)
from src.core.game_state import GameState, GamePhase
from src.map.grid import Grid
from src.map.map_generator import generate_game_map
from src.map.pathfinding import find_path, get_reachable_tiles, get_path_cost
from src.ui.camera import Camera
from src.ui.renderer import Renderer
from src.ui.input_handler import InputHandler, InputAction
from src.entities.civilization import Civilization
from src.entities.city import City
from src.entities.unit_types import create_warrior, create_archer
from src.systems.combat_system import CombatSystem
from src.ai.ai_controller import process_ai_turn


class Game:
    """Main game class that manages the game loop and state."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the game.

        Args:
            seed: Optional random seed for map generation
        """
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = False
        self.seed = seed

        # Core components (initialized in _initialize)
        self.game_state: Optional[GameState] = None
        self.camera: Optional[Camera] = None
        self.renderer: Optional[Renderer] = None
        self.input_handler: Optional[InputHandler] = None

        # Movement preview
        self.movement_preview: dict = {}  # {tile: cost}

        self._initialize()

    def _initialize(self) -> None:
        """Initialize game components."""
        # Generate map
        grid, starting_positions = generate_game_map(
            width=MAP_WIDTH,
            height=MAP_HEIGHT,
            num_civs=3,
            seed=self.seed
        )

        # Create civilizations
        player_civ = Civilization(
            name="Player",
            color_key="PLAYER",
            is_ai=False
        )

        ai_aggressive = Civilization(
            name="Aggressive Empire",
            color_key="AI_AGGRESSIVE",
            is_ai=True,
            ai_personality="AGGRESSIVE"
        )

        ai_balanced = Civilization(
            name="Balanced Kingdom",
            color_key="AI_BALANCED",
            is_ai=True,
            ai_personality="BALANCED"
        )

        civs = [player_civ, ai_aggressive, ai_balanced]

        # Create game state
        self.game_state = GameState(
            grid=grid,
            civilizations=civs
        )
        self.game_state.phase = GamePhase.PLAYING

        # Initialize fog states for all civs
        for civ in civs:
            self.game_state.fog_states[civ.name] = {}

        # Create starting units and cities
        for i, (civ, (start_x, start_y)) in enumerate(zip(civs, starting_positions)):
            # Create capital city
            city = City(
                name=f"{civ.name}'s Capital",
                owner=civ,
                x=start_x,
                y=start_y
            )
            self.game_state.add_city(city)

            # Create starting units
            # Warrior at city
            warrior = create_warrior(civ, start_x, start_y + 1)
            if grid.get_tile(start_x, start_y + 1) and grid.get_tile(start_x, start_y + 1).is_passable:
                self.game_state.add_unit(warrior)
            else:
                # Try adjacent tile
                for dx, dy in [(1, 0), (-1, 0), (0, -1), (1, 1)]:
                    tile = grid.get_tile(start_x + dx, start_y + dy)
                    if tile and tile.is_passable and not tile.has_unit():
                        warrior = create_warrior(civ, start_x + dx, start_y + dy)
                        self.game_state.add_unit(warrior)
                        break

            # Archer nearby
            for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1), (2, 0), (-2, 0)]:
                tile = grid.get_tile(start_x + dx, start_y + dy)
                if tile and tile.is_passable and not tile.has_unit():
                    archer = create_archer(civ, start_x + dx, start_y + dy)
                    self.game_state.add_unit(archer)
                    break

        # Update visibility for all civs
        for civ in civs:
            self.game_state.update_visibility(civ)

        # Create UI components
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler(self.camera)

        # Center camera on player's first city
        player_cities = self.game_state.get_cities_for_civ(player_civ)
        if player_cities:
            self.camera.center_on(player_cities[0].x, player_cities[0].y)

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True

        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(FPS)

        pygame.quit()

    def _handle_events(self) -> None:
        """Handle pygame events."""
        events = self.input_handler.process_events(self.game_state)

        for event in events:
            if event.action == InputAction.QUIT:
                self.running = False

            elif event.action == InputAction.END_TURN:
                self._end_turn()

            elif event.action == InputAction.SELECT_TILE:
                self._handle_select(event)

            elif event.action == InputAction.MOVE_UNIT:
                self._handle_move(event)

            elif event.action == InputAction.ATTACK:
                self._handle_attack(event)

            elif event.action == InputAction.DESELECT:
                self.game_state.selected_unit = None
                self.movement_preview = {}

            elif event.action == InputAction.CYCLE_UNIT:
                self._cycle_unit()

    def _handle_select(self, event) -> None:
        """Handle tile/unit selection.

        Args:
            event: Input event
        """
        if "unit" in event.data:
            unit = event.data["unit"]
            self.game_state.selected_unit = unit
            self._update_movement_preview()
        else:
            # Clicked empty tile
            self.game_state.selected_unit = None
            self.movement_preview = {}

    def _handle_move(self, event) -> None:
        """Handle unit movement.

        Args:
            event: Input event
        """
        unit = self.game_state.selected_unit
        if not unit or not unit.can_move:
            return

        target_tile = self.game_state.grid.get_tile(event.world_x, event.world_y)
        if not target_tile or target_tile.has_unit():
            return

        # Check if tile is reachable
        if target_tile not in self.movement_preview:
            return

        cost = self.movement_preview[target_tile]
        if self.game_state.move_unit(unit, event.world_x, event.world_y, cost):
            self._update_movement_preview()
            self.game_state.update_visibility(unit.owner)

    def _handle_attack(self, event) -> None:
        """Handle combat.

        Args:
            event: Input event
        """
        attacker = self.game_state.selected_unit
        target = event.data.get("target")

        if not attacker or not target or not attacker.can_attack:
            return

        # Check range
        distance = abs(attacker.x - target.x) + abs(attacker.y - target.y)
        if not attacker.can_attack_at_range(distance):
            return

        # Get tiles for combat
        attacker_tile = self.game_state.grid.get_tile(attacker.x, attacker.y)
        defender_tile = self.game_state.grid.get_tile(target.x, target.y)

        if not attacker_tile or not defender_tile:
            return

        # Resolve combat
        result = CombatSystem.resolve_combat(
            attacker, target, attacker_tile, defender_tile
        )

        # Remove dead units
        if result.defender_killed:
            self.game_state.remove_unit(target)

        if result.attacker_killed:
            self.game_state.remove_unit(attacker)
            self.game_state.selected_unit = None
            self.movement_preview = {}

        # Check for victory
        self.game_state.check_victory()

    def _cycle_unit(self) -> None:
        """Cycle to the next unit that can act."""
        player_units = self.game_state.get_units_for_civ(
            self.game_state.player_civ
        )

        # Filter to units that can still act
        actionable = [u for u in player_units if u.can_move or u.can_attack]
        if not actionable:
            return

        # Find next unit after current selection
        current = self.game_state.selected_unit
        if current in actionable:
            idx = actionable.index(current)
            next_unit = actionable[(idx + 1) % len(actionable)]
        else:
            next_unit = actionable[0]

        self.game_state.selected_unit = next_unit
        self._update_movement_preview()
        self.camera.center_on(next_unit.x, next_unit.y)

    def _update_movement_preview(self) -> None:
        """Update the movement preview for selected unit."""
        self.movement_preview = {}
        unit = self.game_state.selected_unit

        if not unit or not unit.can_move:
            return

        start_tile = self.game_state.grid.get_tile(unit.x, unit.y)
        if not start_tile:
            return

        self.movement_preview = get_reachable_tiles(
            self.game_state.grid,
            start_tile,
            unit.remaining_movement,
            unit
        )

    def _update(self) -> None:
        """Update game state."""
        # Handle continuous input (camera scrolling)
        self.input_handler.handle_continuous_input()

        # Check for victory
        if self.game_state.phase == GamePhase.GAME_OVER:
            pass  # Game over, could show victory screen

    def _render(self) -> None:
        """Render the game."""
        self.renderer.clear()

        # Get player's fog state
        fog_state = self.game_state.get_player_fog_state()

        # Render map
        self.renderer.render_grid(self.game_state.grid, self.camera, fog_state)

        # Render movement preview
        self._render_movement_preview()

        # Render cities (only visible ones)
        for city in self.game_state.get_all_cities():
            if fog_state.get((city.x, city.y)) == "VISIBLE":
                self.renderer.render_city(city, self.camera)

        # Render units (only visible ones)
        for unit in self.game_state.get_all_units():
            if fog_state.get((unit.x, unit.y)) == "VISIBLE":
                selected = unit == self.game_state.selected_unit
                self.renderer.render_unit(unit, self.camera, selected)

        # Render HUD
        player = self.game_state.player_civ
        self.renderer.render_hud(
            resources=player.resources,
            current_turn=self.game_state.current_turn,
            current_civ_name=player.name,
            selected_unit=self.game_state.selected_unit
        )

        # Render game over message
        if self.game_state.phase == GamePhase.GAME_OVER:
            self._render_game_over()

        pygame.display.flip()

    def _render_movement_preview(self) -> None:
        """Render movement preview overlay."""
        if not self.movement_preview:
            return

        for tile, cost in self.movement_preview.items():
            if tile.has_unit():
                continue

            screen_x, screen_y = self.camera.world_to_screen(tile.x, tile.y)
            from src.core.settings import TILE_SIZE

            # Semi-transparent overlay
            overlay = pygame.Surface((TILE_SIZE, TILE_SIZE))
            overlay.set_alpha(100)
            overlay.fill((0, 200, 0))  # Green tint for reachable
            self.screen.blit(overlay, (screen_x, screen_y))

    def _render_game_over(self) -> None:
        """Render game over screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(COLORS["BLACK"])
        self.screen.blit(overlay, (0, 0))

        # Victory message
        winner = self.game_state.winner
        if winner:
            if winner == self.game_state.player_civ:
                message = "VICTORY!"
                color = (0, 255, 0)
            else:
                message = f"DEFEAT! {winner.name} wins!"
                color = (255, 0, 0)

            self.renderer.render_text(
                message,
                WINDOW_WIDTH // 2,
                WINDOW_HEIGHT // 2,
                color=color,
                centered=True
            )

    def _end_turn(self) -> None:
        """End the current turn."""
        # Reset all player units
        for unit in self.game_state.get_units_for_civ(self.game_state.player_civ):
            unit.reset_turn()

        # Clear selection
        self.game_state.selected_unit = None
        self.movement_preview = {}

        # Process AI turns
        for civ in self.game_state.ai_civs:
            if not civ.is_eliminated:
                process_ai_turn(civ, self.game_state)
                self.game_state.update_visibility(civ)

        # Reset AI units and process city production
        for civ in self.game_state.ai_civs:
            for unit in self.game_state.get_units_for_civ(civ):
                unit.reset_turn()

        # Process cities (production, etc.)
        for city in self.game_state.get_all_cities():
            city.process_turn()

        # Update player visibility
        self.game_state.update_visibility(self.game_state.player_civ)

        # Increment turn
        self.game_state.current_turn += 1

        # Check victory
        self.game_state.check_victory()

        print(f"Turn {self.game_state.current_turn}")
