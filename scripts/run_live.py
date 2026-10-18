r"""run_live.py - the end-to-end pipeline on live XProtect cameras.

    .venv\Scripts\python.exe scripts\run_live.py --cameras test_04 traffic_flows_in_the_open_lanes --minutes 5

FrameBridge (full-rate live frames) -> tier 0 per camera -> router -> an unverified Low alarm at once, with a
snapshot of the candidate -> Hafnia on the 6 s window centred on the event -> the alarm is raised to High (Hafnia's
description in its history, plus a bookmark), or closed as a false alarm. Everything is logged to
run/live-<UTC time>/events.jsonl.

Hafnia cost: 1 request per routed candidate, plus 1 description per confirmed accident. The router's run cap
(--max-requests, default 10) and the gateway's daily count (--stop-at, default 450) bound it.
The gateway password comes from HAFNIA_GW_PASSWORD (process or user environment); it is never printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from hafnia.gateway import Gateway  # noqa: E402
from hafnia.xprotect_rest import XProtect  # noqa: E402
from incident.bridge import FrameBridge  # noqa: E402
from incident.router import Router, RouterConfig  # noqa: E402
from incident.verify import describe, verify  # noqa: E402
from tier0.pipeline import Tier0  # noqa: E402

HALF_WINDOW = dt.timedelta(seconds=3)   # 6 s event-centred window (run/bench-20261018b)


def gateway_password() -> str:
    pw = os.environ.get("HAFNIA_GW_PASSWORD")
    if not pw:   # shells started before the variable was set do not inherit it: read the user environment
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            pw = winreg.QueryValueEx(k, "HAFNIA_GW_PASSWORD")[0]
    return pw


class Run:
    def __init__(self, args):
        self.args = args
        self.out = REPO / "run" / f"live-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
        self.out.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.xp = XProtect()
        self.cam_ids = self.xp.cameras()
        missing = [c for c in args.cameras if c not in self.cam_ids]
        if missing:
            sys.exit(f"unknown cameras: {missing}")
        self.gw = Gateway()
        self.gw.login(gateway_password())
        self.router = Router(RouterConfig(max_requests=args.max_requests))
        self.pool = ThreadPoolExecutor(max_workers=4)
        self.pending = []

    def log(self, event: str, **fields) -> None:
        rec = {"type": event, "wall": dt.datetime.now(dt.timezone.utc).isoformat(), **fields}
        with self.lock, (self.out / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        brief = {k: v for k, v in fields.items() if k not in ("answer", "description")}
        print(f"{rec['wall'][11:23]} {event:10} {json.dumps(brief, default=str)[:180]}", flush=True)

    def budget_left(self) -> int | None:
        q = self.gw.quota()
        return None if q is None else self.args.stop_at - q["DailySummaryCount"]

    def snapshot(self, frame: np.ndarray, boxes: np.ndarray, text: str) -> bytes:
        img = frame.copy()
        for x1, y1, x2, y2 in boxes.astype(int):
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(img, text, (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()

    def on_candidate(self, camera: str, cand, frame: np.ndarray, boxes: np.ndarray, frame_wall_lag: float) -> None:
        t_event = dt.datetime.fromtimestamp(cand.t, dt.timezone.utc)
        h, w = frame.shape[:2]
        spot = self.router.spot(boxes, w, h) if len(boxes) else (0, 0)
        with self.lock:
            decision = self.router.decide(camera, cand.t, spot, None)
        if decision.send:
            left = self.budget_left()
            if left is not None and left <= 0:
                decision.send, decision.reason = False, "daily budget reached"
        self.log("candidate", camera=camera, t_event=t_event, kind=cand.kind, score=cand.score, spot=spot,
                 detail=cand.detail, send=decision.send, reason=decision.reason, lag_s=round(frame_wall_lag, 2))
        if not decision.send:
            return
        cam_id = self.cam_ids[camera]
        alarm = self.xp.trigger_alarm("Traffic incident? (unverified)",
                                      f"Tier 0: {cand.kind} (score {cand.score}). Hafnia is checking.",
                                      cam_id, t_event, priority="Low", tag="tier0")
        self.xp.attach_snapshot(alarm, self.snapshot(frame, boxes, f"tier 0: {cand.kind}"), w, h)
        self.log("alarm", camera=camera, alarm=alarm, t_event=t_event, priority="Low",
                 since_event_s=round((dt.datetime.now(dt.timezone.utc) - t_event).total_seconds(), 2))
        self.pending.append(self.pool.submit(self.check, camera, cam_id, alarm, t_event, spot, cand.t))

    def check(self, camera, cam_id, alarm, t_event, spot, t_float) -> None:
        start, end = t_event - HALF_WINDOW, t_event + HALF_WINDOW
        try:
            v = verify(self.gw, cam_id, start, end)
        except Exception as e:   # one failed check must not stop the run
            self.log("error", camera=camera, alarm=alarm, error=str(e))
            return
        since = round((dt.datetime.now(dt.timezone.utc) - t_event).total_seconds(), 1)
        self.log("verdict", camera=camera, alarm=alarm, label=v.label, confirmed=v.confirmed, answer=v.answer,
                 hafnia_s=round(v.seconds, 1), since_event_s=since, summary=v.summary_id, error=v.error)
        with self.lock:
            if v.label != "FAILED":
                self.router.feedback(camera, t_float, spot, v.confirmed)
        if v.label == "FAILED":
            self.xp.update_alarm(alarm, f"Hafnia could not check: {v.error[:200]}")
            return
        if not v.confirmed:
            self.xp.update_alarm(alarm, f"Hafnia: no traffic accident ({v.label}). Closed as a false alarm.",
                                 state="Closed")
            return
        self.xp.update_alarm(alarm, "Hafnia confirmed a traffic accident.", priority="High")
        text = ""
        left = self.budget_left()
        if self.args.describe and (left is None or left > 0):
            text, secs = describe(self.gw, cam_id, start, end)
            self.log("describe", camera=camera, alarm=alarm, description=text, hafnia_s=round(secs, 1))
            self.xp.update_alarm(alarm, ("Hafnia: " + text)[:1000])
        ref = self.xp.create_bookmark(cam_id, "Traffic accident (Hafnia confirmed)",
                                      "This summary is AI-generated: " + (text or v.answer), start, end, t_event)
        self.log("bookmark", camera=camera, alarm=alarm, reference=ref)

    def run(self) -> None:
        bridge = FrameBridge(self.args.cameras, log=lambda s: print(s, flush=True))
        t0s = {c: Tier0(conf=0.25) for c in self.args.cameras}
        seen = {c: 0 for c in self.args.cameras}
        stats = {c: [0, 0.0] for c in self.args.cameras}
        stop = time.monotonic() + 60 * self.args.minutes
        last_report = time.monotonic()
        try:
            for camera, when, jpeg in bridge.frames():
                if time.monotonic() > stop:
                    break
                frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                t = when.timestamp()
                tier0 = t0s[camera]
                tier0.feed(t, frame)
                lag = time.time() - t
                stats[camera][0] += 1
                stats[camera][1] = lag
                cands = tier0.detector.candidates
                for cand in cands[seen[camera]:]:
                    boxes = np.array([tier0.detector.tracks[k].box() for k in cand.tracks
                                      if k in tier0.detector.tracks]).reshape(-1, 4)
                    self.on_candidate(camera, cand, frame, boxes, lag)
                seen[camera] = len(cands)
                if time.monotonic() - last_report > 15:
                    last_report = time.monotonic()
                    self.log("health", **{c: {"frames": n, "lag_s": round(lg, 2)} for c, (n, lg) in stats.items()})
        finally:
            bridge.close()
            for f in self.pending:
                f.result()
            self.pool.shutdown()
            self.log("end", requests=self.router.requests)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cameras", nargs="+", required=True)
    ap.add_argument("--minutes", type=float, default=5)
    ap.add_argument("--max-requests", type=int, default=10, help="classification requests in this run")
    ap.add_argument("--stop-at", type=int, default=450, help="stop asking when today's count reaches this")
    ap.add_argument("--no-describe", dest="describe", action="store_false",
                    help="skip the description request for confirmed accidents")
    Run(ap.parse_args()).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
