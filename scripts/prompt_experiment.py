r"""prompt_experiment.py - does a system prompt, or a structured prompt, improve Hafnia's answers on Clearway's clips?

    .venv\Scripts\python.exe scripts\prompt_experiment.py play [--out run\prompt-<UTC>]
    .venv\Scripts\python.exe scripts\prompt_experiment.py ask run\prompt-<UTC> [--cells A B ...] [--stop-at 450] [--dry-run]
    .venv\Scripts\python.exe scripts\prompt_experiment.py score run\prompt-<UTC>
    .venv\Scripts\python.exe scripts\prompt_experiment.py restore

The question (2026-10-28): the gateway's Advanced Settings hold a *System Prompt*, empty on this machine, sent
before the prompt with every request; Clearway's prompt (clearway/prompt.py) is one paragraph of JSON instructions.
Hafnia was trained with "You are a CCTV traffic analyst. Validate upstream alerts. Think briefly, then output in
JSON format." and an AlertValidation JSON task (Milestone's article on Hafnia's training). Which of these helps on the clips the
service really sends?

Test set: the clips the service sent on 2026-10-26 (the three-hour shift) and 2026-10-27 (the 20-minute run), kept
in run/lens/spool as AVIs: crops around the spot, direct asks' crops included. Each is labelled by eye from its
frames (TESTSET): 17 incidents and 11 clips that show none, among them the shift's false cards (a street crop
called STALLED_VEHICLE, a fence called PERSON_ON_TRACKS) and the scooter crop that became "a tree branch".

`play` shows every clip once on the lens camera (lens.client.submit) and measures the span lens_1 recorded it in
from its own frames (lens/clock.py, verified), so every prompt variant is asked about the same recorded seconds.
Hafnia answers the same clip and prompt with the same words (pilot, 2026-10-23), so one request per clip and
variant is the whole sample. `ask` runs the cells (CELLS: a system prompt x a user prompt), switching the gateway's
system prompt through its Settings API between batches, and leaves it as it was (empty). `score` writes README.md
with the category accuracy, false cards, misses, JSON validity, confidence, length and latency per cell, the
per-clip matrix and every answer. Requests: one per clip and cell; the plan is printed first and --dry-run stops
there. Needs lens.publisher (scripts\start_lens.ps1) and FrameBridge (lens_1's frames for the clock).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.prompt import CATEGORIES, PROMPT, parse  # noqa: E402

SPOOL = REPO / "run" / "lens" / "spool"
PARALLEL = 3            # requests in flight at once, as the service
TABLES_MARK = "<!-- tables: written by prompt_experiment.py score; the text above is kept -->"

# --- the test set: (spool AVI, truth, note). truth None: ambiguous, kept for the answers but not scored. ----------
TESTSET = [
    ("20261026T141630839929_cw-0001-person_on_railway_tracks.avi", "PERSON_ON_TRACKS",
     "full frame: sits on the track edge, legs on the track"),
    ("20261026T141635268961_cw-0002-escooter_left_across_sidewalk.avi", "OBSTRUCTION",
     "scooter laid down on the pavement, rider walks away"),
    ("20261026T141640693547_cw-0004-school_gate_break_in_night.avi", "NONE",
     "fence at night, nobody (the shift answered PERSON_ON_TRACKS: the lens lag)"),
    ("20261026T141643796829_cw-0007-bin_pushed_over_onto_sidewalk.avi", "NONE",
     "1.7 s: the street with a passing car, no bin (the shift's false OBSTRUCTION)"),
    ("20261026T141645171209_cw-0008-vehicle_breakdown_traffic_queue.avi", "STALLED_VEHICLE",
     "pickup with smoke, door open, driver out, car queued"),
    ("20261026T141651457474_cw-0012-school_gate_break_in_night.avi", "NONE",
     "fence and pavement at night, nobody"),
    ("20261026T141652792754_cw-0014-graffiti_on_standing_train.avi", "DAMAGE",
     "sprays graffiti on the train, walks away (the shift: 'tree trunk', OBSTRUCTION)"),
    ("20261026T141653717085_cw-0015-school_gate_break_in_night.avi", "TAMPERING",
     "cuts the gate's chain with bolt cutters"),
    ("20261026T141654425006_cw-0013-busy_street.avi", "NONE",
     "dark crowd with phones (busy_street crop)"),
    ("20261026T141706898983_cw-0019-bin_pushed_over_onto_sidewalk.avi", "OBSTRUCTION",
     "pushes the bin over, walks away"),
    ("20261026T141736188745_cw-0021-bin_pushed_over_onto_sidewalk.avi", "OBSTRUCTION",
     "close crop of the bin lying on the pavement"),
    ("20261026T141838439462_cw-0023-traffic_flows_in_the_open_lanes.avi", "NONE",
     "a van drives through, then empty lanes"),
    ("20261026T142130997697_cw-0024-traffic_flows_in_the_open_lanes.avi", "NONE",
     "empty lanes, a car's roof passes (the shift's false STALLED_VEHICLE)"),
    ("20261026T144525864700_cw-0028-school_gate_break_in_night.avi", "NONE",
     "legs walk past the fence, then pavement"),
    ("20261026T150515433995_cw-0031-school_gate_break_in_night.avi", "TAMPERING",
     "person with bolt cutters crouches at the lock"),
    ("20261026T151400177617_cw-0032-escooter_left_across_sidewalk.avi", "NONE",
     "a person walks, a rider rides the scooter away"),
    ("20261026T152514382319_cw-0033-bin_pushed_over_onto_sidewalk.avi", "NONE",
     "a car drives past, then the empty street"),
    ("20261027T124152361867_cw-0001-bin_pushed_over_onto_sidewalk.avi", "OBSTRUCTION",
     "pushes the bin over, walks away"),
    ("20261027T124201017167_cw-0003-vehicle_breakdown_traffic_queue.avi", "STALLED_VEHICLE",
     "pickup with smoke, driver gets out"),
    ("20261027T124204585257_cw-0004-person_on_railway_tracks.avi", "PERSON_ON_TRACKS",
     "sits on the edge, steps onto the tracks, walks along them"),
    ("20261027T124205701116_cw-0005-school_gate_break_in_night.avi", "TAMPERING",
     "crouches at the lock with a tool"),
    ("20261027T124206301555_cw-0006-escooter_left_across_sidewalk.avi", "OBSTRUCTION",
     "hard crop: the rider lays the scooter down, only its handlebar stays in view ('a tree branch' on 10-27)"),
    ("20261027T124207866831_cw-0008-graffiti_on_standing_train.avi", "DAMAGE",
     "sprays graffiti, walks away (OBSTRUCTION before the negatives)"),
    ("20261027T124210265311_cw-0009-school_gate_break_in_night.avi", "NONE",
     "the fence's top at night, nobody (the 'wrong seconds' clip)"),
    ("20261027T124211337185_cw-0010-school_gate_break_in_night.avi", "TAMPERING",
     "crop: crouched at the lock with cutters, the lock, legs leave"),
    ("20261027T124212362072_cw-0011-person_on_railway_tracks.avi", "PERSON_ON_TRACKS",
     "crop: red jacket at the edge, tracks, sitting with legs on the track"),
    ("20261027T124213501036_cw-0012-escooter_left_across_sidewalk.avi", "OBSTRUCTION",
     "crop: scooter lying, pavement empty, rider rides off"),
    ("20261027T124225065659_cw-0013-school_gate_break_in_night.avi", "TAMPERING",
     "crouched at the gate with the tool, lock and chain hang, leaves"),
]

# --- system prompts (the gateway's Advanced Settings) -------------------------------------------------------------
SYSTEM = {
    "none": "",
    # Milestone's article on Hafnia's training: https://www.milestonesys.com/resources/content/articles/smart-city-video-intelligence/
    "trained": "You are a CCTV traffic analyst. Validate upstream alerts. Think briefly, then output in JSON format.",
    # Clearway's own context: what every clip is, and the two habits seen in wrong answers (invented objects, crops)
    "clearway": (
        "You are a CCTV analyst for a city's right-of-way operations: things that block or endanger a public way. "
        "Each clip comes from a fixed camera and may be a magnified crop of one spot, so objects can be cut off at "
        "the edges and look large. Describe only what the frames show; do not guess tools, vehicles or people you "
        "cannot see. Output JSON only, no other text."),
}

# --- user prompts -------------------------------------------------------------------------------------------------
CATEGORY_LINES = (
    "- PERSON_ON_TRACKS: a person on railway tracks, not on a platform.\n"
    "- COLLISION: a vehicle hits another vehicle, a person, a barrier or an object, or spins out of control.\n"
    "- STALLED_VEHICLE: a vehicle stopped or broken down in a traffic lane. Not a vehicle parked at a kerb or "
    "queued behind others.\n"
    "- OBSTRUCTION: an object left lying across a pavement, path or road so that people or vehicles cannot pass. "
    "Not someone painting, breaking or forcing something.\n"
    "- DAMAGE: property damaged or defaced: graffiti being painted, glass broken, a surface cut or burnt. Choose "
    "this even if the damaged thing is next to a path.\n"
    "- TAMPERING: someone forcing, cutting or picking a lock, gate or door.\n"
    "- NONE: none of these: ordinary traffic, people walking, parked vehicles, a stationary train.")
FIELDS = (
    '"object": "<the main object or person involved, at most four words>", '
    '"where": "<one of: track, lane, pavement, platform, other>", '
    '"still_present": <true or false: whether that object or person is still there at the end of the video>, '
    '"summary": "<one sentence on what happens, in the order it happens>"')
PROMPTS = {
    # the service's prompt as it is (one paragraph, definitions with negatives)
    "current": PROMPT,
    # the same content laid out in sections, one category per line, the JSON as a template
    "structured": (
        "TASK\nWatch this CCTV clip, name the one incident category it shows, and describe it.\n\n"
        "CATEGORIES, exactly one:\n" + CATEGORY_LINES + "\n\n"
        "OUTPUT, JSON only, no other text:\n"
        '{"category": "<one category name from the list>", ' + FIELDS + "}"),
    # the structured layout plus context (fixed camera, crop, the detector's alert), rules against invented
    # objects, and two new fields: confidence and evidence
    "structured_plus": (
        "CONTEXT\nThe clip comes from a fixed CCTV camera and may be a magnified crop of one spot, so objects can "
        "be cut off at the edges and look large. An automatic detector flagged this spot because something there "
        "changed and stayed changed; the detector does not know what it is.\n\n"
        "TASK\nWatch the clip, name the one incident category it shows, and describe it.\n\n"
        "CATEGORIES, exactly one:\n" + CATEGORY_LINES + "\n\n"
        "RULES\n"
        "- Describe only what the frames show. Do not guess tools, vehicles or people you cannot see; if the "
        "object is unclear, write \"unclear object\".\n"
        "- If the frames do not clearly show one of the six incidents, answer NONE.\n"
        "- Tell the summary in the order things happen in the clip.\n\n"
        "OUTPUT, JSON only, no other text:\n"
        '{"category": "<one category name from the list>", '
        '"confidence": <0.0 to 1.0: how sure you are of the category>, ' + FIELDS + ", "
        '"evidence": "<what in the frames supports the category, at most twelve words>"}'),
    # Hafnia's trained AlertValidation shape: an upstream alert in, confirm or discard out
    "alert": (
        "You are validating an upstream alert from an automatic change detector on a fixed CCTV camera.\n"
        "Upstream alert: a lasting change at the spot shown in this clip (something arrived and stayed, or someone "
        "is acting on something there), confidence 0.60. The alert does not say what the change is; the clip may "
        "be a magnified crop of the spot.\n"
        "Validate the alert: confirm it only if the clip clearly shows one of these right-of-way incidents, "
        "otherwise discard it.\n\n"
        "CATEGORIES:\n" + CATEGORY_LINES + "\n\n"
        "Reply with JSON only, no other text:\n"
        '{"decision": "<confirm or discard>", "category": "<the category when confirm; NONE when discard>", '
        '"confidence": <0.0 to 1.0>, "reason": "<one sentence on what the frames show, in the order it happens>", '
        '"evidence_frames": "<start, middle or end of the clip>", '
        '"object": "<the main object or person involved, at most four words>", "still_present": <true or false>}'),
}
PROMPTS["trained_in_user"] = SYSTEM["trained"] + "\n\n" + PROMPT   # the trained text as part of the user prompt

# cell -> (system prompt, user prompt, how many clips: None = all). Ordered so the system prompt changes least.
CELLS = {
    "A": ("none", "current", None),           # the service today
    "B": ("none", "structured", None),        # layout alone
    "C": ("none", "structured_plus", None),   # layout, context, rules, confidence
    "D": ("none", "alert", None),             # the trained AlertValidation shape
    "I": ("none", "trained_in_user", 10),     # == E word for word if the gateway only prepends the text
    "E": ("trained", "current", None),
    "F": ("trained", "structured_plus", None),
    "G": ("clearway", "current", None),
    "H": ("clearway", "structured_plus", None),
    "R": ("none", "current", 5),              # after the system prompt is cleared again: == A word for word
    "A2": ("none", "current", None),          # the baseline once more: how much the answers vary on their own
}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def read_clip(path: Path):
    import cv2
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    fps = cap.get(cv2.CAP_PROP_FPS) or 10.0
    cap.release()
    return frames, fps


# --- play ---------------------------------------------------------------------------------------------------------
def play(args) -> int:
    from lens.client import submit, wait
    from lens.clock import LensClock
    out = args.out or REPO / "run" / f"prompt-{utc_now():%Y%m%dT%H%M%SZ}"
    out.mkdir(parents=True, exist_ok=True)
    missing = [a for a, _, _ in TESTSET if not (SPOOL / a).exists()]
    if missing:
        sys.exit(f"{len(missing)} clips missing from {SPOOL}: {missing[:3]}")
    clock = LensClock.standalone(log=lambda s: print(s, flush=True))
    t0 = time.monotonic()
    while not clock.alive() and time.monotonic() - t0 < 90:
        time.sleep(0.5)
    if not clock.alive():
        sys.exit("no readable lens_1 frame in 90 s: is lens.publisher running (scripts\\start_lens.ps1)?")
    print(f"lens clock alive after {time.monotonic() - t0:.1f} s, offset {clock.offset()} s", flush=True)
    rows = []
    with (out / "clips.jsonl").open("w", encoding="utf-8") as f:
        for k, (avi, truth, note) in enumerate(TESTSET, 1):
            frames, fps = read_clip(SPOOL / avi)
            for attempt in (1, 2):
                job = submit(frames, f"pe{k:02d}-{avi.split('_', 1)[1][:36]}", fps=int(round(fps)))
                done = wait(job, timeout=300)
                start, end, info = clock.span_for(done)
                if info.get("verified") or attempt == 2:
                    break
                print(f"  clip {k}: not verified ({info.get('reason') or info}), playing once more", flush=True)
                time.sleep(3.0)
            row = {"k": k, "avi": avi, "truth": truth, "note": note, "job": job, "frames": len(frames),
                   "fps": fps, "wall": [done["start"], done["end"]],
                   "span": [start.isoformat(), end.isoformat()], "attempt": attempt,
                   **{a: b for a, b in info.items() if a != "ready_wall"}}
            rows.append(row)
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(f"clip {k:2d} {avi[16:52]:36} {len(frames):3d}f recorded {start:%H:%M:%S}-{end:%H:%M:%S} "
                  f"seen {info['seen']}/{done['sent']} offset {info.get('offset_s')} s drift {info.get('drift_s')} "
                  f"verified {info['verified']}", flush=True)
    clock.close()
    n_ok = sum(1 for r in rows if r.get("verified"))
    print(f"{len(rows)} clips played, {n_ok} spans verified; wrote {out / 'clips.jsonl'}")
    return 0


# --- ask ----------------------------------------------------------------------------------------------------------
def load_clips(run: Path) -> list[dict]:
    return [json.loads(x) for x in (run / "clips.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def load_results(run: Path) -> list[dict]:
    p = run / "results.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def parse_answer(answer: str) -> dict:
    """clearway.prompt.parse plus the alert shape: a discard with no category is NONE, and the JSON is ok when it
    parsed with a category (the service's parse wants a summary, which the alert shape calls reason)."""
    p = parse(answer)
    if p["category"] not in CATEGORIES and str(p.get("decision", "")).lower() == "discard":
        p["category"] = "NONE"
    try:
        p["json_ok"] = "category" in json.loads(__import__("re").search(r"\{.*\}", answer, 16).group(0))
    except (AttributeError, json.JSONDecodeError, TypeError):
        p["json_ok"] = False
    return p


def ask(args) -> int:
    from hafnia.gateway import Gateway, Tracked, video_uri
    from hafnia.xprotect_rest import XProtect
    from lens_compare import gateway_password
    run = args.run
    clips = load_clips(run)
    done = {(r["cell"], r["k"]) for r in load_results(run) if r.get("progress") == "Completed"}
    cells = args.cells or list(CELLS)
    plan = []
    for cell in cells:
        system, prompt, n = CELLS[cell]
        for c in clips[: n or len(clips)]:
            if (cell, c["k"]) not in done:
                plan.append((cell, system, prompt, c))
    print(f"{len(plan)} requests planned over cells {' '.join(cells)} ({len(clips)} clips; "
          f"{len(done)} answers already in results.jsonl)")
    for cell in cells:
        system, prompt, n = CELLS[cell]
        print(f"  {cell}: system {system!r:12} prompt {prompt!r:18} clips {n or len(clips)}")
    if args.dry_run:
        return 0
    gw = Gateway()
    gw.login(gateway_password())
    q = gw.quota() or {}
    q0 = q.get("DailySummaryCount")
    print(f"today's count before: {q0} of {q.get('DailySummaryQuota')}")
    if q0 is not None and q0 + len(plan) > args.stop_at:
        sys.exit(f"{len(plan)} more would pass --stop-at {args.stop_at}")
    original = gw.system_prompt()
    print(f"the gateway's system prompt before: {original!r}")
    (run / "prompts.json").write_text(json.dumps({"system": SYSTEM, "prompts": PROMPTS, "cells": CELLS,
                                                   "system_prompt_before": original}, indent=1, ensure_ascii=False),
                                      encoding="utf-8")
    lens_id = XProtect().cameras()["lens_1"]
    current_system = original
    n_done = 0
    try:
        with (run / "results.jsonl").open("a", encoding="utf-8") as f:
            i = 0
            while i < len(plan):
                cell, system, prompt, _ = plan[i]
                if SYSTEM[system] != current_system:
                    gw.set_system_prompt(SYSTEM[system])
                    current_system = gw.system_prompt()
                    assert current_system == SYSTEM[system], current_system
                    print(f"system prompt set to {system!r}", flush=True)
                    time.sleep(2.0)
                batch = []
                while i < len(plan) and len(batch) < PARALLEL and plan[i][1] == system:
                    batch.append(plan[i])
                    i += 1
                tracked = []
                for cell, system, prompt, c in batch:
                    start = dt.datetime.fromisoformat(c["span"][0])
                    end = dt.datetime.fromisoformat(c["span"][1])
                    t0 = time.monotonic()
                    created = gw.ask(video_uri(lens_id, start, end), PROMPTS[prompt])
                    tracked.append((cell, system, prompt, c, Tracked(created["Id"], submitted=t0, summary=created)))
                gw.wait_all([t for *_, t in tracked], poll=1.0, timeout=600)
                for cell, system, prompt, c, t in tracked:
                    s = t.summary
                    answer = s.get("Response") or ""
                    p = parse_answer(answer) if answer else {"category": "UNPARSED", "json_ok": False}
                    secs = round(time.monotonic() - t.submitted, 1)
                    phases = {k: round(v - t.submitted, 1) for k, v in t.seen.items()}
                    rec = {"cell": cell, "system": system, "prompt": prompt, "k": c["k"], "avi": c["avi"],
                           "truth": c["truth"], "span": c["span"], "summary_id": t.id,
                           "progress": s.get("Progress"), "error": s.get("LastError"), "response": answer,
                           "category": p["category"], "json_ok": p.get("json_ok", False),
                           "fields": {a: b for a, b in p.items() if a not in ("category", "json_ok")},
                           "seconds": secs, "phases": phases, "chars": len(answer),
                           "wall": utc_now().isoformat()}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    n_done += s.get("Progress") == "Completed"
                    mark = "ok" if p["category"] == c["truth"] else ("?" if c["truth"] is None else "WRONG")
                    print(f"  {cell} clip {c['k']:2d} {c['avi'][16:46]:30} -> {p['category']:16} {mark:5} "
                          f"({s.get('Progress')}, {secs} s) {str(p.get('summary') or p.get('reason') or '')[:90]}",
                          flush=True)
    finally:
        if gw.system_prompt() != original:
            gw.set_system_prompt(original)
            print(f"system prompt restored to {original!r}")
        q1 = (gw.quota() or {}).get("DailySummaryCount")
        print(f"today's count after: {q1} ({n_done} completed here)")
        gw.logout()
    return 0


# --- restore ------------------------------------------------------------------------------------------------------
def restore(args) -> int:
    from hafnia.gateway import Gateway
    from lens_compare import gateway_password
    gw = Gateway()
    gw.login(gateway_password())
    print(f"system prompt was {gw.system_prompt()!r}")
    gw.set_system_prompt("")
    print(f"system prompt now {gw.system_prompt()!r}")
    gw.logout()
    return 0


# --- score --------------------------------------------------------------------------------------------------------
def score(args) -> int:
    run = args.run
    clips = {c["k"]: c for c in load_clips(run)}
    results = load_results(run)
    by_cell: dict[str, dict[int, dict]] = {}
    for r in results:                      # the last answer of a (cell, clip) wins
        if r.get("response"):
            r["json_ok"] = parse_answer(r["response"])["json_ok"]
        by_cell.setdefault(r["cell"], {})[r["k"]] = r
    scored = [k for k, c in clips.items() if c["truth"]]
    positives = [k for k in scored if clips[k]["truth"] != "NONE"]
    negatives = [k for k in scored if clips[k]["truth"] == "NONE"]
    lines = []
    summary = {}
    lines.append(f"# Prompt experiment: a system prompt and structured prompts on Clearway's clips ({run.name})\n")
    lines.append(f"{len(clips)} clips from the lens spool, played again on `lens_1` and asked about the same "
                 f"recorded seconds in every cell; {len(scored)} scored ({len(positives)} incidents, "
                 f"{len(negatives)} with none). One request per clip and cell. See `prompts.json` for the texts, "
                 f"`results.jsonl` for every answer, `answers.md` for the answers by clip.\n")
    lines.append("## Cells\n")
    lines.append("| Cell | System prompt | User prompt | Answers | JSON ok | Right category | False cards (of "
                 f"{len(negatives)}) | Missed (of {len(positives)}) | Wrong category | Confidence right / wrong | "
                 "Chars | Seconds (median) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for cell, (system, prompt, n) in CELLS.items():
        rows = by_cell.get(cell, {})
        if not rows:
            continue
        comp = [r for r in rows.values() if r["progress"] == "Completed"]
        sc = [r for r in comp if r["k"] in scored]
        right = [r for r in sc if r["category"] == clips[r["k"]]["truth"]]
        false_cards = [r for r in sc if clips[r["k"]]["truth"] == "NONE" and r["category"] != "NONE"]
        missed = [r for r in sc if clips[r["k"]]["truth"] != "NONE" and r["category"] == "NONE"]
        wrong_cat = [r for r in sc if clips[r["k"]]["truth"] != "NONE" and r["category"] != "NONE"
                     and r["category"] != clips[r["k"]]["truth"]]
        json_ok = sum(1 for r in comp if r["json_ok"])
        confs_r = [float(r["fields"]["confidence"]) for r in right if _num(r["fields"].get("confidence"))]
        confs_w = [float(r["fields"]["confidence"]) for r in sc if r not in right
                   and _num(r["fields"].get("confidence"))]
        conf = (f"{statistics.mean(confs_r):.2f} / {statistics.mean(confs_w):.2f}" if confs_r and confs_w
                else (f"{statistics.mean(confs_r):.2f} / -" if confs_r else "-"))
        chars = round(statistics.mean(r["chars"] for r in comp)) if comp else 0
        secs = statistics.median(r["seconds"] for r in comp) if comp else 0
        n_sc = len(sc)
        lines.append(f"| {cell} | {system} | {prompt} | {len(comp)} of {len(rows)} | {json_ok} | "
                     f"**{len(right)} of {n_sc}** | {len(false_cards)} | {len(missed)} | {len(wrong_cat)} | {conf} | "
                     f"{chars} | {secs:.1f} |")
        summary[cell] = {"system": system, "prompt": prompt, "completed": len(comp), "json_ok": json_ok,
                         "right": len(right), "scored": n_sc, "false_cards": [r["k"] for r in false_cards],
                         "missed": [r["k"] for r in missed], "wrong_category": [r["k"] for r in wrong_cat],
                         "confidence_right": round(statistics.mean(confs_r), 3) if confs_r else None,
                         "confidence_wrong": round(statistics.mean(confs_w), 3) if confs_w else None,
                         "chars": chars, "seconds_median": round(secs, 1)}
    # identical-answer checks
    lines.append("")
    for a, b, what in (("I", "E", "the trained text in the user prompt (I) against the same text as the system "
                                  "prompt (E)"),
                       ("R", "A", "the baseline asked again after the system prompt was cleared (R) against the "
                                  "baseline (A)"),
                       ("A2", "A", "the baseline asked a second time (A2) against the first time (A)")):
        if a in by_cell and b in by_cell:
            ks = [k for k in by_cell[a] if k in by_cell[b]]
            same = sum(1 for k in ks if by_cell[a][k]["response"] == by_cell[b][k]["response"])
            same_cat = sum(1 for k in ks if by_cell[a][k]["category"] == by_cell[b][k]["category"])
            lines.append(f"- Word-for-word identical answers, {what}: **{same} of {len(ks)}** "
                         f"(same category: {same_cat} of {len(ks)}).")
            summary[f"identical_{a}_{b}"] = {"clips": len(ks), "identical": same, "same_category": same_cat}
    # per-clip matrix
    cells_present = [c for c in CELLS if c in by_cell]
    lines.append("\n## Category per clip\n")
    lines.append("| # | Clip | Truth | " + " | ".join(cells_present) + " |")
    lines.append("|---|---|---|" + "---|" * len(cells_present))
    for k in sorted(clips):
        c = clips[k]
        cells_out = []
        for cell in cells_present:
            r = by_cell[cell].get(k)
            if r is None:
                cells_out.append("")
            elif r["progress"] != "Completed":
                cells_out.append("failed")
            else:
                cat = r["category"]
                conf = r["fields"].get("confidence")
                tag = cat if c["truth"] in (None, cat) else f"**{cat}**"
                cells_out.append(tag + (f" ({float(conf):.1f})" if _num(conf) else ""))
        lines.append(f"| {k} | {c['avi'][16:50]} | {c['truth'] or 'ambiguous'} | " + " | ".join(cells_out) + " |")
    lines.append("\nBold: a category that differs from the truth. The number in brackets is the answer's own "
                 "confidence where the prompt asked for one.\n")
    readme = run / "README.md"
    head = ""
    if readme.exists() and TABLES_MARK in readme.read_text(encoding="utf-8"):
        head = readme.read_text(encoding="utf-8").split(TABLES_MARK)[0]   # the findings written by hand stay
        lines = lines[1:]                                                  # ... with their own title
    readme.write_text(head + TABLES_MARK + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    (run / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    # every answer by clip
    out = [f"# Every answer by clip ({run.name})\n"]
    for k in sorted(clips):
        c = clips[k]
        out.append(f"## {k}. {c['avi']} (truth {c['truth'] or 'ambiguous'})\n\n{c['note']}\n")
        for cell in cells_present:
            r = by_cell[cell].get(k)
            if r:
                out.append(f"- **{cell}** ({r['system']} / {r['prompt']}, {r['seconds']} s): "
                           f"`{r['category']}` {r['response'] if r['progress'] == 'Completed' else r['error']}")
        out.append("")
    (run / "answers.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(lines[:40]))
    print(f"wrote {run / 'README.md'}, summary.json, answers.md")
    return 0


def _num(x) -> bool:
    try:
        float(x)
        return x is not None and not isinstance(x, bool)
    except (TypeError, ValueError):
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("play")
    p.add_argument("--out", type=Path)
    p.set_defaults(fn=play)
    p = sub.add_parser("ask")
    p.add_argument("run", type=Path)
    p.add_argument("--cells", nargs="*", choices=list(CELLS))
    p.add_argument("--stop-at", type=int, default=450)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=ask)
    p = sub.add_parser("score")
    p.add_argument("run", type=Path)
    p.set_defaults(fn=score)
    p = sub.add_parser("restore")
    p.set_defaults(fn=restore)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
