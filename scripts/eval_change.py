r"""eval_change.py - offline check of the change detector (tier0/change.py) on every camera's clip: gate G1 of plan C.

    .venv\Scripts\python.exe scripts\eval_change.py [--loops 6] [--only NAME ...] [--out run\change-<UTC>]

Each clip is played the way its camera plays it: on a loop, at 10 fps. For an incident clip the lasting state (the
bin lying, the truck stopped, ...) starts at a known second of the loop (approximate, from contact sheets, 2026-10-22)
and lasts until the loop restarts: a loop is caught if a change is reported inside that span. Every other report is a
false one, counted per hour; on the negatives (no incident) every report is false. Draws each report's box on the
frame it was reported at (frames\<case>.jpg, git-ignored: footage). Costs no Hafnia requests.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from tier0.change import ChangeDetector, ChangeParams  # noqa: E402

FFMPEG = r"C:\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
DRIVER = Path(r"C:\Program Files (x86)\Milestone\XProtect Recording Server\Drivers\NativeDrivers\StableFPS_DATA\Video\H264")

# name: (clip, Annex B?, loop seconds, incident state (start, end) within the loop or None, role)
CASES = {
    "vehicle_breakdown_traffic_queue": (DRIVER / "832x480_vehicle_breakdown_traffic_queue", True, 17.0, (8.5, 17.0), "incident"),
    "bin_pushed_over_onto_sidewalk": (DRIVER / "832x480_bin_pushed_over_onto_sidewalk", True, 15.0, (10.0, 15.0), "incident"),
    # Rule for every start: the incident's object first comes to rest at the incident spot. For the e-scooter that
    # is when the rider stops on the pavement (7.0 s), before laying it down (9.5 s): corrected on 2026-10-23 after
    # the first runs, where 9.5 s had been used.
    "escooter_left_across_sidewalk": (DRIVER / "832x480_escooter_left_across_sidewalk", True, 15.0, (7.0, 15.0), "incident"),
    "school_gate_break_in_night": (DRIVER / "832x480_school_gate_break_in_night", True, 15.0, (6.0, 15.0), "incident"),
    "person_on_railway_tracks": (DRIVER / "832x480_person_on_railway_tracks", True, 15.0, (4.5, 15.0), "incident"),
    "graffiti_on_standing_train": (DRIVER / "832x480_graffiti_on_standing_train", True, 15.0, (8.0, 15.0), "incident"),
    "vandalism": (DRIVER / "832x480_vandalism", True, 8.0, (4.5, 8.0), "incident"),
    "traffic_flows_in_the_open_lanes": (DRIVER / "832x480_traffic_flows_in_the_open_lanes", True, 8.0, None, "negative"),
    "city_street_7_condensation_inside_housing": (DRIVER / "832x480_city_street_7_condensation_inside_housing", True, 8.0, None, "negative"),
    "busy_street": (DRIVER / "1280x720_busy_street", True, 15.5, None, "negative"),
    "highway_traffic_overcast_weather": (DRIVER / "1920x1080_highway_traffic_overcast_weather", True, 780.0, None, "negative"),
    "test_11": (REPO / "data" / "clips" / "800x410_test_11", True, 900.3, (602.0, 900.3), "real"),
    "mumbai02": (REPO / "data" / "footage" / "commons" / "mumbai02.webm", False, 183.2, None, "real"),
    "mumbai03": (REPO / "data" / "footage" / "commons" / "mumbai03.webm", False, 211.3, None, "real"),
    "duesseldorf": (REPO / "data" / "footage" / "commons" / "duesseldorf.ogv", False, 275.5, None, "real"),
}


def frames(path: Path, annexb: bool, width: int = 640, fps: int = 10):
    """Decoded frames at the camera's 10 fps, scaled to `width` (the detector works smaller still)."""
    src = ["-f", "h264", "-framerate", str(fps), "-i", str(path)] if annexb else ["-i", str(path)]
    probe = subprocess.run([FFMPEG, "-v", "error", *src, "-vf", f"scale={width}:-2", "-frames:v", "1", "-f",
                            "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    h = len(probe) // (width * 3)
    proc = subprocess.Popen([FFMPEG, "-v", "error", *src, "-vf", f"fps={fps},scale={width}:{h}", "-f", "rawvideo",
                             "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    size = width * h * 3
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, width, 3)
    proc.wait()


def person_finder(model):
    """Person boxes on a frame, for holding back changes that someone stands in (None: do not hold back)."""
    if model is None:
        return lambda f: None
    def find(f):
        r = model(f, classes=[0], conf=0.3, imgsz=640, verbose=False)[0]
        return lambda: [tuple(b) for b in r.boxes.xyxy.tolist()]
    return find


def run_case(name: str, loops: int, params: ChangeParams, sheet_dir: Path, people) -> dict:
    path, annexb, loop_s, state, role = CASES[name]
    n_loops = 1 if loop_s > 60 else loops
    det = ChangeDetector(params)
    shots = []
    t = 0.0
    loop_starts = []
    for k in range(n_loops):
        loop_starts.append(t)
        for f in frames(path, annexb):
            for c in det.update(t, f, people(f)):
                if len(shots) < 12:
                    img = f.copy()
                    x1, y1, x2, y2 = c.box
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(img, f"loop {k} t={t - loop_starts[-1]:.1f}s", (6, 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 255, 255), 2)
                    shots.append(img)
            t += 0.1
    scored = [s for s in loop_starts if s >= params.warmup_s] if n_loops > 1 else loop_starts
    n_scored = len(scored)
    total_s = t - (scored[0] if n_loops > 1 else params.warmup_s)
    hits, delays, false = [], [], []
    for c in det.changes:
        if n_loops > 1 and c.t_detect < scored[0]:
            continue   # the loop the warm-up ended in is not scored
        k = max(i for i, s in enumerate(loop_starts) if s <= c.t_detect + 1e-6)
        in_loop = c.t_detect - loop_starts[k]
        if state and state[0] <= in_loop <= state[1] + 0.3:
            hits.append(k)
            delays.append(round(in_loop - state[0], 1))
        else:
            false.append(round(in_loop, 1))
    if shots:
        tiles = [cv2.resize(s, (320, int(320 * s.shape[0] / s.shape[1]))) for s in shots]
        while len(tiles) % 4:
            tiles.append(np.zeros_like(tiles[0]))
        cv2.imwrite(str(sheet_dir / f"{name}.jpg"), np.vstack([np.hstack(tiles[r * 4:(r + 1) * 4])
                                                              for r in range(len(tiles) // 4)]))
    caught = len(set(hits))
    return {"case": name, "role": role, "loops": n_scored, "seconds": round(total_s, 1),
            "loops_caught": caught if state else None, "first_delay_s": sorted(delays)[:n_loops] if state else None,
            "false_reports": len(false), "false_per_hour": round(len(false) / total_s * 3600, 1),
            "false_at_loop_s": false[:20], "scene_jumps": len(det.jumps),
            "reports": [{"t_detect": round(c.t_detect, 1), "t_start": round(c.t_start, 1), "box": c.box,
                         "area": c.area, "closed": c.closed_by} for c in det.changes][:2000]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--loops", type=int, default=6)
    ap.add_argument("--only", nargs="+", choices=list(CASES))
    ap.add_argument("--no-people", action="store_true", help="do not hold back changes that people stand in")
    ap.add_argument("--profile", choices=["loops", "real"], default="loops",
                    help="ChangeParams.loops() for the synthetic clips, .real() for real cameras")
    ap.add_argument("--persist", type=float, help="override ChangeParams.persist_s (seconds a change must last)")
    ap.add_argument("--work-width", type=int, help="override ChangeParams.work_width (pixels)")
    ap.add_argument("--min-area", type=float, help="override ChangeParams.min_area (share of the frame)")
    ap.add_argument("--no-freeze", action="store_true",
                    help="let the slow background learn open changes' spots (the detector before 2026-10-27)")
    ap.add_argument("--scales", type=Path, help="scales.json from scale_fit.py: a floor in square metres per camera")
    ap.add_argument("--world-floor", type=float, help="square metres a blob must cover at its row (needs --scales)")
    ap.add_argument("--at-least", type=float, default=0.0,
                    help="with --world-floor: the floor never goes below this share of the frame (0: pure)")
    ap.add_argument("--out", type=Path, default=REPO / "run" / f"change-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}")
    args = ap.parse_args()
    (args.out / "frames").mkdir(parents=True, exist_ok=True)
    overrides = {k: v for k, v in (("persist_s", args.persist), ("work_width", args.work_width),
                                   ("min_area", args.min_area)) if v is not None}
    if args.no_freeze:
        overrides["freeze_open"] = False
    params = getattr(ChangeParams, args.profile)()
    for k, v in overrides.items():
        setattr(params, k, v)
    model = None
    if not args.no_people:
        from ultralytics import YOLO
        model = YOLO(str(REPO / "models" / "yolo11m.pt"))
    people = person_finder(model)
    scales = None
    if args.world_floor is not None:
        import scale_fit
        scales = scale_fit.load(args.scales)
    rows = []
    print(f"{'case':42} {'role':8} {'loops':>5} {'caught':>6} {'delay s':>14} {'false':>5} {'false/h':>8} jumps")
    for name in args.only or CASES:
        if not CASES[name][0].exists():
            print(f"{name:42} missing: {CASES[name][0]}")
            continue
        if scales is not None:
            sc, m2, least = scales[name], args.world_floor, args.at_least
            params.min_area_fn = lambda foot, sc=sc, m2=m2, least=least: max(least, scale_fit.floor_share(sc, foot, m2))
        r = run_case(name, args.loops, params, args.out / "frames", people)
        rows.append(r)
        caught = "-" if r["loops_caught"] is None else f"{r['loops_caught']}/{r['loops']}"
        delay = "-" if not r["first_delay_s"] else ",".join(str(d) for d in r["first_delay_s"][:4])
        print(f"{name:42} {r['role']:8} {r['loops']:5} {caught:>6} {delay:>14} {r['false_reports']:5} "
              f"{r['false_per_hour']:8} {r['scene_jumps']}", flush=True)
    meta = {"params": {k: v for k, v in vars(params).items() if k != "min_area_fn"}, "cases": rows}
    if scales is not None:
        meta["world_floor_m2"], meta["at_least"], meta["scales"] = args.world_floor, args.at_least, str(args.scales)
    (args.out / "results.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
