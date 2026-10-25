r"""eval_ledger.py - the ledger (clearway/ledger.py) replayed offline on every clip: requests, cards, alarms, misses.

    .venv\Scripts\python.exe scripts\eval_ledger.py [--loops 20] [--only NAME ...] [--out run\ledger-<UTC>]

1. Records an event stream per clip: the change detector (tier0/change.py; loops setting for the organizers' clips,
   real-camera setting for test_11 and the CC0 streets) with people held back, each report's AFTER crop embedded with
   SigLIP 2, and each change's closing.
2. Replays it through three policies with a stand-in for Hafnia, answering LATENCY_S after the report: the camera's
   category when the lens clip it would get (2 s before the change started to 3 s after the report) overlaps the
   incident's lasting state by >= 1 s, NONE otherwise:
     ask_all      every change is a request (no memory, no ledger)
     memory       skip look-alikes of rejected changes at the same spot (run/memory-compare's rule)
     ledger       also recognise recurrences of a known incident (no request, instant card)
Counts per clip: requests, cards (incidents opened), occurrences, alarms (raised or reopened: an incident's alarm
closes once it has stayed cleared for close_after_s),
incident changes never carded (skipped and gone before escalation, or joined to a dismissed incident), seconds from
change to card. No Hafnia requests. Each clip's event stream is saved (events-<clip>.pkl) as soon as it is recorded;
--from-events replays saved streams without the detector.
Caveat: the stand-in never errs, so false cards are not measured here (live runs, M3).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pickle
import statistics
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.ledger import Ledger, Params  # noqa: E402
from eval_change import CASES, frames, person_finder  # noqa: E402
from tier0.change import ChangeDetector, ChangeParams  # noqa: E402
from tier0.memory import Embedder, crop  # noqa: E402

LATENCY_S = 8.0
TRUTH = {"vehicle_breakdown_traffic_queue": "STALLED_VEHICLE", "bin_pushed_over_onto_sidewalk": "OBSTRUCTION",
         "escooter_left_across_sidewalk": "OBSTRUCTION", "school_gate_break_in_night": "TAMPERING",
         "person_on_railway_tracks": "PERSON_ON_TRACKS", "graffiti_on_standing_train": "DAMAGE",
         "vandalism": "DAMAGE", "test_11": "COLLISION"}
REAL = {"test_11", "mumbai02", "mumbai03", "duesseldorf"}


def record(name: str, loops: int, people, emb: Embedder) -> list[dict]:
    """The detector's reports and closings on one clip, in time order, with the stand-in's verdicts."""
    path, annexb, loop_s, state, role = CASES[name]
    params = ChangeParams.real() if name in REAL else ChangeParams.loops()
    n_loops = 1 if loop_s > 60 else loops
    det = ChangeDetector(params)
    events, t, start, open_ids = [], 0.0, 0.0, set()
    for _ in range(n_loops):
        start = t
        for f in frames(path, annexb):
            for c in det.update(t, f, people(f)):
                # What Hafnia would see: the lens clip runs from 2 s before the change started to 3 s after the report.
                # The stand-in calls it an incident when that clip overlaps the incident's lasting state by >= 1 s.
                w0, w1 = c.t_start - 2.0, c.t_detect + 3.0
                seen = 0.0
                if state:
                    for k in range(n_loops + 1):
                        s0, s1 = k * loop_s + state[0], k * loop_s + min(state[1], loop_s)
                        seen += max(0.0, min(w1, s1) - max(w0, s0))
                incident = seen >= 1.0
                if name == "test_11" and incident:   # 300 s follow the crash: only the crash spot is the incident
                    cx, cy = (c.box[0] + c.box[2]) / 2, (c.box[1] + c.box[3]) / 2
                    incident = 100 <= cx <= 280 and 50 <= cy <= 160
                e = emb.images([crop(f, c.box)])[0]
                # Loop guard (test harness only): a change that starts within 1 s before to 2 s after the clip
                # restarts is caused by the cut itself (things jump back to where the clip begins). A real camera
                # never restarts; the live harness finds the restarts by matching frames to the clip's first frame.
                phase = c.t_start % loop_s if n_loops > 1 else None
                cut = phase is not None and (phase < 2.0 or phase > loop_s - 1.0) and c.t_start >= loop_s - 1.0
                events.append({"kind": "report", "t": round(c.t_detect, 2), "t_change": round(c.t_start, 2),
                               "id": c.id, "box": c.box, "emb": e, "incident": incident, "cut": cut,
                               "category": TRUTH.get(name, "NONE") if incident else "NONE"})
                open_ids.add(c.id)
            for c in det.changes:
                if c.id in open_ids and c.t_closed is not None:
                    events.append({"kind": "close", "t": round(c.t_closed, 2), "id": c.id, "how": c.closed_by})
                    open_ids.discard(c.id)
            t += 0.1
    return events, t


def replay(name: str, events: list[dict], policy: str, guard: bool = True) -> dict:
    """One policy over one clip's event stream; with guard, changes caused by a loop restart are dropped."""
    if guard:
        cut_ids = {e["id"] for e in events if e["kind"] == "report" and e["cut"]}
        events = [e for e in events if e["id"] not in cut_ids]
    reports = {e["id"]: e for e in events if e["kind"] == "report"}
    incident_ids = [i for i, e in reports.items() if e["incident"]]
    if policy == "ask_all":
        return {"requests": len(reports), "cards": None, "alarms": None, "incident_changes": len(incident_ids),
                "incident_changes_uncarded": 0,
                "to_card_s": [round(reports[i]["t"] + LATENCY_S - reports[i]["t_change"], 1) for i in incident_ids]}
    params = Params() if policy == "ledger" else Params(recur_sim=9.0)   # recur_sim > 1 disables recurrences
    led = Ledger(None, params)
    due = []                    # (t, incident id, category)
    joined = {}                 # change id -> (incident id, t it joined)
    alarms = 0

    def answer_until(t):
        nonlocal alarms
        while due and due[0][0] <= t:
            t_ans, iid, cat = due.pop(0)
            alarms += len([x for x in led.on_answer(iid, cat, {"category": cat}, t_ans) if "alarm" in x])

    def asked(d, t):
        cid = d.get("change")
        due.append((t + LATENCY_S, d["incident"], reports[cid]["category"]))
        due.sort()

    t_tick = 0.0
    for e in sorted(events, key=lambda x: x["t"]):
        while t_tick + 1.0 <= e["t"]:        # the live service ticks every second
            t_tick += 1.0
            answer_until(t_tick)
            for d in led.tick(t_tick):
                if d.get("action") != "ask":
                    continue                 # an alarm closing
                joined[d["change"]] = (d["incident"], t_tick)
                asked(d, t_tick)
        answer_until(e["t"])
        if e["kind"] == "close":
            led.on_change_closed(name, e["id"], e["t"], e["how"])
            continue
        d = led.on_change(name, e["id"], e["t_change"], e["t"], e["box"], e["emb"])
        if d["action"] == "ask":
            asked(d, e["t"])
        if d["incident"]:
            joined[e["id"]] = (d["incident"], e["t"])
        alarms += len([x for x in d.get("effects", []) if "alarm" in x])
    answer_until(float("inf"))
    to_card, uncarded = [], 0
    for cid in incident_ids:
        if cid not in joined:
            uncarded += 1                    # skipped and left before escalation
            continue
        iid, t_join = joined[cid]
        inc = led.incidents[iid]
        if inc.merged_into:
            inc = led.incidents[inc.merged_into]
        if not inc.category:
            uncarded += 1                    # joined an incident the stand-in dismissed
            continue
        to_card.append(round(max(t_join, inc.t_answer or t_join) - reports[cid]["t_change"], 1))
    cards = [i for i in led.incidents.values() if i.category and not i.merged_into]
    return {"requests": led.stats["asked"], "recurrences": led.stats["recurrences"], "fragments": led.stats["fragments"],
            "skipped": led.stats["skipped"], "escalated": led.stats["escalated"], "cards": len(cards),
            "merged": sum(bool(i.merged_into) for i in led.incidents.values()),
            "occurrences_on_cards": sum(i.occurrences for i in cards),
            "dismissed": sum(i.state == "dismissed" for i in led.incidents.values()), "alarms": alarms,
            "incident_changes": len(incident_ids), "incident_changes_uncarded": uncarded, "to_card_s": to_card}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--loops", type=int, default=20)
    ap.add_argument("--only", nargs="+", choices=list(CASES))
    ap.add_argument("--out", type=Path, default=REPO / "run" / f"ledger-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}")
    ap.add_argument("--from-events", type=Path, nargs="+",
                    help="replay saved event streams (events-<clip>.pkl) instead of running the detector")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    saved = {}
    for d in args.from_events or []:
        for f in sorted(d.glob("events-*.pkl")):
            saved[f.stem[len("events-"):]] = pickle.loads(f.read_bytes())
    people = emb = None
    if not args.from_events:
        from ultralytics import YOLO
        people = person_finder(YOLO(str(REPO / "models" / "yolo11m.pt")))
        emb = Embedder()
    rows = []
    print(f"{'clip':40} {'min':>5} | requests: {'all':>4} {'memory':>6} {'ledger':>6} | "
          f"{'cards':>5} {'occur.':>6} {'alarms':>6} {'uncarded':>8} {'to card s (median)':>18} | no guard: req cards")
    for name in args.only or (list(saved) if saved else CASES):
        if saved:
            if name not in saved:
                continue
            events, seconds = saved[name]
        else:
            if not CASES[name][0].exists():
                continue
            events, seconds = record(name, args.loops, people, emb)
            (args.out / f"events-{name}.pkl").write_bytes(pickle.dumps((events, seconds)))   # kept if the run stops
        res = {p: replay(name, events, p) for p in ("ask_all", "memory", "ledger")}
        res["ledger_no_guard"] = replay(name, events, "ledger", guard=False)
        led = res["ledger"]
        med = statistics.median(led["to_card_s"]) if led["to_card_s"] else None
        rows.append({"clip": name, "seconds": round(seconds, 1), "policies": res})
        (args.out / "results.json").write_text(json.dumps({"latency_s": LATENCY_S, "params": vars(Params()),
                                                           "clips": rows}, indent=2, default=str), encoding="utf-8")
        print(f"{name[:40]:40} {seconds / 60:5.1f} | {'':9} {res['ask_all']['requests']:>4} {res['memory']['requests']:>6} "
              f"{led['requests']:>6} | {led['cards']:>5} {led['occurrences_on_cards']:>6} {led['alarms']:>6} "
              f"{led['incident_changes_uncarded']:>3}/{led['incident_changes']:<4} "
              f"{'' if med is None else f'{med:.1f}':>18} | {res['ledger_no_guard']['requests']:>13} "
              f"{res['ledger_no_guard']['cards']:>5}", flush=True)
    tot = {p: sum(r["policies"][p]["requests"] for r in rows) for p in ("ask_all", "memory", "ledger", "ledger_no_guard")}
    print(f"{'TOTAL requests':40} {sum(r['seconds'] for r in rows) / 60:5.1f} | {'':9} {tot['ask_all']:>4} "
          f"{tot['memory']:>6} {tot['ledger']:>6} | no guard: {tot['ledger_no_guard']}")
    (args.out / "results.json").write_text(json.dumps({"latency_s": LATENCY_S, "params": vars(Params()),
                                                       "clips": rows}, indent=2, default=str), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
