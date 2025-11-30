# Civilization

A turn-based strategy game inspired by Sid Meier's Civilization, built with Python and Pygame.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Pygame](https://img.shields.io/badge/pygame-2.5+-green.svg)

## Features

- **Procedurally Generated Maps** - Each game creates a unique 40x30 tile world with varied terrain (grass, forests, mountains, water, desert, hills)
- **3 Civilizations** - Play against 2 AI opponents with different personalities (Aggressive and Balanced)
- **7 Unit Types** - Build and command military units:
  - *Melee*: Warrior, Spearman, Horseman, Swordsman
  - *Ranged*: Archer, Catapult, Crossbowman
- **Tech Tree** - Research 12 technologies to unlock new units and bonuses
- **Combat System** - Terrain defense bonuses, counterattacks, and health-based damage modifiers
- **Fog of War** - Explore the map with limited unit vision
- **City Production** - Build units from your capital city
- **Domination Victory** - Eliminate all enemy civilizations to win

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ethan-Otto/Civilization.git
   cd Civilization
   ```

2. Install dependencies with uv:
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install pygame
   ```

### Running the Game

With uv:
```bash
uv run python main.py
```

Or directly:
```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Move camera |
| Left Click | Select unit |
| Right Click | Move selected unit / Attack enemy |
| Space / Enter | End turn |
| Tab | Cycle through units |
| Escape | Quit game |

## Gameplay Tips

- **Green tiles** show where your selected unit can move
- Units with **"M"** are melee (attack adjacent tiles)
- Units with **"R"** are ranged (attack from distance)
- **Forests and hills** provide 25% defense bonus
- Damaged units deal less damage - retreat to heal!
- The AI will aggressively pursue weak units

## Project Structure

```
Civilization/
├── main.py              # Game entry point
├── pyproject.toml       # Project dependencies
├── src/
│   ├── core/            # Game loop, settings, state management
│   ├── map/             # Grid, tiles, pathfinding, map generation
│   ├── entities/        # Units, cities, civilizations
│   ├── systems/         # Combat, tech tree, resources
│   ├── ai/              # AI controller, tactics, strategies
│   └── ui/              # Renderer, camera, input handling
└── tests/               # Test suite (98 tests)
```

## Running Tests

```bash
uv run pytest
```

Or with verbose output:
```bash
uv run pytest -v
```

## Tech Tree

```
Agriculture ─────┬──► Archery ──────────┬──► Machinery ──► Crossbowman
                 │                      │
                 ├──► Animal Husbandry ─┴──► Horseback Riding ──► Horseman
                 │
Mining ──────────┼──► Bronze Working ──► Spearman
                 │          │
                 │          └──► Iron Working ──► Swordsman
                 │
                 └──► Masonry (City Walls)
                            │
                            └──► Engineering ──► Catapult
```

## Contributing

Contributions are welcome! The codebase has full test coverage - please include tests for any new features.

## License

MIT License - feel free to use this project for learning or as a base for your own games.
