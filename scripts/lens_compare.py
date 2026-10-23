r"""lens_compare.py - one event, asked about plainly and through the lens camera.

    .venv\Scripts\python.exe scripts\lens_compare.py --camera test_11 --clip data\clips\800x410_test_11 --at 603 `
        --box 140 75 330 180

The camera loops a clip, so the event comes round every loop. FrameBridge watches the camera live and finds the moment
by matching each frame (the region around --box) against the clip's frame at --at. The frames around it then give:
  plain       Hafnia on the camera's own recording, the window centred on the event (as the live pipeline asks);
  crop        the same window cropped around --box and enlarged, played on lens_1;
  crop_slow2  the crop at half speed (each frame twice), so Hafnia's frame sampling sees twice as many moments.
Each is one Hafnia request (1 + the number of --variants) with the live pipeline's one-word incident prompt.
--variants crop_sr adds the crop enlarged by super-resolution (lens/enhance.py) instead of bicubic. Needs lens.publisher
running (scripts\start_lens.ps1). Writes run\lens-<camera>-<UTC>\results.json; the frames sent go to frames\
(git-ignored: footage licences).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from hafnia.gateway import Gateway  # noqa: E402
from hafnia.xprotect_rest import XProtect  # noqa: E402
from incident.bridge import FrameBridge  # noqa: E402
from incident.verify import CLASSIFY, ask, parse  # noqa: E402
from lens.client import crop, slow, span, submit, wait  # noqa: E402
from lens.enhance import SuperRes  # noqa: E402
from locate_event import FFMPEG  # noqa: E402


def gateway_password() -> str:
    """As scripts\\run_live.py: the process environment, else the user environment (shells started earlier)."""
    import os
    pw = os.environ.get("HAFNIA_GW_PASSWORD")
    if not pw:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            pw = winreg.QueryValueEx(k, "HAFNIA_GW_PASSWORD")[0]
    return pw


def source_frame(clip: Path, at: float, fps: int) -> np.ndarray:
    import subprocess
    png = subprocess.run([FFMPEG, "-v", "error", "-f", "h264", "-framerate", str(fps), "-i", str(clip), "-vf",
                          f"select=eq(n\\,{round(at * fps)})", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png",
                          "-"], capture_output=True, check=True).stdout
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)


def region_thumb(img: np.ndarray, box: list[float]) -> np.ndarray:
    """Grayscale thumbnail of the box with as much margin again on every side: the event dominates the score."""
    x1, y1, x2, y2 = box
    mx, my = x2 - x1, y2 - y1
    h, w = img.shape[:2]
    r = img[max(0, int(y1 - my)):min(h, int(y2 + my)), max(0, int(x1 - mx)):min(w, int(x2 + mx))]
    return cv2.resize(cv2.cvtColor(r, cv2.COLOR_BGR2GRAY), (96, 54), interpolation=cv2.INTER_AREA).astype(np.float32)


def sheet(frames: list[np.ndarray], path: Path, n: int = 12) -> None:
    pick = [frames[round(i * (len(frames) - 1) / (n - 1))] for i in range(n)]
    tiles = [cv2.resize(f, (320, int(320 * f.shape[0] / f.shape[1]))) for f in pick]
    h = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in tiles]
    cv2.imwrite(str(path), np.vstack([np.hstack(tiles[r * 4:(r + 1) * 4]) for r in range(n // 4)]))


def find_event(camera: str, ref: np.ndarray, box: list[float], half: float, ratio: float, timeout_s: float
               ) -> tuple[dt.datetime, list[tuple[dt.datetime, np.ndarray]]]:
    """Watch the camera until the event has come round; returns its time and the frames from half + 2 s before to
    half + 1 s after it."""
    bridge = FrameBridge([camera], log=lambda s: print(s, flush=True))
    keep = dt.timedelta(seconds=half + 15)
    buf: deque[tuple[dt.datetime, bytes]] = deque()
    scores: deque[float] = deque(maxlen=600)
    best: tuple[float, dt.datetime] | None = None
    deadline = time.monotonic() + timeout_s
    try:
        for _, t, jpeg in bridge.frames():
            buf.append((t, jpeg))
            while buf and t - buf[0][0] > keep:
                buf.popleft()
            if best and t - best[1] > dt.timedelta(seconds=half + 1):
                break
            if best is None or t - best[1] < dt.timedelta(seconds=1.5):
                frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                s = float(np.abs(region_thumb(frame, box) - ref).mean())
                med = statistics.median(scores) if len(scores) >= 100 else None
                scores.append(s)
                if med and s < ratio * med and (best is None or s < best[0]):
                    if best is None:
                        print(f"{t:%H:%M:%S.%f} match {s:.2f} (median {med:.2f})", flush=True)
                    best = (s, t)
            if time.monotonic() > deadline:
                raise TimeoutError(f"event not seen on {camera} within {timeout_s:.0f} s")
    finally:
        bridge.close()
    t_event = best[1]
    lo = t_event - dt.timedelta(seconds=half + 2)
    frames = [(t, cv2.imdecode(np.frombuffer(j, np.uint8), cv2.IMREAD_COLOR)) for t, j in buf if t >= lo]
    return t_event, frames


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--camera", required=True)
    ap.add_argument("--clip", type=Path, required=True, help="the camera's clip (H.264 Annex B), for the reference frame")
    ap.add_argument("--at", type=float, required=True, help="event time in the clip, seconds")
    ap.add_argument("--box", type=float, nargs=4, required=True, metavar=("X1", "Y1", "X2", "Y2"),
                    help="event region in the camera image (pixels): the crop centre, standing in for tier 0's boxes")
    ap.add_argument("--half", type=float, default=3.0, help="half the window, seconds (6 s windows by default)")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--match-ratio", type=float, default=0.3,
                    help="a match scores below this share of the median score (test_11 offline: event 0.04-0.26, "
                         "best elsewhere 0.46)")
    ap.add_argument("--timeout", type=float, default=1200, help="seconds to wait for the event to come round")
    ap.add_argument("--stop-at", type=int, default=450, help="do not ask when today's count has reached this")
    ap.add_argument("--variants", nargs="+", default=["crop", "crop_slow2"], choices=["crop", "crop_slow2", "crop_sr"],
                    help="lens variants besides plain; crop_sr enlarges the crop with Real-ESRGAN (lens/enhance.py)")
    args = ap.parse_args()

    out = REPO / "run" / f"lens-{args.camera}-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
    (out / "frames").mkdir(parents=True)
    ref = region_thumb(source_frame(args.clip, args.at, args.fps), args.box)
    gw = Gateway()
    gw.login(gateway_password())
    q = gw.quota()
    n = 1 + len(args.variants)
    if q and q["DailySummaryCount"] + n > args.stop_at:
        sys.exit(f"today's count is {q['DailySummaryCount']}: {n} more would pass --stop-at {args.stop_at}")
    cams = XProtect().cameras()

    print(f"watching {args.camera} for the event (the clip loops; up to {args.timeout:.0f} s)", flush=True)
    t_event, frames = find_event(args.camera, ref, args.box, args.half, args.match_ratio, args.timeout)
    lo, hi = t_event - dt.timedelta(seconds=args.half), t_event + dt.timedelta(seconds=args.half)
    window = [f for t, f in frames if lo <= t < hi]
    print(f"event at {t_event:%H:%M:%S.%f} UTC; {len(window)} frames in the window", flush=True)

    crops = [crop(f, args.box) for f in window]
    available = {"crop": lambda: crops, "crop_slow2": lambda: slow(crops, 2),
                 "crop_sr": lambda: SuperRes("general").upscale_all(crops)}
    variants = {v: available[v]() for v in args.variants}
    jobs = {name: submit(fr, f"{args.camera}-{name}", fps=args.fps, meta={"camera": args.camera, "variant": name})
            for name, fr in variants.items()}
    sheet(window, out / "frames" / "plain.jpg")
    for name, fr in variants.items():
        sheet(fr, out / "frames" / f"{name}.jpg")
    played = {name: wait(job) for name, job in jobs.items()}
    time.sleep(5)   # let the last lens frames reach the recording

    asks = {"plain": (cams[args.camera], lo, hi)}
    for name, done in played.items():
        asks[name] = (cams["lens_1"], *span(done))
    results = {"camera": args.camera, "event_utc": t_event.isoformat(), "at": args.at, "box": args.box,
               "half_s": args.half, "prompt": CLASSIFY, "played": played, "answers": {}}
    for name, (cam_id, start, end) in asks.items():
        summary, secs = ask(gw, cam_id, start, end, CLASSIFY)
        answer = summary.get("Response") or ""
        results["answers"][name] = {"start": start.isoformat(), "end": end.isoformat(), "seconds": round(secs, 1),
                                    "progress": summary.get("Progress"), "label": parse(answer) if answer else None,
                                    "answer": answer, "error": summary.get("LastError"), "summary_id": summary.get("Id")}
        print(f"{name:11} {summary.get('Progress'):9} {parse(answer) if answer else '-':9} {secs:5.1f} s  "
              f"{(answer or summary.get('LastError') or '')[:100]}", flush=True)
    (out / "results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
