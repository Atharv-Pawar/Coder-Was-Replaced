"""
The Office: ties the tilemap, objects, and player robot together into
one update/draw unit.
"""

from __future__ import annotations

from engine import constants as c
from engine.camera import Camera
from engine.events import EventBus
from engine.input import InputManager
from engine.renderer import Renderer
from engine.tilemap import TileMap, load_office_map
from game.objects import GameObject, ObjectType, make_object
from game.player import Robot


class Office:
    def __init__(self):
        self.tile_map: TileMap = load_office_map()
        self.robot = Robot(grid_x=12, grid_y=5)
        self.objects: list[GameObject] = self._build_objects()

        self.camera = Camera(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
        self.camera.set_bounds(self.tile_map.pixel_width, self.tile_map.pixel_height)
        self.camera.snap_to(*self.robot.center_pixel_pos)

    # -- setup -----------------------------------------------------------
    def _build_objects(self) -> list[GameObject]:
        objects: list[GameObject] = []

        # Two rows of desks, mirroring the original tile layout but now as
        # real interactable furniture instead of baked-in solid tiles.
        for row_y in (2, 4, 12):
            for col_x in (2, 3, 4, 14, 15, 16):
                objects.append(make_object(ObjectType.DESK, col_x, row_y))

        # A couple of laptops sitting on specific desks.
        objects.append(make_object(ObjectType.LAPTOP, 2, 1))
        objects.append(make_object(ObjectType.LAPTOP, 14, 1))

        # Break room essentials.
        objects.append(make_object(ObjectType.COFFEE_MACHINE, 9, 6))

        # Bugs roaming the open floor -- pick a fight with one.
        objects.append(make_object(ObjectType.BUG, 7, 3))
        objects.append(make_object(ObjectType.BUG, 18, 3))

        # Jira board near the entrance.
        objects.append(make_object(ObjectType.JIRA_TICKET, 21, 2))

        # Infra corner.
        objects.append(make_object(ObjectType.SERVER_RACK, 23, 6))
        objects.append(make_object(ObjectType.WIFI_ROUTER, 23, 5))
        objects.append(make_object(ObjectType.GIT_REPO, 23, 7))

        # Meeting room doors (the rooms themselves are the wall rectangles
        # already in the tilemap; these mark the entrances as interactable).
        objects.append(make_object(ObjectType.MEETING_ROOM, 10, 7))
        objects.append(make_object(ObjectType.MEETING_ROOM, 20, 7))

        return objects

    # -- queries -----------------------------------------------------
    def object_at(self, grid_x: int, grid_y: int) -> GameObject | None:
        for obj in self.objects:
            if not obj.consumed and obj.grid_x == grid_x and obj.grid_y == grid_y:
                return obj
        return None

    def is_walkable(self, grid_x: int, grid_y: int) -> bool:
        if not self.tile_map.is_walkable(grid_x, grid_y):
            return False
        obj = self.object_at(grid_x, grid_y)
        if obj is not None and obj.is_solid:
            return False
        return True

    # -- update / interaction -----------------------------------------------
    def update(self, dt: float, input_manager: InputManager, event_bus: EventBus) -> None:
        direction = input_manager.movement_direction()
        if direction is not None:
            self.robot.try_move(direction[0], direction[1], self.is_walkable)

        if input_manager.interact_pressed():
            self._try_interact(event_bus)

        self.robot.update(dt)
        self.camera.update(dt, *self.robot.center_pixel_pos)

    def _try_interact(self, event_bus: EventBus) -> None:
        fx, fy = self.robot.facing_tile
        obj = self.object_at(fx, fy)
        if obj is not None and obj.is_interactable:
            obj.interact(self.robot, event_bus)

    def get_facing_object(self) -> GameObject | None:
        """The interactable object (if any) directly in front of the robot.
        Used to show the "[E] Interact" prompt.
        """
        fx, fy = self.robot.facing_tile
        obj = self.object_at(fx, fy)
        if obj is not None and obj.is_interactable:
            return obj
        return None

    # -- draw -----------------------------------------------------------
    def draw(self, renderer: Renderer) -> None:
        renderer.draw_tilemap(self.tile_map, self.camera)

        for obj in self.objects:
            renderer.draw_object(self.camera, obj)

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

        facing_obj = self.get_facing_object()
        if facing_obj is not None:
            renderer.draw_interaction_prompt(
                self.camera, facing_obj.grid_x, facing_obj.grid_y,
                f"[E] {facing_obj.display_name}",
            )
