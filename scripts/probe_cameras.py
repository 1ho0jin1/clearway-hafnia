r"""probe_cameras.py - what does Hafnia make of a camera? Each camera, one full loop, each prompt once.

    .venv\Scripts\python.exe scripts\probe_cameras.py --cameras vehicle_breakdown_traffic_queue ... [--window 17]

The window is one loop long and ends --lag seconds ago (recorded for sure), so every moment of the loop is in it once
(possibly split at the loop boundary). Requests: cameras x prompts, sent at once; the run stops before sending if that
would pass --stop-at today. Writes run\probe-<UTC>\results.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from hafnia.gateway import Gateway  # noqa: E402
from hafnia.xprotect_rest import XProtect  # noqa: E402
from incident.verify import ask  # noqa: E402

PROMPTS = {
    "describe": "Describe what happens in this video.",
    "classify": ("What incident, if any, happens in this video? Reply with exactly one word from this list: "
                 "BREAKDOWN (a vehicle breaks down or stops in a traffic lane), OBSTRUCTION (an object is left lying "
                 "across a sidewalk or path), VANDALISM (property is damaged or defaced), GRAFFITI (someone sprays "
                 "paint on something), BREAK_IN (someone forces a lock, gate or door), TRESPASS (a person walks on "
                 "railway tracks or in another forbidden area), ACCIDENT (a traffic collision), NONE."),
}


def gateway_password() -> str:
    import os
    pw = os.environ.get("HAFNIA_GW_PASSWORD")
    if not pw:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            pw = winreg.QueryValueEx(k, "HAFNIA_GW_PASSWORD")[0]
    return pw


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cameras", nargs="+", required=True)
    ap.add_argument("--prompts", nargs="+", default=list(PROMPTS), choices=list(PROMPTS))
    ap.add_argument("--window", type=float, default=17.0, help="seconds: one loop")
    ap.add_argument("--lag", type=float, default=60.0, help="the window ends this many seconds ago")
    ap.add_argument("--stop-at", type=int, default=450)
    args = ap.parse_args()

    cams = XProtect().cameras()
    missing = [c for c in args.cameras if c not in cams]
    if missing:
        sys.exit(f"unknown cameras: {missing}")
    gw = Gateway()
    gw.login(gateway_password())
    n = len(args.cameras) * len(args.prompts)
    q = gw.quota()
    if q and q["DailySummaryCount"] + n > args.stop_at:
        sys.exit(f"today's count is {q['DailySummaryCount']}: {n} more would pass --stop-at {args.stop_at}")
    end = dt.datetime.now(dt.timezone.utc).replace(microsecond=0) - dt.timedelta(seconds=args.lag)
    start = end - dt.timedelta(seconds=args.window)
    jobs = [(c, p) for c in args.cameras for p in args.prompts]
    print(f"{n} requests, window {start:%H:%M:%S}-{end:%H:%M:%S} UTC", flush=True)

    def one(job):
        cam, p = job
        summary, secs = ask(gw, cams[cam], start, end, PROMPTS[p])
        return {"camera": cam, "prompt": p, "progress": summary.get("Progress"), "seconds": round(secs, 1),
                "answer": summary.get("Response") or "", "error": summary.get("LastError"),
                "summary_id": summary.get("Id")}

    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(one, jobs))
    out = REPO / "run" / f"probe-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
    out.mkdir(parents=True)
    (out / "results.json").write_text(json.dumps({"start": start.isoformat(), "end": end.isoformat(),
                                                  "prompts": PROMPTS, "rows": rows}, indent=2), encoding="utf-8")
    for r in rows:
        print(f"--- {r['camera']} / {r['prompt']} ({r['progress']}, {r['seconds']} s)\n{(r['answer'] or r['error'] or '')[:600]}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
