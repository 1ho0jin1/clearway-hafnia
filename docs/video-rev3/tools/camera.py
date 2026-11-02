"""camera.py - camera moves and spotlights over a large still of a chart (the flowchart scenes).

    render(image, shots, duration, out, scale=3, oy=96, canvas=(1800, 1013), move=1.4, fade=0.8)

image: a PNG of the chart rendered at `scale` (e.g. 5400x3039 for a 1800x1013 canvas at 3x).
shots: [{"t": seconds, "box": [x, y, w] | "all", "hi": [[x, y, w, h], ...] | "all"}, ...], sorted by t.
  box is the visible window in chart units (16:9, its height follows from w); y is in drawing units, oy is
  added (the drawing's offset on the canvas). hi are the regions kept bright; the rest is dimmed.
Between shots the window eases over `move` seconds and the spotlight cross-fades over `fade` seconds.
Writes an H.264 1920x1080 30 fps video without audio, through ffmpeg (on PATH, or FFMPEG=...).
"""
from __future__ import annotations

import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter

OUT_W, OUT_H, FPS = 1920, 1080, 30
BG = (15, 20, 26)            # the cards' background, #0f141a
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def _ease(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def render(image, shots, duration, out, scale=3, oy=96, canvas=(1800, 1013), move=1.4, fade=0.8):
    S, (CW, CH) = scale, canvas

    def box_px(b):
        if b == "all":
            return (0.0, 0.0, CW * S, CH * S)
        x0, y0, w = b
        h = w * 9 / 16
        return (x0 * S, (y0 + oy) * S, (x0 + w) * S, (y0 + oy + h) * S)

    bright = Image.open(image).convert("RGB")
    size = bright.size

    def mask_for(hi):
        m = Image.new("L", size, 0)
        if hi == "all":
            m.paste(255, (0, 0, *size))
            return m
        d = ImageDraw.Draw(m)
        for x, y, w, h in hi:
            d.rounded_rectangle([x * S, (y + oy) * S, (x + w) * S, (y + h + oy) * S], radius=14 * S, fill=255)
        return m.filter(ImageFilter.GaussianBlur(6 * S))

    dim = Image.blend(Image.new("RGB", size, BG), bright, 0.28)
    masks = [mask_for(s["hi"]) for s in shots]
    boxes = [box_px(s["box"]) for s in shots]
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for f in range(int(round(duration * FPS))):
        t = f / FPS
        k = max([i for i, s in enumerate(shots) if s["t"] <= t] or [0])
        if k > 0:
            box = tuple(a + (b - a) * _ease((t - shots[k]["t"]) / move) for a, b in zip(boxes[k - 1], boxes[k]))
            a = _ease((t - shots[k]["t"]) / fade)
        else:
            box, a = boxes[0], 1.0
        ib = (max(0, int(box[0]) - 2), max(0, int(box[1]) - 2),
              min(size[0], int(box[2]) + 3), min(size[1], int(box[3]) + 3))
        m = masks[k].crop(ib) if k == 0 or a >= 1 else Image.blend(masks[k - 1].crop(ib), masks[k].crop(ib), a)
        frame = Image.composite(bright.crop(ib), dim.crop(ib), m)
        rel = (box[0] - ib[0], box[1] - ib[1], box[2] - ib[0], box[3] - ib[1])
        ff.stdin.write(frame.resize((OUT_W, OUT_H), Image.BICUBIC, box=rel).tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit(f"ffmpeg failed writing {out}")
