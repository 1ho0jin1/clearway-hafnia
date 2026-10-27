r"""publisher.py - the lens camera's video source: one RTSP stream that XProtect records as camera lens_1.

    .venv\Scripts\python.exe -m lens.publisher [--path lens1] [--size 1280x720] [--fps 10] [--no-wallclock]

Streams frames to MediaMTX (rtsp://127.0.0.1:8554/<path>, see lens/mediamtx.yml) through ffmpeg at a steady frame
rate, forever: an idle frame when there is nothing to show, and each lens clip in turn when one arrives. Clips are
spool jobs written by lens/client.py: <id>.avi plus <id>.json (written last). Each clip is scaled to the stream size
and played in real time, then its last frame is held for a short tail. <id>.done.json then holds the UTC span the clip
played by this process's clock, its job number (seq) and how many frames were sent.

Every frame carries the frame code of lens/code.py in its bottom 16 pixels: the job number, the frame's index and the
wall time it was sent. The recording's time base is not the publisher's: XProtect's Universal driver timestamps the
stream by its own time, which ran 0.3-9.5 s behind the wall clock under load during M3 (run/lens-check-20261027), so
Hafnia was shown neighbouring clips. lens/clock.py reads the code back from lens_1's frames and measures where each
clip really is in the recording. Against the cause, ffmpeg stamps the raw frames with the wall clock
(-use_wallclock_as_timestamps; --no-wallclock restores stamping by count, for comparison): a frame the publisher
drops when the machine is busy then leaves a gap in the stream's time instead of pulling it behind.

The stream never stops between clips: a camera whose stream drops needs time to reconnect, and XProtect would miss the
start of the next clip. Clips start on a whole UTC second and are separated by an idle gap, because the gateway takes
clip times in whole seconds: a request then never includes a neighbouring clip (first test, 2026-10-21: without both,
each request caught about 1 s of the clip before it). Started detached by scripts\start_lens.ps1; logs to run\lens\.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

from lens.code import SEQ_MOD, stamp

REPO = Path(__file__).resolve().parent.parent
FFMPEG = r"C:\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
SPOOL = REPO / "run" / "lens" / "spool"


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def idle_frame(w: int, h: int) -> np.ndarray:
    """Static but for the frame code's band (lens_1 records always: scripts/setup_lens.ps1)."""
    img = np.full((h, w, 3), 40, np.uint8)
    cv2.putText(img, "lens idle", (w // 2 - 75, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (90, 90, 90), 2)
    return img


def fit(frame: np.ndarray, w: int, h: int) -> np.ndarray:
    """Scale to the stream size, keeping the aspect ratio (black bars where it differs)."""
    fh, fw = frame.shape[:2]
    if (fw, fh) == (w, h):
        return frame
    s = min(w / fw, h / fh)
    nw, nh = round(fw * s), round(fh * s)
    out = np.zeros((h, w, 3), np.uint8)
    x, y = (w - nw) // 2, (h - nh) // 2
    out[y:y + nh, x:x + nw] = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    return out


class Encoder:
    """ffmpeg reading raw frames on stdin and publishing H.264 over RTSP/TCP; restarted if it dies.

    With wallclock, each raw frame is stamped with the time ffmpeg read it (in hundredths of a second: the demuxer's
    -framerate only sets that resolution; an input -r would make ffmpeg regenerate the stamps by count) and the
    output is resampled to a constant fps from those stamps, so the stream's time follows the wall clock whatever the
    publisher managed to send. Without it, frames are stamped by count: every frame the publisher does not send
    pulls the stream's time behind."""

    def __init__(self, url: str, w: int, h: int, fps: int, log: Path, wallclock: bool = True):
        inp = (["-use_wallclock_as_timestamps", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                "-framerate", "100", "-i", "-"] if wallclock else
               ["-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"])
        out = ["-fps_mode", "cfr", "-r", str(fps)] if wallclock else []
        self.cmd = [FFMPEG, "-loglevel", "warning", *inp, "-an", "-c:v", "libx264", "-preset", "veryfast",
                    "-tune", "zerolatency", "-profile:v", "main", "-pix_fmt", "yuv420p", "-g", str(fps),
                    "-keyint_min", str(fps), "-sc_threshold", "0", "-bf", "0", *out, "-f", "rtsp",
                    "-rtsp_transport", "tcp", url]
        self.log = log
        self.proc: subprocess.Popen | None = None

    def write(self, frame: np.ndarray) -> None:
        if self.proc is None or self.proc.poll() is not None:
            print(f"{iso(utc_now())} starting ffmpeg: {subprocess.list2cmdline(self.cmd[1:])}", flush=True)
            self.proc = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                         stderr=self.log.open("ab"))
        try:
            self.proc.stdin.write(frame.tobytes())
        except OSError:   # MediaMTX restarted or ffmpeg died: the next frame starts a new ffmpeg
            self.proc.kill()
            self.proc = None


class Job:
    def __init__(self, spec: Path, w: int, h: int, fps: int, seq: int):
        self.spec = spec
        self.meta = json.loads(spec.read_text(encoding="utf-8"))
        self.cap = cv2.VideoCapture(str(spec.with_name(self.meta["video"])))
        self.w, self.h, self.fps, self.seq = w, h, fps, seq
        self.tail = round(float(self.meta.get("tail_s", 1.0)) * fps)
        self.frames = 0                     # clip frames read
        self.sent = 0                       # frames sent: clip frames, then the held tail (the frame code's index)
        self.last: np.ndarray | None = None
        self.start: dt.datetime | None = None
        self.end: dt.datetime | None = None
        now = utc_now()
        self.begin_at = now.replace(microsecond=0) + dt.timedelta(seconds=1)   # the next whole second

    def next_frame(self) -> np.ndarray | None:
        """Idle until the whole second, the clip's frames, then its last frame held for the tail; None when done."""
        if self.start is None and utc_now() < self.begin_at:
            return IDLE
        if self.end is None:
            ok, f = self.cap.read()
            if ok:
                self.frames += 1
                self.last = fit(f, self.w, self.h)
                return self.last
            self.end = utc_now()
            self.cap.release()
        if self.last is not None and self.tail > 0:
            self.tail -= 1
            return self.last
        return None

    def finish(self) -> dict:
        done = {"id": self.meta["id"], "start": iso(self.start or utc_now()), "end": iso(self.end or utc_now()),
                "frames": self.frames, "sent": self.sent, "seq": self.seq, "fps": self.fps,
                "meta": self.meta.get("meta", {})}
        tmp = self.spec.with_name(self.meta["id"] + ".done.json.tmp")
        tmp.write_text(json.dumps(done), encoding="utf-8")
        tmp.replace(self.spec.with_name(self.meta["id"] + ".done.json"))   # in one step: clients poll for it
        with (self.spec.parent.parent / "played.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(done) + "\n")
        return done


IDLE = np.zeros((1, 1, 3), np.uint8)   # placeholder: main() substitutes the idle frame


def next_job(spool: Path, w: int, h: int, fps: int, seq: int) -> Job | None:
    for spec in sorted(spool.glob("*.json")):
        if spec.name.endswith(".done.json") or spec.with_name(spec.stem + ".done.json").exists():
            continue
        try:
            return Job(spec, w, h, fps, seq)
        except (OSError, ValueError, KeyError) as e:   # unreadable job: mark it done with the error, move on
            spec.with_name(spec.stem + ".done.json").write_text(json.dumps({"id": spec.stem, "error": str(e)}),
                                                                encoding="utf-8")
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--path", default="lens1", help="RTSP path on MediaMTX")
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--spool", type=Path, default=SPOOL)
    ap.add_argument("--gap", type=float, default=2.0, help="idle seconds between clips")
    ap.add_argument("--wallclock", action=argparse.BooleanOptionalAction, default=True,
                    help="ffmpeg stamps frames with the wall clock (default) or by count")
    args = ap.parse_args()
    w, h = (int(v) for v in args.size.split("x"))
    args.spool.mkdir(parents=True, exist_ok=True)
    enc = Encoder(f"rtsp://127.0.0.1:8554/{args.path}", w, h, args.fps, args.spool.parent / "ffmpeg.log",
                  wallclock=args.wallclock)
    idle = idle_frame(w, h)
    period = 1.0 / args.fps
    job: Job | None = None
    seq = int(time.time()) % (SEQ_MOD - 1) + 1       # job numbers 1..SEQ_MOD-1 (0 is the idle frame); a restart
    idle_n = 0                                      # lands elsewhere, so a stale number is never matched
    next_t = time.monotonic()
    next_poll = 0.0
    print(f"{iso(utc_now())} lens publisher: rtsp://127.0.0.1:8554/{args.path} {w}x{h} at {args.fps} fps, "
          f"spool {args.spool}, frame code on, timestamps by {'wall clock' if args.wallclock else 'count'}",
          flush=True)
    while True:
        if job is None and time.monotonic() >= next_poll:
            job = next_job(args.spool, w, h, args.fps, seq)
            next_poll = time.monotonic() + 0.5
            if job:
                seq = seq % (SEQ_MOD - 1) + 1
                print(f"{iso(utc_now())} playing {job.meta['id']} as seq {job.seq}", flush=True)
        frame = job.next_frame() if job else None
        if job and frame is None:
            done = job.finish()
            print(f"{iso(utc_now())} played {done['id']}: {done['start']} - {done['end']}, {done['frames']} frames, "
                  f"{done['sent']} sent", flush=True)
            job = None
            next_poll = time.monotonic() + args.gap
        playing = frame is not None and frame is not IDLE
        now = utc_now()
        if playing:
            enc.write(stamp(frame, job.seq, job.sent, now))
            job.sent += 1
            if job.start is None:
                job.start = now
        else:
            enc.write(stamp(idle, 0, idle_n, now))
            idle_n = (idle_n + 1) % 1024
        next_t += period
        delay = next_t - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        elif delay < -1.0:   # fell behind (machine busy): resynchronize instead of bursting frames
            next_t = time.monotonic()


if __name__ == "__main__":
    main()
