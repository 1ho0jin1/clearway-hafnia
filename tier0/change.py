"""Tier 0, plan C: notice that something changed and stayed changed, without knowing what it is.

Dual-rate background (after Porikli, Ivanov and Haga, "Robust abandoned object detection using dual foregrounds",
2008). A fast background follows the scene within about a second; a slow one remembers how it looked. A pixel that
differs from the slow background but not from the fast one is a *static change*: something arrived and stopped (a
bin tipped over, a scooter dropped, a truck halted, paint on a train) or something that was there left. Moving things
differ from both and are ignored. No object classes, no per-camera rules.

- Warm-up: both backgrounds start as the median of the first seconds, so things that move through the warm-up do not
  become ghosts (a car's starting place reported as a change once it drives off). Nothing is reported while warming up.
- A change that people stand in is held back until they have moved away (the caller passes a person detector): a
  person standing still is not an obstruction, the scooter they leave behind is. People in danger zones are a
  separate trigger.
- Changes covering much of the frame at once (light, fog, condensation) are not objects and are not reported. A jump
  of the whole scene (a camera moved) resets both backgrounds. A looped clip restarting is not a jump for a fixed
  camera: its objects simply return to their places, which closes the open changes.
- Each changed region is reported once while it lasts, with the time it started (the centre for Hafnia's window). It
  keeps a snapshot of how the spot looked before; it is closed when the spot looks like that again.
Thresholds apply to the working image (default 320 px wide); boxes are returned in input-frame pixels.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class ChangeParams:
    work_width: int = 320
    warmup_s: float = 10.0           # backgrounds start as the median of this much video; no reports meanwhile
    fast_tau_s: float = 0.5          # time constant of the fast background
    slow_tau_s: float = 600.0        # ... of the slow background (it learns only where nothing moves); minutes, as
                                     # usual for abandoned-object detection: a looped incident must not be learnt
    diff: float = 25.0               # per-pixel colour difference (max over channels, 0-255) that counts as different
    persist_s: float = 1.5           # a pixel must stay static-changed this long
    min_area: float = 0.005          # share of the frame: smaller blobs are noise
    max_area: float = 0.30           # larger single blobs are not objects
    global_area: float = 0.15        # this much of the frame static-changed at once: light, fog; report nothing
    global_diff: float = 0.30        # this much of the frame different from the slow background: the view itself
                                     # changed (fog, condensation, a lens problem); report nothing
    jump_frac: float = 0.6           # this share of pixels changing between two frames: the whole scene jumped
    merge_iou: float = 0.3           # a blob overlapping an open change this much is the same change
    restored_diff: float = 12.0      # mean difference to the "before" snapshot below which the spot is restored
    close_s: float = 1.0             # restored this long: closed
    person_cover: float = 0.5        # a blob this much inside a person's box is held until they leave

    @classmethod
    def loops(cls) -> "ChangeParams":
        """The organizers' synthetic clips: an incident's state lasts only 5-8 s before the clip restarts."""
        return cls()

    @classmethod
    def real(cls) -> "ChangeParams":
        """Real cameras: obstructions last minutes; small distant objects need the larger working image (test_11,
        2026-10-23: the crashed SUV, about 0.1% of the frame, was found after 43 s at 640 px and 0.15%, after 101 s
        at 320 px and 0.5%)."""
        return cls(work_width=640, min_area=0.0015, persist_s=15.0)


@dataclass
class Change:
    id: int
    t_detect: float                  # when it was reported
    t_start: float                   # when its pixels started being static-changed (window centre)
    box: tuple[int, int, int, int]   # x1, y1, x2, y2 in input-frame pixels
    area: float                      # share of the frame
    t_closed: float | None = None
    closed_by: str = ""              # "restored" or "scene_jump"


def _iou(a: tuple, b: tuple) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


@dataclass
class _Open:
    change: Change
    work_box: tuple[int, int, int, int]
    before: np.ndarray               # the slow background in the box when it was reported: the spot before
    restored_since: float | None = None


@dataclass
class ChangeDetector:
    p: ChangeParams = field(default_factory=ChangeParams)
    changes: list[Change] = field(default_factory=list)
    jumps: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.fast: np.ndarray | None = None
        self.slow: np.ndarray | None = None
        self.prev_gray: np.ndarray | None = None
        self.static_since: np.ndarray | None = None
        self.warm: list[np.ndarray] = []
        self.t0: float | None = None
        self.last_t: float | None = None
        self.scale = 1.0
        self.open: dict[int, _Open] = {}
        self._next_id = 1

    def _start(self, img: np.ndarray, gray: np.ndarray) -> None:
        self.fast = img.copy()
        self.slow = img.copy()
        self.prev_gray = gray
        self.static_since = np.full(img.shape[:2], np.nan, np.float32)
        self.static_time = np.zeros(img.shape[:2], np.float32)

    def update(self, t: float, frame: np.ndarray,
               people: Callable[[], list[tuple[float, float, float, float]]] | None = None) -> list[Change]:
        """Feed one frame (BGR) at time t (seconds). Returns the changes newly reported at this frame.
        `people`, if given, returns person boxes (input-frame pixels) for this frame; it is called only when a new
        change is about to be reported."""
        p = self.p
        h0, w0 = frame.shape[:2]
        self.scale = w0 / p.work_width
        small = cv2.resize(frame, (p.work_width, round(h0 / self.scale)), interpolation=cv2.INTER_AREA)
        img = cv2.GaussianBlur(small, (5, 5), 0).astype(np.float32)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if self.t0 is None:
            self.t0 = t
        if self.fast is None:                                  # warming up
            self.warm.append(img)
            if t - self.t0 >= p.warmup_s:
                self._start(np.median(np.stack(self.warm), axis=0).astype(np.float32), gray)
                self.warm = []
                self.last_t = t
            return []
        dt = max(1e-3, t - self.last_t)
        self.last_t = t
        if float((np.abs(gray - self.prev_gray) > 30).mean()) > p.jump_frac:   # the whole scene jumped
            self.jumps.append(t)
            for o in self.open.values():
                o.change.t_closed, o.change.closed_by = t, "scene_jump"
            self.open.clear()
            self._start(img, gray)
            return []
        self.prev_gray = gray

        fg_fast = np.abs(img - self.fast).max(axis=2) > p.diff
        fg_slow = np.abs(img - self.slow).max(axis=2) > p.diff
        self.fast += (1 - np.exp(-dt / p.fast_tau_s)) * (img - self.fast)
        self.slow += np.where(~fg_fast[..., None], (1 - np.exp(-dt / p.slow_tau_s)) * (img - self.slow), 0)

        static = fg_slow & ~fg_fast
        # Each pixel counts how long it has been static-changed. The count pauses while something moves across it (a
        # car passing in front of a stalled one) and restarts only when the spot looks as before again. A plain clock
        # either restarted with every passing car or, if left running, credited a walking person with time they never
        # stood still (2026-10-23).
        self.static_time[~fg_slow] = 0.0
        self.static_since[~fg_slow] = np.nan
        self.static_time[static] += dt
        self.static_since[static & np.isnan(self.static_since)] = t
        persistent = static & (self.static_time >= p.persist_s)
        frame_area = persistent.size
        if persistent.sum() > p.global_area * frame_area or fg_slow.mean() > p.global_diff:
            persistent[:] = False                           # light, fog, condensation: not an object

        reported = self._report(t, img, persistent, frame_area, people)
        self._close(t, img)
        return reported

    def _report(self, t, img, persistent, frame_area, people) -> list[Change]:
        p = self.p
        mask = cv2.morphologyEx(persistent.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        reported, person_boxes = [], None
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            if area < p.min_area * frame_area or area > p.max_area * frame_area:
                continue
            box = (int(x), int(y), int(x + w), int(y + h))
            if any(_iou(box, o.work_box) >= p.merge_iou for o in self.open.values()):
                continue
            blob = labels == i
            if people is not None:
                if person_boxes is None:
                    person_boxes = [tuple(v / self.scale for v in b) for b in people()]
                covered = np.zeros_like(blob)
                for bx1, by1, bx2, by2 in person_boxes:
                    covered[max(0, int(by1)):int(by2), max(0, int(bx1)):int(bx2)] = True
                if (blob & covered).sum() > p.person_cover * area:
                    continue   # someone stands in it: held until they have left, then reported if still there
            c = Change(self._next_id, t, float(np.nanmedian(self.static_since[blob])),
                       tuple(int(round(v * self.scale)) for v in box), round(area / frame_area, 4))
            self._next_id += 1
            self.open[c.id] = _Open(c, box, self.slow[box[1]:box[3], box[0]:box[2]].copy())
            self.changes.append(c)
            reported.append(c)
        return reported

    def _close(self, t: float, img: np.ndarray) -> None:
        """A change is closed when its spot has looked as it did before for close_s."""
        p = self.p
        for cid, o in list(self.open.items()):
            x1, y1, x2, y2 = o.work_box
            d = float(np.abs(img[y1:y2, x1:x2] - o.before).max(axis=2).mean())
            if d > p.restored_diff:
                o.restored_since = None
            elif o.restored_since is None:
                o.restored_since = t
            elif t - o.restored_since >= p.close_s:
                o.change.t_closed, o.change.closed_by = t, "restored"
                del self.open[cid]
