r"""report_recognition.py - how well Hafnia recognizes incidents: one-word classification vs ground truth, plus free
descriptions with a judged verdict. Writes <run_dir>/recognition.html.

    py scripts\report_recognition.py run\bench-20261018 --manifest data\clips.json

Reads <run_dir>/results.jsonl (rows labelled "classify" and "describe" by bench_hafnia.py --label) and, if present,
<run_dir>/recognition_scores.json: {"describe": {"<camera>": {"score": 1 | 0.5 | 0, "note": "..."}}}.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Incident Recognition</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --border: rgba(11,11,11,0.10);
  --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781; --grid: #e1e0d9;
  --seq-0: #f0efec; --seq-1: #cde2fb; --seq-2: #86b6ef; --seq-3: #3987e5; --seq-4: #1c5cab;
  --good: #0ca30c; --serious: #ec835a; --critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
    --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781; --grid: #2c2c2a;
    --seq-0: #262624; --seq-1: #184f95; --seq-2: #256abf; --seq-3: #3987e5; --seq-4: #86b6ef;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --border: rgba(255,255,255,0.10);
  --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781; --grid: #2c2c2a;
  --seq-0: #262624; --seq-1: #184f95; --seq-2: #256abf; --seq-3: #3987e5; --seq-4: #86b6ef;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary); font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1040px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 16px; font-weight: 600; margin: 0 0 4px; }
.sub { color: var(--text-secondary); margin: 0 0 20px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.tile .label { color: var(--text-secondary); font-size: 13px; }
.tile .value { font-size: 28px; font-weight: 600; margin-top: 2px; }
.tile .note { color: var(--text-muted); font-size: 12px; }
.table-wrap { overflow-x: auto; }
table.cm { border-collapse: separate; border-spacing: 2px; font-size: 12px; }
table.cm th { color: var(--text-secondary); font-weight: 600; padding: 4px 6px; white-space: nowrap; }
table.cm th.row { text-align: right; }
table.cm td { width: 64px; height: 36px; text-align: center; border-radius: 4px; font-variant-numeric: tabular-nums; }
table.cm td.diag { outline: 2px solid var(--text-primary); outline-offset: -2px; }
.axis-note { color: var(--text-muted); font-size: 12px; margin-top: 6px; }
.clip { border-top: 1px solid var(--grid); padding: 14px 0; }
.clip:first-child { border-top: 0; padding-top: 0; }
.clip-head { display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: baseline; }
.clip-head b { font-weight: 600; }
.meta { color: var(--text-muted); font-size: 12px; }
.truth { font-size: 13px; color: var(--text-secondary); margin: 4px 0; }
.answers { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13px; margin: 4px 0; }
.mark { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
.mark i { font-style: normal; font-weight: 700; }
.ok i { color: var(--good); } .half i { color: var(--serious); } .bad i { color: var(--critical); }
.desc { font-size: 13px; color: var(--text-secondary); border-left: 3px solid var(--grid); padding: 2px 0 2px 10px; margin-top: 6px; }
.note { font-size: 13px; margin-top: 4px; }
.pill { font-size: 11px; font-weight: 600; border: 1px solid var(--grid); border-radius: 999px; padding: 0 8px; }
ul { margin: 6px 0 0; padding-left: 20px; } li { margin-bottom: 6px; }
.foot { color: var(--text-muted); font-size: 12px; }
</style>
</head>
<body>
<main>
  <h1>Can Hafnia recognize incidents?</h1>
  <p class="sub">__SUBTITLE__</p>
  <div class="tiles" id="tiles"></div>
  <section class="card">
    <h2>One-word classification: truth vs answer</h2>
    <p class="sub" style="margin-bottom:8px">Counts of classification answers. Rows are the ground truth, columns what Hafnia answered; the outlined diagonal is correct.</p>
    <div class="table-wrap"><table class="cm" id="cm"></table></div>
    <p class="axis-note">Accepted alternatives for hard clips count as correct in the tiles, not on the diagonal.</p>
  </section>
  <section class="card">
    <h2>Read this before trusting the numbers</h2>
    <ul id="caveats"></ul>
  </section>
  <section class="card">
    <h2>Clip by clip</h2>
    <div id="clips"></div>
  </section>
  <p class="foot">Generated by scripts/report_recognition.py from results.jsonl, data/clips.json and recognition_scores.json.</p>
</main>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const pct = (a, b) => b ? Math.round(100 * a / b) + "%" : "–";

document.getElementById("tiles").innerHTML = D.tiles.map(t =>
  `<div class="tile"><div class="label">${esc(t.label)}</div><div class="value">${esc(t.value)}</div><div class="note">${esc(t.note)}</div></div>`).join("");

(function cm() {
  const L = D.labels, cols = [...L, "OTHER"];
  const max = Math.max(1, ...Object.values(D.confusion).flatMap(r => Object.values(r)));
  const shade = n => n === 0 ? "var(--seq-0)" : `var(--seq-${Math.min(4, 1 + Math.floor(3 * n / max))})`;
  const rows = L.filter(t => D.confusion[t]);
  let h = `<thead><tr><th></th>${cols.map(c => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>`;
  for (const t of rows) {
    h += `<tr><th class="row">${esc(t)}</th>` + cols.map(p => {
      const n = (D.confusion[t] || {})[p] || 0;
      const ink = n && shade(n).match(/seq-[34]/) ? "#fff" : "var(--text-primary)";
      return `<td class="${p === t ? "diag" : ""}" style="background:${shade(n)};color:${ink}" title="truth ${esc(t)}, answered ${esc(p)}: ${n}">${n || ""}</td>`;
    }).join("") + "</tr>";
  }
  document.getElementById("cm").innerHTML = h + "</tbody>";
})();

document.getElementById("caveats").innerHTML = D.caveats.map(c => `<li>${esc(c)}</li>`).join("");

const mark = (ok, text) => `<span class="mark ${ok === true ? "ok" : ok === "half" ? "half" : "bad"}"><i>${ok === true ? "✓" : ok === "half" ? "½" : "✕"}</i>${esc(text)}</span>`;
document.getElementById("clips").innerHTML = D.clips.map(c => `
  <div class="clip">
    <div class="clip-head"><b>${esc(c.camera)}</b><span class="meta">${esc(c.source || "organizer camera")} · truth ${esc(c.label)}${c.hard ? " · hard" : ""} · window ${c.window} s</span>${c.control ? `<span class="pill">control</span>` : ""}</div>
    ${c.truth ? `<div class="truth">${esc(c.truth)}</div>` : ""}
    <div class="answers">${c.classify.map((a, i) => mark(a.correct, `answer ${i + 1}: ${a.parsed}${a.parsed !== a.raw.trim().toUpperCase() ? ` (“${a.raw.trim().slice(0, 60)}”)` : ""} · ${a.total.toFixed(1)} s`)).join("")}</div>
    ${c.describe ? `<div class="desc">${esc(c.describe.response || c.describe.error)}</div>` : ""}
    ${c.verdict ? `<div class="note">${mark(c.verdict.score === 1 ? true : c.verdict.score === 0.5 ? "half" : false, "description: " + c.verdict.note)}</div>` : ""}
  </div>`).join("");
</script>
</body>
</html>
"""

CAVEATS = [
    "Small set: 10 incident clips (5 accidents, 2 robberies, 2 shootings, 1 arson) and 5 organizer cameras as controls. Two answers per clip at different loop positions.",
    "Ground truth and the description verdicts were written by Opus from contact sheets of the source videos; the clip-by-clip section quotes the evidence so each verdict can be checked.",
    "Two clips are hard by design: in the arson clip no fire is visible, and in one shooting clip no weapon is visible. Their accepted alternatives are listed per clip.",
    "Each window covers one full loop of the clip, so the incident is inside, but it can be split across the loop seam.",
    "Default model only; prompts were not tuned. The camera names are neutral (test_01 ...), so names cannot leak the answer.",
]


def parse_label(text: str, labels: list[str]) -> str:
    """The first allowed label that appears as a whole word; OTHER if none does."""
    hits = [(m.start(), lab) for lab in labels for m in re.finditer(rf"\b{lab}\b", (text or "").upper())]
    return min(hits)[1] if hits else "OTHER"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("run_dir", type=Path)
    p.add_argument("--manifest", type=Path, default=Path("data/clips.json"))
    args = p.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    labels = manifest["labels"]
    rows = [json.loads(l) for l in (args.run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if l]
    scores_file = args.run_dir / "recognition_scores.json"
    verdicts = json.loads(scores_file.read_text(encoding="utf-8")).get("describe", {}) if scores_file.exists() else {}

    entries = [dict(c) for c in manifest["clips"]] + [dict(c, control=True) for c in manifest.get("controls", [])]
    confusion: dict[str, dict[str, int]] = {}
    clips, n_ok, n_all, inc_ok, inc_all, ctl_ok, ctl_all, consistent, pairs = [], 0, 0, 0, 0, 0, 0, 0, 0
    for e in entries:
        cam_rows = [r for r in rows if r["camera"] == e["camera"]]
        accept = e.get("accept", [e["label"]])
        classify = []
        for r in (r for r in cam_rows if r["label"] == "classify" and r["progress"] == "Completed"):
            parsed = parse_label(r["response"], labels)
            classify.append({"raw": r["response"], "parsed": parsed, "correct": parsed in accept, "total": r["total"]})
            confusion.setdefault(e["label"], {}).setdefault(parsed, 0)
            confusion[e["label"]][parsed] += 1
            n_all += 1; n_ok += parsed in accept
            if e.get("control"):
                ctl_all += 1; ctl_ok += parsed in accept
            else:
                inc_all += 1; inc_ok += parsed in accept
        if len(classify) >= 2:
            pairs += 1; consistent += classify[0]["parsed"] == classify[1]["parsed"]
        describe = next((r for r in cam_rows if r["label"] == "describe"), None)
        windows = {r["clip_s"] for r in cam_rows}
        clips.append({**e, "classify": classify, "describe": describe, "verdict": verdicts.get(e["camera"]),
                      "window": "/".join(str(w) for w in sorted(windows)) or "–"})

    desc_scores = [v["score"] for v in verdicts.values()]
    totals = sorted(r["total"] for r in rows if r["progress"] == "Completed" and r.get("total") is not None)
    tiles = [
        {"label": "Incident clips classified correctly", "value": f"{inc_ok} / {inc_all}", "note": f"{round(100 * inc_ok / inc_all) if inc_all else 0}% of answers, accepted alternatives included"},
        {"label": "Controls classified correctly", "value": f"{ctl_ok} / {ctl_all}", "note": "4 normal scenes should be NONE, vandalism VANDALISM"},
        {"label": "Same answer both times", "value": f"{consistent} / {pairs}", "note": "clips whose two classification answers agree"},
        {"label": "Descriptions that caught the incident", "value": f"{sum(desc_scores):g} / {len(desc_scores)}" if desc_scores else "–", "note": "judged against the ground truth (½ for partly)"},
        {"label": "Median time to answer", "value": f"{totals[len(totals) // 2]:.1f} s" if totals else "–", "note": f"{len(totals)} completed requests"},
    ]
    subtitle = (f"{args.run_dir.name} · {len(rows)} Hafnia requests · default model · one-word classification "
                f"({', '.join(labels)}) twice per clip, plus a free description of each incident clip")
    data = {"labels": labels, "confusion": confusion, "clips": clips, "tiles": tiles, "caveats": CAVEATS}
    page = (PAGE.replace("__SUBTITLE__", html.escape(subtitle))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    out = args.run_dir / "recognition.html"
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out}  (incidents {inc_ok}/{inc_all}, controls {ctl_ok}/{ctl_all}, consistent {consistent}/{pairs})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
