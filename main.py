"""
Coder Was Replaced - entry point.

Run with:
    python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when running `python main.py`
# directly from inside the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.game import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
