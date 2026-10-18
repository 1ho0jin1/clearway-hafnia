r"""viz_pipeline.py - one page that follows each incident of a live run through the pipeline.

    .venv\Scripts\python.exe scripts\viz_pipeline.py --run run\live-<UTC> --frames <dir with inc1, inc2, ...>

For every candidate the router sent to Hafnia: the recorded input (the 6 s window Hafnia received), the same frames
with tier 0's detections (YOLO boxes and track IDs; the road users of the candidate in red), the timeline from event
to verdict, and Hafnia's answers. Frames come from scripts\export_window.ps1 (event - 6 s to event + 4 s; the first
3 s only warm up the tracker). YOLO is re-run on the recordings: the live run did not store boxes, so IDs can differ.
Writes <run>\pipeline.html (self-contained; contains video frames, so it is git-ignored).
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from incident.verify import CLASSIFY, DESCRIBE  # noqa: E402
from tier0.pipeline import Tier0  # noqa: E402

THUMB_W = 480
CLS_COLOR = {"person": (230, 160, 40), "bicycle": (60, 200, 230), "motorcycle": (60, 200, 230),
             "car": (220, 220, 220), "truck": (220, 220, 220), "bus": (220, 220, 220)}   # BGR


def b64jpg(img: np.ndarray, width: int = THUMB_W, q: int = 72) -> str:
    h, w = img.shape[:2]
    small = cv2.resize(img, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
    return base64.b64encode(cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, q])[1]).decode()


def parse_t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def incident_frames(folder: Path, t_event: dt.datetime) -> dict:
    """Run tier 0 over the exported frames; return raw and annotated thumbnails for the 6 s Hafnia window."""
    files = sorted(folder.glob("*.jpg"), key=lambda f: int(f.stem))
    t0 = Tier0()
    per_frame = []
    for f in files:
        t = int(f.stem) / 1000
        frame = cv2.imread(str(f))
        r = t0.model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0, 1, 2, 3, 5, 7],
                           conf=t0.conf, imgsz=t0.imgsz, verbose=False, device=t0.device)[0]
        boxes, ids, classes = np.empty((0, 4)), [], []
        if r.boxes.id is not None:
            boxes = r.boxes.xyxy.cpu().numpy()
            ids = r.boxes.id.int().tolist()
            classes = [t0.model.names[c] for c in r.boxes.cls.int().tolist()]
        t0.detector.update(t, ids, classes, boxes)
        per_frame.append((t, frame, boxes, ids, classes))

    te = t_event.timestamp()
    near = [c for c in t0.detector.candidates if abs(c.t - te) <= 1.5]
    hot = {k for c in near for k in c.tracks}
    trigger = min(near, key=lambda c: abs(c.t - te)) if near else None

    raw, ann, times = [], [], []
    for t, frame, boxes, ids, classes in per_frame:
        if not (te - 3.05 <= t <= te + 3.05):
            continue
        a = frame.copy()
        for (x1, y1, x2, y2), k, c in zip(boxes.astype(int), ids, classes):
            red = k in hot
            col = (40, 40, 230) if red else CLS_COLOR.get(c, (200, 200, 200))
            cv2.rectangle(a, (x1, y1), (x2, y2), col, 3 if red else 1)
            cv2.putText(a, f"{c} {k}", (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
        if trigger and abs(t - trigger.t) < 0.051:
            cv2.putText(a, f"TIER 0: {trigger.kind.upper()}", (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (40, 40, 230), 2, cv2.LINE_AA)
        raw.append(b64jpg(frame))
        ann.append(b64jpg(a))
        times.append(round(t - te, 2))
    return {"raw": raw, "ann": ann, "times": times,
            "rerun": None if not trigger else {"kind": trigger.kind, "score": trigger.score,
                                               "dt": round(trigger.t - te, 2), "detail": trigger.detail}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--frames", type=Path, required=True)
    args = ap.parse_args()
    events = [json.loads(l) for l in (args.run / "events.jsonl").read_text(encoding="utf-8").splitlines() if l]

    cands = [e for e in events if e["type"] == "candidate"]
    incidents = []
    for n, c in enumerate((e for e in cands if e["send"]), start=1):
        t_event = parse_t(c["t_event"])
        alarm = next((e for e in events if e["type"] == "alarm" and e["camera"] == c["camera"]
                      and parse_t(e["t_event"]) == t_event), None)
        aid = alarm["alarm"] if alarm else None
        related = {e["type"]: e for e in events if aid and e.get("alarm") == aid}
        steps = [{"label": "Event (tier 0 frame time)", "t": 0.0}]
        steps.append({"label": "Tier 0 candidate logged", "t": round((parse_t(c["wall"]) - t_event).total_seconds(), 2)})
        for kind, label in (("alarm", "Unverified Low alarm raised"), ("verdict", "Hafnia verdict"),
                            ("describe", "Hafnia description"), ("bookmark", "Bookmark created")):
            if kind in related:
                steps.append({"label": label, "t": round((parse_t(related[kind]["wall"]) - t_event).total_seconds(), 2)})
        v = related.get("verdict", {})
        print(f"incident {n}: {c['camera']} {c['t_event']} -> {v.get('label')}", flush=True)
        incidents.append({
            "n": n, "camera": c["camera"], "t_event": c["t_event"][:23], "kind": c["kind"], "score": c["score"],
            "detail": c["detail"], "label": v.get("label", "?"), "confirmed": v.get("confirmed", False),
            "answer": v.get("answer", ""), "hafnia_s": v.get("hafnia_s"),
            "description": related.get("describe", {}).get("description", ""),
            "describe_s": related.get("describe", {}).get("hafnia_s"),
            "bookmark": related.get("bookmark", {}).get("reference", ""),
            "steps": steps, **incident_frames(args.frames / f"inc{n}", t_event)})

    reasons = {}
    for e in cands:
        reasons[e["reason"]] = reasons.get(e["reason"], 0) + 1
    funnel = {"candidates": len(cands), "sent": sum(e["send"] for e in cands),
              "confirmed": sum(i["confirmed"] for i in incidents),
              "requests": sum(e["type"] in ("verdict", "describe") for e in events), "reasons": reasons}
    page = PAGE.replace("__DATA__", json.dumps({"incidents": incidents, "funnel": funnel,
                                                 "prompts": {"classify": CLASSIFY, "describe": DESCRIBE},
                                                 "run": args.run.name}).replace("</", "<\\/"))
    out = args.run / "pipeline.html"
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Incident Pipeline</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --border: rgba(11,11,11,0.10);
  --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7;
  --tier0: #2a78d6; --router: #6250d6; --hafnia: #eb6834; --xprotect: #1baf7a;
  --good: #0ca30c; --critical: #d03b3b; --window: rgba(235,104,52,0.12);
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
    --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781; --grid: #2c2c2a; --axis: #383835;
    --tier0: #3987e5; --router: #9085e9; --hafnia: #d95926; --xprotect: #199e70; --window: rgba(217,89,38,0.18);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
  --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781; --grid: #2c2c2a; --axis: #383835;
  --tier0: #3987e5; --router: #9085e9; --hafnia: #d95926; --xprotect: #199e70; --window: rgba(217,89,38,0.18);
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary); font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1080px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 17px; font-weight: 600; margin: 0 0 4px; }
h3 { font-size: 14px; font-weight: 600; margin: 0 0 6px; color: var(--text-secondary); }
.sub { color: var(--text-secondary); margin: 0 0 20px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 20px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; }
.tile .label { color: var(--text-secondary); font-size: 13px; }
.tile .value { font-size: 26px; font-weight: 600; }
.tile .note { color: var(--text-muted); font-size: 12px; }
svg text { font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--text-secondary); }
.head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; margin-bottom: 12px; }
.badge { font-size: 12px; font-weight: 600; border-radius: 999px; padding: 2px 10px; border: 1px solid; }
.badge.ok { color: var(--good); border-color: var(--good); }
.badge.no { color: var(--text-secondary); border-color: var(--axis); }
.meta { color: var(--text-muted); font-size: 12px; }
.grid2 { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 20px; }
@media (max-width: 820px) { .grid2 { grid-template-columns: 1fr; } }
.player img { width: 100%; border-radius: 8px; display: block; background: #000; }
.controls { display: flex; align-items: center; gap: 10px; margin-top: 8px; flex-wrap: wrap; }
.controls input[type=range] { flex: 1; min-width: 160px; }
button, .seg label { font: inherit; font-size: 13px; border: 1px solid var(--axis); background: var(--surface-1); color: var(--text-primary);
  border-radius: 8px; padding: 4px 10px; cursor: pointer; }
.seg { display: inline-flex; gap: 0; }
.seg input { display: none; }
.seg label { border-radius: 0; }
.seg label:first-of-type { border-radius: 8px 0 0 8px; }
.seg label:last-of-type { border-radius: 0 8px 8px 0; border-left: 0; }
.seg input:checked + label { background: var(--text-primary); color: var(--page); border-color: var(--text-primary); }
.tlabel { font-variant-numeric: tabular-nums; color: var(--text-secondary); font-size: 13px; min-width: 64px; text-align: right; }
.strip { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-top: 10px; }
.strip figure { margin: 0; }
.strip img { width: 100%; border-radius: 4px; display: block; cursor: pointer; }
.strip figcaption { font-size: 11px; color: var(--text-muted); text-align: center; font-variant-numeric: tabular-nums; }
.q { border-left: 3px solid var(--hafnia); padding: 2px 0 2px 10px; margin: 8px 0; }
.q .p { color: var(--text-muted); font-size: 12px; }
.q .a { font-size: 14px; margin-top: 4px; }
.q .a b { font-weight: 600; }
.t0 { border-left: 3px solid var(--tier0); padding: 2px 0 2px 10px; margin: 8px 0; font-size: 13px; }
.note { color: var(--text-muted); font-size: 12px; margin-top: 6px; }
.warn { font-size: 13px; margin-top: 6px; }
.warn::before { content: "\26A0  "; color: var(--hafnia); }
.foot { color: var(--text-muted); font-size: 12px; }
</style>
</head>
<body>
<main>
  <h1>One incident at a time, through the pipeline</h1>
  <p class="sub" id="sub"></p>
  <section class="card">
    <h2>The pipeline</h2>
    <div id="diagram"></div>
  </section>
  <div class="tiles" id="tiles"></div>
  <div id="incidents"></div>
  <p class="foot">Generated by scripts/viz_pipeline.py from events.jsonl and recorded frames exported from XProtect. YOLO was re-run on the recordings to draw boxes; the live run did not store them, so track IDs can differ from the live run.</p>
</main>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
document.getElementById("sub").textContent = `${D.run} · ${D.incidents.length} candidates the router sent to Hafnia · frames: the recorded 6 s window centred on each event`;

// Pipeline diagram.
(function () {
  const steps = [
    ["Camera", "XProtect recording", "var(--xprotect)"],
    ["FrameBridge", "live frames, 10 fps", "var(--xprotect)"],
    ["Tier 0", "YOLO + tracking + rules", "var(--tier0)"],
    ["Router", "cooldown · open incident · rejected spots · budget", "var(--router)"],
    ["Unverified alarm", "Low, with snapshot", "var(--xprotect)"],
    ["Hafnia VLM", "6 s window around the event", "var(--hafnia)"],
    ["Verified alarm", "High + bookmark, or closed", "var(--xprotect)"],
  ];
  const W = 1040, bw = 128, gap = (W - steps.length * bw) / (steps.length - 1), H = 92;
  let s = "";
  steps.forEach(([t, d, c], i) => {
    const x = i * (bw + gap);
    s += `<rect x="${x}" y="14" width="${bw}" height="56" rx="8" fill="none" stroke="${c}" stroke-width="2"/>`;
    s += `<text x="${x + bw / 2}" y="38" text-anchor="middle" style="fill:var(--text-primary);font-weight:600">${esc(t)}</text>`;
    const words = d.split(" "); let line = "", lines = [];
    words.forEach(w => { if ((line + " " + w).trim().length > 20) { lines.push(line.trim()); line = w; } else line += " " + w; });
    lines.push(line.trim());
    lines.slice(0, 2).forEach((l, j) => s += `<text x="${x + bw / 2}" y="${54 + j * 13}" text-anchor="middle" style="font-size:10.5px">${esc(l)}</text>`);
    if (i < steps.length - 1) {
      const x1 = x + bw + 3, x2 = x + bw + gap - 3;
      s += `<line x1="${x1}" y1="42" x2="${x2 - 5}" y2="42" stroke="var(--axis)" stroke-width="1.5"/><path d="M${x2 - 6},38 L${x2},42 L${x2 - 6},46 z" fill="var(--axis)"/>`;
    }
  });
  s += `<text x="${W / 2}" y="88" text-anchor="middle" style="fill:var(--text-muted)">Tier 0 sees every frame; Hafnia only what the router sends; the operator sees the alarm change state.</text>`;
  document.getElementById("diagram").innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Pipeline diagram">${s}</svg>`;
})();

// Funnel tiles.
const F = D.funnel;
document.getElementById("tiles").innerHTML = [
  ["Tier 0 candidates", F.candidates, "in the 5-minute run, two cameras"],
  ["Sent to Hafnia", F.sent, Object.entries(F.reasons).filter(([r]) => r !== "ask Hafnia").map(([r, n]) => `${n} ${r}`).join("; ")],
  ["Confirmed accidents", F.confirmed, "alarm raised to High"],
  ["Hafnia requests", F.requests, "checks plus descriptions"],
].map(([l, v, n]) => `<div class="tile"><div class="label">${esc(l)}</div><div class="value">${v}</div><div class="note">${esc(n)}</div></div>`).join("");

function timeline(inc) {
  const W = 980, L = 210, R = 30, rowH = 22, top = 26;
  const tmin = -3, tmax = Math.max(8, ...inc.steps.map(s => s.t)) + 1;
  const x = t => L + (t - tmin) / (tmax - tmin) * (W - L - R);
  const H = top + inc.steps.length * rowH + 30;
  let s = `<rect x="${x(-3)}" y="${top - 8}" width="${x(3) - x(-3)}" height="${inc.steps.length * rowH + 6}" fill="var(--window)" rx="4"/>`;
  s += `<text x="${(x(-3) + x(3)) / 2}" y="${top - 12}" text-anchor="middle" style="fill:var(--hafnia)">video Hafnia saw (6 s)</text>`;
  for (let t = Math.ceil(tmin); t <= tmax; t += (tmax > 20 ? 4 : 2)) {
    s += `<line x1="${x(t)}" x2="${x(t)}" y1="${top - 6}" y2="${top + inc.steps.length * rowH}" stroke="var(--grid)"/>`;
    s += `<text x="${x(t)}" y="${top + inc.steps.length * rowH + 16}" text-anchor="middle" style="fill:var(--text-muted);font-variant-numeric:tabular-nums">${t > 0 ? "+" : ""}${t} s</text>`;
  }
  const col = l => /Hafnia/.test(l) ? "var(--hafnia)" : /Tier 0|Event/.test(l) ? "var(--tier0)" : "var(--xprotect)";
  inc.steps.forEach((st, i) => {
    const y = top + i * rowH + rowH / 2;
    s += `<text x="0" y="${y + 4}">${esc(st.label)}</text>`;
    s += `<line x1="${x(0)}" x2="${x(st.t)}" y1="${y}" y2="${y}" stroke="${col(st.label)}" stroke-width="2"/>`;
    s += `<circle cx="${x(st.t)}" cy="${y}" r="5" fill="${col(st.label)}" stroke="var(--surface-1)" stroke-width="2"/>`;
    s += `<text x="${x(st.t) + 9}" y="${y + 4}" style="fill:var(--text-primary);font-variant-numeric:tabular-nums">${st.t >= 0 ? "+" : ""}${st.t.toFixed(1)} s</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Timeline from event to verdict">${s}</svg>`;
}

document.getElementById("incidents").innerHTML = D.incidents.map(inc => {
  const mid = inc.times.findIndex(t => t >= 0);
  const picks = [-3, -2, -1, 0, 1, 2, 3].map(t => inc.times.reduce((b, v, i) => Math.abs(v - t) < Math.abs(inc.times[b] - t) ? i : b, 0));
  const contradicts = inc.confirmed && /avoid(s|ed)? a collision|no collision/i.test(inc.description);
  return `<section class="card" data-n="${inc.n}">
    <div class="head"><h2>${inc.n}. ${esc(inc.camera)}</h2>
      <span class="badge ${inc.confirmed ? "ok" : "no"}">${inc.confirmed ? "✓ accident confirmed" : "✕ closed as false alarm"}</span>
      <span class="meta">event ${esc(inc.t_event.replace("T", " "))} UTC</span></div>
    <div class="grid2">
      <div class="player">
        <h3>1 · Input and 2 · tier 0, frame by frame</h3>
        <img id="img${inc.n}" alt="frame">
        <div class="controls">
          <button id="play${inc.n}">▶ Play</button>
          <input type="range" id="sl${inc.n}" min="0" max="${inc.times.length - 1}" value="${mid}" aria-label="frame">
          <span class="tlabel" id="tl${inc.n}"></span>
          <span class="seg"><input type="radio" name="v${inc.n}" id="r${inc.n}" value="raw"><label for="r${inc.n}">Input</label><input type="radio" name="v${inc.n}" id="a${inc.n}" value="ann" checked><label for="a${inc.n}">Tier 0</label></span>
        </div>
        <div class="strip">${picks.map(i => `<figure><img src="data:image/jpeg;base64,${inc.ann[i]}" data-i="${i}" alt=""><figcaption>${inc.times[i] > 0 ? "+" : ""}${inc.times[i].toFixed(1)} s</figcaption></figure>`).join("")}</div>
        <p class="note">Red boxes: the road users in tier 0's candidate. Thin boxes: everything YOLO tracks (class and track ID).</p>
      </div>
      <div>
        <h3>2 · Tier 0 candidate</h3>
        <div class="t0"><b>${esc(inc.kind)}</b>, score ${esc(inc.score)} · ${esc(inc.detail)}${inc.rerun ? `<div class="note">Re-run on the recording: ${esc(inc.rerun.kind)} at ${inc.rerun.dt >= 0 ? "+" : ""}${inc.rerun.dt} s (${esc(inc.rerun.detail)})</div>` : `<div class="note">The re-run on the recording found no candidate within ±1.5 s.</div>`}</div>
        <h3 style="margin-top:14px">3 · Hafnia</h3>
        <div class="q"><div class="p">${esc(D.prompts.classify)}</div><div class="a"><b>${esc(inc.answer || inc.label)}</b> · ${inc.hafnia_s ?? "–"} s</div></div>
        ${inc.description ? `<div class="q"><div class="p">${esc(D.prompts.describe)}</div><div class="a">${esc(inc.description)}</div><div class="note">${inc.describe_s} s</div></div>` : ""}
        ${contradicts ? `<p class="warn">The free description contradicts the confirmed verdict for the same window.</p>` : ""}
        ${inc.bookmark ? `<p class="note">Bookmark ${esc(inc.bookmark)} on the camera's timeline.</p>` : ""}
      </div>
    </div>
    <h3 style="margin-top:16px">4 · Timeline from the event</h3>
    ${timeline(inc)}
  </section>`;
}).join("");

D.incidents.forEach(inc => {
  const n = inc.n, img = document.getElementById("img" + n), sl = document.getElementById("sl" + n),
        tl = document.getElementById("tl" + n), play = document.getElementById("play" + n);
  let timer = null;
  const mode = () => document.querySelector(`input[name=v${n}]:checked`).value;
  const show = () => { const i = +sl.value; img.src = "data:image/jpeg;base64," + inc[mode()][i];
    const t = inc.times[i]; tl.textContent = (t > 0 ? "+" : "") + t.toFixed(1) + " s"; };
  sl.addEventListener("input", show);
  document.querySelectorAll(`input[name=v${n}]`).forEach(r => r.addEventListener("change", show));
  document.querySelectorAll(`section[data-n="${n}"] .strip img`).forEach(im => im.addEventListener("click", () => { sl.value = im.dataset.i; show(); }));
  play.addEventListener("click", () => {
    if (timer) { clearInterval(timer); timer = null; play.textContent = "▶ Play"; return; }
    play.textContent = "❚❚ Pause";
    timer = setInterval(() => { sl.value = (+sl.value + 1) % inc.times.length; show(); }, 100);
  });
  show();
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
