r"""run_clearway.py - the Clearway service (clearway/service.py) on live cameras.

    .venv\Scripts\python.exe scripts\run_clearway.py [--cameras ...] [--minutes 5] [--answers standin|hafnia]
                                                   [--max-requests 10] [--stop-at 450] [--no-lens] [--out DIR]
                                                   [--alarms [--close-alarms-at-end] [--close-after S]]

--answers standin (default): a dry run, no Hafnia requests. The offline replay's stand-in (scripts/eval_ledger.py)
answers LATENCY_S after the lens clip has played: the camera's category when the clip (2 s before the change started
to 3 s after the report) overlaps the incident's lasting state by at least 1 s, NONE otherwise. Live, where the camera
is in its loop is found by matching each frame to the clip's own frames (thumbnails; test harness only: a real camera
has no loop). Cameras without a known incident state are answered NONE.
--answers hafnia: one request per question, on lens_1 over the clip's span (HafniaAnswers); at most --max-requests in
this run, none once today's count reaches --stop-at. The planned count is printed before anything starts.
--alarms: carry out the ledger's effects in XProtect (clearway/alarms.py: one alarm per incident on its camera,
snapshot, bookmarks on the camera and on lens_1; closed once the incident stayed cleared); a dry run's alarms are
named "[dry run] ...". --close-alarms-at-end (test harness) closes the alarms still open when the run ends;
--close-after S (test harness) shortens the ledger's close_after_s (60 s), so that loops close and reopen alarms.
Default cameras: the organizers' six incident cameras; --real cameras use the real-camera detector setting. Writes
run\clearway-<dry|live>-<UTC>\ (ledger.jsonl, service.jsonl, incidents.json). Needs the lens (scripts\start_lens.ps1)
unless --no-lens.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import sys
import threading
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from clearway.ledger import Params  # noqa: E402
from clearway.service import HafniaAnswers, Question, Service  # noqa: E402
from eval_change import CASES, frames  # noqa: E402
from eval_ledger import LATENCY_S, TRUTH  # noqa: E402
from hafnia.xprotect_rest import XProtect  # noqa: E402
from tier0.change import ChangeParams  # noqa: E402

INCIDENT_CAMERAS = ["vehicle_breakdown_traffic_queue", "bin_pushed_over_onto_sidewalk", "escooter_left_across_sidewalk",
                    "school_gate_break_in_night", "person_on_railway_tracks", "graffiti_on_standing_train"]
FPS = 10


class LoopStandIn:
    """Test harness only: answers as the offline replay's stand-in did, with each camera's place in its loop found by
    matching live frames to the clip's own frames (whole-frame grey thumbnails, nearest one).

    It also holds each looped camera's detector back until its loop starts (observe returns False until then), as in
    the offline replay: a real camera is watching before an incident happens. Started in mid-loop, the detector's
    warm-up background held part of the incident: 13 of 17 questions came in the first loop, and on two cameras the
    changes never closed because the spot never looked as it did during the warm-up (2026-10-25)."""
    THUMB = (64, 36)

    def __init__(self, cameras: list[str], latency_s: float = LATENCY_S):
        self.latency_s = latency_s
        self.refs: dict[str, tuple[np.ndarray, float, tuple[float, float]]] = {}
        self.offsets: dict[str, deque[tuple[float, float]]] = {c: deque(maxlen=3000) for c in cameras}
        self.lock = threading.Lock()     # cameras' threads add, answer threads read
        self.started: set[str] = set()   # cameras whose detector runs (their loop has started once)
        self.last_index: dict[str, int] = {}
        for c in cameras:
            if c not in CASES or c not in TRUTH:
                continue
            path, annexb, loop_s, state, _ = CASES[c]
            if loop_s > 60 or state is None or not path.exists():
                continue
            thumbs = np.stack([self._thumb(f) for f in frames(path, annexb, width=160)])
            self.refs[c] = (thumbs, loop_s, state)

    @classmethod
    def _thumb(cls, img: np.ndarray) -> np.ndarray:
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.resize(g, cls.THUMB, interpolation=cv2.INTER_AREA).astype(np.float32).ravel()

    def observe(self, camera: str, t: float, frame: np.ndarray) -> bool | None:
        ref = self.refs.get(camera)
        if ref is None:
            return None
        thumbs, loop_s, _ = ref
        i = int(np.argmin(np.abs(thumbs - self._thumb(frame)).mean(axis=1)))
        with self.lock:
            self.offsets[camera].append((t, (t - i / FPS) % loop_s))    # when the loop (re)started, modulo its length
            prev = self.last_index.get(camera)
            self.last_index[camera] = i
            # the loop starts: its first frames, or the index jumping back (the gate's stream never delivers its
            # first 5 frames: 149 -> 5, 2026-10-25)
            if camera not in self.started and (i <= 2 or (prev is not None and prev - i > len(thumbs) // 2)):
                self.started.add(camera)
            return camera in self.started

    def loop_start(self, camera: str, t0: float, t1: float) -> tuple[float, float]:
        """(the loop's start time modulo its length, share of frames agreeing within 0.3 s) around [t0, t1]."""
        _, loop_s, _ = self.refs[camera]
        with self.lock:
            offs = np.array([o for t, o in self.offsets[camera] if t0 - 30 <= t <= t1 + 5])
        if len(offs) == 0:
            return float("nan"), 0.0
        n = round(loop_s * FPS)
        hist = np.bincount(np.round(offs * FPS).astype(int) % n, minlength=n)
        smooth = sum(np.roll(hist, k) for k in range(-2, 3))
        centre = int(np.argmax(smooth)) / FPS
        d = (offs - centre + loop_s / 2) % loop_s - loop_s / 2      # signed distance on the circle
        near = np.abs(d) <= 0.3
        return (centre + float(d[near].mean())) % loop_s, float(near.mean())

    def __call__(self, q: Question) -> dict:
        time.sleep(self.latency_s)
        return self.judge(q)

    def judge(self, q: Question) -> dict:
        if q.camera not in self.refs:
            return {"category": "NONE", "standin": "no known incident state"}
        _, loop_s, (s0, s1) = self.refs[q.camera]
        off, match = self.loop_start(q.camera, q.w0, q.w1)
        if math.isnan(off):
            return {"category": None, "reason": "stand-in: no frames matched"}
        seen = 0.0
        k0 = math.floor((q.w0 - off) / loop_s) - 1
        for k in range(k0, k0 + 3 + math.ceil((q.w1 - q.w0) / loop_s)):
            a, b = off + k * loop_s + s0, off + k * loop_s + min(s1, loop_s)
            seen += max(0.0, min(q.w1, b) - max(q.w0, a))
        cat = TRUTH[q.camera] if seen >= 1.0 else "NONE"
        return {"category": cat, "standin": True, "seen_s": round(seen, 2), "loop_start": round(off, 2),
                "phase_match": round(match, 2)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cameras", nargs="+", default=INCIDENT_CAMERAS)
    ap.add_argument("--real", nargs="*", default=["test_11"], help="cameras that get the real-camera detector setting")
    ap.add_argument("--minutes", type=float, default=5)
    ap.add_argument("--answers", choices=["standin", "hafnia"], default="standin")
    ap.add_argument("--max-requests", type=int, default=10, help="Hafnia requests in this run (--answers hafnia)")
    ap.add_argument("--stop-at", type=int, default=450, help="ask no more once today's count reaches this")
    ap.add_argument("--no-lens", dest="lens", action="store_false", help="do not play clips on lens_1 (stand-in only)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--alarms", action="store_true", help="raise, reopen and close XProtect alarms and bookmarks")
    ap.add_argument("--close-alarms-at-end", action="store_true", help="test harness: close open alarms at the end")
    ap.add_argument("--close-after", type=float, help="test harness: the ledger's close_after_s")
    args = ap.parse_args()
    mode = "dry" if args.answers == "standin" else "live"
    out = args.out or REPO / "run" / f"clearway-{mode}-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"

    known = XProtect().cameras()
    missing = [c for c in args.cameras + (["lens_1"] if args.lens else []) if c not in known]
    if missing:
        sys.exit(f"unknown cameras: {missing}")
    on_frame = None
    if args.answers == "hafnia":
        if not args.lens:
            sys.exit("--answers hafnia asks about the lens clip: drop --no-lens")
        from hafnia.gateway import Gateway
        from lens_compare import gateway_password
        gw = Gateway()
        gw.login(gateway_password())
        quota = gw.quota()
        if quota and quota["DailySummaryCount"] + args.max_requests > args.stop_at:
            sys.exit(f"today's count is {quota['DailySummaryCount']}: {args.max_requests} more would pass "
                     f"--stop-at {args.stop_at}")
        hafnia = HafniaAnswers(gw, known["lens_1"], args.max_requests, args.stop_at)
        shadow = LoopStandIn(args.cameras)
        on_frame = shadow.observe

        def answer(q: Question) -> dict:
            """Hafnia's answer, with what the stand-in expects (no request) to score it against."""
            return {**hafnia(q), "expected": shadow.judge(q)}
        print(f"live run: at most {args.max_requests} Hafnia requests (today's count "
              f"{quota['DailySummaryCount'] if quota else 'unknown'})", flush=True)
    else:
        answer = LoopStandIn(args.cameras)
        on_frame = answer.observe
        print(f"dry run: no Hafnia requests; stand-in for {sorted(answer.refs)}", flush=True)
    cameras = {c: ChangeParams.real() if c in args.real else ChangeParams.loops() for c in args.cameras}
    params = Params() if args.close_after is None else Params(close_after_s=args.close_after)
    service = Service(cameras, answer, out, lens=args.lens, params=params, on_frame=on_frame,
                      echo=lambda s: print(s, flush=True), close_alarms_at_end=args.close_alarms_at_end)
    if args.alarms:
        from clearway.alarms import XProtectAlarms
        service.alarms = XProtectAlarms(known, known.get("lens_1") if args.lens else None, service.log,
                                        label="[dry run] " if mode == "dry" else "")
    service.run(args.minutes)
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
