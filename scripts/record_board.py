r"""record_board.py - film the owner board (and the shift summary) without a desktop: Edge renders the page headless
every --every seconds into PNG frames, then ffmpeg makes an MP4 of them at --speed times real time.

    .venv\Scripts\python.exe scripts\record_board.py --minutes 10 [--every 1] [--speed 4] [--url http://127.0.0.1:8765/]
                                                     [--out docs\video\board] [--summary]

Run it beside scripts\run_clearway.py (the board follows the newest run): the frames show the cards arriving. --summary
also renders /summary once at the end. The frames are 1920x1080; the MP4 (board.mp4, H.264, no audio) is cut into the
demonstration video by scripts\make_video.py. Costs no request. The frames and the MP4 hold camera footage and are
git-ignored (docs/video/).
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from lens.publisher import FFMPEG  # noqa: E402

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def render(url: str, png: Path, size: str = "1920,1080", budget_ms: int = 4000) -> bool:
    """One headless screenshot of url into png (the page's scripts get budget_ms of virtual time to fetch and draw)."""
    try:
        r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={size}",
                            f"--virtual-time-budget={budget_ms}", f"--screenshot={png}", url],
                           capture_output=True, timeout=30)
    except subprocess.TimeoutExpired:              # Edge held by the saturated machine (2026-11-02): the frame is
        return False                               # skipped, the recording goes on
    return r.returncode == 0 and png.exists()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--every", type=float, default=1.0, help="seconds between frames")
    ap.add_argument("--speed", type=float, default=4.0, help="playback speed against real time")
    ap.add_argument("--url", default="http://127.0.0.1:8765/")
    ap.add_argument("--out", type=Path, default=REPO / "docs" / "video" / "board")
    ap.add_argument("--summary", action="store_true", help="render /summary once at the end")
    args = ap.parse_args()
    frames = args.out / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    t_end = time.monotonic() + 60 * args.minutes
    n = 0
    print(f"rendering {args.url} every {args.every:g} s for {args.minutes:g} min into {frames}", flush=True)
    while time.monotonic() < t_end:
        t0 = time.monotonic()
        if render(args.url, frames / f"{n:05d}.png"):
            n += 1
        else:
            print(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%S} render failed", flush=True)
        if n % 30 == 0:
            print(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%S} {n} frames", flush=True)
        time.sleep(max(0.0, args.every - (time.monotonic() - t0)))
    if args.summary:
        render(args.url.rstrip("/") + "/summary", args.out / "summary.png", budget_ms=6000)
    fps = args.speed / args.every
    mp4 = args.out / "board.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", f"{fps:g}", "-i", str(frames / "%05d.png"),
                    "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-r", "30", "-c:v", "libx264",
                    "-crf", "20", "-preset", "medium", str(mp4)], check=True)
    print(f"{n} frames -> {mp4} ({n * args.every / args.speed:.0f} s at {args.speed:g}x)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
