"""Read live frames from bridge/FrameBridge (C#, MIP .NET library) as (camera name, frame time, JPEG bytes)."""
from __future__ import annotations

import datetime as dt
import struct
import subprocess
import threading
from collections.abc import Iterator
from pathlib import Path

EXE = Path(__file__).resolve().parent.parent / "bridge" / "FrameBridge" / "bin" / "Release" / "FrameBridge.exe"
HEADER = struct.Struct("<iqi")   # camera index, frame time (Unix ms, UTC), JPEG length


class FrameBridge:
    def __init__(self, cameras: list[str], exe: Path = EXE, log=print, width: int = 0):
        """width: the JPEG width the Recording Server transcodes each camera to (0: the camera's own). Every frame
        of every camera is transcoded on the Recording Server, which also records and serves the gateway's exports:
        at full resolution eleven cameras starved it (M3, 2026-10-26: lens frames discarded, 3-5 fps delivered)."""
        self.cameras = cameras
        self.proc = subprocess.Popen([str(exe), "--width", str(width), *cameras], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        threading.Thread(target=self._pump_log, args=(log,), daemon=True).start()

    def _pump_log(self, log) -> None:
        for line in self.proc.stderr:
            log("bridge: " + line.decode(errors="replace").rstrip())

    def _read(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self.proc.stdout.read(n - len(buf))
            if not chunk:
                raise EOFError("FrameBridge stopped")
            buf += chunk
        return bytes(buf)

    def frames(self) -> Iterator[tuple[str, dt.datetime, bytes]]:
        while True:
            index, ms, length = HEADER.unpack(self._read(HEADER.size))
            yield (self.cameras[index], dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc), self._read(length))

    def close(self) -> None:
        try:
            self.proc.stdin.close()   # the bridge exits when stdin closes
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()
