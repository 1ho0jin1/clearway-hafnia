r"""vanilla_poll.py - the plain way to use Hafnia VLM on a set of cameras, measured: the organizers' example question
("Describe what happens in this video.", a 30 s clip ending 5 s ago, as C:\HackathonKit\hafnia-vlm\scripts\ask_hafnia.py)
asked about every camera every --every seconds for --minutes, which is what a recurring XProtect rule with a Hafnia
webhook does. One request per camera per poll; the plan and today's count are printed first; --dry-run stops there.

    .venv\Scripts\python.exe scripts\vanilla_poll.py run --cameras <names...> --minutes 6 --every 60 [--seconds 30]
                                                        [--max-requests 70] [--stop-at 450] [--dry-run] [--out DIR]
    .venv\Scripts\python.exe scripts\vanilla_poll.py score run\vanilla-<UTC>

run: writes run/vanilla-<UTC>/results.jsonl (every answer with its camera, span, timing) and run.json. score: README.md
(the text above the marker is kept), answers.md, summary.json: requests and answers per camera, which answers name an
incident (by the words an operator would search for; read them in answers.md before quoting), and the arithmetic of
the interval: requests per camera-hour, the share of each camera's time the clips cover, and how long the day's
allowance lasts for this many cameras. Clearway's side of the comparison is a live run over the same minutes
(scripts\run_clearway.py), read from its run folder.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

PROMPT = "Describe what happens in this video."      # the organizers' example (ask_hafnia.py)
PARALLEL = 3
TABLES_MARK = "<!-- tables: written by vanilla_poll.py score; the text above is kept -->"
# words an operator would search the answers for; the six categories' vocabulary and its neighbours
INCIDENT_WORDS = {
    "stalled vehicle": r"\b(stall|stalled|broken[- ]down|breakdown|disabled vehicle|hazard lights|smoke)\b",
    "collision": r"\b(collision|collide[sd]?|crash|crashe[sd]|accident|hits?|struck|impact)\b",
    "obstruction": r"\b(obstruct\w*|block\w*|lying across|lies across|knocked over|tipped over|pushed over|on its side)\b",
    "damage": r"\b(graffiti|vandal\w*|spray\w*|damage[sd]?|defac\w*|broken glass)\b",
    "tampering": r"\b(tamper\w*|bolt cutter\w*|cuts? the|cutting|forcing|force[sd] open|break[- ]in|breaking in|pick\w* the lock|lock)\b",
    "person on tracks": r"\b(on the (railway )?tracks?|onto the (railway )?tracks?|on the rails?|trespass\w*)\b",
}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def mentions(text: str) -> list[str]:
    t = (text or "").lower()
    return [name for name, rx in INCIDENT_WORDS.items() if re.search(rx, t)]


# --- run ----------------------------------------------------------------------------------------------------------
def run(args) -> int:
    from hafnia.gateway import Gateway, Tracked, video_uri
    from hafnia.xprotect_rest import XProtect
    from lens_compare import gateway_password
    out = args.out or REPO / "run" / f"vanilla-{utc_now():%Y%m%dT%H%M%SZ}"
    polls = int(round(args.minutes * 60 / args.every))
    planned = polls * len(args.cameras)
    print(f"{planned} requests planned: {len(args.cameras)} cameras x {polls} polls every {args.every:.0f} s for "
          f"{args.minutes:g} min, {args.seconds} s clips ending {args.lag} s ago, prompt {PROMPT!r}")
    print(f"at this interval: {3600 / args.every:.0f} requests per camera-hour, the clips cover "
          f"{100 * args.seconds / args.every:.0f} % of each camera's time, and 500 requests last "
          f"{500 / (len(args.cameras) * 3600 / args.every):.2f} h for {len(args.cameras)} cameras")
    if planned > args.max_requests:
        sys.exit(f"{planned} planned > --max-requests {args.max_requests}")
    if args.dry_run:
        return 0
    out.mkdir(parents=True, exist_ok=True)
    cams = XProtect().cameras()
    missing = [c for c in args.cameras if c not in cams]
    if missing:
        sys.exit(f"cameras not found by name: {missing}")
    gw = Gateway()
    gw.login(gateway_password())
    q = gw.quota() or {}
    q0 = q.get("DailySummaryCount")
    print(f"today's count before: {q0} of {q.get('DailySummaryQuota')}")
    if q0 is not None and q0 + planned > args.stop_at:
        sys.exit(f"{planned} more would pass --stop-at {args.stop_at}")
    (out / "run.json").write_text(json.dumps({
        "started": utc_now().isoformat(), "cameras": args.cameras, "minutes": args.minutes, "every_s": args.every,
        "clip_s": args.seconds, "lag_s": args.lag, "prompt": PROMPT, "polls": polls, "planned": planned,
        "count_before": q0}, indent=1), encoding="utf-8")
    n_done = n_sent = 0
    t_start = time.monotonic()
    try:
        with (out / "results.jsonl").open("a", encoding="utf-8") as f:
            for poll in range(1, polls + 1):
                due = t_start + (poll - 1) * args.every
                late = time.monotonic() - due
                if late < 0:
                    time.sleep(-late)
                poll_wall = utc_now()
                print(f"poll {poll}/{polls} at {poll_wall:%H:%M:%S}Z" + (f" ({late:.0f} s late)" if late > 1 else ""),
                      flush=True)
                for i in range(0, len(args.cameras), PARALLEL):
                    tracked = []
                    for cam in args.cameras[i:i + PARALLEL]:
                        end = utc_now().replace(microsecond=0) - dt.timedelta(seconds=args.lag)
                        start = end - dt.timedelta(seconds=args.seconds)
                        t0 = time.monotonic()
                        created = gw.ask(video_uri(cams[cam], start, end), PROMPT)
                        n_sent += 1
                        tracked.append((cam, start, end, Tracked(created["Id"], submitted=t0, summary=created)))
                    gw.wait_all([t for *_, t in tracked], poll=1.0, timeout=600)
                    for cam, start, end, t in tracked:
                        s = t.summary
                        answer = s.get("Response") or ""
                        secs = round(time.monotonic() - t.submitted, 1)
                        rec = {"poll": poll, "camera": cam, "span": [start.isoformat(), end.isoformat()],
                               "summary_id": t.id, "progress": s.get("Progress"), "error": s.get("LastError"),
                               "response": answer, "mentions": mentions(answer), "seconds": secs,
                               "chars": len(answer), "wall": utc_now().isoformat()}
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        f.flush()
                        n_done += s.get("Progress") == "Completed"
                        print(f"  {cam:44} {s.get('Progress'):10} {secs:5.1f} s  "
                              f"{','.join(rec['mentions']) or '-':24} {answer[:70].replace(chr(10), ' ')}", flush=True)
    finally:
        q1 = (gw.quota() or {}).get("DailySummaryCount")
        print(f"today's count after: {q1} ({n_done} completed of {n_sent} sent)")
        gw.logout()
        info = json.loads((out / "run.json").read_text(encoding="utf-8"))
        info.update(ended=utc_now().isoformat(), sent=n_sent, completed=n_done, count_after=q1)
        (out / "run.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    return 0


# --- score --------------------------------------------------------------------------------------------------------
def score(args) -> int:
    run_dir = args.run
    info = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    rows = load_jsonl(run_dir / "results.jsonl")
    done = [r for r in rows if r.get("progress") == "Completed"]
    per_cam = {}
    for r in rows:
        per_cam.setdefault(r["camera"], []).append(r)
    every, clip, n_cam = info["every_s"], info["clip_s"], len(info["cameras"])
    arith = {"requests_per_camera_hour": round(3600 / every, 1), "coverage_pct": round(100 * clip / every, 1),
             "hours_of_500_for_these_cameras": round(500 / (n_cam * 3600 / every), 2),
             "minutes_of_500_for_these_cameras": round(60 * 500 / (n_cam * 3600 / every), 1)}
    summary = {"cameras": n_cam, "polls": info["polls"], "sent": len(rows), "completed": len(done),
               "failed": len(rows) - len(done),
               "answers_naming_an_incident": sum(bool(r["mentions"]) for r in done),
               "mentions": dict(Counter(m for r in done for m in r["mentions"])),
               "seconds_per_answer": {"min": min((r["seconds"] for r in done), default=None),
                                      "max": max((r["seconds"] for r in done), default=None),
                                      "mean": round(sum(r["seconds"] for r in done) / len(done), 1) if done else None},
               "chars_mean": round(sum(r["chars"] for r in done) / len(done)) if done else None,
               "per_camera": {cam: {"sent": len(rs), "completed": sum(r.get("progress") == "Completed" for r in rs),
                                    "naming_an_incident": sum(bool(r["mentions"]) for r in rs
                                                              if r.get("progress") == "Completed"),
                                    "mentions": dict(Counter(m for r in rs if r.get("progress") == "Completed"
                                                             for m in r["mentions"]))}
                              for cam, rs in per_cam.items()},
               "arithmetic": arith, "run": info}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    text = (f"{len(rows)} requests sent ({len(done)} completed, {len(rows) - len(done)} failed): {n_cam} cameras x "
            f"{info['polls']} polls every {every:.0f} s for {info['minutes']:g} min, {clip} s clips, the prompt "
            f"{PROMPT!r}. Answers took {summary['seconds_per_answer']['min']}-{summary['seconds_per_answer']['max']} s "
            f"(mean {summary['seconds_per_answer']['mean']}), {summary['chars_mean']} characters on average.\n\n"
            f"**At this interval:** {arith['requests_per_camera_hour']:g} requests per camera-hour; the clips cover "
            f"{arith['coverage_pct']:g} % of each camera's time; the day's 500 requests last "
            f"{arith['minutes_of_500_for_these_cameras']:g} minutes for {n_cam} cameras.\n\n"
            "## Per camera\n\n| Camera | Sent | Completed | Answers naming an incident | Words found |\n|---|---|---|---|---|\n")
    for cam, t in summary["per_camera"].items():
        words = ", ".join(f"{m} {n}" for m, n in sorted(t["mentions"].items())) or "-"
        text += f"| {cam} | {t['sent']} | {t['completed']} | {t['naming_an_incident']} | {words} |\n"
    text += ("\n## Every answer\n\n| Poll | Camera | Span (UTC) | s | Words | Answer |\n|---|---|---|---|---|---|\n")
    for r in rows:
        span = f"{r['span'][0][11:19]}-{r['span'][1][11:19]}"
        if r.get("progress") != "Completed":
            text += f"| {r['poll']} | {r['camera']} | {span} | | failed | {str(r.get('error') or '')[:80]} |\n"
            continue
        ans = (r["response"] or "").replace("|", "/").replace("\n", " ")
        text += (f"| {r['poll']} | {r['camera']} | {span} | {r['seconds']} | {', '.join(r['mentions']) or '-'} | "
                 f"{ans[:260]} |\n")
    readme = run_dir / "README.md"
    head = ""
    if readme.exists():
        old = readme.read_text(encoding="utf-8")
        head = old.split(TABLES_MARK)[0] if TABLES_MARK in old else old
    if not head.strip():
        head = "# The plain way: the organizers' example question on a timer\n\n"
    readme.write_text(head.rstrip() + "\n\n" + TABLES_MARK + "\n\n" + text, encoding="utf-8")
    ans = "# Every answer\n\n"
    for r in rows:
        ans += (f"## poll {r['poll']}, {r['camera']}, {r['span'][0][11:19]}-{r['span'][1][11:19]} UTC "
                f"({r.get('progress')}, {r.get('seconds')} s; words: {', '.join(r.get('mentions') or []) or '-'})\n\n"
                f"{r.get('response') or r.get('error') or ''}\n\n")
    (run_dir / "answers.md").write_text(ans, encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("per_camera", "run")}, indent=1))
    for cam, t in summary["per_camera"].items():
        print(f"  {cam:44} {t['completed']:2d} of {t['sent']:2d}; naming an incident {t['naming_an_incident']:2d}  "
              f"{t['mentions']}")
    print(f"wrote {readme}, answers.md, summary.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="stage", required=True)
    r = sub.add_parser("run")
    r.add_argument("--cameras", nargs="+", required=True, help="camera names, as XProtect shows them")
    r.add_argument("--minutes", type=float, default=6.0)
    r.add_argument("--every", type=float, default=60.0, help="seconds between polls")
    r.add_argument("--seconds", type=int, default=30, help="clip length (ask_hafnia.py: 30)")
    r.add_argument("--lag", type=int, default=5, help="the clip ends this many seconds ago (ask_hafnia.py: 5)")
    r.add_argument("--max-requests", type=int, default=70)
    r.add_argument("--stop-at", type=int, default=450)
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--out", type=Path)
    r.set_defaults(fn=run)
    s = sub.add_parser("score")
    s.add_argument("run", type=Path)
    s.set_defaults(fn=score)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
