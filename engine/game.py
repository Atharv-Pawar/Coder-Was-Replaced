"""Main game loop — Phases 1-9 (Final)."""
from __future__ import annotations
import pygame
from engine import constants as c
from engine import sound_manager as sfx
from engine.achievements import AchievementSystem
from engine.events import EventBus
from engine.input import InputManager
from engine.renderer import Renderer
from engine.save_manager import SaveManager
from engine.scripting import ScriptEngine
from game.economy import Economy, SHOP_ITEMS
from game.editor import Editor
from game.employees import EmployeeManager, TIERS
from game.floor_manager import FloorManager
from game.missions import MissionTracker
from game.office import Office
from game.progression import Progression
from game.settings import Settings


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        pygame.key.start_text_input()

        self.settings  = Settings()
        sfx.init()                             # audio — graceful if numpy missing

        self.renderer  = Renderer()
        self._set_window_icon()
        self.input     = InputManager()
        self.clock     = pygame.time.Clock()
        self.events    = EventBus()

        self.office      = Office()
        self.progression = Progression()
        self.economy     = Economy()
        self.missions    = MissionTracker(self.progression, self.economy, self.events)
        self.employees   = EmployeeManager(
            self.office, self.events, self.progression, self.economy, self.missions)
        self.floors      = FloorManager(
            self.office, self.employees, self.events, self.progression)
        self.achievements = AchievementSystem(self.progression, self.economy, self.events)
        self.achievements.on_unlock = lambda aid: sfx.play("achievement",
                                                            self.settings.effective_sfx)
        self.editor      = Editor()
        self.script_engine = ScriptEngine(
            self.office, self.events,
            progression=self.progression,
            economy=self.economy,
            mission_tracker=self.missions,
            robot=self.office.robot,
        )
        self.saves   = SaveManager(self)
        self.saves.load()                      # restore previous session if any

        self._running      = False
        self._shop_open    = False
        self._hire_open    = False
        self._settings_open = False
        self._fps_samples: list[float] = []

        # Counters for detecting state changes → play sounds
        self._prev = dict(bugs=0, coffees=0, commits=0, deploys=0,
                          tests=0, emails=0, refactors=0,
                          missions=0, unlocks=len(self.progression.unlocked_functions),
                          floors=self.floors.current_floor,
                          salary_ticks=0,
                          shop_items=len(self.economy.upgrades),
                          hires=self.employees.count)

    # ── Window icon ───────────────────────────────────────────────────────────
    def _set_window_icon(self) -> None:
        icon = pygame.Surface((32, 32))
        icon.fill(c.COLOR_BG)
        pygame.draw.rect(icon, c.COLOR_PLAYER,
                         pygame.Rect(6, 7, 20, 18), border_radius=4)
        pygame.draw.rect(icon, c.COLOR_PLAYER_OUTLINE,
                         pygame.Rect(6, 7, 20, 18), width=2, border_radius=4)
        for ex, ey in [(10, 13), (18, 13)]:
            pygame.draw.rect(icon, c.COLOR_PLAYER_OUTLINE,
                             pygame.Rect(ex, ey, 4, 4))
        pygame.draw.rect(icon, c.COLOR_PLAYER_OUTLINE,
                         pygame.Rect(11, 20, 10, 3))
        pygame.display.set_icon(icon)

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self) -> None:
        self._running = True
        while self._running:
            dt = min(self.clock.tick(c.FPS) / 1000.0, 1 / 20)
            self._process_events()
            self._update(dt)
            self._draw()
            if self.input.quit_requested:
                self.saves.save()
                self.script_engine.stop()
                self.employees.stop_all()
                self._running = False
        pygame.quit()

    # ── Events ────────────────────────────────────────────────────────────────
    def _process_events(self) -> None:
        self.input.begin_frame()
        for ev in pygame.event.get():
            if ev.type == pygame.VIDEORESIZE:
                self.renderer.handle_resize(ev.w, ev.h)
            self.input.process_event(ev)
            if not self._hire_open and not self._settings_open:
                action = self.editor.handle_event(ev, self.script_engine.is_running)
                if action == "run":
                    self.script_engine.run(self.editor.get_code())
                elif action == "stop":
                    self.script_engine.stop()
                # Volume keys active outside overlays too
                self._handle_volume_keys()

    def _handle_volume_keys(self) -> None:
        if self.input.was_pressed(pygame.K_z):
            self.settings.adjust_master(-0.05)
        if self.input.was_pressed(pygame.K_x):
            self.settings.adjust_master(+0.05)
        if self.input.was_pressed(pygame.K_c):
            self.settings.adjust_sfx(-0.05)
        if self.input.was_pressed(pygame.K_v):
            self.settings.adjust_sfx(+0.05)

    # ── Update ────────────────────────────────────────────────────────────────
    def _update(self, dt: float) -> None:
        # ── Overlay toggles ───────────────────────────────────────────────────
        if self.input.fullscreen_pressed():
            self.settings.fullscreen = not self.settings.fullscreen
            flags = pygame.FULLSCREEN if self.settings.fullscreen else pygame.RESIZABLE
            self.renderer.window = pygame.display.set_mode(
                (c.SCREEN_WIDTH, c.SCREEN_HEIGHT), flags)

        if self.input.settings_pressed() and not self._hire_open and not self._shop_open:
            self._settings_open = not self._settings_open
            if self._settings_open:
                self._hire_open = False; self._shop_open = False

        if self.input.save_pressed():
            self.saves.save()
            self.events.notify("Game saved!")

        if self.input.shop_toggle_pressed() and not self._settings_open:
            self._shop_open = not self._shop_open
            if self._shop_open: self._hire_open = False

        if self.input.hire_panel_pressed() and not self._settings_open:
            self._hire_open = not self._hire_open
            if self._hire_open: self._shop_open = False

        if self.input.advance_floor_pressed() and not self._settings_open:
            self.script_engine.stop()
            self.floors.advance()

        # ── Settings debug toggle ─────────────────────────────────────────────
        if self.input.was_pressed(pygame.K_F3):
            self.settings.show_debug = not self.settings.show_debug

        # ── Shop purchases ────────────────────────────────────────────────────
        if self._shop_open:
            idx = self.input.buy_item_index()
            if idx is not None and idx < len(SHOP_ITEMS):
                ok, msg = self.economy.buy(SHOP_ITEMS[idx].item_id, self.events)
                if ok:
                    sfx.play("buy", self.settings.effective_sfx)
                else:
                    self.events.notify(msg)
                    sfx.play("error", self.settings.effective_sfx)

        # ── Hire panel ────────────────────────────────────────────────────────
        if self._hire_open:
            idx = self.input.buy_item_index()
            if idx is not None and idx < len(TIERS):
                ok, msg = self.employees.hire(TIERS[idx].tier_id)
                if ok:
                    sfx.play("hire", self.settings.effective_sfx)
                else:
                    self.events.notify(msg); sfx.play("error", self.settings.effective_sfx)
            fire = self.input.fire_index_pressed()
            if fire is not None and fire < self.employees.count:
                name = self.employees.employees[fire].name
                self.employees.fire(fire)
                self.events.notify(f"Fired: {name}")

        # ── Robot + world ─────────────────────────────────────────────────────
        if not self.script_engine.is_running:
            self.office.update(dt, self.input, self.events)
        else:
            self.office.robot.update(dt)
            self.office.camera.update(dt, *self.office.robot.center_pixel_pos)

        # ── All systems ───────────────────────────────────────────────────────
        self.script_engine.update(dt)
        self.employees.update(dt)
        self.economy.update(dt, self.progression, self.events)
        self.missions.update(dt)
        self.floors.update(dt)
        self.events.update(dt)
        self.editor.update(dt, self.script_engine, self.progression)
        self.saves.update(dt)

        # ── Achievement stats ─────────────────────────────────────────────────
        at = self.missions.action_totals
        self.achievements.total_moves          = at.get("move", 0)
        self.achievements.bugs_fixed           = at.get("fix_bug", 0)
        self.achievements.coffees_drunk        = at.get("drink_coffee", 0)
        self.achievements.commits_made         = at.get("commit", 0)
        self.achievements.deploys_made         = at.get("deploy", 0)
        self.achievements.employees_hired      = self.employees.count
        self.achievements.employees_active     = self.employees.count
        self.achievements.max_floor            = self.floors.max_floor_reached
        self.achievements.timed_missions_done  = sum(
            1 for m in [self.missions.just_completed] if m and m.time_limit)
        self.achievements.total_salary_earned  = (self.economy.salary +
                                                   self.economy.total_spent)
        self.achievements.shop_upgrades_owned  = len(self.economy.upgrades)
        self.achievements.update(dt)

        # ── Sound triggers ────────────────────────────────────────────────────
        self._trigger_sounds()

        self._fps_samples.append(self.clock.get_fps())
        if len(self._fps_samples) > 30:
            self._fps_samples.pop(0)

    def _trigger_sounds(self) -> None:
        vol = self.settings.effective_sfx
        at  = self.missions.action_totals
        p   = self._prev

        def _chk(key, sound, at_key=None):
            cur = at.get(at_key or key, 0)
            if cur > p.get(key, 0):
                sfx.play(sound, vol)
            p[key] = cur

        _chk("bugs",     "fix_bug",      "fix_bug")
        _chk("coffees",  "coffee",       "drink_coffee")
        _chk("commits",  "commit",       "commit")
        _chk("deploys",  "deploy",       "deploy")
        _chk("tests",    "run_tests",    "run_tests")
        _chk("emails",   "answer_email", "answer_email")
        _chk("refactors","refactor",     "refactor")

        mc = self.missions.total_completed
        if mc > p.get("missions", 0):
            sfx.play("mission", vol)
        p["missions"] = mc

        fc = self.floors.current_floor
        if fc > p.get("floors", 0):
            sfx.play("floor", vol)
        p["floors"] = fc

        ul = len(self.progression.unlocked_functions)
        if ul > p.get("unlocks", 0):
            sfx.play("unlock", vol)
        p["unlocks"] = ul

        sh = len(self.economy.upgrades)
        if sh > p.get("shop_items", 0):
            sfx.play("buy", vol)
        p["shop_items"] = sh

        hi = self.employees.count
        if hi > p.get("hires", 0):
            sfx.play("hire", vol)
        p["hires"] = hi

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self) -> None:
        self.renderer.begin_frame()

        self.editor.draw(self.renderer.surface, self.script_engine,
                         self.progression, self.economy)
        self.office.draw(self.renderer, self.employees)

        self.renderer.draw_energy_bar(self.office.robot.energy_ratio)
        self.renderer.draw_level_hud(self.progression)
        self.renderer.draw_employee_hud(self.employees)
        self.renderer.draw_mission_hud(self.missions)
        self.renderer.draw_floor_hud(self.floors)
        self.renderer.draw_toasts(self.events.toasts)
        self.renderer.draw_achievement_popup(self.achievements)

        if self.settings.show_debug:
            self._draw_debug()

        # Full-screen overlays (order: transition → mission → settings → hire → shop)
        self.renderer.draw_floor_transition(self.floors)
        self.renderer.draw_mission_complete_overlay(self.missions)
        if self._settings_open:
            self.renderer.draw_settings_overlay(self.settings, self.saves)
        elif self._hire_open:
            self.renderer.draw_hire_panel(self.employees, self.economy, self.progression)
        elif self._shop_open:
            self.renderer.draw_shop_overlay(self.economy, self.progression)

        self.renderer.present()

    def _draw_debug(self) -> None:
        avg = sum(self._fps_samples) / len(self._fps_samples) if self._fps_samples else 0
        r, e, m, fl = self.office.robot, self.script_engine, self.missions, self.floors
        from game.procgen import get_config
        cfg = get_config(fl.current_floor)
        lines = [
            f"FPS: {avg:.1f}",
            f"Tile: ({r.grid_x},{r.grid_y})  Facing: {r.facing}",
            f"Energy: {r.energy:.0f}  Moving: {r.is_moving}",
            f"Script: {'running' if e.is_running else 'idle'}",
            f"XP: {self.progression.xp}  |  {self.progression.level.title}",
            f"$ {self.economy.salary}  Rep:{self.economy.reputation}  "
            f"Stars:{self.economy.git_stars}",
            f"Mission: {m.active.title if m.active else 'none'}  "
            f"Done:{m.total_completed}",
            f"Floor {fl.current_floor}: {cfg['width']}x{cfg['height']}  "
            f"Staff:{self.employees.count}  "
            f"Ach:{len(self.achievements.unlocked)}/{len(self.achievements.unlocked.__class__())+12}",
            f"Saved: {self.saves.last_save_str}",
            "F3:debug F5:run F6:stop TAB:shop H:hire N:next S:settings ESC:quit",
        ]
        self.renderer.draw_debug_overlay(lines, x_offset=c.GAME_VIEWPORT_X)
