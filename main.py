#!/usr/bin/env python3
"""Entry point for the Civilization game."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.game import Game


def main():
    """Main entry point."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
