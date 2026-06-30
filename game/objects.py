"""
Interactable office objects.

Each `GameObject` occupies a tile, optionally blocks movement, and
defines what happens when the player faces it and presses Interact.
Effects are intentionally simple flavor/stat changes for now (Phase 2);
once missions and economy exist (Phase 5-6), `on_interact` will also
report progress to those systems instead of just pushing a toast.

Rendering is still simple colored shapes (no sprite sheets yet) but each
object type now has a distinct silhouette so they're readable at a
glance even before real art lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable

from engine import constants as c


class ObjectType(Enum):
    DESK = auto()
    COFFEE_MACHINE = auto()
    BUG = auto()
    JIRA_TICKET = auto()
    SERVER_RACK = auto()
    GIT_REPO = auto()
    WIFI_ROUTER = auto()
    MEETING_ROOM = auto()
    LAPTOP = auto()


# Objects that physically block the robot from walking onto their tile.
SOLID_OBJECT_TYPES = {
    ObjectType.DESK,
    ObjectType.COFFEE_MACHINE,
    ObjectType.SERVER_RACK,
    ObjectType.GIT_REPO,
    ObjectType.WIFI_ROUTER,
    ObjectType.MEETING_ROOM,
}

# Short labels drawn on top of the object's icon (stand-in for sprite art).
OBJECT_LABELS = {
    ObjectType.DESK: "",
    ObjectType.COFFEE_MACHINE: "C",
    ObjectType.BUG: "!",
    ObjectType.JIRA_TICKET: "J",
    ObjectType.SERVER_RACK: "S",
    ObjectType.GIT_REPO: "git",
    ObjectType.WIFI_ROUTER: "WiFi",
    ObjectType.MEETING_ROOM: "M",
    ObjectType.LAPTOP: "L",
}

OBJECT_DISPLAY_NAMES = {
    ObjectType.DESK: "Desk",
    ObjectType.COFFEE_MACHINE: "Coffee Machine",
    ObjectType.BUG: "Bug",
    ObjectType.JIRA_TICKET: "Jira Ticket",
    ObjectType.SERVER_RACK: "Server Rack",
    ObjectType.GIT_REPO: "Git Repository",
    ObjectType.WIFI_ROUTER: "WiFi Router",
    ObjectType.MEETING_ROOM: "Meeting Room",
    ObjectType.LAPTOP: "Laptop",
}


@dataclass
class GameObject:
    obj_type: ObjectType
    grid_x: int
    grid_y: int
    consumed: bool = False  # e.g. a fixed bug disappears
    # on_interact(robot, event_bus) -> None. Set by factory functions below.
    on_interact: Callable | None = field(default=None, repr=False)

    @property
    def is_solid(self) -> bool:
        return not self.consumed and self.obj_type in SOLID_OBJECT_TYPES

    @property
    def is_interactable(self) -> bool:
        return not self.consumed and self.on_interact is not None

    @property
    def display_name(self) -> str:
        return OBJECT_DISPLAY_NAMES.get(self.obj_type, self.obj_type.name.title())

    def interact(self, robot, event_bus) -> None:
        if self.is_interactable:
            self.on_interact(self, robot, event_bus)


# -- interaction behaviors -------------------------------------------------
# Kept as plain functions (rather than methods per subclass) so new object
# types can be added in `data/items.json`-driven content later without
# needing a new Python class for each one.

def _interact_coffee(obj: GameObject, robot, event_bus) -> None:
    before = robot.energy
    robot.energy = min(c.PLAYER_MAX_ENERGY, robot.energy + c.COFFEE_ENERGY_RESTORE)
    gained = robot.energy - before
    event_bus.notify(f"+{gained:.0f} energy (coffee)")


def _interact_bug(obj: GameObject, robot, event_bus) -> None:
    obj.consumed = True
    event_bus.notify("Bug fixed!")


def _interact_jira(obj: GameObject, robot, event_bus) -> None:
    event_bus.notify("Ticket reviewed")


def _interact_server(obj: GameObject, robot, event_bus) -> None:
    event_bus.notify("Server status: nominal")


def _interact_git(obj: GameObject, robot, event_bus) -> None:
    event_bus.notify("Committed (preview)")


def _interact_router(obj: GameObject, robot, event_bus) -> None:
    event_bus.notify("Network: connected")


def _interact_meeting_room(obj: GameObject, robot, event_bus) -> None:
    event_bus.notify("This meeting could've been an email")


def _interact_desk(obj: GameObject, robot, event_bus) -> None:
    event_bus.notify("Just a desk.")


def _interact_laptop(obj: GameObject, robot, event_bus) -> None:
    event_bus.notify("Script editor coming in Phase 3")


_INTERACTIONS: dict[ObjectType, Callable] = {
    ObjectType.COFFEE_MACHINE: _interact_coffee,
    ObjectType.BUG: _interact_bug,
    ObjectType.JIRA_TICKET: _interact_jira,
    ObjectType.SERVER_RACK: _interact_server,
    ObjectType.GIT_REPO: _interact_git,
    ObjectType.WIFI_ROUTER: _interact_router,
    ObjectType.MEETING_ROOM: _interact_meeting_room,
    ObjectType.DESK: _interact_desk,
    ObjectType.LAPTOP: _interact_laptop,
}


def make_object(obj_type: ObjectType, grid_x: int, grid_y: int) -> GameObject:
    """Factory: builds a GameObject with the correct interaction wired up."""
    return GameObject(
        obj_type=obj_type,
        grid_x=grid_x,
        grid_y=grid_y,
        on_interact=_INTERACTIONS.get(obj_type),
    )
