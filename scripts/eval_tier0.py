r"""eval_tier0.py - offline evaluation of tier 0 candidates on the accident clips and normal-traffic clips.

    .venv\Scripts\python.exe scripts\eval_tier0.py --out run\tier0-<date>

Positives: clips in data/clips.json with an "impact" time, played twice back to back like a looped camera; only the
second pass is scored, so the tracker has history before every impact. A hit is a candidate within --tolerance s of
the impact. Negatives: the organizer's normal-traffic clips, looped to at least --negative-seconds. Every candidate
that is not a hit counts as a false candidate. Costs no Hafnia requests.
"""
from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from tier0.pipeline import Tier0  # noqa: E402
from tier0.rules import Params  # noqa: E402
from tier0.source import video_frames  # noqa: E402

FFMPEG = r"C:\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
DRIVER_H264 = Path(r"C:\Program Files (x86)\Milestone\XProtect Recording Server\Drivers\NativeDrivers"
                   r"\StableFPS_DATA\Video\H264")
NORMAL = ["1280x720_busy_street", "1920x1080_highway_traffic_overcast_weather",
          "832x480_city_street_7_condensation_inside_housing", "832x480_traffic_flows_in_the_open_lanes"]


def remux(raw: Path, out_dir: Path) -> Path:
    """Organizer clips are raw H.264 at 10 fps; wrap them in MP4 so OpenCV reads them."""
    out = out_dir / (raw.name + ".mp4")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "h264", "-framerate", "10", "-i", str(raw), "-c", "copy",
                    str(out)], check=True)
    return out


def duration(path: Path) -> float:
    n = sum(1 for _ in video_frames(path, 10.0, 1))
    return n / 10.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tolerance", type=float, default=2.5)
    ap.add_argument("--negative-seconds", type=float, default=60.0)
    ap.add_argument("--cap-negatives", action="store_true",
                    help="stop each normal clip after --negative-seconds (quick tuning; the 13-min highway clip dominates)")
    ap.add_argument("--imgsz", type=int, default=640, help="YOLO inference size")
    ap.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    ap.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE",
                    help="override tier0.rules.Params fields, e.g. --set decel_drop=0.6 contact_gap=0.3")
    args = ap.parse_args()
    overrides = {k: type(getattr(Params(), k))(v) for k, v in (s.split("=", 1) for s in args.set)}
    params = Params(**overrides)
    print(f"params: {overrides or 'defaults'}, imgsz {args.imgsz}, conf {args.conf}")
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((REPO / "data" / "clips.json").read_text(encoding="utf-8"))
    rows, frames_total, t_start = [], 0, time.perf_counter()

    for c in (c for c in manifest["clips"] if "impact" in c):
        src = REPO / "data" / c["source"]
        dur = duration(src)
        t0 = Tier0(params=params, conf=args.conf, imgsz=args.imgsz)
        frames_total += round(2 * dur * 10)
        cands = [x for x in t0.run(video_frames(src, 10.0, loops=2)) if x.t >= dur]                 # second pass only
        impact = dur + c["impact"]
        hits = [x for x in cands if abs(x.t - impact) <= args.tolerance]
        false = [x for x in cands if abs(x.t - impact) > args.tolerance]
        rows.append({"clip": c["camera"], "kind": "accident", "seconds": round(dur, 1), "hit": bool(hits),
                     "hit_delay_s": round(min((x.t - impact for x in hits), key=abs), 1) if hits else None,
                     "false": len(false), "candidates": [asdict(x) | {"t_clip": round(x.t - dur, 1)} for x in cands]})
        print(f"{c['camera']}: {'HIT ' if hits else 'MISS'} false={len(false)}  "
              + "; ".join(f"{x.t - dur:.1f}s {x.kind} {x.score}" for x in cands))

    # A persistent cache, not a temp dir: Windows kept the MP4 locked and TemporaryDirectory's cleanup crashed.
    cache = REPO / "data" / "clips" / "_mp4"
    cache.mkdir(parents=True, exist_ok=True)
    for name in NORMAL:
        mp4 = cache / (name + ".mp4")
        if not mp4.exists():
            mp4 = remux(DRIVER_H264 / name, cache)
        dur = duration(mp4)
        loops = max(1, int(-(-args.negative_seconds // dur)))
        t0 = Tier0(params=params, conf=args.conf, imgsz=args.imgsz)
        seconds = min(loops * dur, args.negative_seconds) if args.cap_negatives else loops * dur
        frames_total += round(seconds * 10)
        cands = t0.run(itertools.takewhile(lambda f: f[0] < seconds, video_frames(mp4, 10.0, loops=loops)))
        rows.append({"clip": name.split("_", 1)[1], "kind": "normal", "seconds": round(seconds, 1),
                     "hit": None, "false": len(cands), "candidates": [asdict(x) for x in cands]})
        print(f"{name}: {seconds:.0f}s false={len(cands)}  "
              + "; ".join(f"{x.t:.1f}s {x.kind} {x.score}" for x in cands[:6]))

    elapsed = time.perf_counter() - t_start
    acc = [r for r in rows if r["kind"] == "accident"]
    normal_minutes = sum(r["seconds"] for r in rows if r["kind"] == "normal") / 60
    summary = {
        "recall": f"{sum(r['hit'] for r in acc)}/{len(acc)}",
        "false_on_accident_clips": sum(r["false"] for r in acc),
        "false_per_minute_normal": round(sum(r["false"] for r in rows if r["kind"] == "normal") / normal_minutes, 2),
        "frames_per_second": round(frames_total / elapsed, 1),
    }
    (args.out / "tier0_results.json").write_text(json.dumps({"params": overrides, "imgsz": args.imgsz, "conf": args.conf, "summary": summary, "rows": rows}, indent=1),
                                                 encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
