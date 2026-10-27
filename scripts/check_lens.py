r"""check_lens.py - measure lens_1's recorded time base against the publisher's clock, with the frame code. No requests.

    .venv\Scripts\python.exe scripts\check_lens.py [--minutes 3] [--clips 4] [--clip-s 6] [--export] [--out DIR]

Reads lens_1's live frames (FrameBridge, with the Recording Server's frame times) through lens/clock.py and logs the
offset (recorded time minus the wall time in each frame's code) every second to <out>\offsets.jsonl. Meanwhile it
plays --clips synthetic clips on the lens (a numbered label and a moving square) and, for each, records the span the
publisher logged, the span the clock measured from the clip's own frames, and the clock's verification
(<out>\clips.jsonl). With --export, the recording itself is then read for each clip's measured span
(scripts\export_window.ps1, MilestonePSTools: slow, about half a minute per clip) and every exported frame's code is
compared with its recorded time: the ground truth that the live feed's times are the recording's, and that the
measured span holds the clip. Run it on a quiet machine, and again while scripts\run_clearway.py loads the Recording
Server, with the publisher started with and without --wallclock (restart it between: scripts\start_lens.ps1 after
stopping the old one), to compare the stream's time bases.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from lens.client import submit, wait  # noqa: E402
from lens.clock import LensClock  # noqa: E402
from lens.code import read  # noqa: E402


def synthetic(k: int, seconds: float, fps: int = 10, w: int = 1280, h: int = 720) -> list[np.ndarray]:
    """A clip no camera shows: a numbered label on a coloured ground, a white square crossing the frame."""
    n = round(seconds * fps)
    colour = [(60, 40, 120), (40, 110, 60), (120, 70, 30), (30, 90, 120)][k % 4]
    frames = []
    for i in range(n):
        f = np.full((h, w, 3), colour, np.uint8)
        cv2.putText(f, f"CHECK {k}", (w // 2 - 220, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 3.0, (255, 255, 255), 6)
        cv2.putText(f, f"frame {i}", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (230, 230, 230), 3)
        x = int(60 + (w - 260) * i / max(1, n - 1))
        cv2.rectangle(f, (x, h - 220), (x + 140, h - 80), (255, 255, 255), -1)
        frames.append(f)
    return frames


def export(camera: str, start: dt.datetime, end: dt.datetime, out: Path, fps: int = 2) -> list[Path]:
    """The recording's frames over [start, end) as <unix-ms>.jpg files (scripts/export_window.ps1)."""
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(REPO / "scripts" / "export_window.ps1"), "-Camera", camera,
                        "-Start", start.strftime("%Y-%m-%dT%H:%M:%SZ"), "-End", end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "-Out", str(out), "-Fps", str(fps)], capture_output=True, text=True)
    if r.returncode:
        print(f"export failed: {r.stderr.strip()[-400:]}", flush=True)
    return sorted(out.glob("*.jpg"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--minutes", type=float, default=3.0)
    ap.add_argument("--clips", type=int, default=4)
    ap.add_argument("--clip-s", type=float, default=6.0)
    ap.add_argument("--export", action="store_true", help="read the recording back for each clip's measured span")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    out = args.out or REPO / "run" / f"lens-check-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
    out.mkdir(parents=True, exist_ok=True)
    clock = LensClock.standalone(log=lambda s: print(s, flush=True))
    stop = threading.Event()

    def ticker() -> None:
        with (out / "offsets.jsonl").open("a", encoding="utf-8") as f:
            n = 0
            while not stop.is_set():
                time.sleep(1.0)
                rec = {"wall": round(time.time(), 2), **clock.stats()}
                f.write(json.dumps(rec) + "\n")
                f.flush()
                n += 1
                if n % 10 == 0:
                    print(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%S} offset {rec['offset_s']} s "
                          f"(last minute {rec['offset_min_s']} to {rec['offset_max_s']}), {rec['decoded']} readable "
                          f"of {rec['frames']} frames, {rec['dropped']} dropped", flush=True)

    threading.Thread(target=ticker, daemon=True).start()
    t_end = time.monotonic() + 60 * args.minutes
    print(f"waiting for lens_1's frames ...", flush=True)
    while not clock.alive() and time.monotonic() < t_end:
        time.sleep(0.5)
    if not clock.alive():
        print("no readable lens_1 frame: is the publisher running with the frame code (lens/publisher.py)?")
        return 1
    print(f"clock alive after {60 * args.minutes - (t_end - time.monotonic()):.1f} s; offset now {clock.offset()}",
          flush=True)
    rows = []
    for k in range(args.clips):
        job = submit(synthetic(k, args.clip_s), f"check-{k}")
        t0 = time.monotonic()
        done = wait(job, timeout=300)
        start, end, info = clock.span_for(done)
        row = {"k": k, "job": job, "seq": done["seq"], "frames": done["frames"], "sent": done["sent"],
               "wall": [done["start"], done["end"]], "measured": [start.isoformat(), end.isoformat()],
               "waited_s": round(time.monotonic() - t0, 1), **{k2: v for k2, v in info.items() if k2 != "ready_wall"}}
        rows.append(row)
        print(f"clip {k}: seq {done['seq']}, sent {done['start'][11:23]}-{done['end'][11:23]}, recorded "
              f"{start:%H:%M:%S}-{end:%H:%M:%S}, offset {info.get('offset_s')} s, drift {info.get('drift_s')} s, "
              f"seen {info['seen']}/{done['sent']}, hole {info.get('hole_s')} s, verified {info['verified']}"
              + (f", assumed: {info['reason']}" if info.get("assumed") else ""), flush=True)
        with (out / "clips.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        if k + 1 < args.clips:
            time.sleep(8.0)
    while time.monotonic() < t_end:
        time.sleep(1.0)
    stop.set()
    offs = [json.loads(x) for x in (out / "offsets.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    xs = [o["offset_s"] for o in offs if o.get("offset_s") is not None]
    summary = {"minutes": args.minutes, "offset_median_s": round(statistics.median(xs), 2) if xs else None,
               "offset_min_s": min(xs, default=None), "offset_max_s": max(xs, default=None),
               "readable": clock.counts["decoded"], "frames": clock.counts["frames"],
               "clips": len(rows), "verified": sum(bool(r["verified"]) for r in rows)}
    print(f"offset over {args.minutes:g} min: median {summary['offset_median_s']} s, min {summary['offset_min_s']}, "
          f"max {summary['offset_max_s']}; {summary['verified']} of {len(rows)} clips verified", flush=True)
    if args.export and rows:
        checks = []
        for r in rows:
            start, end = (dt.datetime.fromisoformat(s) for s in r["measured"])
            folder = out / "recorded" / f"clip{r['k']}"
            folder.mkdir(parents=True, exist_ok=True)
            files = export("lens_1", start - dt.timedelta(seconds=1), end + dt.timedelta(seconds=1), folder)
            inside, codes = 0, []
            for p in files:
                rec_t = int(p.stem) / 1000
                img = cv2.imread(str(p))
                code = read(img, dt.datetime.fromtimestamp(rec_t, dt.timezone.utc)) if img is not None else None
                in_span = start.timestamp() <= rec_t < end.timestamp()
                if code is not None:
                    codes.append({"recorded": rec_t, "seq": code["seq"], "idx": code["idx"],
                                  "offset_s": round(rec_t - code["wall"].timestamp(), 2), "in_span": in_span})
                    inside += in_span and code["seq"] == r["seq"]
            own = [c for c in codes if c["in_span"] and c["seq"] == r["seq"]]
            other = [c for c in codes if c["in_span"] and c["seq"] not in (0, r["seq"])]
            idle = [c for c in codes if c["in_span"] and c["seq"] == 0]
            offs_rec = [c["offset_s"] for c in own]
            chk = {"k": r["k"], "exported": len(files), "readable": len(codes), "in_span_own": len(own),
                   "in_span_other": len(other), "in_span_idle": len(idle),
                   "recorded_offset_s": round(statistics.median(offs_rec), 2) if offs_rec else None,
                   "live_offset_s": r.get("offset_s"), "codes": codes}
            checks.append(chk)
            print(f"recording, clip {r['k']}: {len(files)} frames exported over the measured span (+1 s each side), "
                  f"{len(codes)} readable; inside the span: {len(own)} of this clip, {len(other)} of other clips, "
                  f"{len(idle)} idle; offset in the recording {chk['recorded_offset_s']} s vs live feed "
                  f"{chk['live_offset_s']} s", flush=True)
        summary["recorded"] = [{k2: v for k2, v in c.items() if k2 != "codes"} for c in checks]
        (out / "recorded.json").write_text(json.dumps(checks, indent=1), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    clock.close()
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
