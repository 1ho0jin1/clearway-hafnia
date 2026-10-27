"""The question Hafnia is asked about each clip, and how its answer is read.

Plan C's JSON prompt with definitions (30 of 30 categories right in run/pilot-20261023T162040Z), plus COLLISION
(gate G3, run/lens-test_11-20261024T110155Z; regression check run/pilot-20261024T111134Z). Since 2026-10-27 each
definition also says what it is not: the label had followed the object rather than the act (graffiti being painted
next to a platform was filed OBSTRUCTION with a summary that said "graffiti"). Checked by asking the clean live
run's 14 spans again (scripts/reask.py, run/clearway-live-20261027T124112Z-clean/reask-negatives.jsonl): the
graffiti became DAMAGE, the twelve right answers stayed, and a clip of the wrong seconds stayed NONE; the variant
that asks for the summary before the category did not fix the graffiti. The categories map to owners in
clearway/ledger.py (OWNERS); NONE dismisses the change.
"""
from __future__ import annotations

import json
import re

CATEGORIES = ("PERSON_ON_TRACKS", "COLLISION", "STALLED_VEHICLE", "OBSTRUCTION", "DAMAGE", "TAMPERING", "NONE")
PROMPT = (
    'Reply with JSON only, no other text: {"category": "...", "object": "...", "where": "...", "still_present": '
    'true or false, "summary": "..."}. category is exactly one of: PERSON_ON_TRACKS (a person on railway tracks, '
    'not on a platform), COLLISION (a vehicle hits another vehicle, a person, a barrier or an object, or spins out '
    'of control), STALLED_VEHICLE (a vehicle stopped or broken down in a traffic lane; not a vehicle parked at a '
    'kerb or queued behind others), OBSTRUCTION (an object left lying across a pavement, path or road so that '
    'people or vehicles cannot pass; not someone painting, breaking or forcing something), DAMAGE (property '
    'damaged or defaced: graffiti being painted, glass broken, a surface cut or burnt; choose this even if the '
    'damaged thing is next to a path), TAMPERING (someone forcing, cutting or picking a lock, gate or door), NONE '
    '(none of these: ordinary traffic, people walking, parked vehicles, a stationary train). object: the main '
    'object or person involved, at most four words. where: one of track, lane, pavement, platform, other. '
    'still_present: whether that object or person is still there at the end of the video. summary: one sentence '
    'on what happens, in the order it happens.')


def parse(answer: str) -> dict:
    """The JSON answer, or what can be recovered from it; category falls back to the first category word."""
    m = re.search(r"\{.*\}", answer or "", re.S)
    out = {}
    if m:
        try:
            out = json.loads(m.group(0))
        except json.JSONDecodeError:
            out = {}
    cat = str(out.get("category", "")).upper()
    if cat not in CATEGORIES:
        hits = [(answer.upper().find(c), c) for c in CATEGORIES if c in (answer or "").upper()]
        cat = min(hits)[1] if hits else "UNPARSED"
    out["category"] = cat
    out["json_ok"] = bool(m) and "summary" in out
    return out
