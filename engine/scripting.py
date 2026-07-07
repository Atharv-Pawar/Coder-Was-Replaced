"""
Scripting engine for Phase 3.

Architecture overview
---------------------
The player writes Python that calls engine API functions (move(), look(),
fix_bug(), ...). We execute that code in a *background thread* so it can
block naturally between steps without freezing the UI.

Thread synchronisation model:
  Script thread                     Main thread
  ─────────────                     ───────────
  calls move()
    posts ('move',) to _cmd slot
    sets _cmd_ready
    blocks on _cmd_done  ──────►  update() sees _cmd_ready
                                   starts robot animation
                                   waits (across frames) for anim done
                         ◄──────  sets _cmd_done
  unblocks, continues...

This means only ONE command is ever in-flight at a time. The main thread
owns all mutable game state; the script thread only sends messages and
waits. Thread-safe by construction.

Line highlighting
-----------------
sys.settrace() is used inside the script thread to track the currently
executing source line, enabling the editor to highlight it in real time.
"""

from __future__ import annotations

import re
import sys
import threading
import traceback
from typing import Any, Callable

from engine import constants as c


# ---------------------------------------------------------------------------
# Public constants exposed inside player scripts
# ---------------------------------------------------------------------------
EMPTY = "EMPTY"
WALL = "WALL"
BUG = "BUG"
COFFEE = "COFFEE"
DESK = "DESK"
SERVER = "SERVER"
JIRA = "JIRA"
GIT = "GIT"
WIFI = "WIFI"
MEETING = "MEETING"
LAPTOP = "LAPTOP"

# Map game ObjectType → script constant string
from game.objects import ObjectType as _OT
_OBJ_TO_CONST: dict[_OT, str] = {
    _OT.BUG: BUG,
    _OT.COFFEE_MACHINE: COFFEE,
    _OT.DESK: DESK,
    _OT.SERVER_RACK: SERVER,
    _OT.JIRA_TICKET: JIRA,
    _OT.GIT_REPO: GIT,
    _OT.WIFI_ROUTER: WIFI,
    _OT.MEETING_ROOM: MEETING,
    _OT.LAPTOP: LAPTOP,
}

# Import XP award amounts from progression (single source of truth)
from game.progression import (
    XP_FIX_BUG, XP_COFFEE, XP_COMMIT, XP_DEPLOY,
    XP_RUN_TESTS, XP_ANSWER_EMAIL, XP_REFACTOR,
)
# Import economy award dicts
from game.economy import (
    AWARD_FIX_BUG, AWARD_COFFEE, AWARD_COMMIT, AWARD_DEPLOY,
    AWARD_RUN_TESTS, AWARD_ANSWER_EMAIL, AWARD_REFACTOR,
)

# Facing rotation tables (screen-space, y increases downward)
_TURN_RIGHT = {
    (0, -1): (1, 0),   # UP    → RIGHT
    (1,  0): (0, 1),   # RIGHT → DOWN
    (0,  1): (-1, 0),  # DOWN  → LEFT
    (-1, 0): (0, -1),  # LEFT  → UP
}
_TURN_LEFT = {
    (0, -1): (-1, 0),  # UP    → LEFT
    (-1, 0): (0, 1),   # LEFT  → DOWN
    (0,  1): (1, 0),   # DOWN  → RIGHT
    (1,  0): (0, -1),  # RIGHT → UP
}


class ScriptStopped(BaseException):
    """Raised inside the script thread when the player clicks Stop."""


class ScriptEngine:
    """Manages script execution, threading, and per-step robot control."""

    def __init__(self, office, event_bus, progression=None, economy=None):
        self._office = office
        self._robot = office.robot
        self._event_bus = event_bus
        self._progression = progression   # may be None in tests
        self._economy = economy           # may be None in tests

        # --- inter-thread communication -----------------------------------
        # Slot for one pending command from script → main thread.
        self._pending_cmd: tuple | None = None
        self._cmd_ready = threading.Event()   # script signals: command ready
        self._cmd_done = threading.Event()    # main signals: result ready
        self._stop_flag = threading.Event()   # main signals: stop requested

        # For look(): main thread writes the result here before setting _cmd_done.
        self._look_result: str = EMPTY

        # --- state visible to the editor ----------------------------------
        self.is_running: bool = False
        self.current_line: int = -1   # 0-indexed source line being executed
        self.error: str | None = None
        self.error_line: int = -1

        # --- animation tracking (main thread only) ------------------------
        self._waiting_anim: bool = False      # waiting for move animation to finish
        self._turn_timer: float = 0.0         # brief pause after a turn
        self._step_delay: float = c.SCRIPT_STEP_DELAY_DEFAULT
        self._delay_timer: float = 0.0        # extra delay after each step

        self._thread: threading.Thread | None = None

    # -----------------------------------------------------------------------
    # Public API (called from main thread)
    # -----------------------------------------------------------------------
    def run(self, code: str) -> None:
        """Compile and start executing `code`. Stops any running script first."""
        self.stop()
        self.error = None
        self.error_line = -1
        self.current_line = -1
        self._stop_flag.clear()
        self._cmd_ready.clear()
        self._cmd_done.clear()
        self._waiting_anim = False
        self._turn_timer = 0.0

        # Compile first so syntax errors are caught before launching a thread.
        try:
            code_obj = compile(code, "<script>", "exec")
        except SyntaxError as exc:
            self.error = f"SyntaxError: {exc.msg} (line {exc.lineno})"
            self.error_line = (exc.lineno or 1) - 1
            return

        self.is_running = True
        self._thread = threading.Thread(
            target=self._thread_worker, args=(code_obj,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        if not self.is_running:
            return
        self._stop_flag.set()
        # Unblock the script thread if it's waiting on _cmd_done.
        self._cmd_done.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
        self.is_running = False
        self.current_line = -1

    def update(self, dt: float) -> None:
        """Called once per frame by the main game loop."""
        if not self.is_running:
            return

        self._apply_upgrade_effects()

        # --- phase 1: brief turn display pause ----------------------------
        if self._turn_timer > 0:
            self._turn_timer -= dt
            if self._turn_timer <= 0:
                self._turn_timer = 0.0
                self._finish_step()
            return

        # --- phase 2: wait for move animation to complete -----------------
        if self._waiting_anim:
            if not self._robot.is_moving:
                self._waiting_anim = False
                self._delay_timer = self._step_delay
                if self._delay_timer <= 0:
                    self._finish_step()
            return

        # --- phase 3: optional extra delay between steps ------------------
        if self._delay_timer > 0:
            self._delay_timer -= dt
            if self._delay_timer <= 0:
                self._delay_timer = 0.0
                self._finish_step()
            return

        # --- phase 4: pick up the next command from the script thread -----
        if self._cmd_ready.is_set():
            self._cmd_ready.clear()
            cmd = self._pending_cmd
            self._pending_cmd = None
            self._dispatch(cmd)

    def set_step_delay(self, seconds: float) -> None:
        self._step_delay = max(0.0, seconds)

    # -----------------------------------------------------------------------
    # Internal: main-thread command dispatch
    # -----------------------------------------------------------------------
    def _check_locked(self, fn_name: str) -> bool:
        """Return True and set error if `fn_name` is locked. False = OK."""
        if self._progression is None:
            return False
        if not self._progression.is_unlocked(fn_name):
            self.error = self._progression.unlock_error_msg(fn_name)
            self.error_line = self.current_line
            self.is_running = False
            # Unblock the waiting script thread so it can die cleanly.
            self._cmd_done.set()
            self._stop_flag.set()
            return True
        return False

    def _award_xp(self, amount: int) -> None:
        if self._progression is not None:
            self._progression.add_xp(amount, self._event_bus)

    def _award_economy(self, **currencies) -> None:
        if self._economy is not None:
            self._economy.award(self._event_bus, **currencies)

    def _apply_upgrade_effects(self) -> None:
        """Sync economy upgrade effects to game state each frame."""
        if self._economy is None:
            return
        self._robot.move_duration = (
            c.PLAYER_MOVE_DURATION * self._economy.move_duration_multiplier()
        )

    def _dispatch(self, cmd: tuple) -> None:
        name = cmd[0]

        if name == "move":
            if self._check_locked("move"):
                return
            dx, dy = self._robot.facing
            moved = self._robot.try_move(dx, dy, self._office.is_walkable)
            if moved:
                self._waiting_anim = True
                if self._progression is not None:
                    self._progression.count_move(self._event_bus)
            else:
                self._finish_step()

        elif name == "turn_left":
            if self._check_locked("turn_left"):
                return
            self._robot.facing = _TURN_LEFT[self._robot.facing]
            self._turn_timer = c.SCRIPT_TURN_DISPLAY_TIME

        elif name == "turn_right":
            if self._check_locked("turn_right"):
                return
            self._robot.facing = _TURN_RIGHT[self._robot.facing]
            self._turn_timer = c.SCRIPT_TURN_DISPLAY_TIME

        elif name == "look":
            if self._check_locked("look"):
                return
            look_range = self._economy.look_range() if self._economy else 1
            result = EMPTY
            for dist in range(1, look_range + 1):
                fx = self._robot.grid_x + self._robot.facing[0] * dist
                fy = self._robot.grid_y + self._robot.facing[1] * dist
                if not self._office.tile_map.is_walkable(fx, fy):
                    result = WALL
                    break
                obj = self._office.object_at(fx, fy)
                if obj is not None:
                    result = _OBJ_TO_CONST.get(obj.obj_type, EMPTY)
                    break
            self._look_result = result
            self._finish_step()

        elif name == "fix_bug":
            if self._check_locked("fix_bug"):
                return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj is not None and obj.obj_type == _OT.BUG and not obj.consumed:
                obj.interact(self._robot, self._event_bus)
                self._award_xp(XP_FIX_BUG)
                self._award_economy(**AWARD_FIX_BUG)
            self._finish_step()

        elif name == "drink_coffee":
            if self._check_locked("drink_coffee"):
                return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj is not None and obj.obj_type == _OT.COFFEE_MACHINE:
                restore = (self._economy.coffee_energy_restore()
                           if self._economy else c.COFFEE_ENERGY_RESTORE)
                before = self._robot.energy
                self._robot.energy = min(c.PLAYER_MAX_ENERGY, self._robot.energy + restore)
                gained = self._robot.energy - before
                self._event_bus.notify(f"+{gained:.0f} energy (coffee)")
                self._award_xp(XP_COFFEE)
                self._award_economy(**AWARD_COFFEE)
            self._finish_step()

        elif name == "commit":
            if self._check_locked("commit"):
                return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj is not None and obj.obj_type == _OT.GIT_REPO:
                obj.interact(self._robot, self._event_bus)
                self._award_xp(XP_COMMIT)
                self._award_economy(**AWARD_COMMIT)
            self._finish_step()

        elif name == "deploy":
            if self._check_locked("deploy"):
                return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj is not None and obj.obj_type == _OT.SERVER_RACK:
                obj.interact(self._robot, self._event_bus)
                self._award_xp(XP_DEPLOY)
                self._award_economy(**AWARD_DEPLOY)
            self._finish_step()

        elif name == "run_tests":
            if self._check_locked("run_tests"):
                return
            self._event_bus.notify("Tests: all passing")
            self._award_xp(XP_RUN_TESTS)
            self._award_economy(**AWARD_RUN_TESTS)
            self._finish_step()

        elif name == "answer_email":
            if self._check_locked("answer_email"):
                return
            self._event_bus.notify("Email answered")
            self._award_xp(XP_ANSWER_EMAIL)
            self._award_economy(**AWARD_ANSWER_EMAIL)
            self._finish_step()

        elif name == "refactor":
            if self._check_locked("refactor"):
                return
            self._event_bus.notify("Code refactored")
            self._award_xp(XP_REFACTOR)
            self._award_economy(**AWARD_REFACTOR)
            self._finish_step()

        else:
            self._finish_step()

    def _finish_step(self) -> None:
        """Signal the script thread that it can proceed to the next command."""
        self._cmd_done.set()

    # -----------------------------------------------------------------------
    # Internal: script thread
    # -----------------------------------------------------------------------
    def _thread_worker(self, code_obj) -> None:
        sandbox = self._build_sandbox()
        try:
            sys.settrace(self._tracer)
            exec(code_obj, sandbox)
        except ScriptStopped:
            pass
        except Exception as exc:
            tb = traceback.extract_tb(exc.__traceback__)
            # Find the first frame that's our script ("<script>")
            script_lineno = -1
            for frame in tb:
                if frame.filename == "<script>":
                    script_lineno = frame.lineno - 1
            self.error = f"{type(exc).__name__}: {exc}"
            self.error_line = script_lineno
        finally:
            sys.settrace(None)
            self.is_running = False
            self.current_line = -1

    def _tracer(self, frame, event, arg):
        """sys.settrace callback: tracks current source line for the editor."""
        if event == "line" and frame.f_code.co_filename == "<script>":
            self.current_line = frame.f_lineno - 1  # 0-indexed
            if self._stop_flag.is_set():
                raise ScriptStopped()
        return self._tracer

    # -----------------------------------------------------------------------
    # Script-thread API functions (called from inside exec'd player code)
    # -----------------------------------------------------------------------
    def _post_cmd(self, cmd: tuple) -> None:
        """Post a command to the main thread and block until it's done."""
        if self._stop_flag.is_set():
            raise ScriptStopped()
        self._cmd_done.clear()
        self._pending_cmd = cmd
        self._cmd_ready.set()
        self._cmd_done.wait()
        if self._stop_flag.is_set():
            raise ScriptStopped()

    def _api_move(self) -> None:
        self._post_cmd(("move",))

    def _api_turn_left(self) -> None:
        self._post_cmd(("turn_left",))

    def _api_turn_right(self) -> None:
        self._post_cmd(("turn_right",))

    def _api_look(self) -> str:
        self._post_cmd(("look",))
        return self._look_result

    def _api_fix_bug(self) -> None:
        self._post_cmd(("fix_bug",))

    def _api_drink_coffee(self) -> None:
        self._post_cmd(("drink_coffee",))

    def _api_commit(self) -> None:
        self._post_cmd(("commit",))

    def _api_deploy(self) -> None:
        self._post_cmd(("deploy",))

    def _api_run_tests(self) -> None:
        self._post_cmd(("run_tests",))

    def _api_answer_email(self) -> None:
        self._post_cmd(("answer_email",))

    def _api_refactor(self) -> None:
        self._post_cmd(("refactor",))

    # -----------------------------------------------------------------------
    # Sandbox construction
    # -----------------------------------------------------------------------
    def _build_sandbox(self) -> dict:
        safe_builtins = {
            "range": range, "len": len, "list": list, "tuple": tuple,
            "dict": dict, "set": set, "int": int, "float": float,
            "str": str, "bool": bool, "abs": abs, "min": min, "max": max,
            "print": print, "type": type, "enumerate": enumerate,
            "zip": zip, "reversed": reversed, "sorted": sorted,
            "True": True, "False": False, "None": None,
        }
        return {
            "__builtins__": safe_builtins,
            # Movement
            "move": self._api_move,
            "turn_left": self._api_turn_left,
            "turn_right": self._api_turn_right,
            # Sensing
            "look": self._api_look,
            # Actions — unlockable
            "fix_bug": self._api_fix_bug,
            "drink_coffee": self._api_drink_coffee,
            "commit": self._api_commit,
            "deploy": self._api_deploy,
            "run_tests": self._api_run_tests,
            "answer_email": self._api_answer_email,
            "refactor": self._api_refactor,
            # World constants
            "EMPTY": EMPTY,
            "WALL": WALL,
            "BUG": BUG,
            "COFFEE": COFFEE,
            "DESK": DESK,
            "SERVER": SERVER,
            "JIRA": JIRA,
            "GIT": GIT,
            "WIFI": WIFI,
            "MEETING": MEETING,
            "LAPTOP": LAPTOP,
        }
