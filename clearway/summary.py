r"""The shift summary (docs/PRODUCT.md, F8): what one run of the Clearway service saw, from its logs; no requests.

    .venv\Scripts\python.exe -m clearway.summary run\clearway-live-<UTC>      (writes <run>\shift.json)

A run is a shift. The board serves the same summary as a page (/summary, clearway/summary.html) and the service writes
shift.json when it stops. In operator terms, as in the product plan:
- incidents by owner and by category (the event counts of Hafnia's trained MonitoringSummary, from the ledger: no
  request), and the false cards: those an operator rejected (F7);
- how fast: from the spot changing to its card (the first time it waits for the lens and Hafnia; a repeat is
  recognised at once), to the alarm in XProtect and to the owner told (clearway/notify.py); from the alarm to the spot
  clearing; from clearing to the alarm closing by itself;
- how long: each incident's occurrences, by the ledger's clearing rule replayed over the ledger's log and the
  detector's closings (changes.jsonl): the ledger logs a clearing only for an open card, so on a looped clip an
  occurrence that cleared while its question waited for the lens would otherwise last the lens queue's minute;
- where it keeps happening: incidents by occurrences, with the snapshot of the spot; and per camera the hotspots
  (F9): the ledger's spots (each card with its occurrences; what was not an incident, with the later changes the
  verdict memory skipped as looking like it) and the heat of every change the detector reported, card or not, drawn
  over the camera's scene image (<run>/cameras/, written by the service; older runs: a question's snapshot);
- what it cost: Hafnia requests (questions on a dry run) per camera and per camera-hour, the changes decided without
  one, and how many cameras a 500-a-day allowance would cover at that rate.
Cameras run with the looped-clip detector setting are named: their clips restart every 8-17 s, so an occurrence there
is a replay of one incident, and the times are seconds (the honesty rule in docs/PRODUCT.md).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import statistics
import threading
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from clearway.ledger import OWNERS, Ledger, _overlap
from tier0.change import ChangeParams

ALLOWANCE = 500                 # Hafnia requests a day on the hackathon machines
SHORT_RUN_H = 1.0               # below this the start-up burst (every incident asked at once) dominates the rate
OWNER_ORDER = list(dict.fromkeys(owner for owner, _ in OWNERS.values()))
WORK_WIDTH = 640                # the service's working frame (clearway/service.py): boxes are in its pixels
CELL = 16                       # hotspot heat: changes counted per CELL x CELL pixels of the working frame
_logs: dict[Path, tuple[int, list[dict]]] = {}      # path -> (bytes read, records): the logs only grow
_logs_lock = threading.Lock()


def _read(path: Path) -> list[dict]:
    """A JSONL log without its looks: each SigLIP look (768 numbers, most of every report's and question's line, about
    2 MB of changes.jsonl in 5 min) is cut to [0] before parsing; the summary never compares looks, and the ledger's
    replay only needs a vector there. The board asks every few seconds while a run grows (a 4-hour shift's
    changes.jsonl is some 100 MB), so only lines added since the last call are read."""
    if not path.exists():
        return []
    with _logs_lock:
        done, out = _logs.get(path, (0, []))
        if path.stat().st_size < done:           # rewritten: start again
            done, out = 0, []
        with path.open("rb") as f:
            f.seek(done)
            for raw in f:
                if not raw.endswith(b"\n"):      # a line still being written
                    break
                done += len(raw)
                line = raw.decode("utf-8")
                if not line.strip():
                    continue
                if (i := line.find('"emb": [')) >= 0:
                    line = line[:i] + '"emb": [0]' + line[line.index("]", i) + 1:]
                out.append(json.loads(line))
        _logs[path] = (done, out)
        return list(out)


def _scene(run: Path, camera: str, snaps: list[str]) -> dict:
    """The image a camera's hotspots are drawn over, and the working frame's size: the service's scene image (the
    detector's background, <run>/cameras/), else the newest snapshot of a question on the camera (runs before F9; its
    spot is boxed)."""
    scene = run / "cameras" / f"{camera}.jpg"
    if scene.exists():
        path, url = scene, f"/cameras/{camera}.jpg?run={run.name}&v={scene.stat().st_mtime_ns}"
        kind = "scene"
    else:
        path = next((run / "snaps" / f"{i}.jpg" for i in reversed(snaps) if (run / "snaps" / f"{i}.jpg").exists()), None)
        if path is None:
            return {"image": None, "image_kind": None, "size": None}
        url, kind = f"/snaps/{path.stem}.jpg?run={run.name}", "snapshot"
    img = cv2.imread(str(path))
    if img is None:
        return {"image": None, "image_kind": None, "size": None}
    h, w = img.shape[:2]
    return {"image": url, "image_kind": kind, "size": [WORK_WIDTH, round(h * WORK_WIDTH / w)]}


def _hotspots(run: Path, cameras: list[str], led: Ledger, events: list[dict], changes: list[dict]) -> dict:
    """Per camera (F9): the spots, from the ledger's boxes: each card with its occurrences, and what was not an
    incident (Hafnia's NONE, the operator's rejection) with the later changes the verdict memory skipped because they
    looked like it, those at overlapping spots grouped; and the heat: every change the detector (or a danger zone)
    reported, card or not, counted per CELL-pixel cell."""
    asked_after_all = {(e["camera"], e["change"]) for e in events if e["kind"] == "ask" and e.get("escalated")}
    like = Counter(e["like"] for e in events if e["kind"] == "skip" and e.get("like")
                   and (e["camera"], e["change"]) not in asked_after_all)
    spots: dict[str, list[dict]] = defaultdict(list)
    snaps: dict[str, list[str]] = defaultdict(list)
    for i in sorted(led.incidents.values(), key=lambda i: i.t_report):
        snaps[i.camera].append(i.id)
        if i.merged_into or i.state not in ("open", "cleared", "rejected", "dismissed"):
            continue
        kind = {"rejected": "rejected", "dismissed": "harmless"}.get(i.state, "incident")
        spot = {"kind": kind, "box": list(i.box), "count": i.occurrences + like[i.id], "occurrences": i.occurrences,
                "skipped": like[i.id], "ids": [i.id], "category": i.category, "owner": i.owner,
                "operator": i.operator}
        group = next((g for g in spots[i.camera] if kind != "incident" and g["kind"] == kind
                      and _overlap(g["box"], spot["box"]) >= led.p.min_overlap), None)
        if group is None:
            spots[i.camera].append(spot)
        else:
            for k in ("count", "occurrences", "skipped"):
                group[k] += spot[k]
            group["ids"].append(i.id)
    boxes: dict[str, list] = defaultdict(list)
    for e in changes:
        if e["kind"] == "report":
            boxes[e["camera"]].append(e["box"])
    out, top = [], 1
    for c in cameras:
        cam = {"camera": c, **_scene(run, c, snaps[c]), "changes": len(boxes[c]),
               "spots": sorted(spots[c], key=lambda s: (s["kind"] != "incident", -s["count"]))}
        if cam["size"]:
            w, h = cam["size"]
            heat = np.zeros((math.ceil(h / CELL), math.ceil(w / CELL)), np.int32)
            for x1, y1, x2, y2 in boxes[c]:          # every cell the box touches
                heat[max(0, int(y1)) // CELL:(max(int(y1), int(y2) - 1) // CELL) + 1,
                     max(0, int(x1)) // CELL:(max(int(x1), int(x2) - 1) // CELL) + 1] += 1
            cam.update(rows=heat.shape[0], cols=heat.shape[1], heat=heat.ravel().tolist())
            top = max(top, int(heat.max()))
        out.append(cam)
    out.sort(key=lambda c: (-sum(s["count"] for s in c["spots"] if s["kind"] == "incident"), -c["changes"]))
    return {"cell": CELL, "heat_max": top, "cameras": out}


def _med(xs: list[float]) -> float | None:
    return round(statistics.median(xs), 1) if xs else None


def _occurrences(timeline: list[tuple], began: dict, t_end: float) -> tuple[dict[str, list], set[str]]:
    """Each incident's occurrences as (start, end), by the ledger's clearing rule replayed over both logs in time order
    (timeline: (t, 0, n, ledger event) for asks, pieces, recurrences and merges; (t, 1, n, detector closing)). An
    occurrence starts when its first change started and ends when its largest change closes; the smaller pieces still
    open go with it (on a loop some never look quite as before). Returns the spans and the incidents still open at
    t_end (their last span runs to t_end)."""
    active: dict[str, dict] = defaultdict(dict)     # incident -> {(camera, change): area}
    start: dict[str, float] = {}
    spans: dict[str, list] = defaultdict(list)
    owner: dict[tuple, str] = {}                    # (camera, change) -> incident
    for t, source, _, e in sorted(timeline, key=lambda x: x[:3]):
        if source == 1:                             # the detector: a change closed
            iid = owner.pop((e["camera"], e["change"]), None)
            if iid is None:
                continue
            area = active[iid].pop((e["camera"], e["change"]), 0)
            if active[iid] and area < max(active[iid].values()):
                continue
            for rest in active[iid]:
                owner.pop(rest, None)
            active[iid].clear()
            spans[iid].append((start.pop(iid), t))
        elif e["kind"] == "merge":
            inc, into = e["incident"], e["into"]
            spans[into] += spans.pop(inc, [])
            if active[inc]:
                s = start.pop(inc)
                start[into] = min(start[into], s) if active[into] else s
                for key in active[inc]:
                    owner[key] = into
                active[into].update(active.pop(inc))
        else:                                       # an ask, a piece, a recurrence: the change joins the incident
            key, iid = (e["camera"], e["change"]), e["incident"]
            if not active[iid]:
                start[iid] = began.get(key, t)
            active[iid][key] = e.get("area", 0)
            owner[key] = iid
    still = {iid for iid, a in active.items() if a}
    for iid in still:
        spans[iid].append((start[iid], t_end))
    for iid, sp in spans.items():                   # pieces asked about apart, then merged, overlap
        merged: list[list[float]] = []
        for a, b in sorted(sp):
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        spans[iid] = [(a, b) for a, b in merged]
    return spans, still


def summarise(run: Path, now: float | None = None) -> dict:
    """The run's summary; now (Unix seconds) ends a live run's open occurrences (default: the run's end, else now)."""
    with _logs_lock:                              # the board moved on to another run: forget the last one's logs
        for p in [p for p in _logs if p.parent != run]:
            del _logs[p]
    svc, events, changes = _read(run / "service.jsonl"), _read(run / "ledger.jsonl"), _read(run / "changes.jsonl")
    start = next((e for e in svc if e["kind"] == "start"), None)
    end = next((e for e in svc if e["kind"] == "end"), None)
    if start is None:
        raise ValueError(f"{run}: no start in service.jsonl")
    t_end = end["wall"] if end else (now or time.time())
    hours = max(1e-9, (t_end - start["wall"]) / 3600)
    cameras = list(start["cameras"])
    looped = [c for c, p in start["cameras"].items() if p == asdict(ChangeParams.loops())]

    # the ledger, event by event: cards, repeats (recognised at once), alarms raised
    led = Ledger(None)
    reopen_s, alarms, timeline = [], [], []
    for n, e in enumerate(events):
        k, iid = e["kind"], e.get("incident")
        before = led.incidents[iid].state if iid in led.incidents else None
        led.apply(e)
        if k == "recur" and before == "cleared" and e["state"] == "open":
            reopen_s.append(e["t"] - e["t_change"])
        if k == "alarm":
            alarms.append((iid, e["t"]))
        if k in ("ask", "fragment", "recur", "merge"):
            timeline.append((e["t"], 0, n, e))
    began = {(e["camera"], e["change"]): e["t_change"] for e in changes if e["kind"] == "report"}
    timeline += [(e["t"], 1, n, e) for n, e in enumerate(changes) if e["kind"] == "close"]
    spans, still = _occurrences(timeline, began, t_end)

    def last_open(iid: str, span: tuple) -> bool:
        return iid in still and span[1] >= t_end

    cards = [i for i in led.incidents.values() if i.category and not i.merged_into
             and i.state in ("open", "cleared", "rejected")]
    real = [i for i in cards if i.state != "rejected"]
    snaps = run / "snaps"
    incidents = []
    for i in sorted(real, key=lambda i: i.t_change):
        sp = spans.get(i.id, [])
        incidents.append({
            "id": i.id, "camera": i.camera, "category": i.category, "owner": i.owner, "priority": i.priority,
            "state": i.state, "operator": i.operator, "first_seen": i.t_change, "occurrences": i.occurrences,
            "to_card_s": round(i.t_answer - i.t_change, 1) if i.t_answer else None,
            "open_s": round(sum(b - a for a, b in sp), 1), "longest_s": round(max((b - a for a, b in sp), default=0), 1),
            "open_at_end": i.id in still, "summary": (i.answer or {}).get("summary") or "",
            "snap": f"/snaps/{i.id}.jpg?run={run.name}" if (snaps / f"{i.id}.jpg").exists() else None,
        })

    # alarm -> clear: from the alarm to the end of the occurrence it came in
    alarm_to_clear, cleared_first = [], 0
    for iid, t in alarms:
        span = next(((a, b) for a, b in spans.get(iid, []) if a <= t <= b), None)
        if span is None:
            cleared_first += 1                   # the spot cleared while the question waited for the lens
        elif not last_open(iid, span):
            alarm_to_clear.append(span[1] - t)
    closed_after = [e["t"] - e["t_cleared"] for e in svc
                    if e["kind"] == "effect" and e.get("reason") == "cleared" and e.get("t_cleared")]
    # XProtect: from the card to the alarm in Smart Client (queued behind other actions, then the trigger call)
    to_xprotect = [e["queued_s"] + e["timing"]["trigger"] for e in svc
                   if e["kind"] == "xprotect" and e.get("action") == "raise" and "queued_s" in e
                   and "trigger" in e.get("timing", {})]
    occurrence_s = [b - a for x in incidents for a, b in spans.get(x["id"], []) if not last_open(x["id"], (a, b))]
    # owners told (clearway/notify.py): from the spot changing to the owner's webhook answering
    told = [e for e in svc if e["kind"] == "notify"]
    to_owner = [e["wall"] - dt.datetime.fromisoformat(e["changed_at"]).timestamp() for e in told
                if e.get("ok") and e.get("event") == "opened" and e.get("changed_at")]

    # cost
    kinds: dict[str, int] = defaultdict(int)
    for e in events:
        kinds[e["kind"]] += 1
    escalated = sum(e["kind"] == "ask" and bool(e.get("escalated")) for e in events)
    reports = sum(e["kind"] == "report" for e in changes)
    answers = [e for e in svc if e["kind"] == "answer"]
    dry = any((e.get("answer") or {}).get("standin") for e in answers) or run.name.startswith("clearway-dry")
    asked = [e for e in events if e["kind"] == "ask"] if dry else [
        a for a in answers if "hafnia_s" in (a.get("answer") or {})]
    requests = {c: 0 for c in cameras}
    for e in asked:
        requests[e["camera"]] = requests.get(e["camera"], 0) + 1
    per_cam_h = sum(requests.values()) / max(1, len(cameras)) / hours

    def group(key: str) -> list[dict]:
        out = []
        for name in (OWNER_ORDER if key == "owner" else sorted({x[key] for x in incidents})):
            mine = [x for x in incidents if x[key] == name]
            out.append({key: name, "incidents": len(mine), "occurrences": sum(x["occurrences"] for x in mine),
                        "open_at_end": sum(x["open_at_end"] for x in mine),
                        "to_card_s_median": _med([x["to_card_s"] for x in mine if x["to_card_s"] is not None]),
                        "open_s_total": round(sum(x["open_s"] for x in mine), 1),
                        "longest_s": max((x["longest_s"] for x in mine), default=None)})
        return out

    verdicts = [e for e in events if e["kind"] == "operator"]
    first = [x["to_card_s"] for x in incidents if x["to_card_s"] is not None]
    return {
        "run": run.name, "mode": "dry" if dry else "live", "started": start["wall"],
        "ended": end["wall"] if end else None, "until": t_end, "hours": round(hours, 3),
        "cameras": cameras, "looped_cameras": looped,
        "incidents": len(incidents), "false_cards": len(cards) - len(real),
        "occurrences": sum(x["occurrences"] for x in incidents),
        "open_at_end": sum(x["open_at_end"] for x in incidents),
        "by_owner": group("owner"), "event_counts": {g["category"]: g["incidents"] for g in group("category")},
        "times_s": {
            "change_to_card_first": {"median": _med(first), "max": max(first, default=None), "n": len(first)},
            "change_to_card_repeat": {"median": _med(reopen_s), "n": len(reopen_s)},
            "card_to_xprotect_alarm": {"median": _med(to_xprotect), "n": len(to_xprotect)},
            "change_to_owner_told": {"median": _med(to_owner), "n": len(to_owner)},
            "alarm_to_clear": {"median": _med(alarm_to_clear), "n": len(alarm_to_clear),
                               "cleared_before_alarm": cleared_first},
            "clear_to_alarm_closed": {"median": _med(closed_after), "n": len(closed_after)},
            "occurrence": {"median": _med(occurrence_s), "n": len(occurrence_s)},
        },
        "longest_open": [{k: x[k] for k in ("id", "camera", "category", "owner", "longest_s", "open_at_end")}
                         for x in sorted(incidents, key=lambda x: -x["longest_s"])[:3]],
        "recurring": [{k: x[k] for k in ("id", "camera", "category", "owner", "occurrences", "snap")}
                      for x in sorted(incidents, key=lambda x: -x["occurrences"]) if x["occurrences"] > 1][:5],
        "list": incidents,
        "hotspots": _hotspots(run, cameras, led, events, changes),
        "cost": {
            "kind": "questions" if dry else "Hafnia requests", "dry": dry,
            "by_camera": requests, "total": sum(requests.values()), "per_camera_hour": round(per_cam_h, 1),
            "cameras_per_allowance": round(ALLOWANCE / (per_cam_h * 24), 1) if per_cam_h else None,
            "short_run": hours < SHORT_RUN_H,
            "changes": reports, "without_a_question": reports - (kinds["ask"] - escalated),
            "recurrences": kinds["recur"], "pieces": kinds["fragment"], "skipped": kinds["skip"] - escalated,
            "escalated": escalated,
        },
        "notifications": {"sent": sum(bool(e.get("ok")) for e in told), "failed": sum(not e.get("ok") for e in told),
                          "by_owner": {o: sum(e["owner"] == o and bool(e.get("ok")) for e in told)
                                       for o in OWNER_ORDER if any(e["owner"] == o for e in told)}},
        "operator": {"confirmed": sum(e["verdict"] == "confirmed" for e in verdicts),
                     "rejected": sum(e["verdict"] == "rejected" for e in verdicts),
                     "skipped_like_rejected": sum(e["kind"] == "skip" and e.get("by") == "operator" for e in events),
                     "false_cards_per_camera_hour": round((len(cards) - len(real)) / max(1, len(cameras)) / hours, 2)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run", type=Path)
    args = ap.parse_args()
    s = summarise(args.run)
    (args.run / "shift.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    t = s["times_s"]
    print(f"{s['run']}: {s['hours'] * 60:.0f} min, {len(s['cameras'])} cameras, {s['incidents']} incidents "
          f"({s['false_cards']} false cards), {s['occurrences']} occurrences, {s['cost']['total']} {s['cost']['kind']}")
    for o in s["by_owner"]:
        print(f"  {o['owner']:20} {o['incidents']:>3} incidents {o['occurrences']:>4} occurrences  "
              f"to card {o['to_card_s_median']} s  open {o['open_s_total']} s  longest {o['longest_s']} s")
    print(f"  change to card: first {t['change_to_card_first']['median']} s (max {t['change_to_card_first']['max']}), "
          f"repeat {t['change_to_card_repeat']['median']} s; card to XProtect alarm "
          f"{t['card_to_xprotect_alarm']['median']} s; alarm to clear {t['alarm_to_clear']['median']} s "
          f"({t['alarm_to_clear']['cleared_before_alarm']} cleared before the alarm); clear to alarm closed "
          f"{t['clear_to_alarm_closed']['median']} s; occurrence {t['occurrence']['median']} s")
    print(f"  recurring: {[(r['camera'], r['occurrences']) for r in s['recurring']]}")
    print(f"wrote {args.run / 'shift.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
