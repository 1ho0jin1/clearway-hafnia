r"""bench_tiered_vs_polling.py - tiered pipeline vs Hafnia-only polling on the same recorded footage.

    .venv\Scripts\python.exe scripts\bench_tiered_vs_polling.py --out run\compare-<date> [--span 36] [--dry-run]

For each camera, the same span of recorded video (ending --end-ago seconds ago):
- Ground truth: for accident cameras (data/clips.json with "impact"), one impact is located in the recordings by
  matching recorded frames to the source frame at the impact; the loop repeats it every clip length.
- Polling (Hafnia only): consecutive --poll-seconds windows across the span, each asked the one-word question.
- Tiered: tier 0 replays the recorded frames at 10 fps, the router decides with the live settings, and each routed
  candidate gets Hafnia on the 6 s window centred on it; verdicts feed back into the router, as live.
Scoring, the same for both: an ACCIDENT answer is correct when its window overlaps an impact or the --aftermath
seconds after it; any other ACCIDENT answer is a false alarm.

Cost: polling = cameras x span / poll-seconds requests; tiered = one per routed candidate. --dry-run prints the plan.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from hafnia.gateway import Gateway, Tracked, video_uri  # noqa: E402
from hafnia.xprotect_rest import XProtect  # noqa: E402
from incident.router import Router, RouterConfig  # noqa: E402
from incident.verify import CLASSIFY, parse, verify  # noqa: E402
from scripts.run_live import gateway_password  # noqa: E402
from tier0.pipeline import Tier0  # noqa: E402

_spec = importlib.util.spec_from_file_location("locate_event", REPO / "scripts" / "locate_event.py")
locate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(locate)

HALF = dt.timedelta(seconds=3)
WARMUP_S = 6.0


def export(camera: str, start: dt.datetime, end: dt.datetime, out: Path) -> list[Path]:
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(REPO / "scripts" / "export_window.ps1"), "-Camera", camera, "-Start", start.isoformat(),
                    "-End", end.isoformat(), "-Out", str(out)], check=True, capture_output=True, text=True)
    return sorted(out.glob("*.jpg"), key=lambda f: int(f.stem))


def locate_impacts(clip_entry: dict, frames: list[Path], start: dt.datetime, end: dt.datetime) -> tuple[list, float]:
    """All impact times in [start, end] for a looped accident clip, and the match ratio of the located one."""
    from PIL import Image, ImageChops, ImageStat
    clip = next((REPO / "data" / "clips").glob(f"*_{clip_entry['camera']}"))
    ref = locate.source_frame(clip, clip_entry["impact"], 10)
    scores = [(ImageStat.Stat(ImageChops.difference(ref, locate.thumb(Image.open(f)))).mean[0], int(f.stem))
              for f in frames]
    best, ms = min(scores)
    median = sorted(s for s, _ in scores)[len(scores) // 2]
    loop = clip_entry["loop_s"]   # the camera plays the clip at 10 fps: frames / 10 = its length in clips.json
    t0 = dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc)
    k_lo = math.floor((start - t0).total_seconds() / loop) - 1
    k_hi = math.ceil((end - t0).total_seconds() / loop) + 1
    impacts = [t0 + dt.timedelta(seconds=k * loop) for k in range(k_lo, k_hi + 1)]
    return [t for t in impacts if start <= t <= end], round(best / median, 3) if median else 1.0


def overlaps(w_start: dt.datetime, w_end: dt.datetime, impacts: list, aftermath: float) -> dt.datetime | None:
    for t in impacts:
        if w_start <= t + dt.timedelta(seconds=aftermath) and w_end >= t:
            return t
    return None


def ask_many(gw: Gateway, jobs: list[dict], concurrency: int) -> None:
    """jobs: dicts with camera_id, start, end; adds summary fields in place."""
    for i in range(0, len(jobs), concurrency):
        batch = jobs[i:i + concurrency]
        tracked = []
        for j in batch:
            created = gw.ask(video_uri(j["camera_id"], j["start"], j["end"]), CLASSIFY)
            tracked.append(Tracked(created["Id"], submitted=time.monotonic(), summary=created))
        gw.wait_all(tracked, poll=1.0)
        for j, t in zip(batch, tracked):
            j["progress"] = t.progress
            j["answer"] = t.summary.get("Response", "")
            j["error"] = t.summary.get("LastError", "")
            j["label"] = parse(j["answer"]) if t.progress == "Completed" else "FAILED"
            j["hafnia_s"] = round(t.seen.get(t.progress, t.submitted) - t.submitted, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cameras", nargs="+", default=["test_01", "test_02", "test_03", "test_04", "test_05",
                                                      "traffic_flows_in_the_open_lanes",
                                                      "highway_traffic_overcast_weather"])
    ap.add_argument("--span", type=float, default=36.0, help="seconds of recording per camera")
    ap.add_argument("--end-ago", type=float, default=90.0, help="span ends this many seconds ago")
    ap.add_argument("--poll-seconds", type=float, default=6.0)
    ap.add_argument("--aftermath", type=float, default=6.0)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = {c["camera"]: c for c in json.loads((REPO / "data" / "clips.json").read_text(encoding="utf-8"))["clips"]}
    for c in manifest.values():
        c["loop_s"] = c["seconds"]
    n_poll = len(args.cameras) * math.ceil(args.span / args.poll_seconds)
    print(f"Plan: {len(args.cameras)} cameras x {args.span:.0f} s. Polling: {n_poll} requests. "
          f"Tiered: one per routed candidate (router cap 20).")
    if args.dry_run:
        return 0

    xp, gw = XProtect(), Gateway()
    gw.login(gateway_password())
    cam_ids = xp.cameras()
    end = dt.datetime.now(dt.timezone.utc).replace(microsecond=0) - dt.timedelta(seconds=args.end_ago)
    start = end - dt.timedelta(seconds=args.span)
    args.out.mkdir(parents=True, exist_ok=True)
    result = {"span": [start.isoformat(), end.isoformat()], "params": vars(args) | {"out": str(args.out)},
              "cameras": {}}

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        poll_jobs, tiered_rows = [], []
        router = Router(RouterConfig(max_requests=20))
        for cam in args.cameras:
            entry = manifest.get(cam)
            loop = entry["loop_s"] if entry else 0
            frames = export(cam, start - dt.timedelta(seconds=max(WARMUP_S, loop)), end, Path(tmp) / cam)
            impacts, ratio = (locate_impacts(entry, frames, start, end) if entry and "impact" in entry else ([], None))
            print(f"{cam}: {len(frames)} frames, impacts {[t.strftime('%H:%M:%S.%f')[:-5] for t in impacts]}"
                  + (f" (match ratio {ratio})" if ratio is not None else ""), flush=True)
            result["cameras"][cam] = {"impacts": [t.isoformat() for t in impacts], "match_ratio": ratio,
                                      "frames": len(frames)}

            # Polling windows.
            k = 0
            while start + dt.timedelta(seconds=k * args.poll_seconds) < end:
                ws = start + dt.timedelta(seconds=k * args.poll_seconds)
                poll_jobs.append({"camera": cam, "camera_id": cam_ids[cam], "start": ws,
                                  "end": min(end, ws + dt.timedelta(seconds=args.poll_seconds)), "impacts": impacts})
                k += 1

            # Tiered replay: tier 0 on the recorded frames (warm-up included), router, Hafnia per routed candidate.
            t0 = Tier0()
            seen = 0
            for f in frames:
                t = int(f.stem) / 1000
                img = cv2.imread(str(f))
                t0.feed(t, img)
                for cand in t0.detector.candidates[seen:]:
                    ct = dt.datetime.fromtimestamp(cand.t, dt.timezone.utc)
                    if not (start <= ct <= end - HALF):
                        continue
                    boxes = [t0.detector.tracks[k].box() for k in cand.tracks if k in t0.detector.tracks]
                    b = np.array(boxes).reshape(-1, 4)
                    spot = router.spot(b, img.shape[1], img.shape[0]) if len(b) else (0, 0)
                    d = router.decide(cam, cand.t, spot, None)
                    row = {"camera": cam, "t": ct.isoformat(), "kind": cand.kind, "score": cand.score,
                           "send": d.send, "reason": d.reason}
                    if d.send:
                        v = verify(gw, cam_ids[cam], ct - HALF, ct + HALF)
                        router.feedback(cam, cand.t, spot, v.confirmed)
                        hit = overlaps(ct - HALF, ct + HALF, impacts, args.aftermath)
                        row |= {"label": v.label, "answer": v.answer, "hafnia_s": round(v.seconds, 1),
                                "impact": hit.isoformat() if hit else None, "error": v.error}
                        print(f"  tiered {ct:%H:%M:%S.%f}"[:-3] + f" {cand.kind} -> {v.label}"
                              + (f" (impact {hit:%H:%M:%S})" if hit else ""), flush=True)
                    tiered_rows.append(row)
                seen = len(t0.detector.candidates)

        print(f"Polling: {len(poll_jobs)} requests...", flush=True)
        ask_many(gw, poll_jobs, args.concurrency)

    # Scoring.
    def score(rows, windows_of):
        total_impacts = sum(len(c["impacts"]) for c in result["cameras"].values())
        found, cams_found, false, delays = set(), set(), 0, []
        for r in rows:
            if r.get("label") != "ACCIDENT":
                continue
            ws, we = windows_of(r)
            hit = overlaps(ws, we, [dt.datetime.fromisoformat(t) for t in result["cameras"][r["camera"]]["impacts"]],
                           args.aftermath)
            if hit is None:
                false += 1
                continue
            if (r["camera"], hit) not in found:
                found.add((r["camera"], hit))
                delays.append((we - hit).total_seconds() + r["hafnia_s"])
            cams_found.add(r["camera"])
        acc_cams = [c for c, v in result["cameras"].items() if v["impacts"]]
        requests = sum(1 for r in rows if "label" in r)
        return {"requests": requests, "impacts_found": f"{len(found)}/{total_impacts}",
                "accident_cameras_found": f"{len(cams_found)}/{len(acc_cams)}", "false_alarms": false,
                "alarms": sum(1 for r in rows if r.get("label") == "ACCIDENT"),
                "median_impact_to_verdict_s": round(sorted(delays)[len(delays) // 2], 1) if delays else None}

    poll_rows = [{**{k: v for k, v in j.items() if k not in ("camera_id", "impacts")},
                  "start": j["start"].isoformat(), "end": j["end"].isoformat()} for j in poll_jobs]
    result["polling"] = {"summary": score(poll_jobs, lambda r: (r["start"], r["end"])), "rows": poll_rows}
    result["tiered"] = {"summary": score(tiered_rows, lambda r: (dt.datetime.fromisoformat(r["t"]) - HALF,
                                                               dt.datetime.fromisoformat(r["t"]) + HALF)),
                        "rows": tiered_rows, "candidates": len(tiered_rows)}
    (args.out / "compare_results.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"polling": result["polling"]["summary"], "tiered": result["tiered"]["summary"],
                      "tier0_candidates": len(tiered_rows)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
