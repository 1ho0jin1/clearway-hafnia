r"""The owner board (docs/PRODUCT.md, F4): one column per owner, one card per incident, the clip Hafnia judged playing.

    .venv\Scripts\python.exe -m clearway.board [--run run\clearway-live-<UTC> | --latest] [--port 8765]

A small standard-library web server on 127.0.0.1 that follows a run folder of the Clearway service as it grows: the
ledger's event log applied incrementally (Ledger.apply), the service log for questions, lens spans, answers and camera
health. It is a process of its own, so it can restart without the service, show a finished run, and costs the pipeline
nothing; --latest follows the newest run/clearway-* folder and switches when a new one starts. Smart Client shows the
page in an HTML page view item (F4); a browser on the machine works too.

    /               the board (clearway/board.html, polling /api/board every 2 s)
    /api/board      cards by owner, changes being checked, counts, camera health (JSON)
    /clips/<id>.mp4 the lens clip Hafnia judged, made from the lens spool on first request (H.264, cached in <run>/clips)
    /snaps/<id>.jpg the camera's frame at the end of that clip, the spot boxed (written by the service)
    /summary        the shift summary (F8, clearway/summary.html; /api/summary: clearway/summary.py on the same run,
                    recomputed at most every 10 s)
    /cameras/<camera>.jpg  the camera's scene image, the backdrop of the summary's hotspots (F9; written by the service)
    POST /api/operator  {"incident": "cw-0003", "verdict": "confirmed" | "rejected"}: an operator's verdict on a card
                    (F7), checked against the ledger and appended to <run>/operator.jsonl, which the running service
                    reads (clearway/service.py); the card shows it as pending until the ledger has it. Only from the
                    board's own page: JSON only, and Host and Origin must be this server (another web page open on the
                    machine could otherwise post here).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from clearway.ledger import OWNERS, Ledger
from clearway.summary import summarise
from lens.publisher import FFMPEG, SPOOL

REPO = Path(__file__).resolve().parent.parent
PAGE = Path(__file__).with_name("board.html")
SUMMARY_PAGE = Path(__file__).with_name("summary.html")
SUMMARY_EVERY_S = 10        # a long shift's logs take a second or two to summarise
OWNER_ORDER = list(dict.fromkeys(owner for owner, _ in OWNERS.values()))
PRIORITY = {owner: prio for owner, prio in OWNERS.values()}
INCIDENT_ID = re.compile(r"^cw-\d{4,}$")
SERVICE_QUIET_S = 60        # no line in service.jsonl for this long (health is every 15 s): the service is not running


class _Tail:
    """New complete lines of a growing JSONL file."""

    def __init__(self, path: Path):
        self.path, self.pos = path, 0

    def lines(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open("rb") as f:
            f.seek(self.pos)
            data = f.read()
        end = data.rfind(b"\n")
        if end < 0:
            return []
        self.pos += end + 1
        return [json.loads(x) for x in data[:end].decode("utf-8").splitlines() if x.strip()]


class RunFollower:
    """One run folder, followed as it grows."""

    def __init__(self, run: Path):
        self.run = run
        self.ledger = Ledger(None)
        self.ledger_tail, self.service_tail = _Tail(run / "ledger.jsonl"), _Tail(run / "service.jsonl")
        self.verdicts_tail = _Tail(run / "operator.jsonl")
        self.health: dict = {}
        self.answers: dict[str, dict] = {}
        self.spans: dict[str, list[str]] = {}
        self.not_asked: set[str] = set()           # stopped by the run cap, failed or errored: no answer is coming
        self.requested: dict[str, str] = {}        # incident -> the verdict last sent from the board
        self.refused: dict[str, str] = {}          # incident -> why the service did not apply it
        self.told: dict[str, dict[str, bool]] = {}  # incident -> {owner's target: its latest news delivered}
        self.requests = 0
        self.standin = False
        self.started = self.ended = None
        self.last_wall = 0.0                       # the service's latest log line
        self.lock = threading.Lock()

    def refresh(self) -> None:
        with self.lock:
            for e in self.ledger_tail.lines():
                self.ledger.apply(e)
            for v in self.verdicts_tail.lines():   # before the service's log: a refusal follows its request
                self.requested[v["incident"]] = v["verdict"]
                self.refused.pop(v["incident"], None)
            for e in self.service_tail.lines():
                k = e["kind"]
                self.last_wall = e["wall"]
                if k == "operator" and not e.get("applied") and e.get("incident"):
                    self.refused[e["incident"]] = e.get("reason") or "not applied"
                if k == "notify" and e.get("event") in ("opened", "reopened"):
                    self.told.setdefault(e["incident"], {})[e["target"]] = bool(e.get("ok"))
                if k == "start":
                    self.started = e["wall"]
                elif k == "end":
                    self.ended = e["wall"]
                elif k == "health":
                    self.health = e.get("cameras", {})
                elif k in ("lens", "direct"):
                    self.spans[e["incident"]] = e["span"]
                elif k in ("unanswered", "failed", "error") and e.get("incident"):
                    self.not_asked.add(e["incident"])
                elif k == "answer":
                    a = e.get("answer") or {}
                    self.answers[e["incident"]] = a
                    self.standin = self.standin or bool(a.get("standin"))
                    if "hafnia_s" in a:
                        self.requests += 1

    def state(self) -> dict:
        self.refresh()
        with self.lock:
            incs = list(self.ledger.incidents.values())
            cards = [self._card(i) for i in incs if i.category and not i.merged_into and i.state in
                     ("open", "cleared", "rejected")]
            checking = [{"id": i.id, "camera": i.camera, "t_report": i.t_report} for i in incs
                        if i.state == "pending" and i.id not in self.not_asked]
            owners = []
            for owner in OWNER_ORDER:
                mine = [c for c in cards if c["owner"] == owner]
                mine.sort(key=lambda c: (c["state"] != "open", -(c["t_occurrence"] if c["state"] == "open"
                                                                  else c["t_cleared"] or 0)))
                owners.append({"owner": owner, "priority": PRIORITY[owner], "cards": mine,
                               "open": sum(c["state"] == "open" for c in mine)})
            return {
                "run": self.run.name, "now": time.time(), "started": self.started, "ended": self.ended,
                "mode": "dry" if self.standin or self.run.name.startswith("clearway-dry") else "live",
                "verdicts": self._service_running(),
                "owners": owners, "checking": checking,
                "counts": {"open": sum(c["state"] == "open" for c in cards), "cards": len(cards),
                           "checking": len(checking), "questions": len(incs),   # each question opens an incident
                           "requests": self.requests,
                           "dismissed": sum(i.state == "dismissed" for i in incs)},
                "cameras": {c: {"fps": h.get("fps"), "lag_s": h.get("lag_s")} for c, h in self.health.items()},
            }

    def _service_running(self) -> bool:
        return self.started is not None and self.ended is None and time.time() - self.last_wall < SERVICE_QUIET_S

    def take_verdict(self, incident: str, verdict: str) -> str | None:
        """An operator's verdict from the board, passed on to the service (<run>/operator.jsonl); returns why not, or
        None."""
        self.refresh()
        with self.lock:
            if not self._service_running():
                return "the service is not running: this run has ended"
            if problem := self.ledger.verdict_problem(incident, verdict):
                return problem
            if self.requested.get(incident) == verdict and incident not in self.refused:
                return f"{incident}: already sent, waiting for the service"
            with (self.run / "operator.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"incident": incident, "verdict": verdict, "wall": round(time.time(), 3),
                                    "via": "board"}) + "\n")
            self.requested[incident] = verdict       # the tail reads it back later; a second click meanwhile is refused
            self.refused.pop(incident, None)
        return None

    def _card(self, i) -> dict:
        a = i.answer or {}
        asked = self.requested.get(i.id, "")
        return {"id": i.id, "camera": i.camera, "category": i.category, "owner": i.owner, "priority": i.priority,
                "state": i.state, "operator": i.operator, "alarm_open": i.alarm_open,
                "verdict_pending": asked if asked and asked != i.operator and i.id not in self.refused else "",
                "verdict_refused": self.refused.get(i.id, ""),
                "told": "" if i.id not in self.told else "sent" if all(self.told[i.id].values()) else "failed",
                "t_change": i.t_change, "t_occurrence": i.t_occurrence or i.t_change, "t_cleared": i.t_cleared,
                "t_answer": i.t_answer, "occurrences": i.occurrences,
                "summary": a.get("summary") or "", "object": a.get("object") or "", "standin": bool(a.get("standin")),
                # ?run=: incident ids start again in every run and these are cached for an hour, so a browser showed
                # the previous run's snapshot under the same id after the board switched runs (2026-10-25)
                "clip": f"/clips/{i.id}.mp4?run={self.run.name}" if i.clip else None,
                "snap": f"/snaps/{i.id}.jpg?run={self.run.name}" if (self.run / "snaps" / f"{i.id}.jpg").exists()
                else None}

    def clip(self, incident: str) -> Path | None:
        """The incident's crop as MP4, made from the spool's AVI on first request (the clip Hafnia judged on the lens,
        or the crop the service stored beside a direct ask on the camera's own recording)."""
        with self.lock:
            inc = self.ledger.incidents.get(incident)
            job = inc.clip if inc else ""
        if not job:
            return None
        out = self.run / "clips" / f"{incident}.mp4"
        if out.exists():
            return out
        src = SPOOL / f"{job}.avi"
        if not src.exists():
            return None
        out.parent.mkdir(exist_ok=True)
        tmp = out.with_suffix(".tmp.mp4")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(src), "-vf", "scale=640:-2:flags=lanczos",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", "-an", str(tmp)], check=True, timeout=60)
        tmp.replace(out)
        return out


class Board:
    def __init__(self, run: Path | None = None, latest: bool = False, runs: Path = REPO / "run"):
        self.latest, self.runs = latest, runs
        self.follower = RunFollower(run or self._newest())
        self._checked = time.monotonic()
        self._clip_lock = threading.Lock()
        self._summary_lock = threading.Lock()
        self._summary: tuple[Path, float, dict] | None = None    # run, when, summary

    def _newest(self) -> Path:
        found = sorted((p for p in self.runs.glob("clearway-*") if (p / "service.jsonl").exists()),
                       key=lambda p: (p / "service.jsonl").stat().st_mtime)
        if not found:
            raise SystemExit(f"no run/clearway-* folder with a service.jsonl in {self.runs}")
        return found[-1]

    def current(self) -> RunFollower:
        if self.latest and time.monotonic() - self._checked > 5:
            self._checked = time.monotonic()
            newest = self._newest()
            if newest != self.follower.run:
                self.follower = RunFollower(newest)
        return self.follower

    def clip(self, incident: str) -> Path | None:
        with self._clip_lock:      # one conversion at a time; later requests find the cached file
            return self.current().clip(incident)

    def summary(self) -> dict:
        run = self.current().run
        with self._summary_lock:
            if self._summary is None or self._summary[0] != run or (
                    time.monotonic() - self._summary[1] > SUMMARY_EVERY_S):
                self._summary = (run, time.monotonic(), summarise(run))
            return self._summary[2]


def make_handler(board: Board):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args) -> None:
            """One line per request with the browser engine (Smart Client's HTML page item: Edge WebView2 in standard
            display mode, Internet Explorer in compatibility mode); the board's 2 s polls are not logged."""
            agent = self.headers.get("User-Agent", "")
            if self.path.startswith(("/api/board", "/api/summary")):
                seen = board.__dict__.setdefault("_pollers", set())
                if agent in seen:
                    return
                seen.add(agent)                 # each browser's first poll only: it shows the page's script runs
            print(f"{time.strftime('%H:%M:%S')} {self.command} {self.path} {args[1] if len(args) > 1 else ''} "
                  f"| {self.headers.get('User-Agent', '')[:160]}", flush=True)

        def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store" if ctype.startswith(("application/json", "text/html"))
                             else "max-age=3600")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _file(self, path: Path, ctype: str) -> None:
            data = path.read_bytes()
            rng = re.match(r"bytes=(\d+)-(\d*)", self.headers.get("Range", ""))
            if rng:                             # video elements ask for ranges
                a = int(rng.group(1))
                b = min(int(rng.group(2)) if rng.group(2) else len(data) - 1, len(data) - 1)
                self._send(HTTPStatus.PARTIAL_CONTENT, data[a:b + 1], ctype,
                           {"Content-Range": f"bytes {a}-{b}/{len(data)}", "Accept-Ranges": "bytes"})
            else:
                self._send(HTTPStatus.OK, data, ctype, {"Accept-Ranges": "bytes"})

        def _json(self, status: int, obj: dict) -> None:
            self._send(status, json.dumps(obj).encode(), "application/json")

        def do_HEAD(self) -> None:
            self.do_GET()

        def do_POST(self) -> None:
            try:
                if self.path.split("?")[0] != "/api/operator":
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                port = self.server.server_address[1]
                ours = {f"127.0.0.1:{port}", f"localhost:{port}"}
                origin = self.headers.get("Origin")
                if self.headers.get("Host") not in ours or (origin and origin not in {f"http://{h}" for h in ours}):
                    return self._json(HTTPStatus.FORBIDDEN, {"error": "only from the board's own page"})
                if self.headers.get_content_type() != "application/json":
                    return self._json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "send JSON"})
                n = int(self.headers.get("Content-Length") or 0)
                if not 0 < n <= 1024:
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": "empty or too long"})
                body = json.loads(self.rfile.read(n))
                incident, verdict = body.get("incident"), body.get("verdict")
                if not isinstance(incident, str) or not INCIDENT_ID.match(incident) or verdict not in (
                        "confirmed", "rejected"):
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": "incident and verdict (confirmed|rejected)"})
                problem = board.current().take_verdict(incident, verdict)
                if problem:
                    return self._json(HTTPStatus.CONFLICT, {"error": problem})
                self._json(HTTPStatus.ACCEPTED, {"ok": True, "incident": incident, "verdict": verdict})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:              # the board must keep serving
                self._json(HTTPStatus.BAD_REQUEST if isinstance(e, (ValueError, AttributeError))
                           else HTTPStatus.INTERNAL_SERVER_ERROR, {"error": repr(e)})

        def do_GET(self) -> None:
            path = self.path.split("?")[0]
            try:
                if path in ("/", "/index.html"):
                    self._send(HTTPStatus.OK, PAGE.read_bytes(), "text/html; charset=utf-8")
                elif path == "/api/board":
                    self._send(HTTPStatus.OK, json.dumps(board.current().state()).encode(), "application/json")
                elif path == "/summary":
                    self._send(HTTPStatus.OK, SUMMARY_PAGE.read_bytes(), "text/html; charset=utf-8")
                elif path == "/api/summary":
                    self._send(HTTPStatus.OK, json.dumps(board.summary()).encode(), "application/json")
                elif m := re.match(r"^/clips/(cw-\d+)\.mp4$", path):
                    clip = board.clip(m.group(1))
                    if clip is None:
                        self._send(HTTPStatus.NOT_FOUND, b"no clip", "text/plain")
                    else:
                        self._file(clip, "video/mp4")
                elif (m := re.match(r"^/snaps/(cw-\d+)\.jpg$", path)) and INCIDENT_ID.match(m.group(1)):
                    snap = board.current().run / "snaps" / f"{m.group(1)}.jpg"
                    if snap.exists():
                        self._file(snap, "image/jpeg")
                    else:
                        self._send(HTTPStatus.NOT_FOUND, b"no snapshot", "text/plain")
                elif m := re.match(r"^/cameras/([A-Za-z0-9_-]+)\.jpg$", path):    # the hotspots' scene images
                    scene = board.current().run / "cameras" / f"{m.group(1)}.jpg"
                    if scene.exists():
                        self._file(scene, "image/jpeg")
                    else:
                        self._send(HTTPStatus.NOT_FOUND, b"no scene image", "text/plain")
                else:
                    self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:              # the board must keep serving
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, repr(e).encode(), "text/plain")

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--run", type=Path, help="a run folder of the Clearway service")
    src.add_argument("--latest", action="store_true", help="follow the newest run/clearway-* folder (the default)")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    board = Board(args.run, latest=args.run is None)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(board))
    print(f"board on http://127.0.0.1:{args.port}/ following {board.follower.run}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
