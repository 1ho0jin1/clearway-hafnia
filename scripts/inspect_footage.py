r"""inspect_footage.py - is a candidate video useful for near-miss work? A contact sheet and road-user counts.

    .venv\Scripts\python.exe scripts\inspect_footage.py VIDEO [VIDEO ...] [--out data\footage\inspect] [--max-s 180]

For each video: 12 frames spread over it (<name>_sheet.jpg), and YOLO11m detections at 1 frame per second over the
first --max-s seconds: road users per frame by class, and the median box height of people (in pixels and as a share
of the frame height), which says whether pedestrians are big enough to track. Costs no Hafnia requests.
"""
from __future__ import annotations

import argparse
import statistics
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

REPO = Path(__file__).resolve().parent.parent
CLASSES = {0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def frames_at(path: Path, times: list[float]) -> list[tuple[float, np.ndarray]]:
    cap = cv2.VideoCapture(str(path))
    out = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if ok:
            out.append((t, f))
    return out


def duration(path: Path) -> float:
    cap = cv2.VideoCapture(str(path))
    n, fps = cap.get(cv2.CAP_PROP_FRAME_COUNT), cap.get(cv2.CAP_PROP_FPS) or 10
    if n > 0:
        return n / fps
    t = 0.0   # no frame count (partial AVI): walk the file
    while cap.grab():
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("videos", type=Path, nargs="+")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "footage" / "inspect")
    ap.add_argument("--max-s", type=float, default=180)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(REPO / "models" / "yolo11m.pt"))
    print(f"{'video':38} {'dur s':>6} {'size':>9}  per frame: person bicycle motorcycle car bus truck | person h px (share)")
    for v in args.videos:
        d = duration(v)
        sheet = frames_at(v, [d * (i + 0.5) / 12 for i in range(12)])
        if not sheet:
            print(f"{v.name[:38]:38} unreadable (a truncated AVI cannot be seeked: convert it to MP4 first)")
            continue
        tiles = [cv2.resize(f, (400, int(400 * f.shape[0] / f.shape[1]))) for _, f in sheet]
        for (t, _), tile in zip(sheet, tiles):
            cv2.putText(tile, f"{t:.0f}s", (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        if tiles:
            h = max(x.shape[0] for x in tiles)
            tiles = [cv2.copyMakeBorder(x, 0, h - x.shape[0], 0, 0, cv2.BORDER_CONSTANT) for x in tiles]
            cv2.imwrite(str(args.out / f"{v.stem}_sheet.jpg"), np.vstack([np.hstack(tiles[r * 4:(r + 1) * 4])
                                                                          for r in range(len(tiles) // 4)]))
        counts, heights, n = Counter(), [], 0
        for _, f in frames_at(v, [float(t) for t in range(int(min(d, args.max_s)))]):
            r = model(f, classes=list(CLASSES), conf=0.25, imgsz=max(640, min(1280, f.shape[1])), verbose=False)[0]
            n += 1
            for c, (x1, y1, x2, y2) in zip(r.boxes.cls.int().tolist(), r.boxes.xyxy.tolist()):
                counts[CLASSES[c]] += 1
                if c == 0:
                    heights.append(y2 - y1)
        fh = sheet[0][1].shape[0] if sheet else 1
        per = " ".join(f"{counts[k] / max(n, 1):5.1f}" for k in ("person", "bicycle", "motorcycle", "car", "bus", "truck"))
        ph = statistics.median(heights) if heights else 0
        size = f"{sheet[0][1].shape[1]}x{fh}" if sheet else "?"
        print(f"{v.name[:38]:38} {d:6.0f} {size:>9}  {per} | {ph:5.0f} ({ph / fh:.2f})", flush=True)


if __name__ == "__main__":
    main()
