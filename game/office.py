"""The Office: tilemap, objects, robot, camera, and bug respawner."""
from __future__ import annotations
import random
from engine import constants as c
from engine.camera import Camera
from engine.events import EventBus
from engine.input import InputManager
from engine.renderer import Renderer
from engine.tilemap import TileMap
from game.objects import GameObject, ObjectType, make_object
from game.player import Robot


class Office:
    def __init__(self):
        # Use procedural generation for all floors (including floor 0)
        from game.procgen import generate
        tilemap, objects, spawn = generate(floor_num=0)

        self.tile_map: TileMap         = tilemap
        self.objects: list[GameObject] = objects
        self.robot = Robot(grid_x=spawn[0], grid_y=spawn[1])
        self.camera = Camera(
            viewport_width=c.GAME_VIEWPORT_W,
            viewport_height=c.GAME_VIEWPORT_H,
            viewport_x=c.GAME_VIEWPORT_X,
        )
        self.camera.set_bounds(self.tile_map.pixel_width, self.tile_map.pixel_height)
        self.camera.snap_to(*self.robot.center_pixel_pos)

        # Bug respawner
        self._respawn_timer: float = 0.0
        self._extra_robots: list[Robot] = []

    def load_generated(self, tilemap: TileMap, objects: list,
                        spawn: tuple[int, int]) -> None:
        """Hot-swap the office layout. Called by FloorManager on floor advance."""
        self.tile_map = tilemap
        self.objects  = list(objects)
        self.robot.grid_x, self.robot.grid_y = spawn
        self.robot.facing = (0, 1)
        self.robot._tween = None
        self._respawn_timer = 0.0
        self.camera.set_bounds(tilemap.pixel_width, tilemap.pixel_height)
        self.camera.snap_to(*self.robot.center_pixel_pos)

    def object_at(self, gx: int, gy: int) -> GameObject | None:
        for obj in self.objects:
            if not obj.consumed and obj.grid_x == gx and obj.grid_y == gy:
                return obj
        return None

    def is_walkable(self, gx: int, gy: int) -> bool:
        if not self.tile_map.is_walkable(gx, gy):
            return False
        obj = self.object_at(gx, gy)
        return obj is None or not obj.is_solid

    def get_facing_object(self) -> GameObject | None:
        fx, fy = self.robot.facing_tile
        obj = self.object_at(fx, fy)
        return obj if obj is not None and obj.is_interactable else None

    # ── Bug respawner ─────────────────────────────────────────────────────────
    def _bug_count(self) -> int:
        return sum(1 for o in self.objects
                   if o.obj_type == ObjectType.BUG and not o.consumed)

    def _spawn_bug(self) -> None:
        if self._bug_count() >= c.BUG_MAX_COUNT:
            return
        attempts = 0
        while attempts < 30:
            x = random.randint(1, self.tile_map.width - 2)
            y = random.randint(1, self.tile_map.height - 2)
            if (self.tile_map.is_walkable(x, y)
                    and self.object_at(x, y) is None
                    and (self.robot.grid_x, self.robot.grid_y) != (x, y)):
                self.objects.append(make_object(ObjectType.BUG, x, y))
                return
            attempts += 1

    # ── Update / draw ─────────────────────────────────────────────────────────
    def update(self, dt: float, input_manager: InputManager,
               event_bus: EventBus) -> None:
        direction = input_manager.movement_direction()
        if direction is not None:
            self.robot.try_move(direction[0], direction[1], self.is_walkable)
        if input_manager.interact_pressed():
            fx, fy = self.robot.facing_tile
            obj = self.object_at(fx, fy)
            if obj is not None and obj.is_interactable:
                obj.interact(self.robot, event_bus)
        self.robot.update(dt)
        self.camera.update(dt, *self.robot.center_pixel_pos)

        # Respawn bugs
        self._respawn_timer += dt
        if self._respawn_timer >= c.BUG_RESPAWN_INTERVAL:
            self._respawn_timer = 0.0
            self._spawn_bug()

    def draw(self, renderer: Renderer, employee_manager=None) -> None:
        renderer.begin_world_draw()
        renderer.draw_tilemap(self.tile_map, self.camera)
        for obj in self.objects:
            renderer.draw_object(self.camera, obj)

        # Draw employees before player so player appears on top
        if employee_manager is not None:
            renderer.draw_employees(employee_manager, self.camera)

        # Player robot
        rx, ry = self.robot.world_pixel_pos
        renderer.draw_entity_rect(
            self.camera, rx + 2, ry + 2,
            size=c.TILE_SIZE - 4,
            color=c.COLOR_PLAYER, outline=c.COLOR_PLAYER_OUTLINE,
            facing=self.robot.facing,
        )

        fo = self.get_facing_object()
        if fo is not None:
            renderer.draw_interaction_prompt(
                self.camera, fo.grid_x, fo.grid_y, f"[E] {fo.display_name}")
        renderer.end_world_draw()
