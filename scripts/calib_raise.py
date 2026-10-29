r"""calib_raise.py - the calibrated floor in its "raise only" form, scored without a run (2026-10-29): if a blob also
had to cover at least X square metres at its row, which of the baseline's candidates would be gone?

    .venv\Scripts\python.exe scripts\calib_raise.py run\calib-20261029 [--floors 0.1 0.25 0.5 1 2]

Exact for this direction: the frame-share floor stays, so the calibrated detector raises a subset of the baseline's
candidates (the detector's state can differ a little once a blob is dropped, which this ignores). Reads scales.json,
eval-baseline/results.json (the staged loops: a loop stays caught if any report inside the incident window
survives) and run/holdout-20261029 (the hard negatives and Hafnia's answers). Prints and writes raise.md and
raise.json under the folder. Costs no request.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import scale_fit  # noqa: E402
from calib_compare import BASELINE, WORK_H, answers_of, card, jl  # noqa: E402
from eval_change import CASES  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--floors", type=float, nargs="+", default=[0.1, 0.25, 0.5, 1.0, 2.0])
    args = ap.parse_args()
    scales = scale_fit.load(args.out / "scales.json")
    ev = json.loads((args.out / "eval-baseline" / "results.json").read_text(encoding="utf-8"))

    # the loops: per case, per loop, the sizes of the reports inside the incident window
    loops: dict[str, dict[int, list[float]]] = {}
    false_m2: dict[str, list[float]] = {}
    for c in ev["cases"]:
        path, annexb, loop_s, state, role = CASES[c["case"]]
        sc = scales[c["case"]]
        per_loop: dict[int, list[float]] = {}
        falses: list[float] = []
        for r in c["reports"]:
            k = int(r["t_detect"] // loop_s) if loop_s <= 60 else 0
            if loop_s <= 60 and k * loop_s < ev["params"]["warmup_s"]:
                continue                        # the loop the warm-up ended in is not scored (eval_change.py)
            in_loop = r["t_detect"] - k * loop_s if loop_s <= 60 else r["t_detect"]
            m2 = scale_fit.world_m2(sc, r["box"][3] / WORK_H, r["area"])
            if state and state[0] <= in_loop <= state[1] + 0.3:
                per_loop.setdefault(k, []).append(m2)
            else:
                falses.append(m2)
        loops[c["case"]] = per_loop
        false_m2[c["case"]] = falses

    # the streets: the baseline's candidates with their answers
    base_ans = answers_of(BASELINE)
    cands = jl(BASELINE / "candidates.jsonl")
    for c in cands:
        c["m2"] = scale_fit.world_m2(scales[c["clip"]], c["box"][3] / WORK_H, c["area"])
        c["card"] = card(base_ans.get(c["cid"]))

    lines = ["| Floor, m² | Loops still caught (of the baseline's) | Loop false reports left | Hard negatives left (of 74) | "
             "False cards left (of 31) | NONE answers left (of 8) |", "|---|---|---|---|---|---|"]
    rows = []
    for fl in args.floors:
        caught = []
        for c in ev["cases"]:
            if CASES[c["case"]][3] is None:
                continue
            base = c["loops_caught"]
            kept = sum(1 for k, ms in loops[c["case"]].items() if any(m >= fl for m in ms))
            caught.append((c["case"].split("_")[0], kept, base))
        lf = sum(sum(1 for m in ms if m >= fl) for ms in false_m2.values())
        lf_all = sum(len(ms) for ms in false_m2.values())
        left = [c for c in cands if c["m2"] >= fl]
        fc = sum(1 for c in left if c["card"] == "false")
        nn = sum(1 for c in left if c["card"] == "none")
        rows.append({"floor_m2": fl, "caught": caught, "loop_false_left": lf, "loop_false_all": lf_all,
                     "candidates_left": len(left), "false_cards_left": fc, "none_left": nn})
        lines.append(f"| {fl} | " + ", ".join(f"{n} {k}/{b}" for n, k, b in caught) + f" | {lf} of {lf_all} | "
                     f"{len(left)} | {fc} | {nn} |")
    text = "\n".join(lines)
    print(text)
    (args.out / "raise.md").write_text(text + "\n", encoding="utf-8")
    (args.out / "raise.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
