r"""eval_memory.py - how many Hafnia requests would the verdict memory (tier0/memory.py) save, and what would it miss?

    .venv\Scripts\python.exe scripts\eval_memory.py [--persist 1.5] [--only NAME ...] [--out run\memory-<UTC>]

Replays each clip of scripts\eval_change.py through the change detector, cuts a BEFORE crop (1 s before the change
started) and an AFTER crop (when it was reported) for every change, and embeds them with SigLIP 2. Hafnia is stood in
for by the ground truth (an *oracle*): a change inside the clip's incident span is an incident, any other is nothing.
The memory is then replayed in time order per camera, for several similarity thresholds: a change it skips saves a
request; a skipped incident is a miss. Also scores every AFTER crop against short descriptions (zero-shot).
Costs no Hafnia requests. Crops go to frames\ (git-ignored: footage).

Caveat: looped clips repeat exactly, which flatters any memory; the real clips (test_11, Mumbai, Duesseldorf) do not.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from eval_change import CASES, frames, person_finder  # noqa: E402
from tier0.change import ChangeDetector, ChangeParams  # noqa: E402
from tier0.memory import Embedder, Entry, VerdictMemory, crop  # noqa: E402

PROMPTS = [
    "a vehicle broken down in a traffic lane with smoke",
    "a crashed car stopped against a barrier",
    "a car or bus stopped in traffic",
    "a bus at a bus stop",
    "a parked car",
    "a wheelie bin lying on its side on a pavement",
    "an e-scooter lying on a pavement",
    "a person on railway tracks",
    "graffiti sprayed on a train",
    "a person crouching at a gate at night",
    "a person standing on a pavement",
    "an empty street",
]


def collect(name: str, loops: int, params: ChangeParams, people, crop_dir: Path) -> list[dict]:
    """The detector's changes on one clip, with crops and the oracle's verdict."""
    path, annexb, loop_s, state, role = CASES[name]
    n_loops = 1 if loop_s > 60 else loops
    det = ChangeDetector(params)
    buf: deque[tuple[float, np.ndarray]] = deque(maxlen=int(10 * (params.persist_s + 8)))
    rows, t, starts = [], 0.0, []
    crop_dir.mkdir(parents=True, exist_ok=True)
    for _ in range(n_loops):
        starts.append(t)
        for f in frames(path, annexb):
            buf.append((t, f))
            for c in det.update(t, f, people(f)):
                before = min(buf, key=lambda x: abs(x[0] - (c.t_start - 1.0)))[1]
                k = max(i for i, s in enumerate(starts) if s <= c.t_detect + 1e-6)
                in_loop = c.t_detect - starts[k]
                scored = n_loops == 1 or starts[k] >= params.warmup_s
                incident = bool(state and state[0] <= in_loop <= state[1] + 0.3)
                i = len(rows)
                a, b = crop(f, c.box), crop(before, c.box)
                cv2.imwrite(str(crop_dir / f"{i:03d}_after.jpg"), a)
                cv2.imwrite(str(crop_dir / f"{i:03d}_before.jpg"), b)
                rows.append({"case": name, "i": i, "t": round(c.t_detect, 1), "loop": k, "in_loop": round(in_loop, 1),
                             "box": c.box, "incident": incident, "scored": scored, "after": a, "before": b})
            t += 0.1
    return rows


def simulate(rows: list[dict], embs: np.ndarray, tau: float) -> dict:
    """Replay the memory in time order (each camera has its own entries); the oracle answers every request."""
    mem = VerdictMemory(reject_sim=tau)
    asked = skipped = missed = 0
    for r, e in zip(rows, embs):
        decision, _, _ = mem.decide(r["case"], tuple(r["box"]), e)
        if decision == "skip":
            skipped += r["scored"]
            missed += r["scored"] and r["incident"]
            continue
        asked += r["scored"]
        mem.add(Entry(r["case"], tuple(r["box"]), e, r["incident"], t=r["t"]))
    return {"asked": asked, "skipped": skipped, "missed_incidents": missed}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--loops", type=int, default=7)
    ap.add_argument("--persist", type=float, default=1.5)
    ap.add_argument("--only", nargs="+", choices=list(CASES))
    ap.add_argument("--taus", type=float, nargs="+", default=[0.75, 0.80, 0.85, 0.90, 0.95])
    ap.add_argument("--out", type=Path, default=REPO / "run" / f"memory-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}")
    args = ap.parse_args()
    from ultralytics import YOLO
    people = person_finder(YOLO(str(REPO / "models" / "yolo11m.pt")))
    params = ChangeParams(persist_s=args.persist)
    emb = Embedder()
    text = emb.texts(PROMPTS)

    rows = []
    for name in args.only or CASES:
        if CASES[name][0].exists():
            got = collect(name, args.loops, params, people, args.out / "frames" / name)
            print(f"{name:42} {len(got):4} changes ({sum(r['incident'] for r in got)} in the incident span)", flush=True)
            rows += got
    embs = np.concatenate([emb.images([r["after"] for r in rows[i:i + 32]]) for i in range(0, len(rows), 32)])
    zs = emb.zero_shot(embs, text)

    per_case = {}
    for name in dict.fromkeys(r["case"] for r in rows):
        idx = [i for i, r in enumerate(rows) if r["case"] == name]
        sub, sub_e = [rows[i] for i in idx], embs[idx]
        total = sum(r["scored"] for r in sub)
        inc = sum(r["scored"] and r["incident"] for r in sub)
        sims = {str(tau): simulate(sub, sub_e, tau) for tau in args.taus}
        tops = [PROMPTS[int(np.argmax(zs[i]))] for i in idx if rows[i]["incident"]]
        per_case[name] = {"changes": total, "incidents": inc, "memory": sims,
                          "zero_shot_top_for_incidents": {p: tops.count(p) for p in dict.fromkeys(tops)}}
    totals = {str(tau): {k: sum(c["memory"][str(tau)][k] for c in per_case.values())
                         for k in ("asked", "skipped", "missed_incidents")} for tau in args.taus}
    print(f"\n{'case':42} {'changes':>7} {'incid.':>6}  asked/missed at tau " + " ".join(f"{t:>9}" for t in args.taus))
    for name, c in per_case.items():
        cells = " ".join(f"{c['memory'][str(t)]['asked']:>5}/{c['memory'][str(t)]['missed_incidents']:<3}" for t in args.taus)
        print(f"{name:42} {c['changes']:7} {c['incidents']:6}  {cells}")
    cells = " ".join(f"{totals[str(t)]['asked']:>5}/{totals[str(t)]['missed_incidents']:<3}" for t in args.taus)
    print(f"{'TOTAL':42} {sum(c['changes'] for c in per_case.values()):7} "
          f"{sum(c['incidents'] for c in per_case.values()):6}  {cells}")
    for name, c in per_case.items():
        if c["zero_shot_top_for_incidents"]:
            print(f"zero-shot top description for {name}'s incidents: {c['zero_shot_top_for_incidents']}")
    (args.out / "results.json").write_text(json.dumps({"persist_s": args.persist, "prompts": PROMPTS, "totals": totals,
                                                       "cases": per_case}, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
