r"""owner_inbox.py - a stand-in for the owners' own channels: receives Clearway's owner notifications (clearway/notify.py)
and shows them per owner, as each team's chat or phone would.

    .venv\Scripts\python.exe scripts\owner_inbox.py [--port 8770]      (scripts\start_inbox.ps1 starts it detached)

    POST /hook/<owner>   one notification (JSON, clearway.notification/1). With CLEARWAY_HOOK_SECRET set, the
                         X-Clearway-Signature header must be the body's HMAC-SHA256 with it, or 401
    GET  /               the inbox page (scripts/owner_inbox.html), polling /api/messages
    GET  /api/messages?after=N   messages after the N-th, oldest first, without their snapshots
    GET  /snap/<n>.jpg   the n-th message's snapshot of the spot

Messages are kept in memory and appended to run\inbox\received.jsonl (git-ignored: snapshots are camera footage), and
read back from it on start. 127.0.0.1 only. A test tool: a real owner's channel is their Teams, Slack, phone or
work-order system.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGE = Path(__file__).with_name("owner_inbox.html")
STORE = REPO / "run" / "inbox" / "received.jsonl"
SECRET_ENV = "CLEARWAY_HOOK_SECRET"


class Inbox:
    def __init__(self, store: Path = STORE):
        self.store, self.lock = store, threading.Lock()
        self.messages: list[dict] = []
        self.snaps: list[bytes | None] = []
        if store.exists():
            for line in store.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._keep(json.loads(line))

    def _keep(self, rec: dict) -> None:
        snap = (rec["message"].get("snapshot") or {}).get("jpeg_base64")
        self.snaps.append(base64.b64decode(snap) if snap else None)
        msg = {k: v for k, v in rec["message"].items() if k != "snapshot"}
        self.messages.append({"n": len(self.messages) + 1, "hook": rec["hook"], "received": rec["received"],
                              "signed": rec["signed"], "has_snap": snap is not None, **msg})

    def add(self, hook: str, message: dict, signed: bool) -> int:
        rec = {"hook": hook, "received": round(time.time(), 3), "signed": signed, "message": message}
        with self.lock:
            self.store.parent.mkdir(parents=True, exist_ok=True)
            with self.store.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            self._keep(rec)
            return len(self.messages)


def make_handler(inbox: Inbox, secret: bytes | None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args) -> None:
            if not self.path.startswith(("/api/", "/snap/")):
                print(f"{time.strftime('%H:%M:%S')} {self.command} {self.path} {args[1] if len(args) > 1 else ''}",
                      flush=True)

        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store" if not ctype.startswith("image/") else "max-age=3600")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            m = re.match(r"^/hook/([a-z0-9-]{1,40})$", self.path)
            if not m:
                return self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            if self.headers.get_content_type() != "application/json":
                return self._send(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, b"send JSON", "text/plain")
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 < n <= 5_000_000:
                return self._send(HTTPStatus.BAD_REQUEST, b"empty or too long", "text/plain")
            body = self.rfile.read(n)
            signed = False
            if secret is not None:
                want = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(want, self.headers.get("X-Clearway-Signature", "")):
                    print(f"{time.strftime('%H:%M:%S')} refused: bad or missing signature on /hook/{m.group(1)}",
                          flush=True)
                    return self._send(HTTPStatus.UNAUTHORIZED, b"bad signature", "text/plain")
                signed = True
            try:
                msg = json.loads(body)
                assert isinstance(msg, dict) and msg.get("schema", "").startswith("clearway.notification/")
            except (ValueError, AssertionError):
                return self._send(HTTPStatus.BAD_REQUEST, b"not a Clearway notification", "text/plain")
            n = inbox.add(m.group(1), msg, signed)
            self._send(HTTPStatus.OK, json.dumps({"ok": True, "n": n}).encode(), "application/json")

        def do_GET(self) -> None:
            path, _, query = self.path.partition("?")
            if path == "/":
                self._send(HTTPStatus.OK, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/messages":
                after = int(m.group(1)) if (m := re.search(r"after=(\d+)", query)) else 0
                with inbox.lock:
                    out = inbox.messages[after:]
                self._send(HTTPStatus.OK, json.dumps({"messages": out, "signing": secret is not None}).encode(),
                           "application/json")
            elif (m := re.match(r"^/snap/(\d+)\.jpg$", path)) and 0 < int(m.group(1)) <= len(inbox.snaps) \
                    and inbox.snaps[int(m.group(1)) - 1]:
                self._send(HTTPStatus.OK, inbox.snaps[int(m.group(1)) - 1], "image/jpeg")
            else:
                self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8770)
    args = ap.parse_args()
    secret = os.environ.get(SECRET_ENV)
    inbox = Inbox()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(inbox, secret.encode() if secret else None))
    print(f"owner inbox on http://127.0.0.1:{args.port}/ ({len(inbox.messages)} messages kept; "
          f"{'signatures checked' if secret else 'unsigned messages accepted'})", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
