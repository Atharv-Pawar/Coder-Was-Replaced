"""
The Office: ties the tilemap and the player robot together into one
update/draw unit. Future phases will add interactable objects (coffee
machine, desks, bug spawns) here.
"""

from __future__ import annotations

import pygame

from engine import constants as c
from engine.camera import Camera
from engine.input import InputManager
from engine.renderer import Renderer
from engine.tilemap import TileMap, load_office_map
from game.player import Robot


class Office:
    def __init__(self):
        self.tile_map: TileMap = load_office_map()
        self.robot = Robot(grid_x=12, grid_y=5)

        self.camera = Camera(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
        self.camera.set_bounds(self.tile_map.pixel_width, self.tile_map.pixel_height)
        self.camera.snap_to(*self.robot.center_pixel_pos)

    def update(self, dt: float, input_manager: InputManager) -> None:
        direction = input_manager.movement_direction()
        if direction is not None:
            self.robot.try_move(direction[0], direction[1], self.tile_map)

        self.robot.update(dt)
        self.camera.update(dt, *self.robot.center_pixel_pos)

    def draw(self, renderer: Renderer) -> None:
        renderer.draw_tilemap(self.tile_map, self.camera)

        robot_x, robot_y = self.robot.world_pixel_pos
        renderer.draw_entity_rect(
            self.camera,
            robot_x + 2,
            robot_y + 2,
            size=c.TILE_SIZE - 4,
            color=c.COLOR_PLAYER,
            outline=c.COLOR_PLAYER_OUTLINE,
            facing=self.robot.facing,
        )
