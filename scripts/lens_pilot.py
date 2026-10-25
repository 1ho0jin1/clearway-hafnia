r"""lens_pilot.py - plan C's lens pilot (M1, gate G2): the same incident shown to Hafnia five ways.

    .venv\Scripts\python.exe scripts\lens_pilot.py [--cameras ...] [--repeat 1] [--stop-at 450]

For each of the organizers' six synthetic incident cameras:
1. Offline, the change detector (tier0/change.py, loops setting) finds the incident's spot, when it started changing
   and when it was reported (see locate()). For the two person incidents (tracks, gate) YOLO's person box at a fixed
   moment stands in for the planned person triggers.
2. Live, FrameBridge watches the camera until that moment comes round (frame matching, as scripts\lens_compare.py).
3. Five views of the same moment, one Hafnia request each, all with the same JSON prompt:
     full_loop     the camera's recording, one loop long, centred on the event window (contains a loop cut: the
                   probe's case)
     centred       the camera's recording, the event window: from 2 s before the change started to 3 s after
                   it was reported (so the outcome, e.g. the scooter lying, is in it)
     crop          the event window cropped to the spot and enlarged (bicubic), on lens_1
     crop_sr       the same, enlarged with Real-ESRGAN (lens/enhance.py), on lens_1
     before_after  the crop with the spot BEFORE and AFTER held 2 s each and captioned, on lens_1
   Pairs isolate one factor each: full_loop/centred the window, centred/crop the crop, crop/crop_sr the upscaler,
   crop/before_after the before-and-after stills.
Requests: 5 per camera and repeat (30 for one repeat of all six). Needs lens.publisher (scripts\start_lens.ps1).
Writes run\pilot-<UTC>\results.json; frames sent and lens clips' first frames to frames\ (git-ignored).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.prompt import PROMPT, parse  # noqa: E402
from eval_change import CASES, frames, person_finder  # noqa: E402
from hafnia.gateway import Gateway  # noqa: E402
from hafnia.xprotect_rest import XProtect  # noqa: E402
from incident.verify import ask  # noqa: E402
from lens.client import before_after, span, submit, wait, zoom  # noqa: E402
from lens.enhance import SuperRes  # noqa: E402
from lens_compare import find_event, gateway_password, region_thumb, sheet, source_frame  # noqa: E402
from tier0.change import ChangeDetector, ChangeParams  # noqa: E402

CAMERAS = ["vehicle_breakdown_traffic_queue", "bin_pushed_over_onto_sidewalk", "escooter_left_across_sidewalk",
           "school_gate_break_in_night", "person_on_railway_tracks", "graffiti_on_standing_train"]
TRUTH = {"vehicle_breakdown_traffic_queue": "STALLED_VEHICLE", "bin_pushed_over_onto_sidewalk": "OBSTRUCTION",
         "escooter_left_across_sidewalk": "OBSTRUCTION", "school_gate_break_in_night": "TAMPERING",
         "person_on_railway_tracks": "PERSON_ON_TRACKS", "graffiti_on_standing_train": "DAMAGE"}
PERSON_AT = {"person_on_railway_tracks": 6.5,     # seconds into the loop: sitting on the edge, legs on the track
             "school_gate_break_in_night": 11.0}  # crouched at the padlock with the cutters
VARIANTS = ["full_loop", "centred", "crop", "crop_sr", "before_after"]
BEFORE_S = 2.0          # the window starts this long before the change started
AFTER_S = 3.0           # ... and ends this long after it was reported


def locate(name: str, people) -> tuple[float, float, tuple[int, int, int, int], str]:
    """(seconds into the loop the change started, ... it was reported, box in native clip pixels, how it was found).

    Changes: the largest report within 3 s of the first one inside the incident span (the first can be a fragment).
    Person incidents (tracks, gate): the change detector holds people back by design (the gate's reports in its span
    are lit pavement and shadow beside the crouching person, not the lock), so YOLO's largest person box at a fixed
    moment stands in for the planned danger-zone and person triggers."""
    path, annexb, loop_s, state, _ = CASES[name]
    if name in PERSON_AT:
        at = PERSON_AT[name]
        f = next(f for i, f in enumerate(frames(path, annexb, width=832)) if i == round(at * 10))
        from ultralytics import YOLO
        r = YOLO(str(REPO / "models" / "yolo11m.pt"))(f, classes=[0], conf=0.3, verbose=False)[0]
        x1, y1, x2, y2 = max(r.boxes.xyxy.tolist(), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        return at, at, (int(x1), int(y1), int(x2), int(y2)), "yolo person (person-trigger stand-in)"
    det = ChangeDetector(ChangeParams.loops())
    t, found = 0.0, []
    for _ in range(3):
        start = t
        for f in frames(path, annexb, width=832):
            for c in det.update(t, f, people(f)):
                if start >= 10 and state[0] - 1.0 <= c.t_detect - start <= state[1]:
                    found.append((c, start))
            t += 0.1
        if found:
            break
    if not found:
        raise RuntimeError(f"{name}: no change in the incident span")
    first = found[0][0].t_detect
    c, start = max((x for x in found if x[0].t_detect - first <= 3.0), key=lambda x: x[0].area)
    return max(0.0, c.t_start - start), c.t_detect - start, c.box, "change detector"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cameras", nargs="+", default=CAMERAS, choices=CAMERAS)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--stop-at", type=int, default=450)
    ap.add_argument("--match-ratio", type=float, default=0.5)
    ap.add_argument("--variants", nargs="+", default=VARIANTS, choices=VARIANTS,
                    help="views to ask about (default all five), e.g. --variants crop for a prompt regression check")
    args = ap.parse_args()
    n = len(args.cameras) * len(args.variants) * args.repeat
    out = REPO / "run" / f"pilot-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
    (out / "frames").mkdir(parents=True)

    gw = Gateway()
    gw.login(gateway_password())
    q = gw.quota()
    if q and q["DailySummaryCount"] + n > args.stop_at:
        sys.exit(f"today's count is {q['DailySummaryCount']}: {n} more would pass --stop-at {args.stop_at}")
    cams = XProtect().cameras()
    from ultralytics import YOLO
    people = person_finder(YOLO(str(REPO / "models" / "yolo11m.pt")))
    sr = SuperRes("general") if "crop_sr" in args.variants else None
    print(f"{n} requests planned", flush=True)

    jobs = []   # (camera, repeat, variant, camera id, start, end)
    events = {}
    for name in args.cameras:
        at, reported, box, how = locate(name, people)
        loop_s = CASES[name][2]
        after = reported - at + AFTER_S          # the window runs to AFTER_S past the report: the outcome is in it
        events[name] = {"start_in_loop_s": round(at, 1), "reported_in_loop_s": round(reported, 1), "box": box,
                        "found_by": how, "window_s": round(BEFORE_S + after, 1)}
        print(f"{name}: change from {at:.1f} s, reported {reported:.1f} s into the loop, box {box} ({how})", flush=True)
        ref = region_thumb(source_frame(CASES[name][0], at, 10), list(box))
        for rep in range(args.repeat):
            t_event, fr = find_event(name, ref, list(box), max(BEFORE_S, after), args.match_ratio,
                                     timeout_s=3 * loop_s + 30)
            w0, w1 = t_event - dt.timedelta(seconds=BEFORE_S), t_event + dt.timedelta(seconds=after)
            window = [f for t, f in fr if w0 <= t < w1]
            tag = f"{name}-r{rep}"
            makers = {"crop": lambda: zoom(window, box), "crop_sr": lambda: zoom(window, box, sr=sr),
                      "before_after": lambda: before_after(window, box)}
            renders = {v: make() for v, make in makers.items() if v in args.variants}
            sheet(window, out / "frames" / f"{tag}-centred.jpg")
            for v, r in renders.items():
                sheet(r, out / "frames" / f"{tag}-{v}.jpg")
            lens_jobs = {v: submit(r, f"{tag}-{v}", meta={"camera": name, "variant": v}) for v, r in renders.items()}
            mid = w0 + (w1 - w0) / 2
            if "full_loop" in args.variants:
                jobs.append((name, rep, "full_loop", cams[name], mid - dt.timedelta(seconds=loop_s / 2),
                             mid + dt.timedelta(seconds=loop_s / 2)))
            if "centred" in args.variants:
                jobs.append((name, rep, "centred", cams[name], w0, w1))
            for v, job in lens_jobs.items():
                s, e = span(wait(job, timeout=180))
                jobs.append((name, rep, v, cams["lens_1"], s, e))
            events[name].setdefault("t_event_utc", []).append(t_event.isoformat())
            print(f"  repeat {rep}: event at {t_event:%H:%M:%S.%f} UTC, lens clips played", flush=True)

    latest = max(e for *_, e in jobs)
    wait_s = (latest - dt.datetime.now(dt.timezone.utc)).total_seconds() + 5
    if wait_s > 0:
        time.sleep(wait_s)   # every window recorded

    def one(job):
        name, rep, v, cam_id, s, e = job
        summary, secs = ask(gw, cam_id, s, e, PROMPT)
        answer = summary.get("Response") or ""
        p = parse(answer)
        return {"camera": name, "repeat": rep, "variant": v, "start": s.isoformat(), "end": e.isoformat(),
                "progress": summary.get("Progress"), "seconds": round(secs, 1), "answer": answer, "parsed": p,
                "truth": TRUTH[name], "correct": p["category"] == TRUTH[name], "error": summary.get("LastError"),
                "summary_id": summary.get("Id")}

    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(one, jobs))
    (out / "results.json").write_text(json.dumps({"prompt": PROMPT, "events": events, "rows": rows}, indent=2,
                                                 default=str), encoding="utf-8")
    print(f"\n{'camera':34} " + " ".join(f"{v:>13}" for v in args.variants))
    for name in args.cameras:
        for rep in range(args.repeat):
            cells = []
            for v in args.variants:
                r = next(x for x in rows if x["camera"] == name and x["repeat"] == rep and x["variant"] == v)
                cells.append(("+" if r["correct"] else "-") + r["parsed"]["category"][:12])
            print(f"{name[:34]:34} " + " ".join(f"{c:>13}" for c in cells))
    for v in args.variants:
        rs = [r for r in rows if r["variant"] == v]
        print(f"{v:13} correct {sum(r['correct'] for r in rs)}/{len(rs)}, JSON ok {sum(r['parsed']['json_ok'] for r in rs)}/{len(rs)}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
