# Civilization Game - Claude Code Instructions

## Project Overview

Turn-based 2D strategy game inspired by Sid Meier's Civilization, built with Python and Pygame.

## Quick Commands

```bash
# Run the game
uv run python main.py

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_combat_system.py -v
```

## Architecture

### Key Patterns

- **Dataclasses**: All entities (Unit, City, Civilization) use dataclasses with immutable stats and mutable state
- **ID-based storage**: Entities stored by UUID in GameState dicts, referenced by ID
- **Systems architecture**: Combat, tech, resources handled by dedicated system classes with static methods
- **Dual-layer AI**: Strategic (long-term) + Tactical (short-term) decision layers

### Directory Structure

- `src/core/` - Game loop, state management, settings
- `src/map/` - Grid, tiles, pathfinding, map generation
- `src/entities/` - Unit, City, Civilization classes
- `src/systems/` - Combat, tech tree, resource systems
- `src/ai/` - AI controller, tactics, strategies
- `src/data/` - Data definitions (unit stats, tech tree, resources)
- `src/ui/` - Renderer, camera, input handling

### Central State

`GameState` (dataclass in `src/core/game_state.py`) holds all game data:
- `grid`: Map tiles
- `units`: Dict of all units by ID
- `cities`: Dict of all cities by ID
- `civilizations`: List of all civs

## Code Conventions

- Use type hints throughout
- Use `TYPE_CHECKING` for imports that would cause circular dependencies
- Keep data definitions separate from logic (see `src/data/`)
- Static methods for pure calculations in system classes

## Testing Requirements

- All new features must have tests using real game data
- Use fixtures from `tests/conftest.py` for consistent test data
- Use fixed seeds for deterministic, reproducible results
- Run full test suite before committing: `uv run pytest`

### Test Fixtures Available

- `small_grid`, `medium_grid` - Pre-sized grids
- `generated_map` - Procedurally generated map with seed
- `starting_positions` - Valid spawn locations
- `sample_unit`, `sample_city` - Real entity instances

## Game Features

- 3 civilizations (1 human, 2 AI with personalities)
- 7 unit types (Warrior, Archer, Horseman, Spearman, Catapult, Swordsman, Knight)
- 12 technologies with prerequisites
- Fog of war with visibility tracking
- A* pathfinding with terrain costs
- Domination victory condition
