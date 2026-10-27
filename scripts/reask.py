r"""reask.py - ask Hafnia again about the spans a run already asked about, with a prompt variant, to steer the
category choice. Costs one request per span; the plan is printed first and --dry-run stops there.

    .venv\Scripts\python.exe scripts\reask.py run\clearway-live-<UTC> --variant negatives [--incidents cw-0008 ...]
                                              [--max-requests 10] [--dry-run]

The run's service.jsonl holds, per question, the view (direct: the camera's own recording; lens: lens_1) and the
whole-second span Hafnia was asked about; recordings are kept 24 h, so a span can be asked again the same day. Each
variant is PROMPT with one change (VARIANTS below); the answer is parsed as the service parses it, and old against
new category, with the new summary, is printed and written to <run>\reask-<variant>.jsonl. Scoring is by eye
against the known scene (and the stand-in's expected category, kept from the run): a variant earns its place when
it fixes the wrong labels without losing the right ones.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.prompt import PROMPT, parse  # noqa: E402

DEFINITIONS = (
    'PERSON_ON_TRACKS (a person on railway tracks), COLLISION (a vehicle hits another vehicle, a person, a barrier or '
    'an object, or spins out of control), STALLED_VEHICLE (a vehicle stopped or broken down in a traffic lane), '
    'OBSTRUCTION (an object left lying across a pavement, path or road), DAMAGE (property damaged or defaced, such as '
    'graffiti or broken glass), TAMPERING (someone forcing a lock, gate or door), NONE (none of these)')

VARIANTS = {
    # the service's prompt as it is now (since 2026-10-27 the definitions with what each is not)
    "current": PROMPT,
    "negatives": PROMPT,
    # the prompt before 2026-10-27: definitions without negatives (the pilot's 30 of 30, run/pilot-20261023T162040Z)
    "original": (
        'Reply with JSON only, no other text: {"category": "...", "object": "...", "where": "...", "still_present": '
        'true or false, "summary": "..."}. category is exactly one of: PERSON_ON_TRACKS (a person on railway tracks), '
        'COLLISION (a vehicle hits another vehicle, a person, a barrier or an object, or spins out of control), '
        'STALLED_VEHICLE (a vehicle stopped or broken down in a traffic lane), OBSTRUCTION (an object left lying across '
        'a pavement, path or road), DAMAGE (property damaged or defaced, such as graffiti or broken glass), TAMPERING '
        '(someone forcing a lock, gate or door), NONE (none of these). object: the main object or person involved, at '
        'most four words. where: one of track, lane, pavement, platform, other. still_present: whether that object or '
        'person is still there at the end of the video. summary: one sentence on what happens, in the order it '
        'happens.'),
    # the summary first, then the category chosen to match it
    "summary_first": (
        'Reply with JSON only, no other text: {"summary": "...", "object": "...", "where": "...", "still_present": '
        'true or false, "category": "..."}. summary: one sentence on what happens, in the order it happens. object: '
        'the main object or person involved, at most four words. where: one of track, lane, pavement, platform, '
        'other. still_present: whether that object or person is still there at the end of the video. category: '
        'exactly one of ' + DEFINITIONS + ', chosen so that it matches the summary.'),
}


def spans(run: Path) -> dict[str, dict]:
    """incident -> {camera, view, start, end, category, expected, summary} from the run's service.jsonl."""
    out: dict[str, dict] = {}
    for line in (run / "service.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if e["kind"] in ("lens", "direct") and e.get("span"):
            out.setdefault(e["incident"], {})
            out[e["incident"]].update(camera=e["camera"], view=e["kind"] if e["kind"] == "direct" else "lens",
                                      start=e["span"][0], end=e["span"][1])
        elif e["kind"] == "answer":
            a = e.get("answer") or {}
            out.setdefault(e["incident"], {})
            out[e["incident"]].update(category=e["category"], expected=(a.get("expected") or {}).get("category"),
                                      summary=a.get("summary", ""), view=e.get("view"))
    return {k: v for k, v in out.items() if "start" in v and "category" in v}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run", type=Path)
    ap.add_argument("--variant", choices=list(VARIANTS), default="current")
    ap.add_argument("--incidents", nargs="*", help="which questions to ask again (default: all answered)")
    ap.add_argument("--max-requests", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    todo = spans(args.run)
    if args.incidents:
        todo = {k: v for k, v in todo.items() if k in args.incidents}
    todo = dict(sorted(todo.items()))
    print(f"{len(todo)} spans in {args.run.name}; variant {args.variant}; at most {args.max_requests} requests")
    for k, v in todo.items():
        print(f"  {k} {v['camera'][:28]:28} {v['view']:6} {v['start'][11:19]}-{v['end'][11:19]} was {v['category']:16} "
              f"expected {str(v.get('expected')):16}")
    if args.dry_run:
        return 0
    if len(todo) > args.max_requests:
        sys.exit(f"{len(todo)} spans would pass --max-requests {args.max_requests}: name --incidents or raise the cap")
    from hafnia.gateway import Gateway
    from hafnia.xprotect_rest import XProtect
    from incident.verify import ask
    from lens_compare import gateway_password
    cams = XProtect().cameras()
    gw = Gateway()
    gw.login(gateway_password())
    q0 = (gw.quota() or {}).get("DailySummaryCount")
    print(f"today's count before: {q0}")
    out = args.run / f"reask-{args.variant}.jsonl"
    changed = kept = 0
    with out.open("a", encoding="utf-8") as f:
        for k, v in todo.items():
            cam = cams["lens_1"] if v["view"] == "lens" else cams[v["camera"]]
            start = dt.datetime.fromisoformat(v["start"])
            end = dt.datetime.fromisoformat(v["end"])
            summary, secs = ask(gw, cam, start, end, VARIANTS[args.variant])
            answer = summary.get("Response") or ""
            p = parse(answer)
            rec = {"incident": k, "camera": v["camera"], "view": v["view"], "span": [v["start"], v["end"]],
                   "variant": args.variant, "was": v["category"], "expected": v.get("expected"), "now": p["category"],
                   "summary": p.get("summary", ""), "response": answer, "progress": summary.get("Progress"),
                   "hafnia_s": round(secs, 1), "wall": dt.datetime.now(dt.timezone.utc).isoformat()}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            mark = "same" if p["category"] == v["category"] else "CHANGED"
            changed += mark == "CHANGED"
            kept += mark == "same"
            print(f"  {k}: {v['category']} -> {p['category']} ({mark}; expected {v.get('expected')}, {secs:.1f} s) "
                  f"{p.get('summary', '')[:140]}")
    q1 = (gw.quota() or {}).get("DailySummaryCount")
    print(f"today's count after: {q1}; {changed} changed, {kept} kept; wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
