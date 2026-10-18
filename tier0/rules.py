"""Per-track features and candidate rules. Everything is normalized by box size, so the thresholds hold across camera
distances and resolutions: speed is in box diagonals per second.

Tuned for recall: tier 0 should catch every incident and let Hafnia (tier 1) reject false candidates.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

VEHICLES = {"car", "bus", "truck", "motorcycle", "bicycle"}
ROAD_USERS = VEHICLES | {"person"}


@dataclass
class Params:
    history_s: float = 3.0          # how much track history to keep
    smooth_n: int = 3               # median over this many speed samples
    moving: float = 0.5             # diagonals/s: "was moving"
    stopped: float = 0.15           # diagonals/s: "has stopped"
    decel_window_s: float = 1.0     # moving -> stopped within this time is a sharp deceleration
    decel_drop: float = 0.0         # also fire when speed falls by this share (e.g. 0.6) without fully stopping;
                                    # 0 disables. Crashing two-wheelers slide or tip over instead of stopping cleanly.
    contact_gap: float = 0.15       # boxes overlap, or the gap is under this share of the smaller diagonal
    upright: float = 1.3            # person box height / width when upright
    lying: float = 0.9              # ... when lying
    fall_window_s: float = 1.5      # upright -> lying within this time
    fall_hold_s: float = 0.8        # and stays lying this long
    merge_s: float = 3.0            # candidates closer than this on one camera are one incident


@dataclass
class Candidate:
    t: float
    kind: str                       # "collision" | "fall" | "sudden_stop"
    score: float
    tracks: tuple[int, ...]
    detail: str = ""


@dataclass
class Track:
    cls: str
    samples: deque = field(default_factory=deque)   # (t, x1, y1, x2, y2)

    def add(self, t: float, box: np.ndarray, keep_s: float) -> None:
        self.samples.append((t, *box))
        while self.samples and t - self.samples[0][0] > keep_s:
            self.samples.popleft()

    def box(self) -> np.ndarray:
        return np.array(self.samples[-1][1:])

    def speeds(self, n: int) -> list[tuple[float, float]]:
        """(t, speed in diagonals/s), median-smoothed over n samples."""
        s = list(self.samples)
        raw = []
        for (t0, *a), (t1, *b) in zip(s, s[1:]):
            a, b = np.array(a), np.array(b)
            ca, cb = (a[:2] + a[2:]) / 2, (b[:2] + b[2:]) / 2
            diag = np.hypot(*(b[2:] - b[:2])) or 1.0
            raw.append((t1, float(np.hypot(*(cb - ca)) / diag / max(t1 - t0, 1e-3))))
        return [(raw[i][0], float(np.median([v for _, v in raw[max(0, i - n + 1):i + 1]]))) for i in range(len(raw))]

    def aspects(self) -> list[tuple[float, float]]:
        return [(t, (y2 - y1) / max(x2 - x1, 1e-3)) for t, x1, y1, x2, y2 in self.samples]


def sharp_decel(track: Track, p: Params, allow_drop: bool = False) -> tuple[bool, float]:
    """Was moving, now stopped (or, with allow_drop, slowed by decel_drop), within decel_window_s.
    Returns (fired, peak speed before)."""
    sp = track.speeds(p.smooth_n)
    if len(sp) < 3:
        return False, 0.0
    t_now, v_now = sp[-1]
    before = [v for t, v in sp if t_now - p.decel_window_s <= t < t_now]
    peak = max(before, default=0.0)
    if peak < p.moving:
        return False, peak
    stopped = v_now <= p.stopped
    dropped = allow_drop and p.decel_drop > 0 and v_now <= (1 - p.decel_drop) * peak
    return stopped or dropped, peak


def gap(a: np.ndarray, b: np.ndarray) -> float:
    """Distance between two boxes as a share of the smaller diagonal; 0 when they overlap."""
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    small = min(np.hypot(a[2] - a[0], a[3] - a[1]), np.hypot(b[2] - b[0], b[3] - b[1])) or 1.0
    return float(np.hypot(dx, dy) / small)


class Detector:
    """Feed tracked boxes frame by frame; collect candidates."""

    def __init__(self, params: Params | None = None):
        self.p = params or Params()
        self.tracks: dict[int, Track] = {}
        self.candidates: list[Candidate] = []
        self._fired: dict[tuple, float] = {}

    def _emit(self, c: Candidate) -> None:
        key = (c.kind, c.tracks)
        if c.t - self._fired.get(key, -1e9) < self.p.merge_s:
            return
        self._fired[key] = c.t
        self.candidates.append(c)

    def update(self, t: float, ids: list[int], classes: list[str], boxes: np.ndarray) -> None:
        p = self.p
        seen = set()
        for tid, cls, box in zip(ids, classes, boxes):
            if cls not in ROAD_USERS:
                continue
            tr = self.tracks.setdefault(tid, Track(cls))
            tr.add(t, box, p.history_s)
            seen.add(tid)
        for tid in [k for k, tr in self.tracks.items() if t - tr.samples[-1][0] > p.history_s]:
            del self.tracks[tid]

        live = {k: self.tracks[k] for k in seen}
        decel = {k: sharp_decel(tr, p) for k, tr in live.items()}
        # Contact makes a collision plausible, so a partial drop in speed is enough there; on its own (sudden stop)
        # a partial drop is mostly detection jitter on normal traffic.
        slowed = {k: sharp_decel(tr, p, allow_drop=True) for k, tr in live.items()}

        # Collision: two road users in contact while at least one decelerates sharply.
        ids_live = sorted(live)
        for i, a in enumerate(ids_live):
            for b in ids_live[i + 1:]:
                ta, tb = live[a], live[b]
                if ta.cls == "person" and tb.cls == "person":
                    continue
                g = gap(ta.box(), tb.box())
                if g > p.contact_gap:
                    continue
                (fa, va), (fb, vb) = slowed[a], slowed[b]
                if fa or fb:
                    self._emit(Candidate(t, "collision", round(min(1.0, max(va, vb) / (2 * p.moving)) * (1 - g), 3),
                                         (a, b), f"{ta.cls}+{tb.cls}, gap {g:.2f}, peak speed {max(va, vb):.2f}"))

        # Fall: a person goes from upright to lying and stays down.
        for k, tr in live.items():
            if tr.cls != "person":
                continue
            asp = tr.aspects()
            if len(asp) < 4 or asp[-1][1] > p.lying:
                continue
            t_now = asp[-1][0]
            lying_since = t_now
            for ts, r in reversed(asp):
                if r > p.lying:
                    break
                lying_since = ts
            if t_now - lying_since < p.fall_hold_s:
                continue
            up = [r for ts, r in asp if lying_since - p.fall_window_s <= ts < lying_since]
            if up and max(up) >= p.upright:
                self._emit(Candidate(lying_since, "fall", round(min(1.0, max(up) / (2 * p.upright)), 3), (k,),
                                     f"aspect {max(up):.2f} -> {asp[-1][1]:.2f}"))

        # Sudden stop of a vehicle (no contact needed: breakdowns, near misses, collisions we did not see).
        for k, (fired, peak) in decel.items():
            if fired and live[k].cls in VEHICLES and peak >= 2 * p.moving:
                self._emit(Candidate(t, "sudden_stop", round(min(1.0, peak / (4 * p.moving)), 3), (k,),
                                     f"{live[k].cls}, peak speed {peak:.2f}"))


def merge(cands: list[Candidate], window_s: float) -> list[Candidate]:
    """One incident per cluster. A cluster is anchored at its first candidate (no chaining) and keeps that time: the
    first signal is the best centre for Hafnia's window. Score is the cluster's best; kinds are all kinds seen."""
    out: list[Candidate] = []
    for c in sorted(cands, key=lambda c: c.t):
        if out and c.t - out[-1].t <= window_s:
            first = out[-1]
            kinds = "+".join(sorted(set(first.kind.split("+")) | {c.kind}))
            best = c if c.score > first.score else first
            out[-1] = Candidate(first.t, kinds, best.score, best.tracks, best.detail)
        else:
            out.append(c)
    return out
