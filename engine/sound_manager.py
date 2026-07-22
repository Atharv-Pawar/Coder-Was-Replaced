"""
Sound manager — Phase 9.

Generates all sound effects procedurally using numpy + pygame.sndarray
so the game has real audio with zero external assets.
Degrades silently if numpy or the mixer are unavailable.
"""
from __future__ import annotations
import pygame

SAMPLE_RATE = 44100
_SOUNDS: dict[str, pygame.mixer.Sound] = {}
_AVAILABLE = False


def init() -> None:
    global _AVAILABLE
    try:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        import numpy as np
        _generate_all(np)
        _AVAILABLE = True
    except Exception:
        _AVAILABLE = False


def play(name: str, volume: float = 1.0) -> None:
    if not _AVAILABLE:
        return
    sound = _SOUNDS.get(name)
    if sound:
        sound.set_volume(max(0.0, min(1.0, volume)))
        sound.play()


# ── Waveform helpers ──────────────────────────────────────────────────────────

def _sine(np, freq: float, dur: float, vol: float = 0.28) -> "np.ndarray":
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), dtype=np.float32)
    w = np.sin(2 * np.pi * freq * t) * vol
    _fade(np, w)
    return w


def _sweep(np, f0: float, f1: float, dur: float, vol: float = 0.28) -> "np.ndarray":
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, dtype=np.float32)
    freqs = np.linspace(f0, f1, n, dtype=np.float32)
    phase = np.cumsum(2 * np.pi * freqs / SAMPLE_RATE)
    w = np.sin(phase) * vol
    _fade(np, w)
    return w


def _chord(np, freqs: list[float], dur: float, vol: float = 0.22) -> "np.ndarray":
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), dtype=np.float32)
    w = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs) * vol
    _fade(np, w)
    return w


def _sequence(np, parts: list) -> "np.ndarray":
    return np.concatenate(parts)


def _fade(np, w: "np.ndarray", ms: int = 20) -> None:
    n = min(int(SAMPLE_RATE * ms / 1000), len(w) // 2)
    if n > 0:
        w[:n]  *= np.linspace(0, 1, n, dtype=np.float32)
        w[-n:] *= np.linspace(1, 0, n, dtype=np.float32)


def _make(np, wave: "np.ndarray") -> pygame.mixer.Sound:
    s16 = (wave * 32767).astype(np.int16)
    stereo = np.stack([s16, s16], axis=-1)
    return pygame.sndarray.make_sound(stereo)


# ── Sound catalog ─────────────────────────────────────────────────────────────

def _generate_all(np) -> None:
    _SOUNDS["click"]        = _make(np, _sine(np, 900,  0.018, 0.15))
    _SOUNDS["fix_bug"]      = _make(np, _sweep(np, 520, 280,  0.14, 0.30))
    _SOUNDS["coffee"]       = _make(np, _sine(np, 200,  0.22, 0.25))
    _SOUNDS["commit"]       = _make(np, _chord(np, [440, 554, 659], 0.20))
    _SOUNDS["deploy"]       = _make(np, _sweep(np, 280, 880,  0.28, 0.28))
    _SOUNDS["run_tests"]    = _make(np, _chord(np, [523, 659], 0.16))
    _SOUNDS["answer_email"] = _make(np, _sine(np, 660,  0.12, 0.22))
    _SOUNDS["refactor"]     = _make(np, _chord(np, [330, 415, 523], 0.18))
    _SOUNDS["ping"]         = _make(np, _sine(np, 1040, 0.07, 0.20))
    _SOUNDS["unlock"]       = _make(np, _sequence(np, [
        _sine(np, 523, 0.10, 0.25),
        _sine(np, 659, 0.10, 0.25),
        _sine(np, 784, 0.16, 0.28),
    ]))
    _SOUNDS["mission"]      = _make(np, _sequence(np, [
        _chord(np, [523, 659, 784], 0.14, 0.26),
        _chord(np, [659, 784, 988], 0.14, 0.26),
        _chord(np, [784, 988, 1047], 0.22, 0.30),
    ]))
    _SOUNDS["achievement"]  = _make(np, _sequence(np, [
        _sine(np, 659,  0.10, 0.28),
        _sine(np, 784,  0.10, 0.28),
        _sine(np, 1047, 0.22, 0.32),
    ]))
    _SOUNDS["floor"]        = _make(np, _sweep(np, 220, 660, 0.40, 0.26))
    _SOUNDS["error"]        = _make(np, _sweep(np, 300, 180, 0.18, 0.28))
    _SOUNDS["hire"]         = _make(np, _chord(np, [440, 523], 0.18, 0.24))
    _SOUNDS["buy"]          = _make(np, _sequence(np, [
        _sine(np, 523, 0.08, 0.22),
        _sine(np, 784, 0.12, 0.26),
    ]))
