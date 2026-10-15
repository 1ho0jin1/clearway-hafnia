"""report_compare.py - side-by-side report of Hafnia's answers and another model's answers on the same clips.

    py scripts\report_compare.py run\bench-20261015

Reads results.jsonl (Hafnia, from bench_hafnia.py), opus_results.jsonl (the other model, same clips, from frames
exported by export_frames.ps1) and scores.json (answer key and per-clip scores). Writes compare.html.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hafnia vs Opus</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --border: rgba(11,11,11,0.10);
  --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7;
  --series-1: #2a78d6; --series-2: #eb6834;
  --good: #0ca30c; --serious: #ec835a; --critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
    --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
    --grid: #2c2c2a; --axis: #383835;
    --series-1: #3987e5; --series-2: #d95926;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
  --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
  --grid: #2c2c2a; --axis: #383835;
  --series-1: #3987e5; --series-2: #d95926;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1040px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 16px; font-weight: 600; margin: 0 0 4px; }
.sub { color: var(--text-secondary); margin: 0 0 20px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.tile .label { color: var(--text-secondary); font-size: 13px; display: flex; align-items: center; gap: 6px; }
.tile .value { font-size: 28px; font-weight: 600; margin-top: 2px; }
.tile .note { color: var(--text-muted); font-size: 12px; }
.key { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.legend { display: flex; gap: 16px; margin: 8px 0 4px; color: var(--text-secondary); font-size: 13px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
svg { display: block; width: 100%; height: auto; }
svg text { fill: var(--text-secondary); font-size: 12px; }
svg .val { fill: var(--text-primary); font-variant-numeric: tabular-nums; }
#tip { position: fixed; pointer-events: none; background: var(--surface-1); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,.12); display: none; max-width: 300px; z-index: 10; }
.clip { border-top: 1px solid var(--grid); padding: 14px 0; }
.clip:first-child { border-top: 0; padding-top: 0; }
.clip-head { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: baseline; }
.clip-head b { font-weight: 600; }
.clip-head .meta { color: var(--text-muted); font-size: 12px; }
.facts { display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 6px 0; font-size: 13px; }
.mark { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
.mark i { font-style: normal; font-weight: 700; }
.m1 i { color: var(--good); } .m05 i { color: var(--serious); } .m0 i { color: var(--critical); }
.answers { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 8px; }
@media (max-width: 720px) { .answers { grid-template-columns: 1fr; } }
.answer { font-size: 13px; color: var(--text-secondary); border-left: 3px solid var(--grid); padding: 2px 0 2px 10px; }
.answer .who { display: flex; align-items: center; gap: 6px; color: var(--text-primary); font-weight: 600; font-size: 12px; margin-bottom: 2px; }
.note { font-size: 13px; color: var(--text-primary); margin-top: 6px; }
.diff { display: inline-block; font-size: 11px; font-weight: 600; color: var(--text-primary); border: 1px solid var(--axis); border-radius: 999px; padding: 0 8px; }
ul { margin: 6px 0 0; padding-left: 20px; } li { margin-bottom: 6px; }
.foot { color: var(--text-muted); font-size: 12px; }
</style>
</head>
<body>
<main>
  <h1>Hafnia VLM vs Claude Opus 5.5, same clips</h1>
  <p class="sub">__SUBTITLE__</p>
  <div class="tiles" id="tiles"></div>
  <section class="card">
    <h2>Key facts caught, by scene</h2>
    <p class="sub" style="margin-bottom:0">Share of the answer key's facts each model stated (2 facts per clip; ½ for partly).</p>
    <div class="legend" id="legend"></div>
    <div id="chart"></div>
  </section>
  <section class="card">
    <h2>Read this before trusting the numbers</h2>
    <ul id="caveats"></ul>
  </section>
  <section class="card">
    <h2>Clip by clip</h2>
    <div id="clips"></div>
  </section>
  <p class="foot">Generated by scripts/report_compare.py from results.jsonl, opus_results.jsonl and scores.json.</p>
</main>
<div id="tip" role="tooltip"></div>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const M = {hafnia: {name: "Hafnia VLM", color: "var(--series-1)"}, opus: {name: "Claude Opus 5.5", color: "var(--series-2)"}};
const sum = a => a.reduce((x, y) => x + y, 0);
const fmtScore = v => (v % 1 ? v.toFixed(1) : String(v));

const tot = m => sum(D.scores.flatMap(s => s[m]));
const maxPts = D.scores.length * 2;
const disagree = D.scores.filter(s => sum(s.hafnia) !== sum(s.opus)).length;
document.getElementById("tiles").innerHTML = [
  [M.hafnia, `${fmtScore(tot("hafnia"))} / ${maxPts}`, `${Math.round(100 * tot("hafnia") / maxPts)}% of key facts`],
  [M.opus, `${fmtScore(tot("opus"))} / ${maxPts}`, `${Math.round(100 * tot("opus") / maxPts)}% of key facts`],
  [null, `${disagree} of ${D.scores.length}`, "clips where the scores differ", "Clips that differ"],
  [null, `${D.hafnia_median_s.toFixed(1)} s`, "Hafnia, submit to answer (median); Opus took 40–180 s per agent run, not comparable", "Hafnia speed"],
].map(([m, v, n, l]) => `<div class="tile"><div class="label">${m ? `<i class="key" style="background:${m.color}"></i>${m.name}` : l}</div><div class="value">${v}</div><div class="note">${n}</div></div>`).join("");

document.getElementById("legend").innerHTML = Object.values(M).map(m => `<span><i class="key" style="background:${m.color}"></i>${m.name}</span>`).join("");

// Grouped horizontal bars: per scene, share of facts caught by each model.
(function chart() {
  const scenes = [...new Set(D.scores.map(s => s.camera))];
  const W = 960, labelW = 300, right = 60, barH = 14, gap = 4, groupGap = 18;
  const x = v => labelW + v * (W - labelW - right);
  let y = 4, body = "";
  for (const sc of scenes) {
    const rows = D.scores.filter(s => s.camera === sc);
    const n = rows.length;
    body += `<text x="0" y="${y + barH + 2}" style="fill:var(--text-primary)">${esc(sc)}</text><text x="0" y="${y + barH + 18}">${n} clip${n > 1 ? "s" : ""}</text>`;
    ["hafnia", "opus"].forEach((m, k) => {
      const pts = sum(rows.flatMap(r => r[m])), share = pts / (2 * n);
      const yy = y + k * (barH + gap), w = Math.max(0, x(share) - x(0)), r = Math.min(4, w / 2);
      const d = w > 0 ? `M${x(0)},${yy} h${w - r} a${r},${r} 0 0 1 ${r},${r} v${barH - 2 * r} a${r},${r} 0 0 1 ${-r},${r} h${-(w - r)} z` : "";
      body += `<path d="${d}" fill="${M[m].color}" data-tip="${esc(`<b>${M[m].name}</b><br>${esc(sc)}: ${fmtScore(pts)} of ${2 * n} facts`)}"/>`;
      body += `<rect x="${x(0)}" y="${yy - 2}" width="${W - labelW - right}" height="${barH + 4}" fill="transparent" data-tip="${esc(`<b>${M[m].name}</b><br>${esc(sc)}: ${fmtScore(pts)} of ${2 * n} facts`)}"/>`;
      body += `<text class="val" x="${x(share) + 6}" y="${yy + barH - 2}">${Math.round(share * 100)}%</text>`;
    });
    y += 2 * barH + gap + groupGap + 8;
  }
  let axis = "";
  for (const t of [0, .25, .5, .75, 1]) {
    axis += `<line x1="${x(t)}" x2="${x(t)}" y1="0" y2="${y - groupGap}" stroke="var(--grid)"/>`;
    axis += `<text x="${x(t)}" y="${y - groupGap + 16}" text-anchor="middle" style="fill:var(--text-muted)">${t * 100}%</text>`;
  }
  document.getElementById("chart").innerHTML = `<svg viewBox="0 0 ${W} ${y}" role="img" aria-label="Share of key facts caught per scene by each model">${axis}${body}</svg>`;
})();

const tip = document.getElementById("tip");
document.addEventListener("mousemove", e => {
  const t = e.target.closest("[data-tip]");
  if (!t) { tip.style.display = "none"; return; }
  tip.innerHTML = t.getAttribute("data-tip"); tip.style.display = "block";
  const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(e.clientX + 12, innerWidth - r.width - 8) + "px";
  tip.style.top = Math.min(e.clientY + 12, innerHeight - r.height - 8) + "px";
});

document.getElementById("caveats").innerHTML = D.caveats.map(c => `<li>${esc(c)}</li>`).join("");

const mark = v => v === 1 ? `<span class="mark m1"><i>✓</i>caught</span>` : v === 0.5 ? `<span class="mark m05"><i>½</i>partly</span>` : `<span class="mark m0"><i>✕</i>missed</span>`;
document.getElementById("clips").innerHTML = D.scores.map(s => {
  const facts = D.key[s.camera].facts, h = D.hafnia[s.clip], o = D.opus[s.clip];
  const differs = sum(s.hafnia) !== sum(s.opus);
  return `<div class="clip">
    <div class="clip-head"><b>${esc(s.camera)}</b><span class="meta">${s.clip} · ${o.clip_s} s clip · ${esc(o.label)} · ${o.start_utc}–${o.end_utc.slice(11)}</span>${differs ? `<span class="diff">scores differ</span>` : ""}</div>
    <div class="facts">${facts.map((f, i) => `<span>${esc(f)}: ${M.hafnia.name} ${mark(s.hafnia[i])} · Opus ${mark(s.opus[i])}</span>`).join("")}</div>
    <div class="answers">
      <div class="answer"><div class="who"><i class="key" style="background:${M.hafnia.color}"></i>${M.hafnia.name} · ${h.total.toFixed(1)} s</div>${esc(h.response)}</div>
      <div class="answer"><div class="who"><i class="key" style="background:${M.opus.color}"></i>${M.opus.name} · ${o.frames} frames</div>${esc(o.answer)}</div>
    </div>
    <div class="note">${esc(s.note)}</div>
  </div>`;
}).join("");
</script>
</body>
</html>
"""

CAVEATS = [
    "Small sample: 12 clips, but only 5 distinct scenes (vandalism is 5 of the 12). One prompt only: the generic 'Describe what happens in this video.'",
    "Different inputs: Hafnia received the exported video (10 fps); Opus received JPEG stills at 2 fps from the same recorded spans. Motion between frames is invisible to Opus.",
    "The judge is Opus too (the main session, not blind: it had read both answers). Self-preference bias is possible; the notes quote the deciding phrases so you can check each verdict.",
    "The Opus answers were blind: fresh agents, random folder names, no camera names, each scene seen once per agent. All five agents reported no prior context about the scenes.",
    "Not comparable on cost or speed: Hafnia answers in about 5 s inside the XProtect pipeline, from a daily allowance. An Opus agent took 40-180 s and 50k-170k tokens to read a few clips frame by frame.",
    "Targeted prompts may change the picture: Hafnia was not asked about image quality, and the default model is a traffic model.",
]


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run_dir = Path(sys.argv[1])
    hafnia_rows = [json.loads(l) for l in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if l]
    opus_rows = [json.loads(l) for l in (run_dir / "opus_results.jsonl").read_text(encoding="utf-8").splitlines() if l]
    scores = json.loads((run_dir / "scores.json").read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in hafnia_rows}
    hafnia = {o["clip"]: by_id[o["id"]] for o in opus_rows}
    totals = sorted(r["total"] for r in hafnia_rows if r["progress"] == "Completed")
    median = totals[len(totals) // 2] if len(totals) % 2 else sum(totals[len(totals) // 2 - 1:len(totals) // 2 + 1]) / 2
    data = {"scores": scores["scores"], "key": scores["key"], "hafnia": hafnia,
            "opus": {o["clip"]: o for o in opus_rows}, "caveats": CAVEATS, "hafnia_median_s": median}
    subtitle = (f"{run_dir.name} · {len(opus_rows)} recorded clips · prompt “Describe what happens in this video.” · "
                f"Hafnia: default model, video · Opus: blind agents, stills at 2 fps · scored against a key written from the frames")
    page = (PAGE.replace("__SUBTITLE__", html.escape(subtitle))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    out = run_dir / "compare.html"
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
