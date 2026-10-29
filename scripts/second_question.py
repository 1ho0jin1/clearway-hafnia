r"""second_question.py - Hafnia's AlertValidation shape as a second question: the service's own answer (its category)
becomes the upstream alert, and Hafnia is asked to confirm or discard it on the same recorded span (2026-10-29).

    .venv\Scripts\python.exe scripts\second_question.py plan  [--out run\validate-20261029]
    .venv\Scripts\python.exe scripts\second_question.py ask   run\validate-20261029 [--stop-at 450] [--dry-run]
    .venv\Scripts\python.exe scripts\second_question.py score run\validate-20261029

Why: Hafnia VLM was fine-tuned on an AlertValidation task (an upstream alert in, confirm or discard out; the trained
wording is not published). As a first question with a generic alert (prompt experiment cell D, 2026-10-28) the shape
confirmed nothing false and confirmed all five High-priority incidents, but discarded 10 of 18 incidents: a strict
verifier. The candidate use is a second question before a High-priority alarm: the open question first, then, when
its answer names an incident, that category put to the model as the upstream alert. Both sides are measured here:

- the hold-out's false cards (run/holdout-20261029: 31 answers that named an incident on real streets where there
  was none; a discard is right), and
- the prompt experiment's true incidents (run/prompt-20261028T1605Z, cell A: 18 answers that named the incident the
  clip shows; a confirm is right).

49 requests. Pre-registered: the prompt is cell D's alert prompt with the alert line naming the first answer's
category; nothing else differs; one shot. The hold-out set is a tuning set from now on, so a design adopted on this
result still has to be confirmed on footage neither run used.

plan: writes plan.jsonl from the two runs' results. ask: one request per planned clip on lens_1's recorded span, the
gateway's system prompt as it is (empty; refused otherwise); resumable; the plan and today's count are printed first
and --dry-run stops there. score: README.md (the text above the marker is kept), answers.md, summary.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.ledger import OWNERS  # noqa: E402
from prompt_experiment import CATEGORY_LINES, PARALLEL, parse_answer, utc_now  # noqa: E402

HOLDOUT = REPO / "run" / "holdout-20261029"
PROMPT_RUN = REPO / "run" / "prompt-20261028T1605Z"
DEFAULT_OUT = REPO / "run" / "validate-20261029"
TABLES_MARK = "<!-- tables: written by second_question.py score; the text above is kept -->"

# Cell D's alert prompt (scripts/prompt_experiment.py, "alert") with the alert line naming the first answer's category.
ALERT_PROMPT = (
    "You are validating an upstream alert from an automatic change detector on a fixed CCTV camera.\n"
    "Upstream alert: {category} at the spot shown in this clip, confidence 0.60. The alert does not say more; the "
    "clip may be a magnified crop of the spot.\n"
    "Validate the alert: confirm it only if the clip clearly shows one of these right-of-way incidents, "
    "otherwise discard it.\n\n"
    "CATEGORIES:\n" + CATEGORY_LINES + "\n\n"
    "Reply with JSON only, no other text:\n"
    '{"decision": "<confirm or discard>", "category": "<the category when confirm; NONE when discard>", '
    '"confidence": <0.0 to 1.0>, "reason": "<one sentence on what the frames show, in the order it happens>", '
    '"evidence_frames": "<start, middle or end of the clip>", '
    '"object": "<the main object or person involved, at most four words>", "still_present": <true or false>}')


def alert_text(category: str) -> str:
    return ALERT_PROMPT.replace("{category}", category)      # not str.format: the JSON template has braces


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def priority(category: str) -> str:
    return OWNERS[category][1] if category in OWNERS else ""


# --- plan ---------------------------------------------------------------------------------------------------------
def plan(args) -> int:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    hold = [r for r in load_jsonl(HOLDOUT / "results.jsonl") if r.get("progress") == "Completed"]
    for r in hold:
        if r["category"] == "NONE":
            continue
        rows.append({"source": "holdout", "src_k": r["k"], "clip": r["cid"], "view": r["view"],
                     "profile": r["profile"], "span": r["span"], "first": r["category"],
                     "first_summary": (r.get("fields") or {}).get("summary", ""), "truth": r["truth"],
                     "priority": priority(r["category"]), "want": "discard" if r["truth"] == "NONE" else "confirm"})
    prompt = [r for r in load_jsonl(PROMPT_RUN / "results.jsonl") if r.get("cell") == "A"
              and r.get("progress") == "Completed"]
    notes = {}
    for c in load_jsonl(PROMPT_RUN / "clips.jsonl"):
        notes[c["k"]] = c.get("note", "")
    for r in prompt:
        if r["category"] == "NONE":
            continue
        rows.append({"source": "prompt", "src_k": r["k"], "clip": r["avi"], "view": "lens", "profile": "loops",
                     "span": r["span"], "first": r["category"],
                     "first_summary": (r.get("fields") or {}).get("summary", ""), "truth": r["truth"],
                     "note": notes.get(r["k"], ""), "priority": priority(r["category"]),
                     "want": "discard" if r["truth"] == "NONE" else "confirm"})
    for k, row in enumerate(rows, 1):
        row["k"] = k
    with (out / "plan.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out / "prompt.json").write_text(json.dumps({"template": ALERT_PROMPT, "example": alert_text("STALLED_VEHICLE")},
                                                indent=1, ensure_ascii=False), encoding="utf-8")
    by = Counter((r["source"], r["want"], r["priority"]) for r in rows)
    print(f"{len(rows)} second questions planned: "
          f"{sum(r['source'] == 'holdout' for r in rows)} hold-out false cards (a discard is right), "
          f"{sum(r['source'] == 'prompt' for r in rows)} true incidents of the prompt experiment (a confirm is right)")
    for (source, want, prio), n in sorted(by.items()):
        print(f"  {source:8} want {want:8} {prio or '-':7} {n}")
    print(f"wrote {out / 'plan.jsonl'} and prompt.json")
    return 0


# --- ask ----------------------------------------------------------------------------------------------------------
def ask(args) -> int:
    from hafnia.gateway import Gateway, Tracked, video_uri
    from hafnia.xprotect_rest import XProtect
    from lens_compare import gateway_password
    run = args.run
    rows = load_jsonl(run / "plan.jsonl")
    done = {r["k"] for r in load_jsonl(run / "results.jsonl") if r.get("progress") == "Completed"}
    todo = [r for r in rows if r["k"] not in done]
    print(f"{len(todo)} requests planned, one per clip with the alert prompt ({len(rows)} planned, "
          f"{len(done)} answered already)")
    if args.dry_run:
        return 0
    gw = Gateway()
    gw.login(gateway_password())
    q = gw.quota() or {}
    q0 = q.get("DailySummaryCount")
    print(f"today's count before: {q0} of {q.get('DailySummaryQuota')}")
    if q0 is not None and q0 + len(todo) > args.stop_at:
        sys.exit(f"{len(todo)} more would pass --stop-at {args.stop_at}")
    system = gw.system_prompt()
    if system:
        sys.exit(f"the gateway's system prompt is not empty ({system!r}): the service runs without one")
    lens_id = XProtect().cameras()["lens_1"]
    n_done = 0
    try:
        with (run / "results.jsonl").open("a", encoding="utf-8") as f:
            for i in range(0, len(todo), PARALLEL):
                tracked = []
                for c in todo[i:i + PARALLEL]:
                    start = dt.datetime.fromisoformat(c["span"][0])
                    end = dt.datetime.fromisoformat(c["span"][1])
                    text = alert_text(c["first"])
                    t0 = time.monotonic()
                    created = gw.ask(video_uri(lens_id, start, end), text)
                    tracked.append((c, Tracked(created["Id"], submitted=t0, summary=created)))
                gw.wait_all([t for _, t in tracked], poll=1.0, timeout=600)
                for c, t in tracked:
                    s = t.summary
                    answer = s.get("Response") or ""
                    p = parse_answer(answer) if answer else {"category": "UNPARSED", "json_ok": False}
                    decision = str(p.get("decision", "")).lower() or ("discard" if p["category"] == "NONE" else "")
                    secs = round(time.monotonic() - t.submitted, 1)
                    rec = {**{a: c[a] for a in ("k", "source", "src_k", "clip", "view", "profile", "span", "first",
                                                 "truth", "priority", "want")},
                           "summary_id": t.id, "progress": s.get("Progress"), "error": s.get("LastError"),
                           "response": answer, "decision": decision, "category": p["category"],
                           "json_ok": p.get("json_ok", False),
                           "fields": {a: b for a, b in p.items() if a not in ("category", "json_ok", "decision")},
                           "seconds": secs, "phases": {k: round(v - t.submitted, 1) for k, v in t.seen.items()},
                           "chars": len(answer), "wall": utc_now().isoformat()}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    n_done += s.get("Progress") == "Completed"
                    mark = "ok" if decision == c["want"] else "WRONG"
                    print(f"  {c['k']:2d} {c['source']:7} {str(c['clip'])[:30]:30} {c['first']:16} -> "
                          f"{decision or '?':8} {p['category']:16} {mark:5} ({s.get('Progress')}, {secs} s) "
                          f"{str(p.get('reason') or '')[:80]}", flush=True)
    finally:
        q1 = (gw.quota() or {}).get("DailySummaryCount")
        print(f"today's count after: {q1} ({n_done} completed here)")
        gw.logout()
    return 0


# --- score --------------------------------------------------------------------------------------------------------
def tally(rows: list[dict]) -> dict:
    done = [r for r in rows if r.get("progress") == "Completed"]
    return {"asked": len(rows), "answered": len(done), "failed": len(rows) - len(done),
            "right": sum(r["decision"] == r["want"] for r in done),
            "confirmed": sum(r["decision"] == "confirm" for r in done),
            "discarded": sum(r["decision"] == "discard" for r in done),
            "other": sum(r["decision"] not in ("confirm", "discard") for r in done),
            "category_kept": sum(r["decision"] == "confirm" and r["category"] == r["first"] for r in done),
            "category_right": sum(r["decision"] == "confirm" and r["category"] == r["truth"] for r in done),
            "json_ok": sum(bool(r.get("json_ok")) for r in done)}


def score(args) -> int:
    run = args.run
    rows = load_jsonl(run / "results.jsonl")
    by_k = {}
    for r in rows:                                   # the last answer per k counts (a retry after a failure)
        if r.get("progress") == "Completed" or r["k"] not in by_k:
            by_k[r["k"]] = r
    rows = [by_k[k] for k in sorted(by_k)]
    plan_rows = {r["k"]: r for r in load_jsonl(run / "plan.jsonl")}
    sets = {
        "hold-out false cards (a discard is right)": [r for r in rows if r["source"] == "holdout"],
        "... of which High priority (the alarm gate)": [r for r in rows if r["source"] == "holdout"
                                                         and r["priority"] == "High"],
        "true incidents (a confirm is right)": [r for r in rows if r["source"] == "prompt"],
        "... of which High priority": [r for r in rows if r["source"] == "prompt" and r["priority"] == "High"],
        "all": rows,
    }
    summary = {name: tally(rs) for name, rs in sets.items()}
    by_first = {}
    for r in rows:
        key = (r["source"], r["first"])
        by_first.setdefault(key, []).append(r)
    summary["by_first_category"] = {f"{s}/{c}": tally(rs) for (s, c), rs in sorted(by_first.items())}
    by_view = {}
    for r in rows:
        if r["source"] == "holdout":
            by_view.setdefault(r["view"], []).append(r)
    summary["holdout_by_view"] = {v: tally(rs) for v, rs in sorted(by_view.items())}
    confs = [r["fields"].get("confidence") for r in rows if r.get("progress") == "Completed"]
    confs = [float(c) for c in confs if isinstance(c, (int, float))]
    summary["confidence"] = {"n": len(confs), "min": min(confs) if confs else None, "max": max(confs) if confs else None,
                             "mean": round(sum(confs) / len(confs), 3) if confs else None}
    summary["evidence_frames"] = dict(Counter(str(r["fields"].get("evidence_frames")) for r in rows
                                              if r.get("progress") == "Completed"))
    (run / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    def table(name_rows: list[tuple[str, list[dict]]]) -> str:
        s = ("| Set | Asked | Answered | Right | Confirmed | Discarded | Other | Category kept on confirm | Valid JSON |\n"
             "|---|---|---|---|---|---|---|---|---|\n")
        for name, rs in name_rows:
            t = tally(rs)
            s += (f"| {name} | {t['asked']} | {t['answered']} | {t['right']} | {t['confirmed']} | {t['discarded']} | "
                  f"{t['other']} | {t['category_kept']} | {t['json_ok']} |\n")
        return s

    text = (f"{len(rows)} second questions asked ({summary['all']['answered']} answered, "
            f"{summary['all']['failed']} failed) with the alert prompt (`prompt.json`) on the spans the first answers "
            f"were about; the gateway's system prompt empty.\n\n"
            "## The verdicts\n\n" + table(list(sets.items())) +
            "\n## By the first answer's category\n\n" +
            table([(f"{s} / {c} ({priority(c) or '-'})", rs) for (s, c), rs in sorted(by_first.items())]) +
            "\n## The hold-out false cards by view\n\n" +
            table([(v, rs) for v, rs in sorted(by_view.items())]) +
            f"\nConfidence: {summary['confidence']}. Evidence frames: {summary['evidence_frames']}.\n\n"
            "## Every second question\n\n"
            "| # | Source | Clip | First answer | Truth | Want | Decision | Category | Reason |\n|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        if r.get("progress") != "Completed":
            text += (f"| {r['k']} | {r['source']} | {r['clip']} | {r['first']} | {r['truth']} | {r['want']} | "
                     f"failed | | {str(r.get('error') or '')[:80]} |\n")
            continue
        mark = "" if r["decision"] == r["want"] else " **wrong**"
        reason = str(r["fields"].get("reason") or "").replace("|", "/").replace("\n", " ")
        text += (f"| {r['k']} | {r['source']} | {r['clip']} | {r['first']} | {r['truth']} | {r['want']} | "
                 f"{r['decision']}{mark} | {r['category']} | {reason[:220]} |\n")
    readme = run / "README.md"
    head = ""
    if readme.exists():
        old = readme.read_text(encoding="utf-8")
        head = old.split(TABLES_MARK)[0] if TABLES_MARK in old else old
    if not head.strip():
        head = "# The AlertValidation shape as a second question (2026-10-29)\n\n"
    readme.write_text(head.rstrip() + "\n\n" + TABLES_MARK + "\n\n" + text, encoding="utf-8")
    ans = "# The second question's answers\n\n"
    for r in rows:
        p = plan_rows.get(r["k"], {})
        ans += (f"## {r['k']}. {r['source']} {r['clip']} — first answer {r['first']}, truth {r['truth']}, "
                f"want {r['want']}\n\n"
                f"First answer's summary: {p.get('first_summary', '')}\n\n"
                + (f"Note: {p['note']}\n\n" if p.get("note") else "")
                + f"Decision: **{r.get('decision')}** ({r.get('category')}; {r.get('progress')}, {r.get('seconds')} s)\n\n"
                f"```\n{r.get('response') or r.get('error') or ''}\n```\n\n")
    (run / "answers.md").write_text(ans, encoding="utf-8")
    for name, t in summary.items():
        if isinstance(t, dict) and "asked" in t:
            print(f"{name}: {t['answered']} answered, {t['right']} right, {t['confirmed']} confirmed, "
                  f"{t['discarded']} discarded, {t['other']} other")
    print(f"wrote {readme}, answers.md, summary.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="stage", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.set_defaults(fn=plan)
    a = sub.add_parser("ask")
    a.add_argument("run", type=Path)
    a.add_argument("--stop-at", type=int, default=450)
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(fn=ask)
    s = sub.add_parser("score")
    s.add_argument("run", type=Path)
    s.set_defaults(fn=score)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
