"""Tier 1: ask Hafnia about an event-centred window and parse a one-word verdict.

The prompt is the one measured in run/bench-20261018b: with 6 s windows centred on the impact it answered ACCIDENT
10 of 10 times on accident clips, and NONE on all normal-traffic controls in run/bench-20261018.
"""
from __future__ import annotations

import datetime as dt
import re
import time
from dataclasses import dataclass

from hafnia.gateway import Gateway, Tracked, video_uri

CLASSIFY = ("What kind of incident, if any, happens in this video? Reply with exactly one word from this list: "
            "ACCIDENT (a traffic collision or crash), ROBBERY, SHOOTING, ARSON, VANDALISM, FIGHT, NONE.")
DESCRIBE = "Describe what happens in this video."
LABELS = ("ACCIDENT", "ROBBERY", "SHOOTING", "ARSON", "VANDALISM", "FIGHT", "NONE")


@dataclass
class Verdict:
    confirmed: bool
    label: str
    answer: str
    summary_id: str
    seconds: float
    error: str = ""


def parse(answer: str) -> str:
    hits = [(m.start(), lab) for lab in LABELS for m in re.finditer(rf"\b{lab}\b", (answer or "").upper())]
    return min(hits)[1] if hits else "OTHER"


def ask(gw: Gateway, camera_id: str, start: dt.datetime, end: dt.datetime, prompt: str, timeout: float = 600
        ) -> tuple[dict, float]:
    """One Hafnia request; waits for Completed or Failed. A window ending in the future waits for the recording."""
    t0 = time.monotonic()
    created = gw.ask(video_uri(camera_id, start, end), prompt)
    tracked = Tracked(created["Id"], submitted=t0, summary=created)
    gw.wait_all([tracked], poll=1.0, timeout=timeout)
    return tracked.summary, time.monotonic() - t0


def verify(gw: Gateway, camera_id: str, start: dt.datetime, end: dt.datetime) -> Verdict:
    summary, secs = ask(gw, camera_id, start, end, CLASSIFY)
    if summary.get("Progress") != "Completed":
        return Verdict(False, "FAILED", "", summary.get("Id", ""), secs, summary.get("LastError", "not completed"))
    answer = summary.get("Response", "")
    label = parse(answer)
    return Verdict(label == "ACCIDENT", label, answer, summary["Id"], secs)


def describe(gw: Gateway, camera_id: str, start: dt.datetime, end: dt.datetime) -> tuple[str, float]:
    summary, secs = ask(gw, camera_id, start, end, DESCRIBE)
    return (summary.get("Response") or summary.get("LastError") or ""), secs
