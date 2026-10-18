"""Router: decides which tier 0 candidates are worth a Hafnia request.

Every request costs 1 of 500 a day, and looped test cameras repeat the same scene every few seconds, so:
- cooldown: after asking about a camera, wait before asking about it again;
- open incident: after Hafnia confirms an accident on a camera, hold further requests there (one incident, one alarm);
- learned trust (v0): when Hafnia rejects a candidate, remember where in the image it was and suppress candidates in
  that spot for a while: tier 0 keeps flagging the same harmless spot, Hafnia keeps saying no;
- budget: never past --stop-at requests today (gateway count) or --max-requests in this run.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class RouterConfig:
    cooldown_s: float = 30.0
    incident_hold_s: float = 300.0
    rejected_spot_hold_s: float = 600.0
    grid: int = 6                       # spots are cells of a grid x grid division of the image
    max_requests: int = 20


@dataclass
class Decision:
    send: bool
    reason: str
    spot: tuple[int, int] | None = None


@dataclass
class Router:
    cfg: RouterConfig = field(default_factory=RouterConfig)
    last_ask: dict[str, float] = field(default_factory=dict)
    open_until: dict[str, float] = field(default_factory=dict)
    rejected: dict[tuple[str, tuple[int, int]], float] = field(default_factory=dict)
    requests: int = 0

    def spot(self, boxes: np.ndarray, width: int, height: int) -> tuple[int, int]:
        """Grid cell of the centre of the candidate's boxes."""
        cx = float((boxes[:, 0] + boxes[:, 2]).mean() / 2) / width
        cy = float((boxes[:, 1] + boxes[:, 3]).mean() / 2) / height
        g = self.cfg.grid
        return min(g - 1, int(cx * g)), min(g - 1, int(cy * g))

    def decide(self, camera: str, t: float, spot: tuple[int, int], budget_left: int | None) -> Decision:
        if self.requests >= self.cfg.max_requests:
            return Decision(False, "run cap reached", spot)
        if budget_left is not None and budget_left <= 0:
            return Decision(False, "daily budget reached", spot)
        if t < self.open_until.get(camera, 0):
            return Decision(False, "incident already open on this camera", spot)
        if t < self.rejected.get((camera, spot), 0):
            return Decision(False, "spot recently rejected by Hafnia", spot)
        if t - self.last_ask.get(camera, -1e9) < self.cfg.cooldown_s:
            return Decision(False, "camera cooldown", spot)
        self.last_ask[camera] = t
        self.requests += 1
        return Decision(True, "ask Hafnia", spot)

    def feedback(self, camera: str, t: float, spot: tuple[int, int], confirmed: bool) -> None:
        if confirmed:
            self.open_until[camera] = t + self.cfg.incident_hold_s
        else:
            self.rejected[(camera, spot)] = t + self.cfg.rejected_spot_hold_s
