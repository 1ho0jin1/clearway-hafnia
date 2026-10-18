"""Frame sources for tier 0. Offline: a video file resampled to the camera frame rate (10 fps on our cameras)."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np


def video_frames(path: Path, fps: float = 10.0, loops: int = 1) -> Iterator[tuple[float, np.ndarray]]:
    """Yield (seconds, BGR frame) at `fps`, playing the file `loops` times back to back, as a looped test camera does.
    Time keeps running across loops. Frames are streamed, one at a time: a minute of 1080p held in a list is ~4 GB."""
    offset = 0.0
    for _ in range(loops):
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise FileNotFoundError(path)
        src_fps = cap.get(cv2.CAP_PROP_FPS) or fps
        i = n = 0
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                # Keep the source frame nearest each output tick.
                if i == 0 or int(i * fps / src_fps) != int((i - 1) * fps / src_fps):
                    yield offset + n / fps, frame
                    n += 1
                i += 1
        finally:
            cap.release()
        offset += n / fps
