"""The Clearway service (docs/PRODUCT.md, F2): live cameras in, the ledger's decisions out.

    service = Service({"bin_pushed_over_onto_sidewalk": ChangeParams.loops()}, answer, out=Path("run/clearway-..."))
    service.run(minutes=5)

One process for all cameras, one thread per camera (decoding and the detector's image work release the GIL: one thread
managed about 4.3 of 10 fps on each of six cameras, 2026-10-25); YOLO and SigLIP share the GPU behind a lock. A camera
that falls more than QUEUE frames behind skips its oldest frames (counted as dropped). Per frame (FrameBridge, 10 fps
per camera):
1. the change detector (tier0/change.py) on the frame scaled to 640 px, people held back (YOLO11m, run only when a
   change is about to be reported); on a camera with a danger zone (tier0/zones.py, config/zones.json) also YOLO on
   every ZONE_EVERY-th frame, and a person's feet inside the zone for its dwell time reported like a change;
2. each reported change's crop is embedded with SigLIP 2 (tier0/memory.py) and given to the ledger
   (clearway/ledger.py), which decides: a piece of a known occurrence, a recurrence of a known incident, a known
   rejection (held, and asked about after all if it stays: Ledger.tick, every second), or a question;
3. a question, on a worker thread: the event window (2 s before the change started to 3 s after it was reported, as
   scripts/lens_pilot.py) cropped to the spot and played on the lens camera (lens/client.py), then one answer:
   HafniaAnswers (one request on lens_1 over the clip's span, the JSON prompt of clearway/prompt.py) or a test
   stand-in passed in by the caller;
4. the answer goes back to the ledger. Closed changes go to the ledger too: an incident clears when its largest change
   closes.
The ledger's effects (raise, reopen or close an incident's alarm) are carried out in XProtect by clearway/alarms.py
(XProtectAlarms, F3: one alarm per incident, with a snapshot and bookmarks) when one is given, and logged. Operators'
verdicts on the cards (F7: confirm or reject on the board, clearway/board.py) arrive in <out>/operator.jsonl, which
the board appends to and the service reads every second (Ledger.on_operator).

Writes <out>/ledger.jsonl (the ledger's event log; Ledger.replay rebuilds the state), <out>/service.jsonl (changes,
questions, lens spans, answers, effects, health), <out>/changes.jsonl (every report with its look, and every closing:
the ledger's input, so a live run can be replayed offline with a changed ledger), <out>/snaps/<incident>.jpg (the
camera's frame at the end of each question's clip, the spot boxed; for the board, clearway/board.py) and, at the end,
<out>/incidents.json. Times are frame times (Unix
seconds, UTC) unless named wall.
"""
from __future__ import annotations

import datetime as dt
import json
import queue
import threading
import time
import traceback
from collections import deque
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from clearway.ledger import Ledger, Params
from clearway.prompt import PROMPT, parse
from incident.bridge import FrameBridge
from lens.client import mark, span, submit, wait, zoom
from tier0.change import Change, ChangeDetector, ChangeParams
from tier0.memory import Embedder, crop
from tier0.zones import Zone, ZoneWatch

REPO = Path(__file__).resolve().parent.parent
WORK_WIDTH = 640    # frames for the detector and the look, as in the offline replay (scripts/eval_ledger.py)
BEFORE_S = 2.0      # the lens clip starts this long before the change started ...
AFTER_S = 3.0       # ... and ends this long after it was reported, so the outcome is in it
MAX_CLIP_S = 30.0   # a change reported long after it started (real cameras: at least 15 s) is shown in its last 30 s
KEEP_S = 90.0       # frames kept per camera: an escalated question (30 s after the report) still needs its clip
QUEUE = 50          # frames waiting per camera (5 s); beyond that the oldest are dropped
ZONE_EVERY = 2      # a camera with a danger zone looks for people on every 2nd frame (5 fps)


@dataclass
class Question:
    """One incident's question: what the answerer gets."""
    incident: str
    camera: str
    change: int
    t_change: float                         # the change started
    t_report: float                         # the detector reported it
    box: tuple[int, int, int, int]          # in WORK_WIDTH pixels
    escalated: bool                         # a held skip that stayed
    t_asked: float                          # the ledger decided to ask
    w0: float = 0.0                         # the clip's window
    w1: float = 0.0
    lens_job: str = ""
    span: tuple[dt.datetime, dt.datetime] | None = None   # what lens_1 recorded of the clip (whole seconds)


class Recent:
    """The last keep_s seconds of one camera's frames, kept as the JPEGs FrameBridge sent (decoded only for a clip)."""

    def __init__(self, keep_s: float = KEEP_S):
        self.keep_s = keep_s
        self.buf: deque[tuple[float, bytes]] = deque()
        self.lock = threading.Lock()

    def add(self, t: float, jpeg: bytes) -> None:
        with self.lock:
            self.buf.append((t, jpeg))
            while self.buf and t - self.buf[0][0] > self.keep_s:
                self.buf.popleft()

    def latest(self) -> float:
        with self.lock:
            return self.buf[-1][0] if self.buf else 0.0

    def window(self, t0: float, t1: float) -> list[bytes]:
        with self.lock:
            return [j for t, j in self.buf if t0 <= t < t1]


class HafniaAnswers:
    """One Hafnia request per question: lens_1 over the clip's span, with the JSON prompt. At most max_requests in
    this run and none once today's count reaches stop_at; a question past either bound is not asked (its incident
    stays pending). A failed request is not retried."""

    def __init__(self, gw, lens_camera_id: str, max_requests: int, stop_at: int):
        self.gw, self.lens_id = gw, lens_camera_id
        self.max_requests, self.stop_at = max_requests, stop_at
        self.requests = 0
        self.lock = threading.Lock()

    def __call__(self, q: Question) -> dict:
        from incident.verify import ask
        with self.lock:
            if self.requests >= self.max_requests:
                return {"category": None, "capped": True, "reason": f"run cap ({self.max_requests}) reached"}
            quota = self.gw.quota()
            if quota and quota["DailySummaryCount"] >= self.stop_at:
                return {"category": None, "capped": True, "reason": f"today's count reached {self.stop_at}"}
            self.requests += 1
        start, end = q.span
        late = (end - dt.datetime.now(dt.timezone.utc)).total_seconds() + 2
        if late > 0:
            time.sleep(late)        # the clip's last frames recorded
        summary, secs = ask(self.gw, self.lens_id, start, end, PROMPT)
        if summary.get("Progress") != "Completed":
            return {"category": None, "reason": "request failed", "error": summary.get("LastError"),
                    "summary_id": summary.get("Id"), "hafnia_s": round(secs, 1)}
        answer = summary.get("Response") or ""
        return {**parse(answer), "response": answer, "summary_id": summary.get("Id"), "hafnia_s": round(secs, 1)}


def _json(o):
    if isinstance(o, np.ndarray):
        return [round(float(v), 5) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, (dt.datetime, dt.date)):
        return o.isoformat()
    if isinstance(o, (set, tuple)):
        return list(o)
    raise TypeError(type(o))


class Service:
    def __init__(self, cameras: dict[str, ChangeParams], answer: Callable[[Question], dict], out: Path,
                 lens: bool = True, params: Params | None = None, workers: int = 32,
                 on_frame: Callable[[str, float, np.ndarray], bool | None] | None = None, echo=print,
                 alarms=None, close_alarms_at_end: bool = False, zones: dict[str, list[Zone]] | None = None):
        """cameras: name -> change detector setting. answer: Question -> {"category": ... or None, ...}, called on a
        worker thread after the clip has played. workers: questions in flight; each captures its clip as soon as its
        window has passed, so none may wait for a free worker (the frames are kept only KEEP_S). on_frame (camera,
        frame time, 640-px frame), for test harnesses: returning False keeps that frame from the detector. alarms: an
        XProtectAlarms (clearway/alarms.py) to carry out the ledger's effects; close_alarms_at_end (test harness):
        close the alarms still open when the run ends. zones: {camera name: [Zone, ...]}, the danger zones
        (tier0/zones.load_zones)."""
        from ultralytics import YOLO
        self.cameras, self.answer, self.out, self.lens = cameras, answer, out, lens
        self.on_frame, self.echo = on_frame, echo
        out.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(out / "ledger.jsonl", params)
        self.lock = threading.Lock()                    # the ledger is not thread-safe
        self.gpu = threading.Lock()                     # one model call at a time
        self.detectors = {c: ChangeDetector(p) for c, p in cameras.items()}
        self.open: dict[str, dict[int, Change]] = {c: {} for c in cameras}   # reported, not yet closed
        self.recent = {c: Recent() for c in cameras}
        self.inbox = {c: queue.Queue(maxsize=QUEUE) for c in cameras}
        self.stats = {c: {"t_first": None, "received": 0, "frames": 0, "dropped": 0, "fps": 0.0, "lag_s": 0.0,
                          "reports": 0, "zone_reports": 0, "errors": 0} for c in cameras}
        self.zones = {c: [ZoneWatch(z, first_id=1_000_000 * (i + 1)) for i, z in enumerate(zs)]
                      for c, zs in (zones or {}).items() if c in cameras}
        self.embedder = Embedder()
        self.yolo = YOLO(str(REPO / "models" / "yolo11m.pt"))
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.questions: list[Future] = []
        self.alarms, self.close_alarms_at_end = alarms, close_alarms_at_end
        self.evidence: dict[str, dict] = {}             # incident -> snapshot of the clip Hafnia judged, lens span
        self.now = 0.0                                  # the latest frame time, any camera
        self.closed = False                             # no more frames are coming
        self._log_lock = threading.Lock()
        self._verdicts_read = 0                         # bytes of operator.jsonl taken in

    # --- logging -------------------------------------------------------------------------------------------------
    def log(self, kind: str, **fields) -> None:
        rec = {"kind": kind, "wall": round(time.time(), 3), **fields}
        with self._log_lock:
            with (self.out / "service.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=_json, ensure_ascii=False) + "\n")
            brief = {k: v for k, v in fields.items() if k not in ("answer", "cameras", "params")}
            self.echo(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%S} {kind:10} "
                      f"{json.dumps(brief, default=_json, ensure_ascii=False)[:220]}")

    def _record(self, **rec) -> None:
        with self._log_lock, (self.out / "changes.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=_json) + "\n")

    # --- per frame -----------------------------------------------------------------------------------------------
    def _people(self, frame: np.ndarray) -> list[tuple[float, float, float, float]]:
        with self.gpu:
            r = self.yolo(frame, classes=[0], conf=0.3, imgsz=640, verbose=False)[0]
        return [tuple(b) for b in r.boxes.xyxy.tolist()]

    def _camera(self, camera: str) -> None:
        """One camera's thread: its frames in order, through the detector, until the None sentinel."""
        inbox, det, s = self.inbox[camera], self.detectors[camera], self.stats[camera]
        while (item := inbox.get()) is not None:
            t, jpeg = item
            try:
                frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                h, w = frame.shape[:2]
                if w != WORK_WIDTH:
                    frame = cv2.resize(frame, (WORK_WIDTH, round(h * WORK_WIDTH / w)), interpolation=cv2.INTER_AREA)
                if self.on_frame is not None and self.on_frame(camera, t, frame) is False:
                    s["frames"] += 1
                    continue
                people = None
                if camera in self.zones and s["frames"] % ZONE_EVERY == 0:
                    people = self._people(frame)
                    for zw in self.zones[camera]:
                        for o in zw.update(t, people, frame.shape[1], frame.shape[0])[0]:
                            s["zone_reports"] += 1
                            self._on_report(camera, o, frame, source=zw.zone.name)
                for c in det.update(t, frame, (lambda: people) if people is not None else (lambda: self._people(frame))):
                    s["reports"] += 1
                    self._on_report(camera, c, frame)
                self._closings(camera)       # changes and zone occupations alike
                s["frames"] += 1
                s["lag_s"] = round(time.time() - t, 2)
            except Exception as e:           # one bad frame must not stop the camera
                s["errors"] += 1
                if s["errors"] <= 5:
                    self.log("error", camera=camera, error=repr(e))

    def _ticker(self) -> None:
        """Every second: the ledger's held skips that stayed become questions; alarms of incidents that stayed
        cleared close; operators' verdicts from the board are taken in."""
        while not self.closed:
            time.sleep(1.0)
            with self.lock:
                out = self.ledger.tick(self.now)
                qs = [self._question(d, self.now) for d in out if d.get("action") == "ask"]
            for q in qs:
                self._ask(q)
            for e in out:
                if e.get("action") != "ask":     # an alarm closing
                    self._effect(e)
            self._verdicts()

    def _verdicts(self) -> None:
        """The verdicts the board appended to <out>/operator.jsonl since the last look, into the ledger."""
        path = self.out / "operator.jsonl"
        if not path.exists():
            return
        with path.open("rb") as f:
            f.seek(self._verdicts_read)
            data = f.read()
        end = data.rfind(b"\n")
        if end < 0:
            return
        self._verdicts_read += end + 1
        for line in data[:end].decode("utf-8").splitlines():
            if not line.strip():
                continue
            v: dict = {}
            try:
                v = d if isinstance(d := json.loads(line), dict) else {}
                with self.lock:
                    effects = self.ledger.on_operator(v["incident"], v["verdict"], self.now)
            except Exception as e:           # a verdict that does not apply (or a bad line) must not stop the ticker
                self.log("operator", incident=v.get("incident"), verdict=v.get("verdict"), applied=False,
                         reason=str(e))
                continue
            self.log("operator", incident=v["incident"], verdict=v["verdict"], applied=True,
                     since_click_s=round(time.time() - v["wall"], 1) if "wall" in v else None)
            for e in effects:
                self._effect(e)

    def _on_report(self, camera: str, c: Change, frame: np.ndarray, source: str = "detector") -> None:
        """A change from the detector, or a zone occupation (tier0.zones.Occupation, shaped alike)."""
        with self.gpu:
            emb = self.embedder.images([crop(frame, c.box)])[0]
        self.open[camera][c.id] = c
        self._record(kind="report", camera=camera, change=c.id, t_change=c.t_start, t=c.t_detect, box=c.box,
                     area=c.area, emb=emb, source=source)
        with self.lock:
            d = self.ledger.on_change(camera, c.id, c.t_start, c.t_detect, c.box, emb)
            q = self._question(d, c.t_detect) if d["action"] == "ask" else None
        self.log("change", camera=camera, change=c.id, source=source, t_change=round(c.t_start, 2),
                 t=round(c.t_detect, 2), box=c.box, area=c.area, action=d["action"], incident=d.get("incident"),
                 similarity=round(d["similarity"], 3) if "similarity" in d else None)
        for e in d.get("effects", []):
            self._effect(e)
        if q is not None:
            self._ask(q)

    def _closings(self, camera: str) -> None:
        for cid, c in list(self.open[camera].items()):
            if c.t_closed is None:
                continue
            del self.open[camera][cid]
            self._record(kind="close", camera=camera, change=cid, t=c.t_closed, how=c.closed_by)
            with self.lock:
                effects = self.ledger.on_change_closed(camera, cid, c.t_closed, c.closed_by)
            for e in effects:
                self._effect(e)

    def _effect(self, e: dict) -> None:
        self.log("effect", **e)
        if self.alarms is None:
            return
        iid = e.get("alarm") or e.get("close_alarm") or e.get("confirm_alarm")
        with self.lock:
            inc = self.ledger.incidents[iid].public()
        ev = dict(self.evidence.get(iid, {}))
        if "alarm" in e and (e.get("recurrence") or "jpeg" not in ev):
            ev.update(self._snapshot(inc["camera"], inc["box"]))     # the spot as it is now
        self.alarms.submit(e, inc, ev)

    def _snapshot(self, camera: str, box, frame: np.ndarray | None = None) -> dict:
        """A JPEG of the camera's frame (the latest one if none is given) with the spot boxed."""
        if frame is None:
            jpegs = self.recent[camera].window(self.recent[camera].latest(), float("inf"))
            if not jpegs:
                return {}
            frame = cv2.imdecode(np.frombuffer(jpegs[-1], np.uint8), cv2.IMREAD_COLOR)
        scale = frame.shape[1] / WORK_WIDTH
        img = mark(frame, [tuple(v * scale for v in box)], width=3)
        h, w = img.shape[:2]
        return {"jpeg": cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes(), "size": (w, h)}

    # --- questions -----------------------------------------------------------------------------------------------
    def _question(self, d: dict, t: float) -> Question:
        """Called with the ledger locked, right after it decided to ask: the incident still holds the change's own
        times (t_last is the original report time, also for an escalated skip)."""
        inc = self.ledger.incidents[d["incident"]]
        q = Question(inc.id, inc.camera, d["change"], inc.t_change, inc.t_last, tuple(inc.box), d["escalated"], t)
        q.w1 = q.t_report + AFTER_S
        q.w0 = max(q.t_change - BEFORE_S, q.w1 - MAX_CLIP_S)
        return q

    def _ask(self, q: Question) -> None:
        self.log("question", incident=q.incident, camera=q.camera, change=q.change, escalated=q.escalated,
                 t_change=round(q.t_change, 2), t_report=round(q.t_report, 2), clip_s=round(q.w1 - q.w0, 1),
                 box=q.box)
        self.questions.append(self.pool.submit(self._answer, q))

    def _answer(self, q: Question) -> None:
        try:
            recent = self.recent[q.camera]
            while recent.latest() < q.w1 and not self.closed:
                time.sleep(0.2)                 # the window's last frames
            frames = [cv2.imdecode(np.frombuffer(j, np.uint8), cv2.IMREAD_COLOR) for j in recent.window(q.w0, q.w1)]
            if not frames:
                self._failed(q, "no frames in the window")
                return
            scale = frames[0].shape[1] / WORK_WIDTH
            box = tuple(v * scale for v in q.box)
            ev = self.evidence[q.incident] = self._snapshot(q.camera, q.box, frames[-1])   # the clip's last frame
            (self.out / "snaps").mkdir(exist_ok=True)
            (self.out / "snaps" / f"{q.incident}.jpg").write_bytes(ev["jpeg"])           # for the board
            t0 = time.monotonic()
            if self.lens:
                q.lens_job = submit(zoom(frames, box), f"{q.incident}-{q.camera}",
                                    meta={"incident": q.incident, "camera": q.camera})
                n_frames, frames = len(frames), None     # written to the spool: free them while the lens plays
                q.span = ev["span"] = span(wait(q.lens_job, timeout=600))
                self.log("lens", incident=q.incident, camera=q.camera, job=q.lens_job, span=q.span,
                         frames=n_frames, waited_s=round(time.monotonic() - t0, 1))
            result = self.answer(q)
            cat = result.get("category")
            if cat is None:
                if result.get("capped"):     # stays pending: asking again would be refused too
                    self.log("unanswered", incident=q.incident, camera=q.camera, answer=result,
                             reason=result.get("reason"))
                else:
                    self._failed(q, result.get("reason") or "no answer", answer=result)
                return
            t = self.now
            with self.lock:
                effects = self.ledger.on_answer(q.incident, cat, result, t, clip=q.lens_job)
                inc = self.ledger.incidents[q.incident]
                state, merged = inc.state, inc.merged_into
            self.log("answer", incident=q.incident, camera=q.camera, category=cat, state=state, merged_into=merged,
                     since_change_s=round(t - q.t_change, 1), since_report_s=round(t - q.t_report, 1),
                     since_asked_s=round(t - q.t_asked, 1), answer=result)
            for e in effects:
                self._effect(e)
        except Exception as e:               # one failed question must not stop the service
            self.log("error", incident=q.incident, camera=q.camera, error=repr(e), trace=traceback.format_exc())
            self._failed(q, repr(e))

    def _failed(self, q: Question, reason: str, **fields) -> None:
        """No answer will come: the ledger drops the pending incident, so the next occurrence is asked anew."""
        with self.lock:
            self.ledger.on_failed(q.incident, self.now, reason)
        self.log("failed", incident=q.incident, camera=q.camera, reason=reason, **fields)

    # --- the loop ------------------------------------------------------------------------------------------------
    def run(self, minutes: float | None = None) -> dict:
        self.log("start", cameras={c: asdict(p) for c, p in self.cameras.items()}, lens=self.lens,
                 params=vars(self.ledger.p))
        bridge = FrameBridge(list(self.cameras), log=lambda s: self.echo(s))
        threads = [threading.Thread(target=self._camera, args=(c,), name=c, daemon=True) for c in self.cameras]
        threads.append(threading.Thread(target=self._ticker, name="ticker", daemon=True))
        for th in threads:
            th.start()
        stop = None if minutes is None else time.monotonic() + 60 * minutes
        counted = {c: 0 for c in self.cameras}
        next_health, last_health = time.monotonic() + 15, time.monotonic()
        try:
            for camera, when, jpeg in bridge.frames():
                if stop is not None and time.monotonic() > stop:
                    break
                t = when.timestamp()
                self.now = max(self.now, t)
                self.recent[camera].add(t, jpeg)
                st = self.stats[camera]
                st["received"] += 1
                if st["t_first"] is None:
                    st["t_first"] = t
                inbox = self.inbox[camera]
                while True:
                    try:
                        inbox.put_nowait((t, jpeg))
                        break
                    except queue.Full:       # the camera's thread is behind: skip its oldest frame
                        try:
                            inbox.get_nowait()
                            self.stats[camera]["dropped"] += 1
                        except queue.Empty:
                            pass
                if time.monotonic() >= next_health:
                    span_s = time.monotonic() - last_health
                    for c, st in self.stats.items():
                        st["fps"] = round((st["frames"] - counted[c]) / span_s, 1)
                        counted[c] = st["frames"]
                    next_health, last_health = time.monotonic() + 15, time.monotonic()
                    self.log("health", cameras=self.stats, ledger=dict(self.ledger.stats),
                             questions_open=sum(not f.done() for f in self.questions))
        finally:
            bridge.close()
            for c in self.cameras:
                self.inbox[c].put(None)      # each camera finishes the frames it has, then stops
            for th in threads[:-1]:
                th.join()
            self.closed = True
            threads[-1].join()
            for f in list(self.questions):
                f.result()
            self.pool.shutdown()
            if self.alarms is not None:
                if self.close_alarms_at_end:
                    self.alarms.close_all("Test run ended: closed by the test harness, not because the spot cleared.")
                self.alarms.drain()
            incidents = self.ledger.snapshot()
            (self.out / "incidents.json").write_text(json.dumps(incidents, indent=2, default=_json), encoding="utf-8")
            self.log("end", ledger=dict(self.ledger.stats), cameras=self.stats,
                     cards=sum(bool(i["category"]) and not i["merged_into"] for i in incidents))
        return {"ledger": dict(self.ledger.stats), "cameras": self.stats}
