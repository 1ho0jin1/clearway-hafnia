r"""report_clearway.py - one Clearway run (scripts\run_clearway.py) per camera, beside the offline replay.

    .venv\Scripts\python.exe scripts\report_clearway.py run\clearway-dry-<UTC> [--replay run\ledger-F1] [--xprotect]

Per camera: questions (start-up ones apart: reported within one loop after the detector's warm-up, which starts at
the first loop start after the first frame; a real camera has no loop), answers, cards,
occurrences on them, seconds from the change to its card (questions: until the answer; recurrences: at once), the
lens's wait, frame rate. Live runs also score Hafnia's category against the stand-in's (answer["expected"]). The
offline replay's "no guard" ledger (run/ledger-F1/results.json, about 5 min per camera) is shown beside it. With
--xprotect, the run's XProtect alarms (F3) are read back: name, priority, state against the last action logged.
Writes <run>\summary.json. No requests.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.ledger import OWNERS  # noqa: E402
from eval_change import CASES  # noqa: E402
from tier0.change import ChangeParams  # noqa: E402


def read(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def med(xs: list[float]) -> float | None:
    return round(statistics.median(xs), 1) if xs else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run", type=Path)
    ap.add_argument("--replay", type=Path, default=REPO / "run" / "ledger-F1")
    ap.add_argument("--xprotect", action="store_true", help="read the run's alarms back from XProtect")
    args = ap.parse_args()
    svc = read(args.run / "service.jsonl")
    led = read(args.run / "ledger.jsonl") if (args.run / "ledger.jsonl").exists() else []
    incidents = {i["id"]: i for i in json.loads((args.run / "incidents.json").read_text(encoding="utf-8"))}
    start = next(e for e in svc if e["kind"] == "start")
    end = next((e for e in svc if e["kind"] == "end"), None)
    health = [e for e in svc if e["kind"] == "health"]
    stats = (end or health[-1])["cameras"]
    cameras = list(start["cameras"])
    warmup = ChangeParams().warmup_s
    replay = {}
    if (args.replay / "results.json").exists():
        for r in json.loads((args.replay / "results.json").read_text(encoding="utf-8"))["clips"]:
            replay[r["clip"]] = r["policies"]["ledger_no_guard"]

    rows = {c: defaultdict(list) for c in cameras}
    t_first = {c: stats[c].get("t_first") for c in cameras}
    for e in svc:
        c = e.get("camera")
        if c not in rows:
            continue
        r = rows[c]
        if e["kind"] == "question":
            loop_s = CASES[c][2] if c in CASES and CASES[c][2] <= 60 else 0.0
            t0 = t_first[c]
            startup = t0 is not None and e["t_report"] < t0 + loop_s + warmup + loop_s
            r["questions"].append(e["incident"])
            if startup:
                r["startup"].append(e["incident"])
            if e["escalated"]:
                r["escalated"].append(e["incident"])
        elif e["kind"] == "lens":
            r["lens_wait_s"].append(e["waited_s"])
        elif e["kind"] == "answer":
            r["answers"].append(e["category"])
            if e["category"] in OWNERS and not e["merged_into"]:
                r["to_card_s"].append(e["since_change_s"])
            a = e.get("answer") or {}
            if "hafnia_s" in a:
                r["hafnia_s"].append(a["hafnia_s"])
            if "expected" in a:
                exp = a["expected"].get("category")
                r["scored"].append({"incident": e["incident"], "hafnia": e["category"], "expected": exp,
                                    "agree": e["category"] == exp, "summary": a.get("summary", "")})
        elif e["kind"] in ("unanswered", "failed"):
            r["unanswered"].append(e.get("reason"))
    for e in led:
        if e["kind"] == "recur" and e["camera"] in rows:
            rows[e["camera"]]["recur_to_card_s"].append(round(e["t"] - e["t_change"], 1))

    out = {"run": args.run.name, "minutes": None, "cameras": {}}
    if end:
        out["minutes"] = round((end["wall"] - start["wall"]) / 60, 1)
    print(f"{'camera':32} {'fps':>4} {'drop':>4} | {'questions':>9} {'start-up':>8} {'esc.':>4} | {'cards':>5} "
          f"{'occur.':>6} {'dismissed':>9} {'merged':>6} | {'to card s: asked':>16} {'recurrence':>10} | "
          f"{'lens wait s':>11} | replay: req cards")
    for c in cameras:
        r = rows[c]
        cards = [i for i in incidents.values() if i["camera"] == c and i["category"] and not i["merged_into"]]
        row = {
            "fps": round(stats[c]["frames"] / max(1e-9, (end["wall"] - start["wall"]) if end else 1), 1),
            "dropped": stats[c].get("dropped", 0),
            "questions": len(r["questions"]), "startup_questions": len(r["startup"]),
            "escalated": len(r["escalated"]), "unanswered": r["unanswered"],
            "answers": dict((k, r["answers"].count(k)) for k in sorted(set(r["answers"]))),
            "cards": len(cards), "occurrences_on_cards": sum(i["occurrences"] for i in cards),
            "dismissed": sum(i["camera"] == c and i["state"] == "dismissed" for i in incidents.values()),
            "merged": sum(i["camera"] == c and bool(i["merged_into"]) for i in incidents.values()),
            "to_card_s_asked_median": med(r["to_card_s"]), "to_card_s_recurrence_median": med(r["recur_to_card_s"]),
            "lens_wait_s_median": med(r["lens_wait_s"]), "hafnia_s_median": med(r["hafnia_s"]),
            "scored": r["scored"], "replay_no_guard": {k: replay[c][k] for k in ("requests", "cards")} if c in replay else None,
        }
        out["cameras"][c] = row
        rp = row["replay_no_guard"] or {}
        print(f"{c[:32]:32} {row['fps']:>4} {row['dropped']:>4} | {row['questions']:>9} {row['startup_questions']:>8} "
              f"{row['escalated']:>4} | {row['cards']:>5} {row['occurrences_on_cards']:>6} {row['dismissed']:>9} "
              f"{row['merged']:>6} | {str(row['to_card_s_asked_median']):>16} {str(row['to_card_s_recurrence_median']):>10} | "
              f"{str(row['lens_wait_s_median']):>11} | {rp.get('requests', '-'):>12} {rp.get('cards', '-'):>5}")
    tot = {k: sum(out["cameras"][c][k] for c in cameras) for k in ("questions", "startup_questions", "cards")}
    print(f"{'TOTAL':32} {'':>9} | {tot['questions']:>9} {tot['startup_questions']:>8} {'':>4} | {tot['cards']:>5}"
          f"   replay: {sum((out['cameras'][c]['replay_no_guard'] or {}).get('requests', 0) for c in cameras)} requests")
    scored = [s for c in cameras for s in out["cameras"][c]["scored"]]
    if scored:
        print(f"Hafnia agrees with the stand-in on {sum(s['agree'] for s in scored)} of {len(scored)} answers")
        for s in scored:
            if not s["agree"]:
                print(f"  {s['incident']}: Hafnia {s['hafnia']}, expected {s['expected']}: {s['summary'][:150]}")
    out["totals"] = tot
    actions = [e for e in svc if e["kind"] == "xprotect"]
    if actions:
        n = {a: sum(e.get("action") == a for e in actions) for a in ("raise", "reopen", "close")}
        marks = sum(len(e.get("bookmarks", [])) for e in actions)
        errs = [e for e in svc if e["kind"] == "xprotect_error"] + [e for e in actions if e.get("errors")]
        secs = [e["seconds"] for e in actions if "seconds" in e]
        print(f"XProtect: {n['raise']} alarms raised, {n['reopen']} reopened, {n['close']} closed, {marks} bookmarks, "
              f"{sum(bool(e.get('snapshot')) for e in actions)} snapshots, {len(errs)} errors; "
              f"seconds per action: median {med(secs)}, max {max(secs, default=None)}")
        out["xprotect"] = {**n, "bookmarks": marks, "errors": [e.get("error") or e.get("errors") for e in errs]}
        if args.xprotect:
            from hafnia.xprotect_rest import XProtect, _unwrap
            xp, last = XProtect(), {}
            for e in actions:
                if e.get("alarm"):
                    last[e["alarm"]] = e["action"]
            checked = []
            for alarm, action in last.items():
                a = _unwrap(xp.call("GET", f"/alarms/{alarm}"))
                want = "Closed" if action == "close" else "New"
                checked.append({"alarm": alarm, "name": a["name"], "priority": a["priority"]["name"],
                                "state": a["state"]["name"], "expected": want, "ok": a["state"]["name"] == want})
                print(f"  {a['name'][:52]:52} {a['priority']['name']:6} {a['state']['name']:8} "
                      f"(expected {want}) {a.get('sourceName', '')}")
            print(f"  {sum(c['ok'] for c in checked)} of {len(checked)} alarms in the expected state")
            out["xprotect"]["checked"] = checked
    (args.run / "summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {args.run / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
