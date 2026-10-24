r"""viz_walkthrough.py - figures that show each step of plan C's pipeline on real camera frames, for the presentation.

    .venv\Scripts\python.exe scripts\viz_walkthrough.py [--out docs\walkthrough]

No Hafnia requests: answers are read from earlier runs (run/pilot-20261023T162040Z, run/memory-compare). Only footage
we may show is used: the organizers' cameras (on every machine) and Wikimedia Commons CC0 clips; never test_11 (the AI
City licence forbids redistribution). Writes one JPEG per step and facts.json (numbers and answers the page quotes).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from eval_change import CASES, frames, person_finder  # noqa: E402
from lens.client import before_after, caption, crop, zoom  # noqa: E402
from tier0.change import ChangeDetector, ChangeParams  # noqa: E402
from tier0.memory import iou  # noqa: E402

FONT = cv2.FONT_HERSHEY_SIMPLEX
RED, GREEN, YELLOW, WHITE = (40, 40, 230), (60, 180, 60), (0, 210, 255), (255, 255, 255)
PILOT = REPO / "run" / "pilot-20261023T162040Z"
MEMORY = REPO / "run" / "memory-compare"


def label(img: np.ndarray, text: str, color=WHITE) -> np.ndarray:
    out = img.copy()
    h, w = out.shape[:2]
    bar = max(22, h // 12)
    cv2.rectangle(out, (0, 0), (w, bar), (20, 20, 20), -1)
    cv2.putText(out, text, (8, int(bar * 0.72)), FONT, bar / 34, color, max(1, bar // 18), cv2.LINE_AA)
    return out


def fit(img: np.ndarray, w: int) -> np.ndarray:
    return cv2.resize(img, (w, round(img.shape[0] * w / img.shape[1])), interpolation=cv2.INTER_AREA)


def grid(tiles: list[np.ndarray], cols: int, w: int = 400, pad: int = 6) -> np.ndarray:
    tiles = [fit(t, w) for t in tiles]
    h = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(30, 30, 30)) for t in tiles]
    while len(tiles) % cols:
        tiles.append(np.full_like(tiles[0], 30))
    rows = []
    for r in range(len(tiles) // cols):
        row = tiles[r * cols:(r + 1) * cols]
        rows.append(np.hstack([np.pad(t, ((pad, pad), (pad, pad), (0, 0)), constant_values=255) for t in row]))
    return np.vstack(rows)


def box(img: np.ndarray, b, color=RED, text: str = "") -> np.ndarray:
    out = img.copy()
    x1, y1, x2, y2 = (int(v) for v in b)
    cv2.rectangle(out, (x1, y1), (x2, y2), color, 3)
    if text:
        cv2.putText(out, text, (x1 + 4, max(18, y1 - 8)), FONT, 0.7, color, 2, cv2.LINE_AA)
    return out


def tint(img: np.ndarray, mask: np.ndarray, color=RED, alpha: float = 0.55) -> np.ndarray:
    m = cv2.resize(mask.astype(np.uint8), (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
    out = img.copy()
    out[m] = (out[m] * (1 - alpha) + np.array(color) * alpha).astype(np.uint8)
    return out


def clip_frames(name: str, width: int = 832) -> list[np.ndarray]:
    path, annexb, *_ = CASES[name]
    return list(frames(path, annexb, width=width))


class Probe:
    """Runs the change detector over a looped clip and records, at chosen moments, what it sees inside."""

    def __init__(self, name: str, people, loops: int = 3, params: ChangeParams | None = None):
        self.name, self.people, self.loops = name, people, loops
        self.p = params or ChangeParams.loops()
        self.fr = clip_frames(name)
        self.loop_s = len(self.fr) / 10

    def masks(self, det: ChangeDetector, f: np.ndarray):
        small = cv2.resize(f, (self.p.work_width, round(f.shape[0] / (f.shape[1] / self.p.work_width))),
                           interpolation=cv2.INTER_AREA)
        img = cv2.GaussianBlur(small, (5, 5), 0).astype(np.float32)
        fg_slow = np.abs(img - det.slow).max(axis=2) > self.p.diff
        fg_fast = np.abs(img - det.fast).max(axis=2) > self.p.diff
        static = fg_slow & ~fg_fast
        persistent = static & (det.static_time >= self.p.persist_s)
        return fg_slow, persistent, det.slow.clip(0, 255).astype(np.uint8)

    def run(self, moments: list[tuple[int, float]], track_change_at: float | None = None):
        """moments: (loop index, seconds into the loop). Returns snapshots and the detector."""
        det = ChangeDetector(self.p)
        want = {(k, round(t * 10)) for k, t in moments}
        snaps, t = {}, 0.0
        self.closing = []
        for k in range(self.loops):
            for i, f in enumerate(self.fr):
                det.update(t, f, self.people(f))
                if (k, i) in want:
                    fg_slow, persistent, slow = self.masks(det, f)
                    snaps[(k, i / 10)] = {"frame": f, "fg_slow": fg_slow, "persistent": persistent, "slow": slow,
                                          "open": [o.change for o in det.open.values()],
                                          "opens": list(det.open.values())}
                for o in det.open.values():
                    x1, y1, x2, y2 = o.work_box
                    small = cv2.resize(f, (self.p.work_width, round(f.shape[0] / (f.shape[1] / self.p.work_width))),
                                       interpolation=cv2.INTER_AREA)
                    img = cv2.GaussianBlur(small, (5, 5), 0).astype(np.float32)
                    d = float(np.abs(img[y1:y2, x1:x2] - o.before).max(axis=2).mean())
                    self.closing.append((k, i / 10, o.change.id, d))
                t += 0.1
        return snaps, det


def fig_cameras(out: Path) -> dict:
    names = ["vehicle_breakdown_traffic_queue", "bin_pushed_over_onto_sidewalk", "escooter_left_across_sidewalk",
             "person_on_railway_tracks", "graffiti_on_standing_train", "school_gate_break_in_night", "vandalism",
             "traffic_flows_in_the_open_lanes", "busy_street", "city_street_7_condensation_inside_housing",
             "highway_traffic_overcast_weather"]
    at = {"vehicle_breakdown_traffic_queue": 12.0, "bin_pushed_over_onto_sidewalk": 13.0,
          "escooter_left_across_sidewalk": 12.0, "person_on_railway_tracks": 7.0, "graffiti_on_standing_train": 11.0,
          "school_gate_break_in_night": 11.0, "vandalism": 6.0, "city_street_7_condensation_inside_housing": 6.0}
    tiles = []
    for n in names:
        path, annexb, *_ = CASES[n]
        target = round(at.get(n, 3.0) * 10)
        f = next(f for i, f in enumerate(frames(path, annexb, width=832)) if i == target)
        tiles.append(label(f, n))
    lens = sorted(p for p in (REPO / "run" / "lens" / "sr-smoke").glob("*.jpg") if p.name not in ("sheet.jpg",))
    if lens:
        tiles.append(label(cv2.imread(str(lens[-1])), "lens_1 (ours): what Hafnia is shown", YELLOW))
    cv2.imwrite(str(out / "01_cameras.jpg"), grid(tiles, 4, 400), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return {"cameras": names}


def fig_detector(out: Path, people) -> dict:
    pr = Probe("bin_pushed_over_onto_sidewalk", people, loops=3)
    moments = [(1, 7.0), (1, 9.4), (1, 10.6), (1, 14.0)]
    snaps, det = pr.run(moments)
    tiles = []
    titles = {7.0: "7.0 s: a man reaches the bin", 9.4: "9.4 s: he tips it over", 10.6: "10.6 s: reported",
              14.0: "14.0 s: it stays there"}
    main = max((c for c in det.changes if 15 + 9 <= c.t_detect <= 30), key=lambda c: c.area)
    for (k, t) in moments:
        s = snaps[(k, t)]
        f = s["frame"]
        live = f.copy()
        if any(c.id == main.id for c in s["open"]):
            live = box(live, main.box, RED, f"change, reported {main.t_detect - 15:.1f} s")
        tiles += [label(live, titles[t]),
                  label(cv2.resize(s["slow"], (f.shape[1], f.shape[0])), "slow background: how it looked"),
                  label(tint(f, s["fg_slow"], YELLOW), "different from the slow background"),
                  label(tint(f, s["persistent"], RED), "static for 1.5 s and more: a change")]
    cv2.imwrite(str(out / "02_detector_bin.jpg"), grid(tiles, 4, 360), [cv2.IMWRITE_JPEG_QUALITY, 82])
    bin_changes = [c for c in det.changes if 9.0 <= c.t_detect - 15 <= 15]
    return {"bin_reports": [{"t_detect_in_loop": round(c.t_detect - 15, 1), "box": c.box, "area": c.area}
                            for c in bin_changes]}


def fig_people(out: Path, people) -> dict:
    from ultralytics import YOLO
    model = YOLO(str(REPO / "models" / "yolo11m.pt"))
    tiles = []
    for name, at, text in (("person_on_railway_tracks", 7.0, "person on the tracks: held back"),
                           ("school_gate_break_in_night", 11.0, "person at the gate: held back")):
        pr = Probe(name, people, loops=2)
        snaps, _ = pr.run([(1, at)])
        s = snaps[(1, at)]
        f = s["frame"]
        r = model(f, classes=[0], conf=0.3, verbose=False)[0]
        img = tint(f, s["persistent"], RED)
        for b in r.boxes.xyxy.tolist():
            img = box(img, b, GREEN, "person")
        tiles.append(label(img, text))
    cv2.imwrite(str(out / "03_people_held.jpg"), grid(tiles, 2, 560), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return {}


def fig_negatives(out: Path, people) -> dict:
    g1 = {c["case"]: c for c in json.loads((REPO / "run" / "change-G1-loops" / "results.json").read_text())["cases"]}
    tiles, facts = [], {}
    for name, at, text in (("traffic_flows_in_the_open_lanes", 5.0, "roadworks all the time: part of the background"),
                           ("city_street_7_condensation_inside_housing", 6.5, "the view fogs up: mostly ignored"),
                           ("busy_street", 8.0, "a dense crowd: everything moves")):
        pr = Probe(name, people, loops=3)
        k = 2
        snaps, det = pr.run([(k, at)])
        s = snaps[(k, at)]
        f = s["frame"]
        n, secs = g1[name]["false_reports"], g1[name]["seconds"]
        facts[name] = {"false_reports": n, "seconds": secs}
        tiles.append(label(tint(f, s["fg_slow"], YELLOW), text))
        tiles.append(label(tint(f, s["persistent"], RED), f"false reports in G1: {n} in {secs:.0f} s"))
    cv2.imwrite(str(out / "04_negatives.jpg"), grid(tiles, 2, 480), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return {"negatives": facts}


def fig_memory(out: Path) -> dict:
    d = np.load(MEMORY / "embeddings.npz")
    rows, embs = json.loads(str(d["meta"])), d["embs"]

    def replay(case):
        idx = [i for i, r in enumerate(rows) if r["case"] == case]
        mem, events = [], []
        for i in idx:
            r, e = rows[i], embs[i]
            here = [m for m in mem if iou(tuple(r["box"]), m[0]) >= 0.1]
            rej = [m for m in here if not m[2]]
            conf = [m for m in here if m[2]]
            best_rej = max(rej, key=lambda m: float(e @ m[1]), default=None)
            s_rej = float(e @ best_rej[1]) if best_rej else 0.0
            s_conf = max((float(e @ m[1]) for m in conf), default=0.0)
            skip = s_rej >= 0.85 and s_rej > s_conf
            events.append({"row": r, "skip": skip, "sim": s_rej, "match": best_rej[3] if best_rej else None,
                           "spot_rule_skips": bool(rej)})
            if not skip:
                mem.append((tuple(r["box"]), e, r["incident"], r))
        return events

    def crop_img(r):
        return fit(cv2.imread(str(MEMORY / "frames" / r["case"] / f"{r['i']:03d}_after.jpg")), 420)

    tiles, facts = [], {}
    ev = replay("mumbai02")
    sk = [x for x in ev if x["skip"] and x["match"] is not None and x["row"]["scored"]]
    pick = sorted(sk, key=lambda x: abs(x["sim"] - 0.92))[0]
    tiles += [label(crop_img(pick["match"]), f"{pick['match']['t']:.0f} s: asked -> NONE"),
              label(crop_img(pick["row"]), f"{pick['row']['t']:.0f} s: sim {pick['sim']:.2f} -> skipped", YELLOW)]
    facts["mumbai_skip"] = {"asked_t": pick["match"]["t"], "skipped_t": pick["row"]["t"], "sim": round(pick["sim"], 3)}
    ev = replay("escooter_left_across_sidewalk")
    inc = [x for x in ev if x["row"]["incident"] and x["spot_rule_skips"] and not x["skip"] and x["row"]["scored"]]
    if inc:
        x = inc[0]
        rej_here = [y for y in ev if not y["row"]["incident"] and not y["skip"] and y["row"]["t"] < x["row"]["t"]
                    and iou(tuple(y["row"]["box"]), tuple(x["row"]["box"])) >= 0.1]
        if rej_here:
            y = rej_here[-1]
            sim = float(embs[rows.index(x["row"])] @ embs[rows.index(y["row"])])
            tiles += [label(crop_img(y["row"]), f"{y['row']['t']:.0f} s: asked -> NONE"),
                      label(crop_img(x["row"]), f"{x['row']['t']:.0f} s: sim {sim:.2f} -> asked", RED)]
            facts["escooter_asked"] = {"rejected_t": y["row"]["t"], "incident_t": x["row"]["t"], "sim": round(sim, 3)}
    cv2.imwrite(str(out / "05_memory.jpg"), grid(tiles, 2, 420), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return facts


def fig_lens(out: Path) -> dict:
    res = json.loads((PILOT / "results.json").read_text(encoding="utf-8"))
    ev = res["events"]["graffiti_on_standing_train"]
    b = ev["box"]
    fr = clip_frames("graffiti_on_standing_train")
    a, z = round((ev["start_in_loop_s"] - 2) * 10), round((ev["reported_in_loop_s"] + 3) * 10)
    window = fr[a:z]
    picks = [round(i * (len(window) - 1) / 4) for i in range(5)]
    top = [label(box(window[i], b, RED), f"+{(a + i) / 10:.1f} s") for i in picks]
    crops = zoom(window, b)
    bottom = [label(crops[i], "lens_1 shows") for i in picks]
    cv2.imwrite(str(out / "06_lens_graffiti.jpg"), grid(top + bottom, 5, 300), [cv2.IMWRITE_JPEG_QUALITY, 85])
    ans = next(r for r in res["rows"] if r["camera"] == "graffiti_on_standing_train" and r["variant"] == "crop")
    return {"graffiti_window": [round(ev["start_in_loop_s"] - 2, 1), round(ev["reported_in_loop_s"] + 3, 1)],
            "graffiti_box": b, "graffiti_answer": ans["parsed"], "graffiti_answer_raw": ans["answer"],
            "answers_by_camera": {r["camera"]: r["parsed"] for r in res["rows"] if r["variant"] == "crop"}}


def fig_lens_options(out: Path) -> dict:
    from lens.enhance import SuperRes, bicubic
    res = json.loads((PILOT / "results.json").read_text(encoding="utf-8"))
    g = res["events"]["school_gate_break_in_night"]
    f = clip_frames("school_gate_break_in_night")[round(11.5 * 10)]
    c = crop(f, g["box"])
    sr = SuperRes("general")
    tiles = [label(bicubic([c])[0], "crop, bicubic (default)"), label(sr.upscale(c), "crop, Real-ESRGAN: no gain")]
    s = res["events"]["escooter_left_across_sidewalk"]
    fr = clip_frames("escooter_left_across_sidewalk")
    window = fr[round((s["start_in_loop_s"] - 2) * 10):round((s["reported_in_loop_s"] + 3) * 10)]
    ba = before_after(window, s["box"])
    tiles += [label(ba[0], "BEFORE still"), label(ba[-1], "AFTER still: read as \"parked\"")]
    cv2.imwrite(str(out / "07_lens_options.jpg"), grid(tiles, 2, 480), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return {}


def fig_loopcut(out: Path) -> dict:
    res = json.loads((PILOT / "results.json").read_text(encoding="utf-8"))
    rows = {r["variant"]: r for r in res["rows"] if r["camera"] == "school_gate_break_in_night"}
    fr = clip_frames("school_gate_break_in_night")
    loop = len(fr)
    seq = [(t, fr[round(t * 10) % loop]) for t in (5.0, 8.0, 11.0, 13.5, 14.8, 15.3, 16.5, 18.0)]
    tiles = [label(f, f"{t % 15:.1f} s" + ("  LOOP RESTARTS" if 15.0 <= t < 15.5 else ""),
                   YELLOW if 15.0 <= t < 15.5 else WHITE) for t, f in seq]
    cv2.imwrite(str(out / "08_loopcut_gate.jpg"), grid(tiles, 4, 330), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return {"gate_full_loop": rows["full_loop"]["parsed"], "gate_centred": rows["centred"]["parsed"]}


def fig_close(out: Path, people) -> dict:
    pr = Probe("bin_pushed_over_onto_sidewalk", people, loops=3)
    moments = [(1, 10.6), (1, 14.0), (2, 0.5), (2, 1.5)]
    snaps, det = pr.run(moments)
    s0 = snaps[(1, 10.6)]
    main = max(s0["opens"], key=lambda o: o.change.area)
    cid = main.change.id
    x1, y1, x2, y2 = main.change.box
    scale = 832 / pr.p.work_width
    before_big = cv2.resize(main.before.clip(0, 255).astype(np.uint8),
                            (round((main.work_box[2] - main.work_box[0]) * scale),
                             round((main.work_box[3] - main.work_box[1]) * scale)))
    tiles = [label(before_big, "BEFORE")]
    diffs = {(k, round(t, 1)): d for k, t, c, d in pr.closing if c == cid}
    for k, t in moments[1:]:
        f = snaps[(k, t)]["frame"]
        d = diffs.get((k, round(t, 1)))
        status = "open" if any(c.id == cid for c in snaps[(k, t)]["open"]) else "CLOSED"
        txt = (f"{'restart+' if k == 2 else ''}{t:.1f} s: diff {d:.0f}" if d is not None
               else f"{'restart+' if k == 2 else ''}{t:.1f} s: closed")
        tiles.append(label(f[y1:y2, x1:x2], txt, GREEN if status == "CLOSED" else RED))
    cv2.imwrite(str(out / "09_auto_close.jpg"), grid(tiles, 4, 300), [cv2.IMWRITE_JPEG_QUALITY, 85])
    ch = next(c for c in det.changes if c.id == cid)
    return {"close": {"reported_at": round(ch.t_detect - 15, 1), "closed_at_abs": ch.t_closed,
                      "closed_by": ch.closed_by, "threshold": pr.p.restored_diff}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "docs" / "walkthrough")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    from ultralytics import YOLO
    people = person_finder(YOLO(str(REPO / "models" / "yolo11m.pt")))
    facts = {}
    for step in (lambda: fig_cameras(args.out), lambda: fig_detector(args.out, people),
                 lambda: fig_people(args.out, people), lambda: fig_negatives(args.out, people),
                 lambda: fig_memory(args.out), lambda: fig_lens(args.out), lambda: fig_lens_options(args.out),
                 lambda: fig_loopcut(args.out), lambda: fig_close(args.out, people)):
        facts.update(step())
        print("done", sorted(p.name for p in args.out.glob("*.jpg"))[-1], flush=True)
    (args.out / "facts.json").write_text(json.dumps(facts, indent=2, default=str), encoding="utf-8")
    print(json.dumps(facts, indent=2, default=str)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
