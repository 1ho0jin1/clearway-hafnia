"""lens_1's recorded time base, read back from the frame code (lens/code.py) in its own frames, so that the span a clip
is asked about is the span the recording really holds it in.

    clock = LensClock()                       # fed by the service: clock.feed(frame_time, jpeg) for lens_1's frames
    clock = LensClock.standalone()            # or with its own FrameBridge on lens_1 (scripts/check_lens.py)
    start, end, info = clock.span_for(done)   # a played clip's recorded span (done: lens.client.wait's record)
    clock.offset()                            # recorded time minus the publisher's wall time, now

The frames come from FrameBridge (incident/bridge.py) with the time the Recording Server gave each one: the same time
base Hafnia's gateway asks the recording by (the direct asks of clearway/service.py are right by it). The code in
each frame says when the publisher sent it and which clip and frame it is; the difference is the offset, which ran
0.3-9.5 s under load during M3 (run/lens-check-20261027). A clip's span is taken from its own frames' recorded times,
whole seconds, extended by the frames not seen at either end, and checked against neighbouring clips' frames; a clip
of which no frame reached the Recording Server is reported as such (seen 0), for the service to play again. Without a
readable feed (an older publisher, no frames in the last ALIVE_S) the span is assumed from the publisher's clock as
before (lens.client.span), shifted by the last known offset, and marked assumed.
"""
from __future__ import annotations

import datetime as dt
import math
import queue
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np

from lens.code import read

LENS_CAMERA = "lens_1"
ALIVE_S = 10.0        # a readable frame this recently means the feed and the code are working
MARGIN_S = 0.3        # added at both ends of a clip's measured span before rounding to whole seconds: the time
                      # base jitters under load (drift within a clip up to 0.6 s, 2026-10-27); the publisher's 2 s
                      # idle gap keeps a neighbouring clip out of the rounded span, and foreign frames are checked
DRIFT_OK_S = 1.0      # a larger change of the offset within one clip leaves its edges uncertain: not verified
HOLE_S = 2.0          # no readable frame for this long is a hole: MediaMTX discards whole stretches of the stream
                      # when XProtect reads too slowly (71 and 197 frames at a time, 2026-10-27), and what it discards
                      # is not recorded either; a starved live feed merely thins the frames (2-5 fps, no such gaps)


@dataclass
class Sample:
    rs: float         # the frame's time by the Recording Server (Unix s)
    wall: float       # when the publisher sent it (Unix s), from the code
    seq: int          # the publisher's job number, 0 for the idle frame
    idx: int          # the frame's index in the job (modulo 1024)
    seen: float       # wall time the frame reached us


def _utc(t: float) -> dt.datetime:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc)


def _parse(s: str) -> float:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


class LensClock:
    def __init__(self, keep_s: float = 1800.0):
        self.keep_s = keep_s
        self.samples: deque[Sample] = deque()
        self.by_seq: dict[int, list[Sample]] = {}
        self.holes: deque[tuple[float, float]] = deque()    # (from, to): consecutive readable frames whose send
                                                            # times (from their codes) are more than HOLE_S apart
        self.lock = threading.Lock()
        self.counts = {"frames": 0, "decoded": 0, "undecodable": 0, "dropped": 0}
        self.q: queue.Queue = queue.Queue(maxsize=30)
        self.bridge = None
        threading.Thread(target=self._work, name="lens-clock", daemon=True).start()

    @classmethod
    def standalone(cls, log=print, **kw) -> "LensClock":
        """With its own FrameBridge on lens_1 (for tools; the service feeds its clock from its one bridge)."""
        from incident.bridge import FrameBridge
        clock = cls(**kw)
        clock.bridge = FrameBridge([LENS_CAMERA], log=log)
        threading.Thread(target=clock._pump, name="lens-clock-bridge", daemon=True).start()
        return clock

    def _pump(self) -> None:
        try:
            for _camera, when, jpeg in self.bridge.frames():
                self.feed(when.timestamp(), jpeg)
        except EOFError:
            pass

    def close(self) -> None:
        if self.bridge is not None:
            self.bridge.close()

    # --- in ------------------------------------------------------------------------------------------------------
    def feed(self, rs: float, jpeg: bytes) -> None:
        """One of lens_1's frames: its Recording Server time (Unix s) and JPEG. Never blocks; a backlog is dropped."""
        try:
            self.q.put_nowait((rs, jpeg, time.time()))
        except queue.Full:
            self.counts["dropped"] += 1

    def _work(self) -> None:
        while True:
            rs, jpeg, seen = self.q.get()
            self.counts["frames"] += 1
            try:
                img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_GRAYSCALE)
                code = read(img, _utc(seen)) if img is not None else None
            except Exception:
                code = None
            if code is None:
                self.counts["undecodable"] += 1
                continue
            s = Sample(rs, code["wall"].timestamp(), code["seq"], code["idx"], seen)
            with self.lock:
                self.counts["decoded"] += 1
                if self.samples and s.wall - self.samples[-1].wall > HOLE_S:   # by the frames' own send times
                    self.holes.append((self.samples[-1].wall, s.wall))
                self.samples.append(s)
                if s.seq:
                    self.by_seq.setdefault(s.seq, []).append(s)
                while self.samples and seen - self.samples[0].seen > self.keep_s:
                    self.samples.popleft()
                while self.holes and seen - self.holes[0][1] > self.keep_s:
                    self.holes.popleft()
                if self.counts["decoded"] % 1000 == 0:
                    self.by_seq = {k: v for k, v in self.by_seq.items() if seen - v[-1].seen <= self.keep_s}

    # --- out -----------------------------------------------------------------------------------------------------
    def _recent(self, window_s: float) -> list[Sample]:
        cut = time.time() - window_s
        out = []
        with self.lock:
            for s in reversed(self.samples):
                if s.seen < cut:
                    break
                out.append(s)
        return out

    def offset(self, window_s: float = 10.0) -> float | None:
        """Recorded time minus the publisher's wall time, the median over the last window_s; None without frames."""
        xs = [s.rs - s.wall for s in self._recent(window_s)]
        return statistics.median(xs) if xs else None

    def alive(self, within_s: float = ALIVE_S) -> bool:
        with self.lock:
            return bool(self.samples) and time.time() - self.samples[-1].seen <= within_s

    def stats(self) -> dict:
        """For the service's health record: counts, the offset now and its range over the last minute."""
        xs = [s.rs - s.wall for s in self._recent(60.0)]
        with self.lock:
            age = round(time.time() - self.samples[-1].seen, 1) if self.samples else None
            holes = [h for h in self.holes if h[1] >= time.time() - 60.0]
        return {**self.counts, "offset_s": round(statistics.median(xs), 2) if xs else None,
                "offset_min_s": round(min(xs), 2) if xs else None, "offset_max_s": round(max(xs), 2) if xs else None,
                "last_readable_age_s": age, "holes": len(holes),
                "hole_s": round(sum(b - a for a, b in holes), 1)}

    def hole_s(self, t0: float, t1: float) -> float:
        """Seconds of [t0, t1] (wall times) that fall in holes of the feed."""
        with self.lock:
            return sum(max(0.0, min(b, t1) - max(a, t0)) for a, b in self.holes)

    def _of(self, seq: int, since: float) -> list[Sample]:
        with self.lock:
            return [s for s in self.by_seq.get(seq, []) if s.seen >= since]

    def _between(self, t0: float, t1: float) -> list[Sample]:
        with self.lock:
            return [s for s in self.samples if t0 <= s.rs < t1]

    def span_for(self, done: dict, timeout_s: float = 20.0, settle_s: float = 3.0,
                 margin_s: float = MARGIN_S) -> tuple[dt.datetime, dt.datetime, dict]:
        """The whole-second span lens_1's recording holds the played clip in (done: the publisher's record, with seq,
        frames, sent, fps, start, end), after waiting up to timeout_s for the clip's last frames to come through the
        live feed (or settle_s after its last seen frame). The clip's first and last frames are placed by a line
        through the frames seen (the live JPEG feed carries only a share of them when the Recording Server is loaded:
        25-40 % with eleven cameras, 2026-10-27, while the recording takes the H.264 stream whole), margin_s is added
        at both ends and the span rounded outwards. info: seen (frames of the clip read back), coverage (their share
        of the frames sent), first_idx, last_idx, offset_s (recorded minus wall at the first frame seen), drift_s
        (the offset's change over the clip), foreign (another clip's frames found inside the span, which is then
        shrunk), verified (frames seen from the clip's first and last quarters, a drift under DRIFT_OK_S, no foreign
        frame, the span still holding the whole clip), ready_wall (the wall time the last frame was seen: the
        recording holds the span shortly after), and assumed with a reason when the span could only be taken from
        the publisher's clock."""
        seq, frames, sent, fps = done["seq"], done["frames"], done["sent"], float(done["fps"])
        wall_start, wall_end = _parse(done["start"]), _parse(done["end"])
        if not self.alive():
            return self._assumed(done, f"no readable lens_1 frame in the last {ALIVE_S:.0f} s")
        deadline = time.monotonic() + timeout_s
        while True:
            samples = self._of(seq, wall_start - 1.0)
            if samples and max(s.idx for s in samples) >= sent - 1:
                break                                        # the last frame sent has come through
            now = time.time()
            if samples and now - max(s.seen for s in samples) > settle_s and now > wall_end + settle_s:
                break                                        # nothing more is coming
            if time.monotonic() > deadline:
                break
            time.sleep(0.25)
        if not samples:
            hole = self.hole_s(wall_start, wall_end + 1.0)
            return self._assumed(done, "no frame of the clip reached the Recording Server's live feed"
                                 + (f" (a hole of {hole:.1f} s in the feed)" if hole else ""), hole)
        first, last = min(samples, key=lambda s: s.idx), max(samples, key=lambda s: s.idx)
        slope = (last.rs - first.rs) / (last.idx - first.idx) if last.idx > first.idx else 1.0 / fps
        rs0 = first.rs - first.idx * slope                   # the clip's first frame, seen or not
        rs1 = first.rs + (frames - 1 - first.idx) * slope + 1.0 / fps   # just past its last frame
        start, end = math.floor(rs0 - margin_s), math.ceil(rs1 + margin_s)
        foreign = [s for s in self._between(start, end) if s.seq not in (0, seq)]
        before = [s.rs for s in foreign if s.rs < rs0]
        after = [s.rs for s in foreign if s.rs >= rs1]
        if before:
            start = math.ceil(max(before) + 1.0 / fps)
        if after:
            end = math.floor(min(after))
        drift = (last.rs - last.wall) - (first.rs - first.wall)
        hole = self.hole_s(wall_start, wall_end + 1.0)       # the feed's holes over the clip and its tail
        info = {"seq": seq, "seen": len(samples), "sent": sent, "frames": frames,
                "coverage": round(len(samples) / max(1, sent), 2), "first_idx": first.idx, "last_idx": last.idx,
                "offset_s": round(first.rs - first.wall, 2), "drift_s": round(drift, 2), "foreign": len(foreign),
                "hole_s": round(hole, 1),
                "verified": (len(samples) >= 3 and first.idx <= frames / 4 and last.idx >= 3 * frames / 4
                             and abs(drift) <= DRIFT_OK_S and not foreign and hole == 0.0
                             and start <= rs0 and rs1 <= end),
                "ready_wall": last.seen, "assumed": False}
        return _utc(start), _utc(end), info

    def _assumed(self, done: dict, reason: str, hole: float = 0.0) -> tuple[dt.datetime, dt.datetime, dict]:
        from lens.client import span
        start, end = span(done)
        off = self.offset(60.0)
        if off is not None:
            shift = dt.timedelta(seconds=round(off))
            start, end = start + shift, end + shift
        return start, end, {"seq": done["seq"], "seen": 0, "sent": done["sent"], "frames": done["frames"],
                            "coverage": 0.0, "offset_s": round(off, 2) if off is not None else None,
                            "hole_s": round(hole, 1), "verified": False, "assumed": True, "reason": reason,
                            "ready_wall": time.time()}
