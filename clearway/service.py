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
   scripts/lens_pilot.py) cropped to the spot. A large spot, one the lens would magnify less than DIRECT_BELOW
   times, is asked about on the camera's own recording over the window (the crop is only stored, for the board's
   card); a small one is played on the lens camera (lens/client.py) and asked about on lens_1 over the span its
   recording really holds the clip in: lens_1's own frames come through FrameBridge too, with the Recording Server's
   times, and the frame code the publisher burns into them says which clip and frame each is (lens/clock.py). The
   lens recording's time base ran 0.3-9.5 s behind the publisher under load (run/lens-check-20261027), so a span
   assumed from the publisher's clock had Hafnia judge neighbouring clips. A clip of which no frame reached the
   Recording Server is played once more. Then one answer: HafniaAnswers (one request, the JSON prompt of
   clearway/prompt.py; a direct ask that fails, e.g. no recording over the window on a camera that records on
   motion, is asked once more on the lens while the window's frames are still kept) or a test stand-in passed in by
   the caller;
4. the answer goes back to the ledger. Closed changes go to the ledger too: an incident clears when its largest change
   closes.
The ledger's effects (raise, reopen or close an incident's alarm) are carried out in XProtect by clearway/alarms.py
(XProtectAlarms, F3: one alarm per incident, with a snapshot and bookmarks) when one is given, and logged; each
incident's owner is told by webhook (clearway/notify.py, OwnerNotifier) when one is given. Operators'
verdicts on the cards (F7: confirm or reject on the board, clearway/board.py) arrive in <out>/operator.jsonl, which
the board appends to and the service reads every second (Ledger.on_operator).

Writes <out>/ledger.jsonl (the ledger's event log; Ledger.replay rebuilds the state), <out>/service.jsonl (changes,
questions, lens spans, answers, effects, health every 15 s with each camera's rates, the lens clock's offsets and the
CPU shares of the machine, the Recording Server, FrameBridge and the service), <out>/changes.jsonl (every report with its look, and every closing:
the ledger's input, so a live run can be replayed offline with a changed ledger), <out>/snaps/<incident>.jpg (the
camera's frame at the end of each question's clip, the spot boxed; for the board, clearway/board.py),
<out>/cameras/<camera>.jpg (the scene as the detector remembers it, every SCENE_EVERY_S and at the end: the backdrop
of the shift summary's hotspots) and, at the end, <out>/incidents.json. Times are frame times (Unix
seconds, UTC) unless named wall.
"""
from __future__ import annotations

import datetime as dt
import json
import math
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
from lens.client import mark, replay, submit, wait, zoom
from lens.clock import LENS_CAMERA, LensClock
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
DETECT_EVERY = 2    # the change detector sees every 2nd frame too: it waits persist_s (1.5 s or more) before
                    # reporting, so 5 fps loses nothing, and the machine's four cores were saturated with eleven
                    # cameras (the service 56-62 %, FrameBridge 22-28 %, 2026-10-27), which starved FrameBridge
                    # to 4-5 of each camera's 10 fps and the lens's live feed with it
SCENE_EVERY_S = 600.0   # each camera's scene image (the detector's slow background) is rewritten this often
DIRECT_BELOW = 2.5      # a spot the lens would magnify less than this is asked about on its own camera: the pilot's
                        # full-frame answers were right down to 2.7x (run/pilot-20261023T162040Z, the graffiti);
                        # test_11's crash (about 6x) still needs the crop (gate G3)
PARALLEL = 3            # Hafnia requests at once: the gateway exports each clip from the Recording Server, which also
                        # serves every camera's live frames (the lens's clips were starved during M3's start-up)
RECORDED_SETTLE_S = 3.0   # asked this long after a window's end: the camera's recording has the last frames
LENS_SETTLE_S = 2.0       # the same for lens_1, after the clip's last frame was seen in its live feed (2026-10-25:
                          # enough on an idle machine)
REPLAY_HOLE_S = 1.0       # a clip over which lens_1's feed had a hole this long (frames MediaMTX discarded, so not
                          # recorded either) is played once more, as is one of which no frame came through
BRIDGE_WIDTH = 832        # FrameBridge asks the Recording Server for frames this wide: the incident cameras' own
                          # width (832x480; test_11 is 800 px), so nothing is lost there, while busy_street (1280),
                          # highway (1920) and lens_1 (1280) cost it less; at full width eleven cameras starved it
                          # (M3; the detector works at WORK_WIDTH anyway)


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
    magnification: float = 0.0              # how much the lens crop would enlarge the spot
    view: str = ""                          # "direct": the camera's own recording; "lens": the crop on lens_1
    clip: str = ""                          # the crop's spool id (lens/client.py): a lens job, or stored for the board
    span: tuple[dt.datetime, dt.datetime] | None = None   # the whole seconds asked about, on the camera or lens_1
    ready_at: float = 0.0                   # wall time (Unix s) by which the recording holds the span (lens)


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


class Load:
    """CPU shares for the health record: the whole machine, the Recording Server (which transcodes every camera's
    frames for FrameBridge, records, and exports the gateway's clips), FrameBridge and this process; percent of all
    cores, averaged since the previous call (psutil). The Recording Server is found by name and looked up again if
    it restarts."""
    RECORDER = "videoos.recorder.service.exe"

    def __init__(self, bridge_pid: int | None = None):
        import psutil
        self.psutil = psutil
        self.cores = psutil.cpu_count() or 1
        self.me = psutil.Process()
        self.bridge = psutil.Process(bridge_pid) if bridge_pid else None
        self.recorder = None
        psutil.cpu_percent(None)
        self._prime(self.me)
        self._prime(self.bridge)
        self._prime(self._recorder())

    def _recorder(self):
        if self.recorder is None or not self.recorder.is_running():
            self.recorder = next((p for p in self.psutil.process_iter(["name"])
                                  if (p.info["name"] or "").lower() == self.RECORDER), None)
        return self.recorder

    def _prime(self, proc) -> None:
        try:
            if proc is not None:
                proc.cpu_percent(None)
        except self.psutil.Error:
            pass

    def _share(self, proc) -> float | None:
        try:
            return round(proc.cpu_percent(None) / self.cores, 1) if proc is not None else None
        except self.psutil.Error:
            return None

    def sample(self) -> dict:
        return {"machine": self.psutil.cpu_percent(None), "recording_server": self._share(self._recorder()),
                "bridge": self._share(self.bridge), "service": self._share(self.me)}


class HafniaAnswers:
    """One Hafnia request per question, with the JSON prompt: on the question's own camera over its window (view
    direct) or on lens_1 over the span the clip played (view lens). At most max_requests in this run and none once
    today's count reaches stop_at; a question past either bound is not asked (its incident stays pending). At most
    parallel requests at once. A failed request is not retried here (the service asks once more on the lens)."""

    def __init__(self, gw, camera_ids: dict[str, str], lens_camera_id: str | None, max_requests: int, stop_at: int,
                 parallel: int = PARALLEL):
        """camera_ids: camera name -> XProtect id. lens_camera_id: lens_1's id (None: no lens, every question is
        direct)."""
        self.gw, self.camera_ids, self.lens_id = gw, camera_ids, lens_camera_id
        self.max_requests, self.stop_at = max_requests, stop_at
        self.requests = 0
        self.lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(parallel)

    def __call__(self, q: Question) -> dict:
        from incident.verify import ask
        with self.lock:
            if self.requests >= self.max_requests:
                return {"category": None, "capped": True, "reason": f"run cap ({self.max_requests}) reached"}
            quota = self.gw.quota()
            if quota and quota["DailySummaryCount"] >= self.stop_at:
                return {"category": None, "capped": True, "reason": f"today's count reached {self.stop_at}"}
            self.requests += 1
        if q.view == "lens":
            camera, settle = self.lens_id, LENS_SETTLE_S
        else:
            camera, settle = self.camera_ids[q.camera], RECORDED_SETTLE_S
        start, end = q.span
        late = (end - dt.datetime.now(dt.timezone.utc)).total_seconds() + settle
        late = max(late, q.ready_at - time.time())      # lens: the span is in the recording's own time base
        if late > 0:
            time.sleep(late)        # the span's last frames recorded
        with self.slots:
            summary, secs = ask(self.gw, camera, start, end, PROMPT)
        asked = {"view": q.view, "summary_id": summary.get("Id"), "hafnia_s": round(secs, 1)}
        if summary.get("Progress") != "Completed":
            return {"category": None, "reason": "request failed", "error": summary.get("LastError"), **asked}
        answer = summary.get("Response") or ""
        return {**parse(answer), "response": answer, **asked}


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
                 alarms=None, close_alarms_at_end: bool = False, zones: dict[str, list[Zone]] | None = None,
                 notifier=None, direct_below: float = DIRECT_BELOW, width: int = BRIDGE_WIDTH,
                 detect_every: int = DETECT_EVERY, below_normal: bool = True):
        """cameras: name -> change detector setting. answer: Question -> {"category": ... or None, ...}, called on a
        worker thread after the clip has played. workers: questions in flight; each captures its clip as soon as its
        window has passed, so none may wait for a free worker (the frames are kept only KEEP_S). on_frame (camera,
        frame time, 640-px frame), for test harnesses: returning False keeps that frame from the detector. alarms: an
        XProtectAlarms (clearway/alarms.py) to carry out the ledger's effects; close_alarms_at_end (test harness):
        close the alarms still open when the run ends. zones: {camera name: [Zone, ...]}, the danger zones
        (tier0/zones.load_zones). notifier: an OwnerNotifier (clearway/notify.py) to tell each incident's owner.
        direct_below: a spot the lens would magnify less than this is asked about on its own camera (0: every spot
        on the lens); without the lens every question is direct. width: the frame width FrameBridge asks the
        Recording Server for (0: each camera's own). detect_every: the detector sees every n-th frame (the frames
        in between are kept for clips and snapshots). below_normal: run this process and FrameBridge below normal
        priority, so that XProtect's services and the API Gateway are served first on a full machine."""
        from ultralytics import YOLO
        self.cameras, self.answer, self.out, self.lens = cameras, answer, out, lens
        self.direct_below, self.width, self.detect_every = direct_below, width, max(1, detect_every)
        self.below_normal = below_normal
        self.clock = LensClock() if lens else None      # lens_1's recorded time base, from its own frames
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
        self.alarms, self.close_alarms_at_end, self.notifier = alarms, close_alarms_at_end, notifier
        self.evidence: dict[str, dict] = {}             # incident -> snapshot of the clip Hafnia judged, lens span
        self.now = 0.0                                  # the latest frame time, any camera
        self.closed = False                             # no more frames are coming
        self._log_lock = threading.Lock()
        self._verdicts_read = 0                         # bytes of operator.jsonl taken in
        self.scened = {c: float("-inf") for c in cameras}   # frame time of each camera's last scene image

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
            s["received_here"] = s.get("received_here", 0) + 1
            if s["received_here"] % self.detect_every:
                continue                                 # kept in Recent for clips; the detector sees the next one
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
                if det.slow is not None and t - self.scened[camera] >= SCENE_EVERY_S:
                    self._scene(camera, t)
                s["frames"] += 1
                s["lag_s"] = round(time.time() - t, 2)
            except Exception as e:           # one bad frame must not stop the camera
                s["errors"] += 1
                if s["errors"] <= 5:
                    self.log("error", camera=camera, error=repr(e))

    def _scene(self, camera: str, t: float) -> None:
        """<out>/cameras/<camera>.jpg: the detector's slow background, the scene as it usually looks (it learns only
        where nothing moves, over minutes, so a looped incident is not in it), at the detector's working size."""
        img = self.detectors[camera].slow.clip(0, 255).astype(np.uint8)
        folder = self.out / "cameras"
        folder.mkdir(exist_ok=True)
        tmp = folder / f"{camera}.jpg.tmp"
        tmp.write_bytes(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes())
        tmp.replace(folder / f"{camera}.jpg")          # the board may be reading the last one
        self.scened[camera] = t

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
                    if v["verdict"] == "rejected":
                        self._release(self.ledger.incidents[v["incident"]])
                for e in effects:            # where it came from: the board, or a phone's ntfy button (F12)
                    e["via"] = v.get("via") or "board"
            except Exception as e:           # a verdict that does not apply (or a bad line) must not stop the ticker
                self.log("operator", incident=v.get("incident"), verdict=v.get("verdict"), applied=False,
                         reason=str(e))
                continue
            self.log("operator", incident=v["incident"], verdict=v["verdict"], applied=True, via=v.get("via") or "board",
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
        """One of the ledger's effects, to each output: XProtect alarms (control room), owner notifications."""
        self.log("effect", **e)
        outputs = [o for o in (self.alarms, self.notifier) if o is not None]
        if not outputs:
            return
        iid = e.get("alarm") or e.get("close_alarm") or e.get("confirm_alarm")
        with self.lock:
            inc = self.ledger.incidents[iid].public()
        ev = dict(self.evidence.get(iid, {}))
        if "alarm" in e and (e.get("recurrence") or "jpeg" not in ev):
            ev.update(self._snapshot(inc["camera"], inc["box"]))     # the spot as it is now
        for o in outputs:
            o.submit(e, inc, ev)

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

    def _frames(self, q: Question) -> list[np.ndarray]:
        """The window's frames, decoded (empty once they have left the camera's buffer)."""
        return [cv2.imdecode(np.frombuffer(j, np.uint8), cv2.IMREAD_COLOR)
                for j in self.recent[q.camera].window(q.w0, q.w1)]

    def _play(self, q: Question, clip: list[np.ndarray]) -> None:
        """The crop on the lens camera: queued for lens/publisher.py, then the span lens_1 recorded it in, read back
        from its own frames (lens/clock.py). A clip of which no frame reached the Recording Server, or over which
        its feed had a hole of REPLAY_HOLE_S (MediaMTX discards stretches of the stream when XProtect reads too
        slowly, and they are not recorded), is played once more."""
        t0 = time.monotonic()
        q.view = "lens"
        q.clip = submit(clip, f"{q.incident}-{q.camera}", meta={"incident": q.incident, "camera": q.camera})
        n_frames = len(clip)
        clip.clear()                            # written to the spool: free the frames while the lens plays
        info = self._lens_span(q, wait(q.clip, timeout=600))
        if self.clock.alive() and (info["seen"] == 0 or info.get("hole_s", 0.0) >= REPLAY_HOLE_S):
            reason = info.get("reason") or f"a hole of {info['hole_s']} s in lens_1's feed over the clip"
            self.log("lens_replay", incident=q.incident, camera=q.camera, job=q.clip, reason=reason)
            q.clip = replay(q.clip)
            info = {**self._lens_span(q, wait(q.clip, timeout=600)), "replayed": True}
        self.log("lens", incident=q.incident, camera=q.camera, job=q.clip, span=q.span, frames=n_frames,
                 magnification=q.magnification, waited_s=round(time.monotonic() - t0, 1),
                 **{k: v for k, v in info.items() if k not in ("ready_wall", "frames")})

    def _lens_span(self, q: Question, done: dict) -> dict:
        """q.span and q.ready_at from the clip's recorded frames; the clock's info (seen, offset_s, verified, ...)."""
        start, end, info = self.clock.span_for(done)
        q.span = (start, end)
        q.ready_at = info["ready_wall"] + LENS_SETTLE_S
        return info

    def _direct(self, q: Question, clip: list[np.ndarray]) -> None:
        """The camera's own recording over the window (whole seconds, as the gateway takes them); the crop is only
        stored, for the board's card."""
        q.view = "direct"
        q.clip = submit(clip, f"{q.incident}-{q.camera}", meta={"incident": q.incident, "camera": q.camera},
                        play=False)
        q.span = (dt.datetime.fromtimestamp(math.floor(q.w0), dt.timezone.utc),
                  dt.datetime.fromtimestamp(math.ceil(q.w1), dt.timezone.utc))
        self.log("direct", incident=q.incident, camera=q.camera, clip=q.clip, span=q.span, frames=len(clip),
                 magnification=q.magnification)

    def _answer(self, q: Question) -> None:
        try:
            recent = self.recent[q.camera]
            while recent.latest() < q.w1 and not self.closed:
                time.sleep(0.2)                 # the window's last frames
            frames = self._frames(q)
            if not frames:
                self._failed(q, "no frames in the window")
                return
            scale = frames[0].shape[1] / WORK_WIDTH
            box = tuple(v * scale for v in q.box)
            ev = self.evidence[q.incident] = self._snapshot(q.camera, q.box, frames[-1])   # the clip's last frame
            (self.out / "snaps").mkdir(exist_ok=True)
            (self.out / "snaps" / f"{q.incident}.jpg").write_bytes(ev["jpeg"])           # for the board
            clip = zoom(frames, box)
            q.magnification = round(frames[0].shape[1] / clip[0].shape[1], 2)
            frames = None
            if self.lens and q.magnification >= self.direct_below:
                self._play(q, clip)
            else:
                self._direct(q, clip)
            clip = None
            ev["span"], ev["view"] = q.span, q.view
            result = self.answer(q)
            if result.get("category") is None and not result.get("capped") and q.view == "direct" and self.lens:
                frames = self._frames(q)        # the recording could not be asked about (a camera that records on
                if frames:                      # motion may have none over the window): the lens, while the frames last
                    self.log("fallback", incident=q.incident, camera=q.camera, reason=result.get("reason"),
                             error=result.get("error"))
                    self._play(q, zoom(frames, box))
                    frames = None
                    ev["span"], ev["view"] = q.span, q.view
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
                effects = self.ledger.on_answer(q.incident, cat, result, t, clip=q.clip)
                inc = self.ledger.incidents[q.incident]
                state, merged = inc.state, inc.merged_into
                harmless = inc if state == "dismissed" else (
                    self.ledger.incidents[merged] if merged and self.ledger.incidents[merged].state == "rejected"
                    else None)
                released = self._release(harmless) if harmless is not None else []
            self.log("answer", incident=q.incident, camera=q.camera, category=cat, view=q.view, state=state,
                     merged_into=merged, released=released or None,
                     since_change_s=round(t - q.t_change, 1), since_report_s=round(t - q.t_report, 1),
                     since_asked_s=round(t - q.t_asked, 1), answer=result)
            for e in effects:
                self._effect(e)
        except Exception as e:               # one failed question must not stop the service
            self.log("error", incident=q.incident, camera=q.camera, error=repr(e), trace=traceback.format_exc())
            self._failed(q, repr(e))

    def _release(self, inc) -> list[int]:
        """A dismissed or rejected incident's open changes are released on its camera's detector (the slow background
        may take their spots in: tier0.change.ChangeDetector.release). Called with the ledger locked."""
        ids = sorted(inc.active)
        det = self.detectors.get(inc.camera)
        if det is not None:
            for cid in ids:
                det.release(cid)
        return ids

    def _failed(self, q: Question, reason: str, **fields) -> None:
        """No answer will come: the ledger drops the pending incident, so the next occurrence is asked anew."""
        with self.lock:
            self.ledger.on_failed(q.incident, self.now, reason)
        self.log("failed", incident=q.incident, camera=q.camera, reason=reason, **fields)

    # --- the loop ------------------------------------------------------------------------------------------------
    def run(self, minutes: float | None = None) -> dict:
        self.log("start", cameras={c: asdict(p) for c, p in self.cameras.items()}, lens=self.lens,
                 direct_below=self.direct_below, width=self.width, detect_every=self.detect_every,
                 params=vars(self.ledger.p))
        names = list(self.cameras)
        if self.clock is not None and LENS_CAMERA not in names:
            names.append(LENS_CAMERA)               # lens_1's own frames, for the clock
        bridge = FrameBridge(names, log=lambda s: self.echo(s), width=self.width)
        try:
            load = Load(bridge.proc.pid)
            if self.below_normal:                  # XProtect's services and the API Gateway come first: our frame
                for proc in (load.me, load.bridge):   # work must not slow the video system it serves (alarm
                    proc.nice(load.psutil.BELOW_NORMAL_PRIORITY_CLASS)   # actions took 19 s under load, 2026-10-27)
                self.log("priority", below_normal=True, pids=[load.me.pid, load.bridge.pid])
        except Exception as e:                     # psutil missing or refused: health goes without CPU shares
            self.log("error", error=f"cpu load: {e!r}")
            load = None
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
                if camera == LENS_CAMERA and self.clock is not None:
                    self.clock.feed(t, jpeg)
                    if camera not in self.cameras:
                        continue
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
                             questions_open=sum(not f.done() for f in self.questions),
                             lens=self.clock.stats() if self.clock is not None else None,
                             cpu=load.sample() if load is not None else None)
        finally:
            bridge.close()
            for c in self.cameras:
                self.inbox[c].put(None)      # each camera finishes the frames it has, then stops
            for th in threads[:-1]:
                th.join()
            for c, det in self.detectors.items():       # the scene as the shift ended
                if det.slow is not None:
                    try:
                        self._scene(c, det.last_t or 0.0)
                    except Exception as e:
                        self.log("error", camera=c, error=f"scene image: {e!r}")
            self.closed = True
            threads[-1].join()
            for f in list(self.questions):
                f.result()
            self.pool.shutdown()
            if self.alarms is not None:
                if self.close_alarms_at_end:
                    self.alarms.close_all("Test run ended: closed by the test harness, not because the spot cleared.")
                self.alarms.drain()
            if self.notifier is not None:
                self.notifier.drain()
            incidents = self.ledger.snapshot()
            (self.out / "incidents.json").write_text(json.dumps(incidents, indent=2, default=_json), encoding="utf-8")
            self.log("end", ledger=dict(self.ledger.stats), cameras=self.stats,
                     cards=sum(bool(i["category"]) and not i["merged_into"] for i in incidents))
            try:                             # the shift summary (F8), from the logs just closed
                from clearway.summary import summarise
                (self.out / "shift.json").write_text(json.dumps(summarise(self.out), indent=2), encoding="utf-8")
            except Exception as e:
                self.log("error", error=f"shift summary: {e!r}", trace=traceback.format_exc())
        return {"ledger": dict(self.ledger.stats), "cameras": self.stats}
