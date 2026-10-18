"""bench_hafnia.py - measure how long Hafnia VLM takes to answer, phase by phase, through the gateway on this machine.

Each completed request costs 1 of the 500 daily requests. The script prints how many it plans to send, refuses plans
larger than --max-requests, and stops before the day's count reaches --stop-at.

    $env:HAFNIA_GW_PASSWORD = [Environment]::GetEnvironmentVariable('HAFNIA_GW_PASSWORD', 'User')
    py scripts\bench_hafnia.py --dry-run                                  # plan and allowance only, costs nothing
    py scripts\bench_hafnia.py --cameras vandalism --clip-seconds 5 15 30   # 3 requests, one after another
    py scripts\bench_hafnia.py --concurrency 5                            # all 5 cameras at once: 5 requests

Phase times are first-seen times from polling, so each is accurate to about --poll seconds.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hafnia.gateway import Gateway, GatewayError, Tracked, parse_time, video_uri  # noqa: E402
from hafnia.xprotect import cameras_by_name  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
# (column, state that starts the phase, state that ends it); None stands for the moment of submission
PHASE_SPANS = (
    ("queue", None, "FetchingVideo"),
    ("fetch", "FetchingVideo", "TransferringAssets"),
    ("upload", "TransferringAssets", "RequestingSummary"),
    ("vlm", "RequestingSummary", "end"),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Measure Hafnia VLM latency per phase.")
    p.add_argument("--cameras", nargs="+", help="camera names (default: every camera)")
    p.add_argument("--clip-seconds", nargs="+", type=int, default=[10], help="clip lengths to try (default 10)")
    p.add_argument("--loop-windows", type=Path,
                   help="clips.json: cameras listed there get one window as long as their looped clip (at least "
                        "--clip-seconds), so one full loop is always inside; --clip-seconds is used for the rest")
    p.add_argument("--repeat", type=int, default=1, help="runs of each camera x clip length (default 1)")
    p.add_argument("--concurrency", type=int, default=1, help="requests submitted together (default 1)")
    what = p.add_mutually_exclusive_group()
    what.add_argument("--prompt", default="Describe what happens in this video.", help="prompt text")
    what.add_argument("--prompt-title", help="title of a saved prompt (gateway rules then check the answer)")
    p.add_argument("--end-offset", type=int, default=5, help="clip ends this many seconds ago (default 5)")
    p.add_argument("--max-requests", type=int, default=10, help="refuse plans larger than this (default 10)")
    p.add_argument("--stop-at", type=int, default=450, help="stop when today's count reaches this (default 450)")
    p.add_argument("--poll", type=float, default=1.0, help="seconds between status checks (default 1)")
    p.add_argument("--run-dir", type=Path,
                   help="folder for this session's results.jsonl; reuse it to collect several runs (default "
                        "run/bench-<UTC time>)")
    p.add_argument("--label", default="", help="tag stored with each row, e.g. 'baseline' or 'concurrency'")
    p.add_argument("--dry-run", action="store_true", help="print the plan and the allowance; send nothing")
    return p.parse_args()


def spans(t: Tracked) -> dict[str, float | None]:
    """Seconds spent in each phase. A phase shorter than the poll interval may go unseen: its time then counts towards
    the phase before it, and it shows 0."""
    if not t.done:
        return {name: None for name, _, _ in PHASE_SPANS} | {"total": None}
    order = [end for _, _, end in PHASE_SPANS]
    seen = {**t.seen, "end": t.seen[t.progress]}

    def boundary(state: str | None) -> float:
        if state is None:
            return t.submitted
        return next(seen[s] for s in order[order.index(state):] if s in seen)

    out = {name: round(boundary(end) - boundary(start), 2) for name, start, end in PHASE_SPANS}
    out["total"] = round(seen["end"] - t.submitted, 2)
    return out


def server_seconds(summary: dict) -> float | None:
    try:
        return round((parse_time(summary["LastUpdatedTimeUtc"]) - parse_time(summary["CreationTimeUtc"])).total_seconds(), 2)
    except (KeyError, ValueError):
        return None


def remaining(gw: Gateway, stop_at: int) -> int | None:
    q = gw.quota()
    return None if q is None else stop_at - q["DailySummaryCount"]


def fmt(v: float | None) -> str:
    return "-" if v is None else f"{v:.1f}"


def main() -> int:
    args = parse_args()
    print("Looking cameras up by name (MilestonePSTools, 10-30 s)...")
    cams = cameras_by_name()
    names = args.cameras or sorted(cams)
    if unknown := [n for n in names if n not in cams]:
        sys.exit(f"Unknown cameras: {', '.join(unknown)}. Known: {', '.join(sorted(cams))}")

    loop_len = {}
    if args.loop_windows:
        manifest = json.loads(args.loop_windows.read_text(encoding="utf-8"))
        loop_len = {c["camera"]: math.ceil(c["seconds"]) for c in manifest.get("clips", []) if "seconds" in c}
    plan = [(n, max(loop_len[n], s) if n in loop_len else s)
            for _ in range(args.repeat) for n in names for s in args.clip_seconds]
    print(f"Plan: {len(plan)} requests ({len(names)} cameras x {len(args.clip_seconds)} clip lengths x "
          f"{args.repeat} repeats), {args.concurrency} at a time. Each completed one costs 1 of 500 today.")
    if len(plan) > args.max_requests:
        sys.exit(f"Refusing: the plan exceeds --max-requests {args.max_requests}.")

    with Gateway() as gw:
        q = gw.quota()
        print(f"Allowance: {q['DailySummaryCount']} of {q['DailySummaryQuota']} used, resets {q['DailySummaryReset']}"
              if q else "Allowance: not available right now")
        default_model = next((m["Name"] for m in gw.models() if m.get("IsDefault")), "?")
        print(f"Model: {default_model}")

        prompt, prompt_id = args.prompt, None
        if args.prompt_title:
            saved = gw.find_prompt(args.prompt_title) or sys.exit(f"No saved prompt titled '{args.prompt_title}'")
            prompt, prompt_id = saved["Text"], saved["Id"]
        if args.dry_run:
            print("Dry run: nothing sent.")
            return 0

        run_dir = args.run_dir or REPO / "run" / f"bench-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
        run_dir.mkdir(parents=True, exist_ok=True)
        out = run_dir / "results.jsonl"
        rows = []
        for i in range(0, len(plan), args.concurrency):
            batch = plan[i:i + args.concurrency]
            left = remaining(gw, args.stop_at)
            if left is not None and left < len(batch):
                print(f"Stopping: today's count would pass --stop-at {args.stop_at}.")
                break
            labels, tracked = {}, []
            end = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=args.end_offset)
            for cam, secs in batch:
                created = gw.ask(video_uri(cams[cam], end - dt.timedelta(seconds=secs), end), prompt, prompt_id)
                t = Tracked(created["Id"], submitted=time.monotonic(), summary=created)
                labels[t.id] = f"{cam} {secs}s"
                tracked.append(t)

            def show(t: Tracked) -> None:
                print(f"  [{labels[t.id]}] {t.progress} at +{t.seen[t.progress] - t.submitted:.1f}s")

            gw.wait_all(tracked, poll=args.poll, on_change=show)
            for t, (cam, secs) in zip(tracked, batch):
                row = {"id": t.id, "label": args.label,
                       "clip_end_utc": f"{end:%Y-%m-%dT%H:%M:%SZ}", "camera": cam, "clip_s": secs, "batch_size": len(batch), "progress": t.progress,
                       **spans(t), "server_total": server_seconds(t.summary),
                       "response": t.summary.get("Response"), "error": t.summary.get("LastError")}
                rows.append(row)
                with out.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

        q = gw.quota()
        if q:
            print(f"\nAllowance now: {q['DailySummaryCount']} of {q['DailySummaryQuota']} used")

    if not rows:
        return 1
    print(f"\n{'camera':<44}{'clip':>5}{'batch':>6}{'queue':>7}{'fetch':>7}{'upload':>7}{'vlm':>7}{'total':>7}{'server':>7}  result")
    for r in rows:
        result = f"{len(r['response'] or '')} chars" if r["progress"] == "Completed" else f"{r['progress']}: {r['error']}"
        print(f"{r['camera']:<44}{r['clip_s']:>5}{r['batch_size']:>6}{fmt(r['queue']):>7}{fmt(r['fetch']):>7}"
              f"{fmt(r['upload']):>7}{fmt(r['vlm']):>7}{fmt(r['total']):>7}{fmt(r['server_total']):>7}  {result}")
    totals = [r["total"] for r in rows if r["progress"] == "Completed" and r["total"] is not None]
    if totals:
        print(f"\nCompleted {len(totals)}/{len(rows)}: total min {min(totals):.1f}s, median "
              f"{statistics.median(totals):.1f}s, max {max(totals):.1f}s")
    print(f"Results: {out}")
    for r in rows:
        if r["response"]:
            print(f"\n--- {r['camera']} {r['clip_s']}s ---\n{r['response']}")
    return 0 if len(totals) == len(rows) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GatewayError as e:
        sys.exit(str(e))
