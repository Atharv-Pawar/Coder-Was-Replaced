"""
Thread-based Python scripting engine — Phases 3-6.

Script thread posts commands and blocks on _cmd_done.
Main thread dispatches, animates, then signals _cmd_done.
MissionTracker.on_action() called after every successful command.
"""
from __future__ import annotations
import sys, threading, traceback
from engine import constants as c

# ── World constants exposed in player scripts ─────────────────────────────────
EMPTY = "EMPTY"; WALL = "WALL"; BUG = "BUG"; COFFEE = "COFFEE"
DESK = "DESK"; SERVER = "SERVER"; JIRA = "JIRA"; GIT = "GIT"
WIFI = "WIFI"; MEETING = "MEETING"; LAPTOP = "LAPTOP"

from game.objects import ObjectType as _OT
_OBJ_TO_CONST = {
    _OT.BUG: BUG, _OT.COFFEE_MACHINE: COFFEE, _OT.DESK: DESK,
    _OT.SERVER_RACK: SERVER, _OT.JIRA_TICKET: JIRA, _OT.GIT_REPO: GIT,
    _OT.WIFI_ROUTER: WIFI, _OT.MEETING_ROOM: MEETING, _OT.LAPTOP: LAPTOP,
}

from game.progression import (XP_FIX_BUG, XP_COFFEE, XP_COMMIT, XP_DEPLOY,
                               XP_RUN_TESTS, XP_ANSWER_EMAIL, XP_REFACTOR)
from game.economy import (AWARD_FIX_BUG, AWARD_COFFEE, AWARD_COMMIT, AWARD_DEPLOY,
                          AWARD_RUN_TESTS, AWARD_ANSWER_EMAIL, AWARD_REFACTOR)

_TURN_RIGHT = {(0,-1):(1,0),(1,0):(0,1),(0,1):(-1,0),(-1,0):(0,-1)}
_TURN_LEFT  = {(0,-1):(-1,0),(-1,0):(0,1),(0,1):(1,0),(1,0):(0,-1)}


class ScriptStopped(BaseException):
    pass


class ScriptEngine:
    def __init__(self, office, event_bus, progression=None,
                 economy=None, mission_tracker=None):
        self._office          = office
        self._robot           = office.robot
        self._event_bus       = event_bus
        self._progression     = progression
        self._economy         = economy
        self._mission_tracker = mission_tracker

        self._pending_cmd   = None
        self._cmd_ready     = threading.Event()
        self._cmd_done      = threading.Event()
        self._stop_flag     = threading.Event()
        self._look_result   = EMPTY

        self.is_running    = False
        self.current_line  = -1
        self.error: str | None = None
        self.error_line    = -1

        self._waiting_anim = False
        self._turn_timer   = 0.0
        self._delay_timer  = 0.0
        self._step_delay   = c.SCRIPT_STEP_DELAY_DEFAULT
        self._thread: threading.Thread | None = None

    # ── Public API ───────────────────────────────────────────────────────────
    def run(self, code: str) -> None:
        self.stop()
        self.error = None; self.error_line = -1; self.current_line = -1
        self._stop_flag.clear(); self._cmd_ready.clear(); self._cmd_done.clear()
        self._waiting_anim = False; self._turn_timer = 0.0
        try:
            code_obj = compile(code, "<script>", "exec")
        except SyntaxError as e:
            self.error = f"SyntaxError: {e.msg} (line {e.lineno})"
            self.error_line = (e.lineno or 1) - 1
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._worker, args=(code_obj,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self.is_running:
            return
        self._stop_flag.set(); self._cmd_done.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        self.is_running = False; self.current_line = -1

    def set_step_delay(self, seconds: float) -> None:
        self._step_delay = max(0.0, seconds)

    def update(self, dt: float) -> None:
        if not self.is_running:
            return
        self._apply_upgrade_effects()

        if self._turn_timer > 0:
            self._turn_timer -= dt
            if self._turn_timer <= 0:
                self._turn_timer = 0.0; self._finish_step()
            return

        if self._waiting_anim:
            if not self._robot.is_moving:
                self._waiting_anim = False
                self._delay_timer = self._step_delay
                if self._delay_timer <= 0:
                    self._finish_step()
            return

        if self._delay_timer > 0:
            self._delay_timer -= dt
            if self._delay_timer <= 0:
                self._delay_timer = 0.0; self._finish_step()
            return

        if self._cmd_ready.is_set():
            self._cmd_ready.clear()
            cmd = self._pending_cmd; self._pending_cmd = None
            self._dispatch(cmd)

    # ── Internal: upgrade effects ─────────────────────────────────────────────
    def _apply_upgrade_effects(self) -> None:
        if self._economy:
            self._robot.move_duration = c.PLAYER_MOVE_DURATION * self._economy.move_duration_multiplier()

    # ── Internal: helpers ────────────────────────────────────────────────────
    def _check_locked(self, fn: str) -> bool:
        if self._progression and not self._progression.is_unlocked(fn):
            self.error      = self._progression.unlock_error_msg(fn)
            self.error_line = self.current_line
            self.is_running = False
            self._cmd_done.set(); self._stop_flag.set()
            return True
        return False

    def _award_xp(self, amount: int) -> None:
        if self._progression:
            self._progression.add_xp(amount, self._event_bus)

    def _award_economy(self, **kw) -> None:
        if self._economy:
            self._economy.award(self._event_bus, **kw)

    def _notify_mission(self, action: str) -> None:
        if self._mission_tracker:
            self._mission_tracker.on_action(action)

    def _finish_step(self) -> None:
        self._cmd_done.set()

    # ── Internal: dispatch ────────────────────────────────────────────────────
    def _dispatch(self, cmd: tuple) -> None:
        name = cmd[0]

        if name == "move":
            if self._check_locked("move"): return
            moved = self._robot.try_move(*self._robot.facing, self._office.is_walkable)
            if moved:
                self._waiting_anim = True
                if self._progression:
                    self._progression.count_move(self._event_bus)
                self._notify_mission("move")
            else:
                self._finish_step()

        elif name == "turn_left":
            if self._check_locked("turn_left"): return
            self._robot.facing = _TURN_LEFT[self._robot.facing]
            self._turn_timer = c.SCRIPT_TURN_DISPLAY_TIME

        elif name == "turn_right":
            if self._check_locked("turn_right"): return
            self._robot.facing = _TURN_RIGHT[self._robot.facing]
            self._turn_timer = c.SCRIPT_TURN_DISPLAY_TIME

        elif name == "look":
            if self._check_locked("look"): return
            look_range = self._economy.look_range() if self._economy else 1
            result = EMPTY
            for dist in range(1, look_range + 1):
                fx = self._robot.grid_x + self._robot.facing[0] * dist
                fy = self._robot.grid_y + self._robot.facing[1] * dist
                if not self._office.tile_map.is_walkable(fx, fy):
                    result = WALL; break
                obj = self._office.object_at(fx, fy)
                if obj is not None:
                    result = _OBJ_TO_CONST.get(obj.obj_type, EMPTY); break
            self._look_result = result
            self._finish_step()

        elif name == "fix_bug":
            if self._check_locked("fix_bug"): return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj and obj.obj_type == _OT.BUG and not obj.consumed:
                obj.interact(self._robot, self._event_bus)
                self._award_xp(XP_FIX_BUG)
                self._award_economy(**AWARD_FIX_BUG)
                self._notify_mission("fix_bug")
            self._finish_step()

        elif name == "drink_coffee":
            if self._check_locked("drink_coffee"): return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj and obj.obj_type == _OT.COFFEE_MACHINE:
                restore = self._economy.coffee_energy_restore() if self._economy else c.COFFEE_ENERGY_RESTORE
                gained = min(c.PLAYER_MAX_ENERGY - self._robot.energy, restore)
                self._robot.energy += gained
                self._event_bus.notify(f"+{gained:.0f} energy (coffee)")
                self._award_xp(XP_COFFEE)
                self._award_economy(**AWARD_COFFEE)
                self._notify_mission("drink_coffee")
            self._finish_step()

        elif name == "commit":
            if self._check_locked("commit"): return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj and obj.obj_type == _OT.GIT_REPO:
                obj.interact(self._robot, self._event_bus)
                self._award_xp(XP_COMMIT)
                self._award_economy(**AWARD_COMMIT)
                self._notify_mission("commit")
            self._finish_step()

        elif name == "deploy":
            if self._check_locked("deploy"): return
            fx, fy = self._robot.facing_tile
            obj = self._office.object_at(fx, fy)
            if obj and obj.obj_type == _OT.SERVER_RACK:
                obj.interact(self._robot, self._event_bus)
                self._award_xp(XP_DEPLOY)
                self._award_economy(**AWARD_DEPLOY)
                self._notify_mission("deploy")
            self._finish_step()

        elif name == "run_tests":
            if self._check_locked("run_tests"): return
            self._event_bus.notify("Tests: all passing")
            self._award_xp(XP_RUN_TESTS)
            self._award_economy(**AWARD_RUN_TESTS)
            self._notify_mission("run_tests")
            self._finish_step()

        elif name == "answer_email":
            if self._check_locked("answer_email"): return
            self._event_bus.notify("Email answered")
            self._award_xp(XP_ANSWER_EMAIL)
            self._award_economy(**AWARD_ANSWER_EMAIL)
            self._notify_mission("answer_email")
            self._finish_step()

        elif name == "refactor":
            if self._check_locked("refactor"): return
            self._event_bus.notify("Code refactored")
            self._award_xp(XP_REFACTOR)
            self._award_economy(**AWARD_REFACTOR)
            self._notify_mission("refactor")
            self._finish_step()

        else:
            self._finish_step()

    # ── Script thread ─────────────────────────────────────────────────────────
    def _worker(self, code_obj) -> None:
        sandbox = self._build_sandbox()
        try:
            sys.settrace(self._tracer)
            exec(code_obj, sandbox)
        except ScriptStopped:
            pass
        except Exception as exc:
            tb = traceback.extract_tb(exc.__traceback__)
            line = next((f.lineno-1 for f in tb if f.filename == "<script>"), -1)
            self.error = f"{type(exc).__name__}: {exc}"
            self.error_line = line
        finally:
            sys.settrace(None)
            self.is_running = False; self.current_line = -1

    def _tracer(self, frame, event, arg):
        if event == "line" and frame.f_code.co_filename == "<script>":
            self.current_line = frame.f_lineno - 1
            if self._stop_flag.is_set():
                raise ScriptStopped()
        return self._tracer

    def _post_cmd(self, cmd: tuple) -> None:
        if self._stop_flag.is_set(): raise ScriptStopped()
        self._cmd_done.clear()
        self._pending_cmd = cmd; self._cmd_ready.set()
        self._cmd_done.wait()
        if self._stop_flag.is_set(): raise ScriptStopped()

    # ── Sandbox API methods ───────────────────────────────────────────────────
    def _api_move(self):          self._post_cmd(("move",))
    def _api_turn_left(self):     self._post_cmd(("turn_left",))
    def _api_turn_right(self):    self._post_cmd(("turn_right",))
    def _api_look(self):          self._post_cmd(("look",)); return self._look_result
    def _api_fix_bug(self):       self._post_cmd(("fix_bug",))
    def _api_drink_coffee(self):  self._post_cmd(("drink_coffee",))
    def _api_commit(self):        self._post_cmd(("commit",))
    def _api_deploy(self):        self._post_cmd(("deploy",))
    def _api_run_tests(self):     self._post_cmd(("run_tests",))
    def _api_answer_email(self):  self._post_cmd(("answer_email",))
    def _api_refactor(self):      self._post_cmd(("refactor",))

    def _build_sandbox(self) -> dict:
        safe = {"range":range,"len":len,"list":list,"tuple":tuple,"dict":dict,
                "set":set,"int":int,"float":float,"str":str,"bool":bool,
                "abs":abs,"min":min,"max":max,"print":print,"type":type,
                "enumerate":enumerate,"zip":zip,"reversed":reversed,
                "sorted":sorted,"True":True,"False":False,"None":None}
        return {
            "__builtins__": safe,
            "move":move,"turn_left":self._api_turn_left,"turn_right":self._api_turn_right,
            "look":self._api_look,"fix_bug":self._api_fix_bug,
            "drink_coffee":self._api_drink_coffee,"commit":self._api_commit,
            "deploy":self._api_deploy,"run_tests":self._api_run_tests,
            "answer_email":self._api_answer_email,"refactor":self._api_refactor,
            "EMPTY":EMPTY,"WALL":WALL,"BUG":BUG,"COFFEE":COFFEE,"DESK":DESK,
            "SERVER":SERVER,"JIRA":JIRA,"GIT":GIT,"WIFI":WIFI,
            "MEETING":MEETING,"LAPTOP":LAPTOP,
        }

# Fix sandbox: move key should map to _api_move
def _make_sandbox(engine: ScriptEngine) -> dict:
    safe = {"range":range,"len":len,"list":list,"tuple":tuple,"dict":dict,
            "set":set,"int":int,"float":float,"str":str,"bool":bool,
            "abs":abs,"min":min,"max":max,"print":print,"type":type,
            "enumerate":enumerate,"zip":zip,"reversed":reversed,
            "sorted":sorted,"True":True,"False":False,"None":None}
    return {
        "__builtins__": safe,
        "move":engine._api_move,"turn_left":engine._api_turn_left,
        "turn_right":engine._api_turn_right,"look":engine._api_look,
        "fix_bug":engine._api_fix_bug,"drink_coffee":engine._api_drink_coffee,
        "commit":engine._api_commit,"deploy":engine._api_deploy,
        "run_tests":engine._api_run_tests,"answer_email":engine._api_answer_email,
        "refactor":engine._api_refactor,
        "EMPTY":EMPTY,"WALL":WALL,"BUG":BUG,"COFFEE":COFFEE,"DESK":DESK,
        "SERVER":SERVER,"JIRA":JIRA,"GIT":GIT,"WIFI":WIFI,
        "MEETING":MEETING,"LAPTOP":LAPTOP,
    }

# Patch _build_sandbox to use the correct helper
ScriptEngine._build_sandbox = lambda self: _make_sandbox(self)
