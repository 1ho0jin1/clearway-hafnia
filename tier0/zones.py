"""Person triggers (plan C tier 0; docs/PRODUCT.md F5): a person's feet inside a camera's danger zone.

The change detector holds people back by design (a person standing still is not an obstruction), so a person on the
tracks needs a trigger of its own. A zone is a polygon in the camera's image (config/zones.json, the only per-camera
setting): a person's feet (the bottom centre of YOLO's box) inside it for dwell_s is reported as an *occupation*, which
the service gives the ledger like a change (same pieces, recurrences, questions); it is closed when nobody's feet have
been inside for clear_s. A detection missed for less than gap_s does not break an occupation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


@dataclass
class Zone:
    name: str
    polygon: list[tuple[float, float]]   # image coordinates as shares of width and height (0-1)
    dwell_s: float = 1.0                 # feet inside this long: reported
    gap_s: float = 0.6                   # a person not seen for less than this is still inside (a missed detection)
    clear_s: float = 2.0                 # nobody's feet inside this long: the occupation is closed
    note: str = ""


@dataclass
class Occupation:
    """Shaped like tier0.change.Change, so the service handles both alike."""
    id: int
    t_start: float                       # the first feet inside
    box: tuple[int, int, int, int]       # union of the boxes of the people inside, until reported (frame pixels)
    t_detect: float | None = None        # reported
    t_seen: float = 0.0                  # the last feet inside
    t_closed: float | None = None
    closed_by: str = ""
    area: float = 0.0


def load_zones(path: Path) -> dict[str, list[Zone]]:
    """{camera name: [Zone, ...]} from config/zones.json."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {cam: [Zone(**{**z, "polygon": [tuple(p) for p in z["polygon"]]}) for z in zones]
            for cam, zones in raw.items()}


def _union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


@dataclass
class ZoneWatch:
    zone: Zone
    first_id: int = 1_000_000            # occupation ids, apart from the change detector's
    cur: Occupation | None = None
    _n: int = 0
    _poly: np.ndarray | None = field(default=None, repr=False)
    _size: tuple[int, int] | None = None

    def inside(self, boxes, width: int, height: int) -> list[tuple[float, float, float, float]]:
        """The boxes whose feet (bottom centre) are inside the zone."""
        if self._size != (width, height):
            self._poly = np.array([(x * width, y * height) for x, y in self.zone.polygon], np.float32)
            self._size = (width, height)
        return [b for b in boxes
                if cv2.pointPolygonTest(self._poly, ((b[0] + b[2]) / 2, float(b[3])), False) >= 0]

    def update(self, t: float, boxes, width: int, height: int) -> tuple[list[Occupation], list[Occupation]]:
        """Person boxes (frame pixels) at time t. Returns (occupations reported now, occupations closed now)."""
        z, reported, closed = self.zone, [], []
        feet = self.inside(boxes, width, height)
        o = self.cur
        if feet:
            box = tuple(int(v) for v in feet[0])
            for b in feet[1:]:
                box = _union(box, tuple(int(v) for v in b))
            if o is not None and o.t_detect is None and t - o.t_seen > z.gap_s:
                o = self.cur = None                  # left before being reported: start again
            if o is None:
                self._n += 1
                o = self.cur = Occupation(self.first_id + self._n, t, box, t_seen=t)
            elif o.t_detect is None:
                o.box = _union(o.box, box)
            o.t_seen = t
            if o.t_detect is None and t - o.t_start >= z.dwell_s:
                o.t_detect = t
                o.area = round((o.box[2] - o.box[0]) * (o.box[3] - o.box[1]) / (width * height), 4)
                reported.append(o)
        elif o is not None:
            if o.t_detect is None and t - o.t_seen > z.gap_s:
                self.cur = None                      # gone before being reported
            elif o.t_detect is not None and t - o.t_seen >= z.clear_s:
                o.t_closed, o.closed_by = t, "zone_empty"
                closed.append(o)
                self.cur = None
        return reported, closed
