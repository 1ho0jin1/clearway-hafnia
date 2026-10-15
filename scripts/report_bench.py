"""report_bench.py - turn a benchmark run folder (results.jsonl from bench_hafnia.py) into a self-contained report.html.

    py scripts\report_bench.py run\bench-20261015

No network and no packages: the page embeds its data and draws inline SVG. Open it in any browser.
"""
from __future__ import annotations

import html
import json
import statistics
import sys
from pathlib import Path

PHASES = [("queue", "Queued in gateway"), ("fetch", "Export from XProtect"),
          ("upload", "Upload to Hafnia"), ("vlm", "Hafnia VLM answer")]

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hafnia Latency Benchmark</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --border: rgba(11,11,11,0.10);
  --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --series-4: #eda100;
  --critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
    --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
    --grid: #2c2c2a; --axis: #383835;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
  --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
  --grid: #2c2c2a; --axis: #383835;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1040px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 16px; font-weight: 600; margin: 0 0 4px; }
.sub { color: var(--text-secondary); margin: 0 0 24px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.tile .label { color: var(--text-secondary); font-size: 13px; }
.tile .value { font-size: 28px; font-weight: 600; margin-top: 2px; }
.tile .note { color: var(--text-muted); font-size: 12px; }
.legend { display: flex; flex-wrap: wrap; gap: 16px; margin: 8px 0 12px; color: var(--text-secondary); font-size: 13px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
svg text { fill: var(--text-secondary); font-size: 12px; }
svg .muted { fill: var(--text-muted); }
svg .group { fill: var(--text-primary); font-weight: 600; }
svg .seg { cursor: default; }
svg .seg:hover { opacity: .8; }
#tip { position: fixed; pointer-events: none; background: var(--surface-1); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,.12); display: none; max-width: 280px; z-index: 10; }
#tip b { font-weight: 600; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; }
tr.nums td { border-bottom: 0; padding-bottom: 2px; }
th { color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
td.answer { color: var(--text-secondary); padding-top: 0; padding-bottom: 14px; }
.status-failed { color: var(--text-primary); white-space: nowrap; }
.status-failed::before { content: "\2715"; color: var(--critical); font-weight: 700; margin-right: 6px; }
.findings li { margin-bottom: 6px; }
.findings { margin: 8px 0 0; padding-left: 20px; }
.foot { color: var(--text-muted); font-size: 12px; }
</style>
</head>
<body>
<main>
  <h1>Hafnia VLM latency benchmark</h1>
  <p class="sub">__SUBTITLE__</p>
  <div class="tiles" id="tiles"></div>
  <section class="card">
    <h2>Where the time goes, per request</h2>
    <p class="sub" style="margin-bottom:0">Seconds from submit to answer, split by gateway phase. Phase boundaries come from polling and are accurate to about one poll interval.</p>
    <div class="legend" id="legend"></div>
    <div id="chart"></div>
  </section>
  <section class="card">
    <h2>Requests and answers</h2>
    <div class="table-wrap"><table id="table"></table></div>
  </section>
  <p class="foot">Generated by scripts/report_bench.py from results.jsonl.</p>
</main>
<div id="tip" role="tooltip"></div>
<script>
const ROWS = __ROWS__;
const PHASES = __PHASES__;
const STATS = __STATS__;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const f1 = v => v == null ? "–" : v.toFixed(1);

document.getElementById("tiles").innerHTML = [
  ["Completed", `${STATS.completed} of ${STATS.total}`, STATS.failed ? `${STATS.failed} failed before reaching Hafnia (free)` : "no failures"],
  ["Median time to answer", `${f1(STATS.median)} s`, `range ${f1(STATS.min)}–${f1(STATS.max)} s`],
  ["Median Hafnia VLM phase", `${f1(STATS.vlm_median)} s`, "of the total, the model's own share"],
  ["Allowance spent", `${STATS.completed}`, "of today's 500; failures are free"],
].map(([l, v, n]) => `<div class="tile"><div class="label">${l}</div><div class="value">${v}</div><div class="note">${n}</div></div>`).join("");

document.getElementById("legend").innerHTML = PHASES.map((p, i) =>
  `<span><i style="background:var(--series-${i + 1})"></i>${esc(p[1])}</span>`).join("") +
  `<span><span class="status-failed">Failed</span></span>`;

// Horizontal stacked bars, one row per request, grouped by run label.
(function drawChart() {
  const W = 960, labelW = 300, rightPad = 56, barH = 18, rowH = 30, groupH = 30, axisH = 28;
  const groups = [...new Set(ROWS.map(r => r.label || "run"))];
  const maxT = Math.max(1, ...ROWS.map(r => r.total || 0));
  const tickStep = maxT > 20 ? 5 : 2;
  const xMax = Math.ceil(maxT / tickStep) * tickStep;
  const x = v => labelW + (v / xMax) * (W - labelW - rightPad);
  let y = 0, body = "";
  for (const g of groups) {
    const inGroup = ROWS.filter(r => (r.label || "run") === g);
    const most = Math.max(...inGroup.map(r => r.batch_size));
    body += `<text class="group" x="0" y="${y + 20}">${esc(g)}<tspan class="muted" style="font-weight:400">${most > 1 ? `  ·  ${most} submitted at once` : "  ·  one at a time"}</tspan></text>`;
    y += groupH;
    for (const r of inGroup) {
      const name = `${r.camera} · ${r.clip_s}s`;
      body += `<text x="0" y="${y + barH / 2 + 4}">${esc(name)}</text>`;
      if (r.progress === "Completed") {
        let acc = 0;
        const segs = PHASES.map(([k], i) => ({k, i, v: r[k] || 0})).filter(s => s.v > 0);
        segs.forEach((s, j) => {
          const x0 = x(acc), x1 = x(acc + s.v), last = j === segs.length - 1;
          const w = Math.max(0, x1 - x0 - (last ? 0 : 2));  // 2px surface gap between segments
          const rad = last ? Math.min(4, w / 2) : 0;          // rounded data-end, square at the baseline
          const d = `M${x0},${y} h${w - rad} a${rad},${rad} 0 0 1 ${rad},${rad} v${barH - 2 * rad} a${rad},${rad} 0 0 1 ${-rad},${rad} h${-(w - rad)} z`;
          body += `<path class="seg" d="${d}" fill="var(--series-${s.i + 1})" data-tip="${esc(`<b>${PHASES[s.i][1]}</b><br>${f1(s.v)} s · ${r.camera}, ${r.clip_s}s clip`)}"/>`;
          acc += s.v;
        });
        body += `<text x="${x(r.total) + 6}" y="${y + barH / 2 + 4}" style="fill:var(--text-primary)">${f1(r.total)} s</text>`;
      } else {
        const reason = (r.error || r.progress).replace(/^.*?:\s*/, "").replace(/^An error was returned from the VMS:\s*/, "");
        body += `<text x="${labelW}" y="${y + barH / 2 + 4}"><tspan class="status-failed" style="fill:var(--critical);font-weight:700">✕ </tspan><tspan style="fill:var(--text-primary)">Failed after ${f1(r.total)} s</tspan><tspan class="muted"> — ${esc(reason)}</tspan></text>`;
      }
      y += rowH;
    }
    y += 6;
  }
  let axis = "";
  for (let t = 0; t <= xMax; t += tickStep) {
    axis += `<line x1="${x(t)}" x2="${x(t)}" y1="0" y2="${y}" stroke="var(--grid)" stroke-width="1"/>`;
    axis += `<text class="muted" x="${x(t)}" y="${y + 18}" text-anchor="middle" style="font-variant-numeric:tabular-nums">${t}${t === xMax ? " s" : ""}</text>`;
  }
  axis += `<line x1="${labelW}" x2="${labelW}" y1="0" y2="${y}" stroke="var(--axis)" stroke-width="1"/>`;
  document.getElementById("chart").innerHTML =
    `<svg viewBox="0 0 ${W} ${y + axisH}" role="img" aria-label="Stacked bars of seconds per phase for each request">${axis}${body}</svg>`;
})();

// Hover tooltip for segments.
const tip = document.getElementById("tip");
document.addEventListener("mousemove", e => {
  const t = e.target.closest("[data-tip]");
  if (!t) { tip.style.display = "none"; return; }
  tip.innerHTML = t.getAttribute("data-tip");
  tip.style.display = "block";
  const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(e.clientX + 12, innerWidth - r.width - 8) + "px";
  tip.style.top = Math.min(e.clientY + 12, innerHeight - r.height - 8) + "px";
});

// Table view: every number plus the full answer.
const SHORT = {queue: "Queue", fetch: "Export", upload: "Upload", vlm: "VLM"};
document.getElementById("table").innerHTML =
  `<thead><tr><th>Run</th><th>Camera</th><th>Clip</th><th>At once</th>${PHASES.map(([k]) => `<th class="num">${SHORT[k]} s</th>`).join("")}<th class="num">Total s</th><th class="num">Gateway s</th></tr></thead><tbody>` +
  ROWS.map(r => `<tr class="nums"><td>${esc(r.label)}</td><td>${esc(r.camera)}</td><td class="num">${r.clip_s} s</td><td class="num">${r.batch_size}</td>` +
    PHASES.map(([k]) => `<td class="num">${f1(r[k])}</td>`).join("") +
    `<td class="num">${f1(r.total)}</td><td class="num">${f1(r.server_total)}</td></tr>` +
    `<tr><td></td><td class="answer" colspan="9">${r.progress === "Completed" ? esc(r.response) : `<span class="status-failed">Failed</span> ${esc(r.error)}`}</td></tr>`).join("") +
  `</tbody>`;
</script>
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run_dir = Path(sys.argv[1])
    rows = [json.loads(line) for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if line]
    done = [r for r in rows if r["progress"] == "Completed"]
    totals = [r["total"] for r in done]
    stats = {
        "total": len(rows), "completed": len(done), "failed": len(rows) - len(done),
        "median": statistics.median(totals) if totals else None,
        "min": min(totals, default=None), "max": max(totals, default=None),
        "vlm_median": statistics.median([r["vlm"] for r in done]) if done else None,
    }
    labels = list(dict.fromkeys(r.get("label") or "run" for r in rows))
    subtitle = (f"{run_dir.name} · {len(rows)} requests in {len(labels)} runs ({', '.join(labels)}) · "
                f"clips ending 5 s before submit · default model")
    page = (PAGE.replace("__SUBTITLE__", html.escape(subtitle))
            .replace("__ROWS__", json.dumps(rows, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__PHASES__", json.dumps(PHASES))
            .replace("__STATS__", json.dumps(stats)))
    out = run_dir / "report.html"
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
