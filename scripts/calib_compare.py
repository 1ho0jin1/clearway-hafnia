r"""calib_compare.py - the calibrated-floor test, scored (2026-10-29): what a floor set in square metres (from a
scale per camera and row, scripts/scale_fit.py) does against the floor set as a share of the frame.

    .venv\Scripts\python.exe scripts\calib_compare.py run\calib-20261029

Reads, under that folder: scales.json; eval-<label>/results.json from scripts/eval_change.py (the staged loops:
incidents caught, false reports); holdout-<label>/ from scripts/holdout.py (the three CC0 street clips: candidates,
clips played, answers), with run/holdout-20261029 as the baseline whose answers a candidate at the same spot and
time inherits; the clean live run of 10-27 for the true cards' sizes. Writes README.md below the marker (the text
above it is kept) and summary.json. Costs no request.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import scale_fit  # noqa: E402

BASELINE = REPO / "run" / "holdout-20261029"
LIVE = REPO / "run" / "clearway-live-20261027T124112Z-clean"
MARK = "<!-- tables: written by calib_compare.py; the text above is kept -->"
WORK_H = 369          # the 640-px work frame's height for the 832x468 bridge frames (boxes of the hold-out and the service)


def jl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []


def dist(xs: list[float]) -> str:
    xs = sorted(xs)
    return f"{len(xs)}: {xs[0]} to {xs[-1]}, median {round(st.median(xs), 2)}" if xs else "0"


def answers_of(run: Path) -> dict[str, dict]:
    out = {}
    for r in jl(run / "results.jsonl"):           # the last answer per candidate wins
        out[r["cid"]] = r
    return out


def card(r: dict | None) -> str:
    """'false' (a card for a hard negative), 'none', 'failed' or '-' (not asked)."""
    if r is None:
        return "-"
    if r.get("progress") != "Completed":
        return "failed"
    return "none" if r["category"] == "NONE" else "false"


def main() -> int:
    out = Path(sys.argv[1])
    scales = scale_fit.load(out / "scales.json")
    lines = [MARK, ""]
    summary: dict = {}

    # --- A. the scales
    lines += ["## The scale per camera", "",
              "Pixels per metre in the 832-pixel frame, from the people (1.7 m) and cars (box 1.5 m high) YOLO11m found, "
              "fitted against the row the box stands on; clamped to 0.3 to 3 times the camera's median.", "",
              "| Camera | Boxes used | At 1/4 height | At 1/2 | At 3/4 | At the bottom |", "|---|---|---|---|---|---|"]
    for name, s in scales.items():
        at = s.get("ppm_at", {})
        lines.append(f"| {name} | {s['n_used']} of {s['n']} | {at.get('0.25', '-')} | {at.get('0.5', '-')} | "
                     f"{at.get('0.75', '-')} | {at.get('1.0', '-')} |")

    # --- B. sizes: the true cards of the clean live run, the hold-out's false cards
    inc = {i["id"]: i for i in json.loads((LIVE / "incidents.json").read_text(encoding="utf-8"))}
    true_m2 = []
    for ch in jl(LIVE / "service.jsonl"):
        if ch.get("kind") == "change" and ch.get("action") == "ask" and ch.get("incident") in inc:
            i = inc[ch["incident"]]
            if i.get("category") and i["state"] != "dismissed":
                m2 = scale_fit.world_m2(scales[ch["camera"]], ch["box"][3] / WORK_H, ch["area"])
                true_m2.append((ch["camera"], i["category"], i["state"], round(m2, 2)))
    base_ans = answers_of(BASELINE)
    base_c = jl(BASELINE / "candidates.jsonl")
    for c in base_c:
        c["world_m2"] = round(scale_fit.world_m2(scales[c["clip"]], c["box"][3] / WORK_H, c["area"]), 2)
    false_m2 = [c["world_m2"] for c in base_c if card(base_ans.get(c["cid"])) == "false"]
    none_m2 = [c["world_m2"] for c in base_c if card(base_ans.get(c["cid"])) == "none"]
    lines += ["", "## What the detector's blobs measure in square metres", "",
              "A blob is the pixels that stayed changed, usually a part of the object, so these are smaller than the "
              "objects. The true cards of the clean live run of 10-27 (the change asked about, at its row):", "",
              "| Camera | Card | State | m² |", "|---|---|---|---|"]
    for cam, cat, state, m2 in sorted(true_m2, key=lambda r: r[3]):
        lines.append(f"| {cam} | {cat} | {state} | {m2} |")
    lines += ["", f"The hold-out's false cards (hard negatives Hafnia confirmed): {dist(false_m2)} m². "
                  f"Its NONE answers: {dist(none_m2)} m². The cracked pane on the vandalism camera: 0.04 m² at the man's "
                  f"scale beside it (0.10 m² by the row fit, which assumes the ground plane)."]
    summary["true_cards_m2"] = true_m2
    summary["holdout_false_m2"], summary["holdout_none_m2"] = sorted(false_m2), sorted(none_m2)

    # --- C/D. the hold-out variants
    base_det = json.loads((BASELINE / "detect.json").read_text(encoding="utf-8"))
    base_rate = {(s["clip"], s["profile"]): s for s in base_det["clips"]}
    n_base_false = len(false_m2)
    n_base_answered = sum(1 for c in base_c if card(base_ans.get(c["cid"])) in ("false", "none"))
    summary["baseline"] = {"candidates": len(base_c), "answered": n_base_answered, "false_cards": n_base_false}
    for run in sorted(out.glob("holdout-*")):
        label = run.name[len("holdout-"):]
        det = json.loads((run / "detect.json").read_text(encoding="utf-8"))
        cands = jl(run / "candidates.jsonl")
        ans = answers_of(run)
        lines += ["", f"## The three streets with the calibrated floor: {label}", "",
                  f"Floor {det.get('world_floor_m2')} m² at the blob's row, never below {det.get('at_least')} of the frame. "
                  f"A candidate at the same spot and time as a baseline candidate inherits that answer; the new ones "
                  f"were played on `lens_1` and asked with the service's prompt.", "",
                  "| Clip | Setting | Baseline per hour | Calibrated per hour | Same as baseline | New | New asked | "
                  "New answered | New false cards | Inherited false cards | Inherited NONE |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        tot = {"cands": 0, "same": 0, "new": 0, "asked": 0, "answered": 0, "false_new": 0, "false_inh": 0, "none_inh": 0,
               "none_new": 0}
        per_set: dict[str, dict] = {}
        for s in det["clips"]:
            key = (s["clip"], s["profile"])
            rows = [c for c in cands if (c["clip"], c["profile"]) == key]
            same = [c for c in rows if c.get("same_as")]
            new = [c for c in rows if not c.get("same_as")]
            asked = [c for c in new if c["cid"] in ans]
            answered = [c for c in asked if ans[c["cid"]].get("progress") == "Completed"]
            false_new = [c for c in answered if ans[c["cid"]]["category"] != "NONE"]
            inh = [card(base_ans.get(c["same_as"])) for c in same]
            b = base_rate.get(key, {})
            lines.append(f"| {s['clip']} | {s['profile']} | {b.get('per_hour', '-')} ({b.get('reports', '-')}) | "
                         f"{s['per_hour']} ({s['reports']}) | {len(same)} | {len(new)} | {len(asked)} | {len(answered)} | "
                         f"{len(false_new)} | {inh.count('false')} | {inh.count('none')} |")
            ps = per_set.setdefault(s["profile"], {"cands": 0, "new": 0, "same": 0, "seconds": 0.0, "asked": 0,
                                                   "answered": 0, "false": 0, "inh_answered": 0, "inh_false": 0,
                                                   "b_cands": 0, "b_seconds": 0.0})
            ps["cands"] += s["reports"]
            ps["new"] += len(new)
            ps["same"] += len(same)
            ps["seconds"] += s["seconds"]
            ps["asked"] += len(asked)
            ps["answered"] += len(answered)
            ps["false"] += len(false_new)
            ps["inh_answered"] += inh.count("false") + inh.count("none")
            ps["inh_false"] += inh.count("false")
            ps["b_cands"] += b.get("reports", 0)
            ps["b_seconds"] += b.get("seconds", 0.0)
            for k, v in (("cands", len(rows)), ("same", len(same)), ("new", len(new)), ("asked", len(asked)),
                         ("answered", len(answered)), ("false_new", len(false_new)), ("false_inh", inh.count("false")),
                         ("none_inh", inh.count("none")), ("none_new", len(answered) - len(false_new))):
                tot[k] += v
        lines += ["", "False cards per hour, estimated: the new candidates' rate times the share of false cards among the "
                      "new ones answered, plus the rate of those at a baseline spot times the share among their inherited "
                      "answers (the baseline: its rate times its own share).", "",
                  "| Setting | Baseline candidates per hour | Baseline false cards per hour | Calibrated candidates per hour | "
                  "Calibrated false cards per hour | Behind it |", "|---|---|---|---|---|---|"]
        for prof, ps in per_set.items():
            b_rate = ps["b_cands"] / ps["b_seconds"] * 3600 if ps["b_seconds"] else 0.0
            b_cards = [card(base_ans.get(c["cid"])) for c in base_c if c["profile"] == prof]
            b_n = b_cards.count("false") + b_cards.count("none")
            b_share = b_cards.count("false") / b_n if b_n else 0.0
            hour = 3600 / ps["seconds"] if ps["seconds"] else 0.0
            new_share = ps["false"] / ps["answered"] if ps["answered"] else 0.0
            inh_share = ps["inh_false"] / ps["inh_answered"] if ps["inh_answered"] else 0.0
            est = ps["new"] * hour * new_share + ps["same"] * hour * inh_share
            ps["false_per_hour"], ps["baseline_false_per_hour"] = round(est, 1), round(b_rate * b_share, 1)
            lines.append(f"| {prof} | {b_rate:.1f} | {b_rate * b_share:.1f} ({b_cards.count('false')} of {b_n} answered) | "
                         f"{ps['cands'] * hour:.1f} | {est:.1f} | new {ps['new'] * hour:.0f}/h at {new_share:.0%} "
                         f"({ps['false']} of {ps['answered']}), same spot {ps['same'] * hour:.0f}/h at {inh_share:.0%} "
                         f"({ps['inh_false']} of {ps['inh_answered']}) |")
        # the new candidates' world sizes and answers
        new_rows = [c for c in cands if not c.get("same_as")]
        lines += ["", f"New candidates: {len(new_rows)}, sizes {dist([c['world_m2'] for c in new_rows if c.get('world_m2') is not None])} m²; "
                      f"asked {tot['asked']}, answered {tot['answered']}, false cards {tot['false_new']}.", ""]
        if tot["asked"]:
            lines += ["| Candidate | Setting | View | m² | Answer | Hafnia says |", "|---|---|---|---|---|---|"]
            for c in new_rows:
                r = ans.get(c["cid"])
                if not r:
                    continue
                said = str(r.get("fields", {}).get("summary") or r.get("error") or "")[:140].replace("|", "/")
                lines.append(f"| {c['cid']} | {c['profile']} | {c['view']} x{c['magnification']} | {c.get('world_m2')} | "
                             f"{r['category'] if r.get('progress') == 'Completed' else 'failed'} | {said} |")
        summary[f"holdout-{label}"] = {"totals": tot, "per_setting": per_set, "world_floor_m2": det.get("world_floor_m2"),
                                       "at_least": det.get("at_least")}

    # --- E. the loops
    evals = {p.name[len("eval-"):]: json.loads((p / "results.json").read_text(encoding="utf-8"))
             for p in sorted(out.glob("eval-*")) if (p / "results.json").exists()}
    if evals:
        labels = list(evals)
        lines += ["", "## The staged loops: incidents caught and false reports", "",
                  "| Camera | " + " | ".join(f"{lb}: caught, delay s, false/h" for lb in labels) + " |",
                  "|---|" + "---|" * len(labels)]
        cases = [c["case"] for c in evals[labels[0]]["cases"]]
        for case in cases:
            cells = []
            for lb in labels:
                r = next((c for c in evals[lb]["cases"] if c["case"] == case), None)
                if r is None:
                    cells.append("-")
                    continue
                caught = "-" if r["loops_caught"] is None else f"{r['loops_caught']}/{r['loops']}"
                delay = ",".join(str(d) for d in (r["first_delay_s"] or [])[:3]) or "-"
                cells.append(f"{caught}, {delay}, {r['false_per_hour']}")
            lines.append(f"| {case} | " + " | ".join(cells) + " |")
        summary["loops"] = {lb: {c["case"]: {"caught": c["loops_caught"], "loops": c["loops"], "false_per_hour": c["false_per_hour"]}
                                 for c in ev["cases"]} for lb, ev in evals.items()}

    readme = out / "README.md"
    head = ""
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        head = text.split(MARK)[0] if MARK in text else text + "\n"
    readme.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {readme}, summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
