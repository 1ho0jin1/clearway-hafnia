"""Detection + tracking (Ultralytics YOLO with ByteTrack) feeding the candidate rules."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
from ultralytics import YOLO

from tier0.rules import Candidate, Detector, Params, merge

COCO_ROAD_USERS = [0, 1, 2, 3, 5, 7]   # person, bicycle, car, motorcycle, bus, truck
DEFAULT_WEIGHTS = Path(__file__).resolve().parent.parent / "models" / "yolo11m.pt"


class Tier0:
    """One instance per camera stream: the tracker keeps state between frames."""

    def __init__(self, weights: Path = DEFAULT_WEIGHTS, params: Params | None = None, device: int | str = 0,
                 conf: float = 0.25, imgsz: int = 640):
        self.model = YOLO(str(weights))
        self.detector = Detector(params)
        self.device, self.conf, self.imgsz = device, conf, imgsz

    def feed(self, t: float, frame: np.ndarray) -> None:
        r = self.model.track(frame, persist=True, tracker="bytetrack.yaml", classes=COCO_ROAD_USERS,
                             conf=self.conf, imgsz=self.imgsz, verbose=False, device=self.device)[0]
        if r.boxes.id is None:
            self.detector.update(t, [], [], np.empty((0, 4)))
            return
        ids = r.boxes.id.int().tolist()
        classes = [self.model.names[c] for c in r.boxes.cls.int().tolist()]
        self.detector.update(t, ids, classes, r.boxes.xyxy.cpu().numpy())

    def run(self, frames: Iterable[tuple[float, np.ndarray]]) -> list[Candidate]:
        for t, frame in frames:
            self.feed(t, frame)
        return self.incidents()

    def incidents(self) -> list[Candidate]:
        return merge(self.detector.candidates, self.detector.p.merge_s)
