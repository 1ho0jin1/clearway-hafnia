r"""holdout.py - the held-out check: Clearway's change detector and prompt on real street footage that neither was
written against (2026-10-29).

    .venv\Scripts\python.exe scripts\holdout.py detect [--out run\holdout-20261029] [--only mumbai02 ...] [--no-people]
    .venv\Scripts\python.exe scripts\holdout.py play run\holdout-20261029 [--max 40]
    .venv\Scripts\python.exe scripts\holdout.py ask run\holdout-20261029 [--stop-at 450] [--dry-run]
    .venv\Scripts\python.exe scripts\holdout.py score run\holdout-20261029

Why: the prompt experiment (run/prompt-20261028T1605Z) compared prompts on 28 clips from the eight looped scenes on
this machine, the scenes the prompt had been written against: a comparison between prompts, not an accuracy. This
script asks what the detector raises, and what Hafnia answers with the service's prompt, on three CC0 street clips
(Wikimedia Commons: Mumbai 02 and 03, Duesseldorf; docs/PLAN-near-miss.md) that no part of Clearway was tuned on:
fixed cameras over dense streets, people crossing between moving cars, cars turning across tram tracks, nothing
that blocks a way for long. Every candidate is a hard negative unless the labels say otherwise.

detect: each clip once at 10 fps, BRIDGE_WIDTH px wide (the frames the service gets from FrameBridge), through
tier0.change twice: with the setting the service gives real cameras (ChangeParams.real: a change must last 15 s)
and with the looped-clip setting (ChangeParams.loops: 1.5 s), the second as a superset of things that paused on a
real street, for more hard negatives. People found by YOLO11m hold changes back as in the service. Each report
becomes the clip the service would send: the window from BEFORE_S before the change to AFTER_S after the report
(at most MAX_CLIP_S), cropped to the spot with lens.client.zoom when the lens would magnify it DIRECT_BELOW times
or more, the whole frame otherwise (a direct ask on the camera's own recording in the service; here the frame is
played on the lens). Writes candidates.jsonl, clips/<cid>.avi, sheets/<cid>.jpg and sheets/grid-*.jpg (for
labelling by eye), detect.json (reports per hour). Costs no request.

labels.json, by hand before asking: {"<cid>": ["NONE" | <category> | null, "note"]}; null: ambiguous, not scored.

play: the clips on lens_1 in order (real-setting candidates first, then the looped-setting extras that are not the
same spot again, evenly sampled up to --max), the recorded span of each verified from lens_1's own frames
(lens/clock.py); writes clips.jsonl. ask: one request per clip with the service's prompt (clearway/prompt.py) and
the gateway's system prompt as it is (empty; refused otherwise); resumable; the plan and today's count are
printed first and --dry-run stops there. score: README.md (the text above the marker is kept), answers.md,
summary.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.prompt import PROMPT  # noqa: E402
from clearway.service import AFTER_S, BEFORE_S, BRIDGE_WIDTH, DIRECT_BELOW, MAX_CLIP_S, WORK_WIDTH  # noqa: E402
from lens.client import zoom  # noqa: E402
from prompt_experiment import PARALLEL, parse_answer, read_clip, utc_now  # noqa: E402
import scale_fit  # noqa: E402
from tier0.change import ChangeDetector, ChangeParams  # noqa: E402

FFMPEG = r"C:\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
FOOTAGE = REPO / "data" / "footage" / "commons"
FPS = 10
DEFAULT_OUT = REPO / "run" / "holdout-20261029"
TABLES_MARK = "<!-- tables: written by holdout.py score; the text above is kept -->"
DUP_IOU = 0.3           # a looped-setting report whose box overlaps a real-setting report this much, started within
DUP_S = 5.0             # ... this many seconds of it, is the same thing reported earlier: not asked twice

# name: (file, what it shows, licence); docs/PLAN-near-miss.md, "Footage"
CLIPS = {
    "mumbai02": (FOOTAGE / "mumbai02.webm", "a Mumbai junction from above by day, 3:03, 960x540", "CC0"),
    "mumbai03": (FOOTAGE / "mumbai03.webm", "a Mumbai street at night, street level, 3:31, 960x540", "CC0"),
    "duesseldorf": (FOOTAGE / "duesseldorf.ogv", "a tram junction in Duesseldorf by day, 4:35, 1280x720", "CC0"),
}
PROFILES = {"real": ChangeParams.real, "loops": ChangeParams.loops}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


# --- detect -------------------------------------------------------------------------------------------------------
def frames(path: Path, width: int = BRIDGE_WIDTH, fps: int = FPS):
    """The clip at fps, width px wide: what the service gets from FrameBridge."""
    probe = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-an", "-vf", f"scale={width}:-2", "-frames:v",
                            "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    h = len(probe) // (width * 3)
    proc = subprocess.Popen([FFMPEG, "-v", "error", "-i", str(path), "-an", "-vf", f"fps={fps},scale={width}:{h}",
                             "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    size = width * h * 3
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, width, 3)
    finally:
        proc.stdout.close()
        proc.wait()


def person_finder(model):
    """As scripts/eval_change.py: person boxes on the detector's frame, for holding back changes someone stands in."""
    if model is None:
        return lambda f: None

    def find(f):
        r = model(f, classes=[0], conf=0.3, imgsz=640, verbose=False)[0]
        return lambda: [tuple(b) for b in r.boxes.xyxy.tolist()]
    return find


def decode(jpeg: bytes) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)


def write_avi(path: Path, clip: list[np.ndarray], fps: int = FPS) -> None:
    """Near-lossless MJPEG, as lens.client.submit writes the spool."""
    h, w = clip[0].shape[:2]
    out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    out.set(cv2.VIDEOWRITER_PROP_QUALITY, 98)
    for f in clip:
        out.write(f if f.shape[:2] == (h, w) else cv2.resize(f, (w, h)))
    out.release()


def sheet(cid: str, report: np.ndarray, box_px, clip: list[np.ndarray], text: str) -> np.ndarray:
    """The report frame with the box, over four frames of the clip Hafnia would see (first, a third, two thirds,
    last), captioned."""
    top = report.copy()
    x1, y1, x2, y2 = (int(round(v)) for v in box_px)
    cv2.rectangle(top, (x1, y1), (x2, y2), (0, 0, 255), 2)
    w = top.shape[1]
    picks = [clip[0], clip[len(clip) // 3], clip[2 * len(clip) // 3], clip[-1]]
    tw = w // 4
    tiles = [cv2.resize(p, (tw, int(tw * p.shape[0] / p.shape[1]))) for p in picks]
    th = max(t.shape[0] for t in tiles)
    row = np.zeros((th, tw * 4, 3), np.uint8)
    for i, t in enumerate(tiles):
        row[:t.shape[0], i * tw:(i + 1) * tw] = t
    bar = np.zeros((26, w, 3), np.uint8)
    cv2.putText(bar, f"{cid}  {text}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return np.vstack([bar, top, row[:, :w]])


def detect_clip(name: str, profile: str, people, out: Path, log, floor=None,
                scale_info: dict | None = None) -> tuple[dict, list[dict]]:
    path, what, _ = CLIPS[name]
    params = PROFILES[profile]()
    if floor is not None:                       # the calibrated-floor test, 2026-10-29: a floor in square metres
        params.min_area_fn = floor
    det = ChangeDetector(params)
    keep_s = MAX_CLIP_S + AFTER_S + 1.0
    ring: deque[tuple[float, bytes]] = deque()          # (t, jpeg) of the last keep_s seconds, as the service keeps
    pending: list[dict] = []                            # windows still collecting frames
    rows: list[dict] = []
    scale = BRIDGE_WIDTH / WORK_WIDTH
    t = 0.0
    n = 0

    def finish(p: dict) -> None:
        c = p["change"]
        cid = f"{name}-{profile}-{c.id:03d}"
        full = [decode(j) for j in p["jpegs"]]
        box_px = tuple(v * scale for v in c.box)
        clip = zoom(full, box_px)
        magnification = round(full[0].shape[1] / clip[0].shape[1], 2)
        view = "lens" if magnification >= DIRECT_BELOW else "direct"
        shown = clip if view == "lens" else full
        write_avi(out / "clips" / f"{cid}.avi", shown)
        text = (f"t {c.t_start:.1f}-{c.t_detect:.1f} s  area {c.area:.4f}  x{magnification} {view}  "
                f"window {p['w0']:.1f}-{p['w1']:.1f} s  {len(shown)} frames")
        cv2.imwrite(str(out / "sheets" / f"{cid}.jpg"), sheet(cid, decode(p["report"]), box_px, clip, text),
                    [cv2.IMWRITE_JPEG_QUALITY, 88])
        rows.append({"cid": cid, "clip": name, "profile": profile, "change": c.id, "t_start": round(c.t_start, 1),
                     "t_detect": round(c.t_detect, 1), "box": list(c.box), "box_px": [round(v) for v in box_px],
                     "area": round(c.area, 5), "foot": round(box_px[3] / full[0].shape[0], 3),
                     "world_m2": (round(scale_fit.world_m2(scale_info, box_px[3] / full[0].shape[0], c.area), 2)
                                  if scale_info else None),
                     "w0": round(p["w0"], 1), "w1": round(p["w1"], 1),
                     "frames": len(shown), "magnification": magnification, "view": view,
                     "avi": f"clips/{cid}.avi", "sheet": f"sheets/{cid}.jpg", "_change": c})
        log(f"  {cid}: t {c.t_start:.1f}-{c.t_detect:.1f} s, box {c.box}, x{magnification} {view}, "
            f"{len(shown)} frames")

    for f in frames(path):
        n += 1
        jpeg = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()
        ring.append((t, jpeg))
        while ring and ring[0][0] < t - keep_s:
            ring.popleft()
        still = []
        for p in pending:                   # windows opened at earlier frames take this frame or close
            if t <= p["w1"] + 1e-6:
                p["jpegs"].append(jpeg)
                still.append(p)
            else:
                finish(p)
        pending = still
        small = cv2.resize(f, (WORK_WIDTH, round(f.shape[0] * WORK_WIDTH / f.shape[1])), interpolation=cv2.INTER_AREA)
        for c in det.update(t, small, people(small)):
            w1 = c.t_detect + AFTER_S
            w0 = max(c.t_start - BEFORE_S, w1 - MAX_CLIP_S)
            pending.append({"change": c, "w0": w0, "w1": w1, "report": jpeg,
                            "jpegs": [j for tt, j in ring if tt >= w0 - 1e-6]})
        t += 1.0 / FPS
    for p in pending:
        finish(p)
    for r in rows:                          # closings are known only now
        c = r.pop("_change")
        r["closed_by"] = c.closed_by
        r["t_closed"] = round(c.t_closed, 1) if c.t_closed is not None else None
    seconds = round(t - params.warmup_s, 1)
    summary = {"clip": name, "profile": profile, "what": what, "frames": n, "seconds": seconds,
               "reports": len(rows), "per_hour": round(len(rows) / seconds * 3600, 1) if seconds > 0 else None,
               "scene_jumps": len(det.jumps)}
    return summary, rows


def mark_duplicates(rows: list[dict]) -> int:
    """A looped-setting report of the same spot a real-setting report covers (started within DUP_S, boxes overlap
    DUP_IOU) is the same thing seen with the shorter wait: marked, not asked twice."""
    n = 0
    real = [r for r in rows if r["profile"] == "real"]
    for r in rows:
        if r["profile"] != "loops":
            continue
        for s in real:
            if s["clip"] == r["clip"] and abs(s["t_start"] - r["t_start"]) <= DUP_S and iou(s["box"], r["box"]) >= DUP_IOU:
                r["dup_of"] = s["cid"]
                n += 1
                break
    return n


def mark_same_as(rows: list[dict], baseline: list[dict]) -> int:
    """A candidate of the same clip and setting as a baseline candidate, started within DUP_S of it with boxes
    overlapping DUP_IOU, is the same thing the baseline already asked about: its answer is inherited, not asked
    again (the calibrated-floor test against run/holdout-20261029)."""
    n = 0
    for r in rows:
        for b in baseline:
            if (b["clip"] == r["clip"] and b["profile"] == r["profile"] and abs(b["t_start"] - r["t_start"]) <= DUP_S
                    and iou(b["box"], r["box"]) >= DUP_IOU):
                r["same_as"] = b["cid"]
                n += 1
                break
    return n


def grids(out: Path, rows: list[dict], per: int = 4) -> None:
    """Four sheets per image, for labelling with fewer looks."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["clip"], r["profile"]), []).append(r)
    for (clip, profile), rs in groups.items():
        for i in range(0, len(rs), per):
            imgs = [cv2.imread(str(out / r["sheet"])) for r in rs[i:i + per]]
            w = max(im.shape[1] for im in imgs)
            imgs = [im if im.shape[1] == w else cv2.resize(im, (w, int(im.shape[0] * w / im.shape[1]))) for im in imgs]
            h = max(im.shape[0] for im in imgs)
            cells = [np.vstack([im, np.zeros((h - im.shape[0], w, 3), np.uint8)]) for im in imgs]
            while len(cells) % 2:
                cells.append(np.zeros((h, w, 3), np.uint8))
            grid = np.vstack([np.hstack(cells[j:j + 2]) for j in range(0, len(cells), 2)])
            cv2.imwrite(str(out / "sheets" / f"grid-{clip}-{profile}-{i // per + 1:02d}.jpg"), grid,
                        [cv2.IMWRITE_JPEG_QUALITY, 85])


def detect(args) -> int:
    out = args.out
    (out / "clips").mkdir(parents=True, exist_ok=True)
    (out / "sheets").mkdir(exist_ok=True)
    logf = (out / "detect.log").open("a", encoding="utf-8")

    def log(s: str) -> None:
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()

    model = None
    if not args.no_people:
        from ultralytics import YOLO
        model = YOLO(str(REPO / "models" / "yolo11m.pt"))
    people = person_finder(model)
    scales = scale_fit.load(args.scales) if args.world_floor is not None else None
    if scales is not None:
        log(f"calibrated floor: {args.world_floor} m2 at the blob's row (scales {args.scales}), never below "
            f"{args.at_least} of the frame")
    log(f"detect {utc_now().isoformat()} clips {' '.join(args.only or CLIPS)} profiles {' '.join(args.profiles)} "
        f"people {'yolo11m' if model else 'off'}; frames {BRIDGE_WIDTH} px at {FPS} fps, detector at {WORK_WIDTH} px; "
        f"window -{BEFORE_S}/+{AFTER_S} s, at most {MAX_CLIP_S} s; lens from x{DIRECT_BELOW}")
    summaries, rows = [], []
    for name in args.only or list(CLIPS):
        for profile in args.profiles:
            t0 = time.monotonic()
            log(f"{name} {profile}: {CLIPS[name][1]}")
            floor = None
            if scales is not None:
                floor = (lambda foot, sc=scales[name], m2=args.world_floor, least=args.at_least:
                         max(least, scale_fit.floor_share(sc, foot, m2)))
            s, rs = detect_clip(name, profile, people, out, log, floor=floor,
                                scale_info=scales.get(name) if scales else None)
            s["took_s"] = round(time.monotonic() - t0, 1)
            summaries.append(s)
            rows.extend(rs)
            log(f"  {s['reports']} reports in {s['seconds']} s ({s['per_hour']} per hour), {s['scene_jumps']} scene "
                f"jumps, {s['took_s']} s")
    n_dup = mark_duplicates(rows)
    n_same = mark_same_as(rows, load_jsonl(args.baseline / "candidates.jsonl")) if args.baseline else 0
    grids(out, rows)
    with (out / "candidates.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (out / "detect.json").write_text(json.dumps({
        "when": utc_now().isoformat(), "params": {p: vars(PROFILES[p]()) for p in args.profiles},
        "bridge_width": BRIDGE_WIDTH, "work_width": WORK_WIDTH, "fps": FPS,
        "window": {"before_s": BEFORE_S, "after_s": AFTER_S, "max_clip_s": MAX_CLIP_S, "direct_below": DIRECT_BELOW},
        "people": "yolo11m" if model else None, "clips": summaries, "duplicates": n_dup,
        "world_floor_m2": args.world_floor, "at_least": args.at_least, "scales": str(args.scales) if scales else None,
        "baseline": str(args.baseline) if args.baseline else None, "same_as_baseline": n_same}, indent=1),
        encoding="utf-8")
    log(f"{len(rows)} candidates ({sum(r['profile'] == 'real' for r in rows)} real-setting, "
        f"{sum(r['profile'] == 'loops' for r in rows)} looped-setting of which {n_dup} the same spot as a real-setting "
        f"one; {n_same} the same spot and time as a baseline candidate); wrote {out / 'candidates.jsonl'}")
    return 0


# --- play ---------------------------------------------------------------------------------------------------------
def choose(run: Path, cap: int) -> list[dict]:
    cands = load_jsonl(run / "candidates.jsonl")
    real = [c for c in cands if c["profile"] == "real" and not c.get("same_as")]
    extra = [c for c in cands if c["profile"] == "loops" and not c.get("dup_of") and not c.get("same_as")]
    room = max(0, cap - len(real))
    if len(extra) > room:
        extra = [extra[int(i * len(extra) / room)] for i in range(room)] if room else []
    return real + extra


def play(args) -> int:
    from lens.client import submit, wait
    from lens.clock import LensClock
    run = args.run
    chosen = choose(run, args.max)
    labels = json.loads((run / "labels.json").read_text(encoding="utf-8")) if (run / "labels.json").exists() else {}
    print(f"{len(chosen)} clips to play ({sum(c['profile'] == 'real' for c in chosen)} real-setting, the rest "
          f"looped-setting extras; cap {args.max}); {len(labels)} labels")
    clock = LensClock.standalone(log=lambda s: print(s, flush=True))
    t0 = time.monotonic()
    while not clock.alive() and time.monotonic() - t0 < 90:
        time.sleep(0.5)
    if not clock.alive():
        sys.exit("no readable lens_1 frame in 90 s: is lens.publisher running (scripts\\start_lens.ps1)?")
    print(f"lens clock alive after {time.monotonic() - t0:.1f} s, offset {clock.offset()} s", flush=True)
    rows = []
    with (run / "clips.jsonl").open("w", encoding="utf-8") as f:
        for k, c in enumerate(chosen, 1):
            frames_, fps = read_clip(run / c["avi"])
            for attempt in (1, 2):
                job = submit(frames_, f"ho-{c['cid']}", fps=int(round(fps)))
                done = wait(job, timeout=300)
                start, end, info = clock.span_for(done)
                if info.get("verified") or attempt == 2:
                    break
                print(f"  clip {k}: not verified ({info.get('reason') or info}), playing once more", flush=True)
                time.sleep(3.0)
            truth, note = (labels.get(c["cid"]) or [None, ""])[:2]
            row = {"k": k, "cid": c["cid"], "clip": c["clip"], "profile": c["profile"], "view": c["view"],
                   "magnification": c["magnification"], "t_detect": c["t_detect"], "truth": truth, "note": note,
                   "avi": c["avi"], "job": job, "frames": len(frames_), "fps": fps,
                   "wall": [done["start"], done["end"]], "span": [start.isoformat(), end.isoformat()],
                   "attempt": attempt, **{a: b for a, b in info.items() if a != "ready_wall"}}
            rows.append(row)
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(f"clip {k:2d} {c['cid']:28} {len(frames_):3d}f recorded {start:%H:%M:%S}-{end:%H:%M:%S} "
                  f"seen {info['seen']}/{done['sent']} offset {info.get('offset_s')} s verified {info['verified']}",
                  flush=True)
    clock.close()
    print(f"{len(rows)} clips played, {sum(1 for r in rows if r.get('verified'))} spans verified; "
          f"wrote {run / 'clips.jsonl'}")
    return 0


# --- ask ----------------------------------------------------------------------------------------------------------
def ask(args) -> int:
    from hafnia.gateway import Gateway, Tracked, video_uri
    from hafnia.xprotect_rest import XProtect
    from lens_compare import gateway_password
    run = args.run
    clips = load_jsonl(run / "clips.jsonl")
    done = {r["k"] for r in load_jsonl(run / "results.jsonl") if r.get("progress") == "Completed"}
    plan = [c for c in clips if c["k"] not in done]
    print(f"{len(plan)} requests planned, one per clip with the service's prompt ({len(clips)} clips, "
          f"{len(done)} answered already)")
    if args.dry_run:
        return 0
    gw = Gateway()
    gw.login(gateway_password())
    q = gw.quota() or {}
    q0 = q.get("DailySummaryCount")
    print(f"today's count before: {q0} of {q.get('DailySummaryQuota')}")
    if q0 is not None and q0 + len(plan) > args.stop_at:
        sys.exit(f"{len(plan)} more would pass --stop-at {args.stop_at}")
    system = gw.system_prompt()
    if system:
        sys.exit(f"the gateway's system prompt is not empty ({system!r}): the service runs without one")
    (run / "prompt.json").write_text(json.dumps({"prompt": PROMPT, "system_prompt": system}, indent=1,
                                                ensure_ascii=False), encoding="utf-8")
    lens_id = XProtect().cameras()["lens_1"]
    n_done = 0
    try:
        with (run / "results.jsonl").open("a", encoding="utf-8") as f:
            for i in range(0, len(plan), PARALLEL):
                tracked = []
                for c in plan[i:i + PARALLEL]:
                    start = dt.datetime.fromisoformat(c["span"][0])
                    end = dt.datetime.fromisoformat(c["span"][1])
                    t0 = time.monotonic()
                    created = gw.ask(video_uri(lens_id, start, end), PROMPT)
                    tracked.append((c, Tracked(created["Id"], submitted=t0, summary=created)))
                gw.wait_all([t for _, t in tracked], poll=1.0, timeout=600)
                for c, t in tracked:
                    s = t.summary
                    answer = s.get("Response") or ""
                    p = parse_answer(answer) if answer else {"category": "UNPARSED", "json_ok": False}
                    secs = round(time.monotonic() - t.submitted, 1)
                    rec = {"k": c["k"], "cid": c["cid"], "clip": c["clip"], "profile": c["profile"],
                           "view": c["view"], "truth": c["truth"], "span": c["span"], "summary_id": t.id,
                           "progress": s.get("Progress"), "error": s.get("LastError"), "response": answer,
                           "category": p["category"], "json_ok": p.get("json_ok", False),
                           "fields": {a: b for a, b in p.items() if a not in ("category", "json_ok")},
                           "seconds": secs, "phases": {k: round(v - t.submitted, 1) for k, v in t.seen.items()},
                           "chars": len(answer), "wall": utc_now().isoformat()}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    n_done += s.get("Progress") == "Completed"
                    mark = "ok" if p["category"] == c["truth"] else ("?" if c["truth"] is None else "WRONG")
                    print(f"  clip {c['k']:2d} {c['cid']:28} -> {p['category']:16} {mark:5} ({s.get('Progress')}, "
                          f"{secs} s) {str(p.get('summary') or '')[:90]}", flush=True)
    finally:
        q1 = (gw.quota() or {}).get("DailySummaryCount")
        print(f"today's count after: {q1} ({n_done} completed here)")
        gw.logout()
    return 0


# --- score --------------------------------------------------------------------------------------------------------
def score(args) -> int:
    run = args.run
    det = json.loads((run / "detect.json").read_text(encoding="utf-8"))
    cands = load_jsonl(run / "candidates.jsonl")
    clips = {c["k"]: c for c in load_jsonl(run / "clips.jsonl")}
    labels = json.loads((run / "labels.json").read_text(encoding="utf-8")) if (run / "labels.json").exists() else {}
    results: dict[int, dict] = {}
    for r in load_jsonl(run / "results.jsonl"):     # the last answer per clip wins
        if r.get("response"):
            r["json_ok"] = parse_answer(r["response"])["json_ok"]
        results[r["k"]] = r
    for k, c in clips.items():                      # labels may have been added after play
        if c["cid"] in labels:
            c["truth"], c["note"] = (labels[c["cid"]] + [""])[:2]

    def tally(ks: list[int]) -> dict:
        asked = [k for k in ks if k in results]
        answered = [k for k in asked if results[k].get("progress") == "Completed"]
        scored = [k for k in answered if clips[k].get("truth")]
        none = [k for k in scored if clips[k]["truth"] == "NONE"]
        inc = [k for k in scored if clips[k]["truth"] != "NONE"]
        false = [k for k in none if results[k]["category"] != "NONE"]
        missed = [k for k in inc if results[k]["category"] == "NONE"]
        wrong = [k for k in inc if results[k]["category"] not in ("NONE", clips[k]["truth"])]
        return {"asked": len(asked), "answered": len(answered), "failed": len(asked) - len(answered),
                "scored": len(scored), "none": len(none),
                "incidents": len(inc), "right": len(scored) - len(false) - len(missed) - len(wrong),
                "false_cards": len(false), "missed": len(missed), "wrong_category": len(wrong),
                "false_ks": false, "ambiguous": len([k for k in answered if not clips[k].get("truth")]),
                "json_ok": sum(results[k].get("json_ok", False) for k in answered)}

    sets = {
        "real-setting candidates (what the service would send from a real camera)":
            [k for k, c in clips.items() if c["profile"] == "real"],
        "looped-setting extras (things that paused 1.5 s; more hard negatives)":
            [k for k, c in clips.items() if c["profile"] == "loops"],
        "all": list(clips),
    }
    by_view = {v: [k for k, c in clips.items() if c["view"] == v] for v in ("lens", "direct")}
    summary = {"sets": {name: tally(ks) for name, ks in sets.items()},
               "views": {v: tally(ks) for v, ks in by_view.items()},
               "detector": det["clips"], "duplicates": det.get("duplicates"),
               "candidates": len(cands), "played": len(clips), "answered": len(results),
               "lens_verified": sum(1 for c in clips.values() if c.get("verified")),
               "hafnia_phase_s": sorted(r["phases"].get("Completed", r["seconds"]) for r in results.values()
                                        if r.get("progress") == "Completed")}
    (run / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    lines = [TABLES_MARK, "",
             f"{len(cands)} candidates from the detector ({det.get('duplicates')} looped-setting ones the same spot as "
             f"a real-setting one), {len(clips)} played on `lens_1` ({summary['lens_verified']} spans verified), "
             f"{len(results)} answered with the service's prompt. Labels by eye (`labels.json`); an ambiguous "
             f"candidate (no label) is listed, not scored.", "",
             "## The detector on the three streets", "",
             "| Clip | Setting | Seconds scored | Reports | Per hour | Scene jumps |", "|---|---|---|---|---|---|"]
    for s in det["clips"]:
        lines.append(f"| {s['clip']} | {s['profile']} | {s['seconds']} | {s['reports']} | {s['per_hour']} | "
                     f"{s['scene_jumps']} |")
    lines += ["", "## Hafnia's answers", "",
              "| Set | Asked | Answered | Failed | Scored | Of them NONE | Incidents | Right | False cards | Missed | Wrong category | Valid JSON |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, t in summary["sets"].items():
        lines.append(f"| {name} | {t['asked']} | {t['answered']} | {t['failed']} | {t['scored']} | {t['none']} | "
                     f"{t['incidents']} | {t['right']} | {t['false_cards']} | {t['missed']} | {t['wrong_category']} | "
                     f"{t['json_ok']} |")
    for v, t in summary["views"].items():
        lines.append(f"| view: {v} | {t['asked']} | {t['answered']} | {t['failed']} | {t['scored']} | {t['none']} | "
                     f"{t['incidents']} | {t['right']} | {t['false_cards']} | {t['missed']} | {t['wrong_category']} | "
                     f"{t['json_ok']} |")
    lines += ["", "## Every candidate asked", "",
              "| # | Candidate | Setting | At (s) | View | Truth | Answer | Hafnia says |", "|---|---|---|---|---|---|---|---|"]
    for k in sorted(clips):
        c, r = clips[k], results.get(k)
        if not r:
            continue
        f = r.get("fields", {})
        said = str(f.get("summary") or r.get("error") or "")[:160].replace("|", "/")
        if r.get("progress") != "Completed":
            answer = "failed"
        else:
            answer = r["category"] + ("" if c.get("truth") is None else (" ✓" if r["category"] == c["truth"] else " ✗"))
        lines.append(f"| {k} | {c['cid']} | {c['profile']} | {c['t_detect']} | {c['view']} x{c['magnification']} | "
                     f"{c.get('truth') or '?'} | {answer} | {said} |")
    readme = run / "README.md"
    head = ""
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        head = text.split(TABLES_MARK)[0] if TABLES_MARK in text else text + "\n"
    readme.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    ans = ["# Every answer", ""]
    for k in sorted(clips):
        c, r = clips[k], results.get(k)
        if not r:
            continue
        ans += [f"## {k}. {c['cid']} ({c['profile']}, {c['view']} x{c['magnification']}, at {c['t_detect']} s)", "",
                f"Truth: {c.get('truth')}. {c.get('note') or ''}", "", f"Answer: **{r['category']}**", "", "```",
                (r.get("response") or r.get("error") or "").strip(), "```", ""]
    (run / "answers.md").write_text("\n".join(ans), encoding="utf-8")
    for name, t in summary["sets"].items():
        print(f"{name}: asked {t['asked']}, answered {t['answered']} (failed {t['failed']}), scored {t['scored']} "
              f"({t['none']} NONE, {t['incidents']} incidents): right {t['right']}, false cards {t['false_cards']}, "
              f"missed {t['missed']}, wrong {t['wrong_category']}")
    print(f"wrote {readme}, answers.md, summary.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="stage", required=True)
    d = sub.add_parser("detect")
    d.add_argument("--out", type=Path, default=DEFAULT_OUT)
    d.add_argument("--only", nargs="+", choices=list(CLIPS))
    d.add_argument("--profiles", nargs="+", choices=list(PROFILES), default=list(PROFILES))
    d.add_argument("--no-people", action="store_true")
    d.add_argument("--scales", type=Path, help="scales.json from scale_fit.py (the calibrated-floor test)")
    d.add_argument("--world-floor", type=float, help="square metres a blob must cover at its row (needs --scales)")
    d.add_argument("--at-least", type=float, default=0.0,
                   help="with --world-floor: the floor never goes below this share of the frame (0: pure)")
    d.add_argument("--baseline", type=Path, help="a run whose candidates at the same spot and time are not asked again")
    d.set_defaults(fn=detect)
    p = sub.add_parser("play")
    p.add_argument("run", type=Path)
    p.add_argument("--max", type=int, default=40, help="clips to play and ask, at most")
    p.set_defaults(fn=play)
    a = sub.add_parser("ask")
    a.add_argument("run", type=Path)
    a.add_argument("--stop-at", type=int, default=450)
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(fn=ask)
    s = sub.add_parser("score")
    s.add_argument("run", type=Path)
    s.set_defaults(fn=score)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
