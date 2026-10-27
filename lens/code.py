"""The frame code: a row of black and white blocks the publisher burns into every lens frame, so that any frame read
back from lens_1 (live through FrameBridge, or exported from the recording) says which clip and frame it is and the
publisher's wall time when it was sent. lens/clock.py compares that with the time XProtect gave the frame: the
recording's time base ran 0.3-9.5 s behind the publisher under load (run/lens-check-20261027), so a span computed
from the publisher's clock alone asked about the wrong footage.

    stamp(frame, seq=17, idx=42, when=utc_now())      # in place, the bottom BAND of the frame
    code = read(frame)                                # {"seq": 17, "idx": 42, "cs": ..., "wall": datetime} or None

Layout: the bottom 16/720 of the frame, BLOCKS equal blocks across its full width; white is 1, black is 0. 64 bits:
8 sync bits (SYNC), 48 payload bits (seq 14: the publisher's job number, 0 for the idle frame; idx 10: the frame's
index in the job, modulo 1024; cs 24: centiseconds since 00:00 UTC) and a CRC-8 of the payload. Each block is
sampled at its centre, so the code survives the stream's H.264, XProtect's JPEG transcoding and scaling to any width
(a 640-px frame leaves 10 x 8 px per block).
"""
from __future__ import annotations

import datetime as dt

import cv2
import numpy as np

BAND = 16 / 720      # the band's height as a share of the frame's
BLOCKS = 64
SYNC = 0b10110010    # fixed first byte: a frame without the band never decodes
SEQ_BITS, IDX_BITS, CS_BITS = 14, 10, 24
SEQ_MOD, IDX_MOD = 1 << SEQ_BITS, 1 << IDX_BITS
CONTRAST = 60        # least difference (grey levels) between the darkest and lightest block of a readable band


def crc8(data: bytes) -> int:
    """CRC-8, polynomial 0x07, no initial value: one byte that catches any single bit error in the payload."""
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def cs_of_day(when: dt.datetime) -> int:
    """Centiseconds since 00:00 UTC."""
    when = when.astimezone(dt.timezone.utc)
    return (when.hour * 3600 + when.minute * 60 + when.second) * 100 + when.microsecond // 10000


def resolve(cs: int, near: dt.datetime) -> dt.datetime:
    """The UTC time with these centiseconds of day closest to near (the frame was sent within hours of being read)."""
    near = near.astimezone(dt.timezone.utc)
    day = near.replace(hour=0, minute=0, second=0, microsecond=0)
    t = day + dt.timedelta(milliseconds=cs * 10)
    if (t - near).total_seconds() > 43200:
        t -= dt.timedelta(days=1)
    elif (near - t).total_seconds() > 43200:
        t += dt.timedelta(days=1)
    return t


def bits_of(seq: int, idx: int, cs: int) -> list[int]:
    payload = ((seq % SEQ_MOD) << (IDX_BITS + CS_BITS)) | ((idx % IDX_MOD) << CS_BITS) | (cs & ((1 << CS_BITS) - 1))
    word = (SYNC << 56) | (payload << 8) | crc8(payload.to_bytes(6, "big"))
    return [(word >> (63 - i)) & 1 for i in range(64)]


def band_rows(h: int) -> tuple[int, int]:
    """The band's first row and the row after its last, for a frame h pixels high."""
    bh = max(2, round(h * BAND))
    return h - bh, h


def stamp(frame: np.ndarray, seq: int, idx: int, when: dt.datetime) -> np.ndarray:
    """Draw the code into the frame's bottom band, in place; returns the frame."""
    h, w = frame.shape[:2]
    y0, y1 = band_rows(h)
    row = np.zeros(w, np.uint8)
    for i, bit in enumerate(bits_of(seq, idx, cs_of_day(when))):
        if bit:
            row[round(i * w / BLOCKS):round((i + 1) * w / BLOCKS)] = 255
    frame[y0:y1] = row[None, :, None] if frame.ndim == 3 else row[None, :]
    return frame


def read(frame: np.ndarray, near: dt.datetime | None = None) -> dict | None:
    """The code in a frame (any size, the stream's aspect ratio), or None when there is none or it is damaged:
    {"seq", "idx", "cs", "wall": the frame's send time as a UTC datetime, resolved against near (default now)}."""
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    h, w = grey.shape[:2]
    y0, y1 = band_rows(h)
    bh = y1 - y0
    r0, r1 = y0 + bh // 4, max(y0 + bh // 4 + 1, y1 - bh // 4)
    bw = w / BLOCKS
    means = np.empty(BLOCKS)
    for i in range(BLOCKS):
        c0 = round(i * bw + bw * 0.3)
        c1 = max(c0 + 1, round(i * bw + bw * 0.7))
        means[i] = grey[r0:r1, c0:c1].mean()
    lo, hi = means.min(), means.max()
    if hi - lo < CONTRAST:
        return None
    bits = (means > (lo + hi) / 2).astype(int)
    word = 0
    for b in bits:
        word = (word << 1) | int(b)
    if word >> 56 != SYNC:
        return None
    payload = (word >> 8) & ((1 << 48) - 1)
    if crc8(payload.to_bytes(6, "big")) != word & 0xFF:
        return None
    cs = payload & ((1 << CS_BITS) - 1)
    return {"seq": payload >> (IDX_BITS + CS_BITS), "idx": (payload >> CS_BITS) % IDX_MOD, "cs": cs,
            "wall": resolve(cs, near or dt.datetime.now(dt.timezone.utc))}
