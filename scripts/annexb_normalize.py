"""annexb_normalize.py - rewrite an H.264 Annex B file into the layout the StableFPS driver accepts.

The organizer clips have SPS and PPS once at the start, no SEI, and a 4-byte start code (00 00 00 01) before every NAL
unit. ffmpeg's usual output repeats SPS/PPS before every keyframe, adds an x264 SEI and uses some 3-byte start codes;
the Recording Server then logs "Unable to add one or more frames to the frame collector. Error code = 5" and the camera
shows nothing. This keeps the first SPS and PPS, drops SEI and later SPS/PPS, and writes every NAL with a 4-byte code.

    py scripts\annexb_normalize.py <in> <out>
"""
from __future__ import annotations

import re
import sys

SEI, SPS, PPS = 6, 7, 8
START = b"\x00\x00\x00\x01"


def nal_units(data: bytes) -> list[bytes]:
    """Split on 3-byte start codes; 00 00 01 never occurs inside a NAL (emulation prevention). The extra zero of a
    4-byte code, and any trailing_zero_8bits, sit at the end of the previous unit and are stripped."""
    starts = [m.end() for m in re.finditer(b"\x00\x00\x01", data)]
    units = []
    for i, s in enumerate(starts):
        end = starts[i + 1] - 3 if i + 1 < len(starts) else len(data)
        unit = data[s:end].rstrip(b"\x00")
        if unit:
            units.append(unit)
    return units


def normalize(data: bytes) -> bytes:
    out, seen = [], set()
    for unit in nal_units(data):
        kind = unit[0] & 0x1F
        if kind == SEI:
            continue
        if kind in (SPS, PPS):
            if kind in seen:
                continue
            seen.add(kind)
        out.append(START + unit)
    if seen != {SPS, PPS}:
        raise ValueError("no SPS/PPS found: is this an H.264 Annex B file?")
    return b"".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    data = open(src, "rb").read()
    result = normalize(data)
    open(dst, "wb").write(result)
    print(f"{dst}: {len(data):,} -> {len(result):,} bytes")
