"""scale_probe.py - what a person and a car measure, in pixels, on each camera (offline; no Hafnia requests).

Runs YOLO11m on sampled frames of each clip, keeps person / car / truck / bus boxes that are whole (not cut by the
frame edge), and prints per camera: the median person height as a share of the frame height, the median person box
area as a share of the frame, the same for vehicles, the scale in pixels per metre those imply (person 1.7 m tall,
vehicle box 1.5 m high), and what the detector's area floors mean in square metres at that scale.
"""
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(r"C:\hafnia-hackathon-2026")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
from eval_change import CASES, frames  # noqa: E402
from ultralytics import YOLO  # noqa: E402

PERSON_M, VEHICLE_H_M = 1.7, 1.5
FLOORS = {"loops 0.5 %": 0.005, "real 0.15 %": 0.0015, "pane 0.11 %": 0.0011}
VEHICLES = {"car", "truck", "bus"}
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("scale_probe.json")

model = YOLO(str(REPO / "models" / "yolo11m.pt"))
rows = {}
for name, (path, annexb, loop_s, state, role) in CASES.items():
    if name == "test_11" or not path.exists():
        continue
    step = 5 if loop_s <= 60 else 20                     # every 0.5 s on a loop, every 2 s on a real clip
    limit = int(loop_s * 10) if loop_s <= 60 else 1500   # one loop, or the first 150 s
    persons, vehicles, dets = [], [], []
    H = W = None
    for i, f in enumerate(frames(path, annexb, width=832)):
        if i >= limit:
            break
        if i % step:
            continue
        H, W = f.shape[:2]
        r = model(f, classes=[0, 2, 5, 7], conf=0.5, imgsz=640, verbose=False)[0]
        for (x1, y1, x2, y2), c, p in zip(r.boxes.xyxy.tolist(), r.boxes.cls.int().tolist(), r.boxes.conf.tolist()):
            h, w = y2 - y1, x2 - x1
            if y1 < 2 or y2 > H - 2 or x1 < 2 or x2 > W - 2 or h < 12:
                continue                                 # cut by the edge, or too small to trust
            cls = model.names[c]
            d = {"t": round(i / 10, 1), "cls": cls, "box": [round(v) for v in (x1, y1, x2, y2)],
                 "h_pct": round(100 * h / H, 1), "w_pct": round(100 * w / W, 1),
                 "area_pct": round(100 * w * h / (W * H), 2), "foot": round(y2 / H, 2)}
            dets.append(d)
            (persons if cls == "person" else vehicles if cls in VEHICLES else []).append(d)
    def med(xs, k):
        return round(st.median(x[k] for x in xs), 2) if xs else None
    row = {"role": role, "frame": [W, H], "n_person": len(persons), "n_vehicle": len(vehicles),
           "person_h_pct": med(persons, "h_pct"), "person_area_pct": med(persons, "area_pct"),
           "vehicle_h_pct": med(vehicles, "h_pct"), "vehicle_w_pct": med(vehicles, "w_pct"),
           "vehicle_area_pct": med(vehicles, "area_pct")}
    # perspective: person height in the lower and the upper half of where feet land
    if len(persons) >= 6:
        feet = sorted(persons, key=lambda d: d["foot"])
        lo, hi = feet[: len(feet) // 3], feet[-(len(feet) // 3):]
        row["person_h_pct_far"] = med(lo, "h_pct")     # feet high in the frame: far from the camera
        row["person_h_pct_near"] = med(hi, "h_pct")    # feet low in the frame: near
        row["foot_far"], row["foot_near"] = med(lo, "foot"), med(hi, "foot")
    # scale and what the floors mean in square metres
    for key, n, h_pct, metres in (("person", len(persons), row["person_h_pct"], PERSON_M),
                                  ("vehicle", len(vehicles), row["vehicle_h_pct"], VEHICLE_H_M)):
        if n and h_pct and H:
            ppm = (h_pct / 100 * H) / metres
            row[f"ppm_{key}"] = round(ppm, 1)
            row[f"floors_m2_{key}"] = {fl: round(share * W * H / ppm ** 2, 2) for fl, share in FLOORS.items()}
    rows[name] = row
    if name == "vandalism":
        row["persons_near_window"] = [d for d in persons if 1.0 <= d["t"] <= 5.0]
    print(f"{name:42} {role:8} frame={W}x{H} persons={len(persons):3} h%={row['person_h_pct']} area%={row['person_area_pct']} "
          f"vehicles={len(vehicles):3} h%={row['vehicle_h_pct']} w%={row['vehicle_w_pct']} area%={row['vehicle_area_pct']} "
          f"ppm_p={row.get('ppm_person')} ppm_v={row.get('ppm_vehicle')}", flush=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("wrote", OUT)
