r"""viz_walkthrough.py - figures that show each step of Clearway's pipeline on real camera frames (docs/walkthrough/).

    .venv\Scripts\python.exe scripts\viz_walkthrough.py [--out docs\walkthrough] [--only fade lens_code pages ...]

No Hafnia requests: answers are read from earlier runs (run/pilot-20261023T162040Z, run/memory-compare), the fade
figure from the replays run/change-fade-before and -after3, the lens-code figure from a clip in the lens spool
(run/lens/spool, git-ignored: it needs a machine that has played one), the board and summary figures from the
headless renders of docs/video/render (git-ignored; scripts/make_video.py --render-cards makes them). Only footage
we may show is used: the organizers' cameras (on every machine) and Wikimedia Commons CC0 clips; never test_11 (the AI
City licence forbids redistribution). Writes one JPEG per step and facts.json (numbers and answers the page quotes);
--only makes some of the figures (YOLO is loaded only for the ones that need it) and merges their facts into the file.
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


def titled(img: np.ndarray, text: str | list[str], color=WHITE, line: int = 34) -> np.ndarray:
    """A dark title bar above the image, one or more lines (label() draws over the image's top rows: wrong for a
    strip a few pixels high)."""
    lines = [text] if isinstance(text, str) else list(text)
    h, w = img.shape[:2]
    bar = line * len(lines)
    out = np.full((h + bar, w, 3), 20, np.uint8)
    out[bar:] = img
    for i, t in enumerate(lines):
        cv2.putText(out, t, (8, int(line * (i + 0.7))), FONT, line / 40, color, 1, cv2.LINE_AA)
    return out


def fig_fade(out: Path) -> dict:
    """10_fade.jpg: when the detector reported over 30 minutes of two looped cameras, before and after the fade fix
    (run/change-fade-before, run/change-fade-after3: scripts/eval_change.py --loops 120). One tick per report; the
    old detector's rows are grey, the fixed detector's in the accent (emphasis, not a palette)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    runs = {"before": REPO / "run" / "change-fade-before", "after": REPO / "run" / "change-fade-after3"}
    cases = {"bin_pushed_over_onto_sidewalk": "Bin", "escooter_left_across_sidewalk": "E-scooter"}
    rows, facts = [], {}
    for case, name in cases.items():
        for state, folder in runs.items():
            res = json.loads((folder / "results.json").read_text(encoding="utf-8"))
            c = next(x for x in res["cases"] if x["case"] == case)
            times = sorted(r["t_detect"] / 60 for r in c["reports"])
            rows.append((f"{name}, {'the detector before the fix' if state == 'before' else 'after the fix'}",
                         times, c["loops_caught"], c["loops"], state))
            facts[f"{case}_{state}"] = {"reports": len(times), "loops_caught": c["loops_caught"], "loops": c["loops"],
                                        "last_report_min": round(times[-1], 1) if times else None}
    ink, muted, rule, accent, grey = "#1b232c", "#5a6673", "#d5dbe1", "#b86e00", "#9aa4ae"
    fig, ax = plt.subplots(figsize=(16, 5.2), dpi=100)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    minutes = max(r[1][-1] if r[1] else 0 for r in rows)
    span = 30.0 if minutes <= 30 else minutes
    for i, (name, times, caught, loops, state) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.vlines(times, y - 0.32, y + 0.32, color=accent if state == "after" else grey, linewidth=1.2)
        ax.text(-0.4, y, name, ha="right", va="center", fontsize=12, color=ink)
        note = (f"{caught} of {loops} loops, {len(times)} reports"
                + (f"; the last at {times[-1]:.1f} min" if state == "before" and times and times[-1] < span - 1 else ""))
        ax.text(span + 0.4, y, note, ha="left", va="center", fontsize=11, color=muted)
    ax.set_xlim(0, span)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xticks(range(0, int(span) + 1, 5))
    ax.set_xticklabels([f"{m} min" for m in range(0, int(span) + 1, 5)], fontsize=11, color=muted)
    ax.set_yticks([])
    for x in range(5, int(span) + 1, 5):
        ax.axvline(x, color=rule, linewidth=1, zorder=0)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="x", length=0, pad=8)
    fig.subplots_adjust(left=0.24, right=0.76, top=0.96, bottom=0.12)
    fig.savefig(str(out / "10_fade.jpg"), format="jpg", pil_kwargs={"quality": 88})
    plt.close(fig)
    return {"fade": facts}


def fig_lens_code(out: Path) -> dict:
    """11_lens_code.jpg: a lens frame as the publisher plays it on lens_1 (a clip from the spool, fitted to the stream
    size, the frame code in its bottom band), and the band enlarged, with what reads back from a scaled,
    JPEG-recompressed copy (as lens_1's frames reach the service through FrameBridge). Needs a played clip in the
    spool (run/lens/spool, git-ignored)."""
    import datetime as dt
    from lens.code import band_rows, read, stamp
    from lens.publisher import SPOOL, fit
    jobs = []
    for pattern in ("*person_on_railway_tracks.avi", "*bin_pushed_over_onto_sidewalk.avi", "*.avi"):
        jobs = sorted(p for p in SPOOL.glob(pattern) if p.with_suffix(".done.json").exists())
        if jobs:
            break
    if not jobs:
        print("no played clip in the lens spool: 11_lens_code.jpg not made", flush=True)
        return {}
    avi = jobs[-1]
    done = json.loads(avi.with_suffix(".done.json").read_text(encoding="utf-8"))
    cap = cv2.VideoCapture(str(avi))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    idx = min(7, len(frames) - 1)
    fps = done.get("fps", 10)
    when = dt.datetime.fromisoformat(done["start"].replace("Z", "+00:00")) + dt.timedelta(seconds=idx / fps)
    frame = stamp(fit(frames[idx], 1280, 720), done["seq"], idx, when)
    # what reaches the service: the stream transcoded to JPEG and scaled by the Recording Server for FrameBridge
    small = cv2.resize(frame, (832, 468), interpolation=cv2.INTER_AREA)
    small = cv2.imdecode(cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 70])[1], cv2.IMREAD_COLOR)
    code = read(small, near=when)
    y0, y1 = band_rows(720)
    strip = cv2.resize(frame[y0:y1], (1280, (y1 - y0) * 8), interpolation=cv2.INTER_NEAREST)
    top = titled(frame, f"what lens_1 plays: {avi.name.split('_', 1)[1][:-4]}, job {done['seq']}, frame {idx}, "
                        f"sent {when:%H:%M:%S.%f}"[:-4] + " UTC")
    read_back = (f"job {code['seq']}, frame {code['idx']}, sent {code['wall']:%H:%M:%S.%f}"[:-4] + " UTC"
                 if code else "unreadable")
    bottom = titled(strip, ["the bottom band enlarged: 64 blocks = 8 sync bits, job, frame, centiseconds of the day, CRC-8",
                            f"read back from an 832-px JPEG of the frame: {read_back}"], YELLOW)
    img = np.vstack([top, np.full((16, 1280, 3), 30, np.uint8), bottom])
    cv2.imwrite(str(out / "11_lens_code.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return {"lens_code": {"clip": avi.name, "seq": done["seq"], "frame": idx, "sent": when.isoformat(),
                          "read_back": {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in code.items()}
                          if code else None}}


def fig_pages(out: Path) -> dict:
    """12_board.jpg and 13_summary.jpg: the owner board and the shift summary as rendered headless at the end of the
    clean live run (docs/video/render/board-final.png, summary-final.png: scripts/make_video.py --render-cards with
    the board on port 8766 following run/clearway-live-20261027T124112Z-clean). Skipped when the renders are not
    there."""
    made = []
    for src, dst in (("board-final.png", "12_board.jpg"), ("summary-final.png", "13_summary.jpg")):
        png = REPO / "docs" / "video" / "render" / src
        if not png.exists():
            print(f"{png} is not there: {dst} not made", flush=True)
            continue
        img = cv2.imread(str(png))
        cv2.imwrite(str(out / dst), fit(img, 1600), [cv2.IMWRITE_JPEG_QUALITY, 85])
        made.append(dst)
    return {"pages": made} if made else {}


FIGURES = {   # name -> (needs YOLO's person finder, function)
    "cameras": (False, fig_cameras), "detector": (True, fig_detector), "people": (True, fig_people),
    "negatives": (True, fig_negatives), "memory": (False, fig_memory), "lens": (False, fig_lens),
    "lens_options": (False, fig_lens_options), "loopcut": (False, fig_loopcut), "close": (True, fig_close),
    "fade": (False, fig_fade), "lens_code": (False, fig_lens_code), "pages": (False, fig_pages),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "docs" / "walkthrough")
    ap.add_argument("--only", nargs="+", choices=sorted(FIGURES), help="make only these figures")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    names = args.only or list(FIGURES)
    people = None
    if any(FIGURES[n][0] for n in names):
        from ultralytics import YOLO
        people = person_finder(YOLO(str(REPO / "models" / "yolo11m.pt")))
    facts_path = args.out / "facts.json"
    facts = json.loads(facts_path.read_text(encoding="utf-8")) if args.only and facts_path.exists() else {}
    for n in names:
        needs_people, fn = FIGURES[n]
        facts.update(fn(args.out, people) if needs_people else fn(args.out))
        print("done", n, flush=True)
    facts_path.write_text(json.dumps(facts, indent=2, default=str), encoding="utf-8")
    print(json.dumps(facts, indent=2, default=str)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
