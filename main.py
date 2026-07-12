"""Coder Was Replaced — entry point. Run with: python main.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.game import Game

if __name__ == "__main__":
    Game().run()
