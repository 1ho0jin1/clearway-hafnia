r"""locate_event.py - find when a looped clip's event was recorded, by matching recorded frames to the source frame.

Injected cameras loop their clip, so an event recurs every loop at an unknown phase. This decodes the source frame at
the event time and compares it with recorded frames (JPEG files named <unix-ms>.jpg) on small grayscale thumbnails;
the closest frame gives the recorded time of the event.

    py scripts\locate_event.py --clip data\clips\1384x712_test_04 --at 1.2 --frames <dir> [--fps 10]

Prints JSON: {"best_ms", "best_score", "median_score", "ratio"}. A ratio (best / median) well below 1 means a
confident match; near 1 means the frames all look alike and the match is unreliable.
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

FFMPEG = r"C:\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
THUMB = (96, 54)


def thumb(img: Image.Image) -> Image.Image:
    return img.convert("L").resize(THUMB, Image.BILINEAR)


def source_frame(clip: Path, at: float, fps: int) -> Image.Image:
    n = round(at * fps)
    png = subprocess.run([FFMPEG, "-v", "error", "-f", "h264", "-framerate", str(fps), "-i", str(clip),
                          "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True).stdout
    return thumb(Image.open(io.BytesIO(png)))


def main() -> None:
    p = argparse.ArgumentParser(description="Locate a looped clip's event in recorded frames.")
    p.add_argument("--clip", type=Path, required=True)
    p.add_argument("--at", type=float, required=True, help="event time in the source clip, seconds")
    p.add_argument("--frames", type=Path, required=True, help="folder of recorded frames named <unix-ms>.jpg")
    p.add_argument("--fps", type=int, default=10)
    args = p.parse_args()

    ref = source_frame(args.clip, args.at, args.fps)
    scores = []
    for f in sorted(args.frames.glob("*.jpg")):
        diff = ImageChops.difference(ref, thumb(Image.open(f)))
        scores.append((ImageStat.Stat(diff).mean[0], int(f.stem)))
    best_score, best_ms = min(scores)
    median = statistics.median(s for s, _ in scores)
    print(json.dumps({"best_ms": best_ms, "best_score": round(best_score, 2), "median_score": round(median, 2),
                      "ratio": round(best_score / median, 3) if median else None, "frames": len(scores)}))


if __name__ == "__main__":
    main()
