"""collect_dets.py - every whole person / car / bus / truck box YOLO11m finds on sampled frames of each clip, with
its row, for fitting a scale per row and camera (offline; no Hafnia requests). Frames 832 wide, like the bridge."""
import json
import sys
from pathlib import Path

REPO = Path(r"C:\hafnia-hackathon-2026")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
from eval_change import CASES, frames  # noqa: E402
from ultralytics import YOLO  # noqa: E402

OUT = Path(sys.argv[1])
model = YOLO(str(REPO / "models" / "yolo11m.pt"))
out = {}
for name, (path, annexb, loop_s, state, role) in CASES.items():
    if name == "test_11" or not path.exists():
        continue
    step = 5 if loop_s <= 60 else 10                     # every 0.5 s on a loop, every 1 s on a real clip
    limit = int(loop_s * 10) if loop_s <= 60 else 1800   # one loop, or the first 180 s
    dets, H, W = [], None, None
    for i, f in enumerate(frames(path, annexb, width=832)):
        if i >= limit:
            break
        if i % step:
            continue
        H, W = f.shape[:2]
        r = model(f, classes=[0, 2, 5, 7], conf=0.5, imgsz=640, verbose=False)[0]
        for (x1, y1, x2, y2), c in zip(r.boxes.xyxy.tolist(), r.boxes.cls.int().tolist()):
            if y1 < 2 or y2 > H - 2 or x1 < 2 or x2 > W - 2 or y2 - y1 < 12:
                continue
            dets.append([round(i / 10, 1), model.names[c], round(x1), round(y1), round(x2), round(y2)])
    out[name] = {"role": role, "frame": [W, H], "dets": dets}
    print(f"{name:42} {len(dets):5} boxes", flush=True)
OUT.write_text(json.dumps(out), encoding="utf-8")
print("wrote", OUT)
