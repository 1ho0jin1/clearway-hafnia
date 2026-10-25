"""Lens clients: render a clip from source frames and queue it for lens/publisher.py.

    job = submit(slow([crop(f, box) for f in frames], 2), label="test_11-crash")
    done = wait(job)                 # after the clip has played
    start, end = span(done)          # ask Hafnia about lens_1 over this span

Rendering is plain image work here (crop, slow motion by repeating frames, boxes drawn on frames), plus optional
super-resolution of the crop (zoom(..., sr=lens.enhance.SuperRes())); the publisher scales each clip to the stream size. Clips are stored as near-lossless MJPEG so the lens adds no compression of its own before
the stream's H.264.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import time
from collections.abc import Sequence
from pathlib import Path

import cv2
import numpy as np

from lens.publisher import SPOOL, utc_now


def crop(frame: np.ndarray, box: Sequence[float], aspect: float = 16 / 9, pad: float = 0.5) -> np.ndarray:
    """The region around box (x1, y1, x2, y2) plus pad on every side, widened to the aspect ratio, inside the frame."""
    fh, fw = frame.shape[:2]
    x1, y1, x2, y2 = box
    bw, bh = (x2 - x1) * (1 + 2 * pad), (y2 - y1) * (1 + 2 * pad)
    if bw / bh < aspect:
        bw = bh * aspect
    else:
        bh = bw / aspect
    bw, bh = min(bw, fw), min(bh, fh)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    left = int(round(min(max(0, cx - bw / 2), fw - bw)))
    top = int(round(min(max(0, cy - bh / 2), fh - bh)))
    return frame[top:top + int(bh), left:left + int(bw)].copy()


def zoom(frames: list[np.ndarray], box: Sequence[float], sr=None, **crop_kw) -> list[np.ndarray]:
    """crop() of every frame, enlarged by a super-resolution model (lens.enhance.SuperRes) when sr is given; without
    it the publisher enlarges with bicubic interpolation when it fits the clip to the stream."""
    crops = [crop(f, box, **crop_kw) for f in frames]
    return sr.upscale_all(crops) if sr is not None else crops


def caption(img: np.ndarray, text: str) -> np.ndarray:
    """A black bar across the top with white text, sized to the image."""
    out = img.copy()
    h, w = out.shape[:2]
    bar = max(18, h // 9)
    scale = bar / 30
    cv2.rectangle(out, (0, 0), (w, bar), (0, 0, 0), -1)
    cv2.putText(out, text, (max(4, w // 60), int(bar * 0.75)), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255),
                max(1, round(scale * 2)), cv2.LINE_AA)
    return out


def before_after(frames: list[np.ndarray], box: Sequence[float], sr=None, still_s: float = 2.0, fps: int = 10,
                 **crop_kw) -> list[np.ndarray]:
    """The spot BEFORE (first frame, held still_s, captioned), the event as it happened, and the spot AFTER (last
    frame, held, captioned). Made against the probe's time-order errors (run/probe-20261022T054342Z/audit.md): the
    model is shown which state came first instead of having to infer it."""
    z = zoom(frames, box, sr, **crop_kw)
    n = round(still_s * fps)
    return [caption(z[0], "BEFORE")] * n + z + [caption(z[-1], "AFTER")] * n


def slow(frames: list[np.ndarray], factor: int) -> list[np.ndarray]:
    """Slow motion by repeating each frame: factor 2 plays a 6 s window in 12 s."""
    return [f for f in frames for _ in range(factor)]


def mark(frame: np.ndarray, boxes: Sequence[Sequence[float]], color=(0, 0, 255), width: int = 2) -> np.ndarray:
    out = frame.copy()
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), color, width)
    return out


def submit(frames: list[np.ndarray], label: str, fps: int = 10, tail_s: float = 1.0, meta: dict | None = None,
           spool: Path = SPOOL) -> str:
    """Write the clip and its job file; returns the job id. The publisher plays jobs in id (time) order."""
    spool.mkdir(parents=True, exist_ok=True)
    job_id = f"{utc_now():%Y%m%dT%H%M%S%f}_{re.sub(r'[^A-Za-z0-9_-]', '_', label)}"
    h, w = frames[0].shape[:2]
    video = spool / f"{job_id}.avi"
    out = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    out.set(cv2.VIDEOWRITER_PROP_QUALITY, 98)
    for f in frames:
        out.write(f if f.shape[:2] == (h, w) else cv2.resize(f, (w, h)))
    out.release()
    spec = {"id": job_id, "video": video.name, "fps": fps, "tail_s": tail_s, "meta": meta or {}}
    tmp = spool / f"{job_id}.json.tmp"
    tmp.write_text(json.dumps(spec), encoding="utf-8")
    tmp.replace(spool / f"{job_id}.json")   # the publisher only looks at *.json: write it last, in one step
    return job_id


def wait(job_id: str, timeout: float = 300, spool: Path = SPOOL) -> dict:
    """Block until the publisher has played the job; returns its done record (start, end, frames)."""
    done = spool / f"{job_id}.done.json"
    deadline = time.monotonic() + timeout
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(f"lens job {job_id} not played within {timeout:.0f} s: is lens.publisher running?")
        try:
            record = json.loads(done.read_text(encoding="utf-8"))
            break
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            time.sleep(0.5)     # not played yet, being renamed into place (Windows refuses the open), or half written
    if "error" in record:
        raise RuntimeError(f"lens job {job_id}: {record['error']}")
    return record


def span(done: dict, delay_s: float = 0.3) -> tuple[dt.datetime, dt.datetime]:
    """The whole-second span to ask Hafnia about (the gateway takes whole seconds). The publisher starts clips on a
    whole second and frames reach the recording about 0.2 s after they are sent (first test, 2026-10-21), so the start
    is that second and the end is rounded up past the last frame; the held tail and the idle gap cover the rounding."""
    def parse(s: str) -> dt.datetime:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    start = parse(done["start"]).replace(microsecond=0)
    end = parse(done["end"]) + dt.timedelta(seconds=delay_s)
    if end.microsecond:
        end = end.replace(microsecond=0) + dt.timedelta(seconds=1)
    return start, end
