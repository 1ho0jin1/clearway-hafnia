r"""scale_fit.py - a scale per camera and row, in pixels per metre, from the people and cars YOLO sees (offline; no
Hafnia requests). The test of the calibrated floor, 2026-10-29: does a floor set in square metres instead of a share
of the frame change what the detector raises?

    .venv\Scripts\python.exe scripts\scale_fit.py fit DETS.json OUT.json      # scales.json from collected boxes
    .venv\Scripts\python.exe scripts\scale_fit.py show OUT.json               # the scales, per camera

A person is taken as PERSON_M tall and a car's box as CAR_M high. For each camera the pixels per metre each box
implies (its height over its metres) are fitted against the row its bottom edge sits on, as a share of the frame
height: a straight line, the standard single-view assumption of a flat ground plane (near the bottom of the frame a
metre is more pixels than near the horizon). The fit is robust (points beyond three median deviations are dropped
twice), and the line is clamped to between 0.3 and 3 times the camera's median so the floor cannot vanish at the
horizon. Cameras with fewer than MIN_POINTS usable boxes get a constant: their median.

Helpers for the detector scripts: `load`, `ppm`, `floor_share`, `world_m2`. Shares are resolution-free: a caller
passes the bottom row and the blob's area as shares of its own frame and gets a share back; the metres come out in
the 832-pixel frame the boxes were measured in.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

PERSON_M, CAR_M = 1.7, 1.5
METRES = {"person": PERSON_M, "car": CAR_M}
MIN_POINTS = 8
CLAMP = (0.3, 3.0)


def fit_camera(dets: list[list], H: int) -> dict:
    pts = [((d[5]) / H, (d[5] - d[3]) / METRES[d[1]]) for d in dets if d[1] in METRES and d[5] > d[3]]
    n = len(pts)
    if n == 0:
        return {"n": 0, "n_used": 0, "a": 0.0, "b": None, "median": None}
    med = st.median(p[1] for p in pts)
    if n < MIN_POINTS:
        return {"n": n, "n_used": n, "a": 0.0, "b": med, "median": med}
    import numpy as np
    x = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    keep = np.ones(n, bool)
    a = b = 0.0
    for _ in range(3):
        a, b = np.polyfit(x[keep], y[keep], 1)
        res = y - (a * x + b)
        mad = float(np.median(np.abs(res[keep] - np.median(res[keep]))))
        nxt = np.abs(res) <= max(3 * 1.4826 * mad, 0.05 * med)   # never tighter than 5 % of the median
        if nxt.sum() < MIN_POINTS:
            break
        keep = nxt
    if keep.sum() < MIN_POINTS or a < 0:          # a scale that shrinks towards the bottom is not a ground plane
        return {"n": n, "n_used": int(keep.sum()), "a": 0.0, "b": med, "median": med, "note": "constant: fit rejected"}
    return {"n": n, "n_used": int(keep.sum()), "a": float(a), "b": float(b), "median": float(med),
            "spread": float(np.std(res[keep]) / med)}


def ppm(scale: dict, foot_share: float) -> float:
    """Pixels per metre (in the 832-px frame) at a row given as a share of the frame height (1.0 = bottom)."""
    med = scale["median"]
    v = scale["a"] * foot_share + scale["b"]
    return float(min(CLAMP[1] * med, max(CLAMP[0] * med, v)))


def floor_share(scale: dict, foot_share: float, world_m2: float) -> float:
    """The blob area (share of the frame) that `world_m2` square metres cover at that row."""
    W, H = scale["frame"]
    return world_m2 * ppm(scale, foot_share) ** 2 / (W * H)


def world_m2(scale: dict, foot_share: float, area_share: float) -> float:
    """Square metres a blob of `area_share` of the frame covers at that row."""
    W, H = scale["frame"]
    return area_share * W * H / ppm(scale, foot_share) ** 2


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fit(dets_path: Path, out: Path) -> dict:
    raw = json.loads(Path(dets_path).read_text(encoding="utf-8"))
    scales = {}
    for name, d in raw.items():
        W, H = d["frame"]
        s = fit_camera(d["dets"], H)
        s["frame"] = [W, H]
        s["role"] = d["role"]
        if s["median"]:
            s["ppm_at"] = {str(r): round(ppm(s, r), 1) for r in (0.25, 0.5, 0.75, 1.0)}
        scales[name] = s
    out.write_text(json.dumps(scales, indent=1), encoding="utf-8")
    return scales


def show(scales: dict) -> None:
    print(f"{'camera':42} {'role':8} {'boxes':>5} {'used':>5} {'median':>7} {'at 1/4':>7} {'at 1/2':>7} {'at 3/4':>7} {'bottom':>7} spread")
    for name, s in scales.items():
        at = s.get("ppm_at", {})
        print(f"{name:42} {s['role']:8} {s['n']:5} {s['n_used']:5} {s['median'] and round(s['median'], 1)!s:>7} "
              f"{at.get('0.25', '-')!s:>7} {at.get('0.5', '-')!s:>7} {at.get('0.75', '-')!s:>7} {at.get('1.0', '-')!s:>7} "
              f"{round(s['spread'], 2) if s.get('spread') is not None else s.get('note', '-')}")


def main() -> int:
    if len(sys.argv) >= 4 and sys.argv[1] == "fit":
        show(fit(Path(sys.argv[2]), Path(sys.argv[3])))
        return 0
    if len(sys.argv) == 3 and sys.argv[1] == "show":
        show(load(Path(sys.argv[2])))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
