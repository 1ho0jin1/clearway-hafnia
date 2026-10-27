"""Owner notifications: each incident's news sent to whoever owns it (docs/PRODUCT.md, "Who uses it").

The ledger decides (clearway/ledger.py); XProtect alarms (clearway/alarms.py) are one output, for the control room.
This is another, for the people whose job it is and who do not sit at the VMS: rail control, traffic operations,
street services, the asset owner, security. Per ledger effect, one event to each of the owner's targets:
- opened: a new card (its alarm raised): category, Hafnia's sentence (marked AI-generated), the camera, when the spot
  changed, a snapshot of the spot (targets that want it);
- reopened: it happened again after its alarm had closed;
- cleared: the spot has looked as before for the ledger's close_after_s, the alarm closed: stand down;
- confirmed / rejected: the operator's verdict (F7), from the board or from a phone.

Two kinds of target (config/owners.json, "type"):
- "webhook" (the default): a JSON POST (schema clearway.notification/1) to the owner's own system. A webhook URL
  usually carries its own credential, so the file names an environment variable that holds it (url_env), and an
  optional signing key the same way (secret_env: HMAC-SHA256 of the body in X-Clearway-Signature). Plain URLs are for
  receivers on this machine (scripts/owner_inbox.py).
- "ntfy": a push notification on the owner's phone through an ntfy topic (https://ntfy.sh, or a self-hosted ntfy
  server; the ntfy app on Android and iOS, or https://ntfy.sh/<topic> in a browser): a title, a short text, the
  priority from the incident's priority (High rings through, cleared and verdicts are quiet), a snapshot of the spot
  attached, and, when a reply topic is configured (reply_url_env), **Confirm** and **Reject** buttons. The topic is
  the credential, so its URL comes from an environment variable (url_env) and is never written to the logs. A tap on
  a button makes the phone post a small JSON to the reply topic; NtfyReplies, a thread in the service, follows that
  topic (outbound only: nothing can reach this machine from a phone) and appends the verdict to <run>/operator.jsonl,
  exactly as the board does (F7). With secret_env set, each button carries a token (HMAC-SHA256 of the incident and
  the verdict) that the listener checks, so a verdict needs a notification that was really sent. The public server's
  limits (ntfy.sh, per IP: 250 messages a day, 2 MB per attachment and 20 MB of attachments a day, 60 requests then
  one per 5 s) are guarded: one daily budget for all ntfy targets (past NTFY_DAILY_SOFT only new and returning
  incidents are pushed, past NTFY_DAILY_HARD nothing), max_per_hour per target (default 60), and the snapshot scaled
  down to NTFY_SNAPSHOT_WIDTH pixels.
URLs and keys never reach the logs: deliveries are logged by target name. Each target has its own thread, so one
slow or unreachable target cannot hold the others back, and gets its events in order. A delivery is retried on a
connection error, a timeout, 429 or 5xx (after 1 s and 4 s), not on another 4xx.

Self-test:  .venv\\Scripts\\python.exe -m clearway.notify --test [--owner "Rail control"] [--listen 120]
sends one sample "opened" notification (a drawn snapshot, no footage) to the owner's targets and, with --listen,
follows the reply topic for that long and prints the verdicts the phone's buttons send (scripts/setup_ntfy.ps1
creates the topic names and the secret).
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import deque
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "clearway.notification/1"
TIMEOUT_S = {"webhook": 5.0, "ntfy": 15.0}   # an ntfy push carries the snapshot
RETRY_AFTER_S = (1.0, 4.0)     # two retries
STREAM_TIMEOUT_S = 90.0        # ntfy sends a keepalive every 45 s on an open subscription
NTFY_DAILY_SOFT = 170          # ntfy pushes in 24 h, all targets, after which only opened / reopened are sent
NTFY_DAILY_HARD = 230          # ... after which nothing is sent (ntfy.sh allows 250 a day per IP)
NTFY_SNAPSHOT_WIDTH = 640      # the snapshot is scaled to this width for a push (about 40 KB; 20 MB a day per IP)
INCIDENT_ID = re.compile(r"cw-\d{4}")
CATEGORY = {"PERSON_ON_TRACKS": "Person on the tracks", "COLLISION": "Collision", "STALLED_VEHICLE": "Stalled vehicle",
            "OBSTRUCTION": "Obstruction", "DAMAGE": "Damage", "TAMPERING": "Tampering"}
# ntfy priorities: 5 rings and vibrates through do-not-disturb on most phones, 4 rings, 3 is a normal notification,
# 2 is silent. News of a new or returning incident takes the incident's XProtect priority; the rest is quiet.
NTFY_PRIORITY = {"High": 5, "Medium": 4, "Low": 3}
NTFY_QUIET = {"cleared": 3, "confirmed": 2, "rejected": 2}
NTFY_TAGS = {"PERSON_ON_TRACKS": "rotating_light,train", "COLLISION": "rotating_light,boom",
             "STALLED_VEHICLE": "warning,car", "OBSTRUCTION": "warning,construction", "DAMAGE": "warning,art",
             "TAMPERING": "warning,lock"}
NTFY_EVENT_TAGS = {"reopened": "repeat", "cleared": "white_check_mark", "confirmed": "white_check_mark", "rejected": "x"}


@dataclass
class Target:
    name: str                  # for the logs, instead of the URL
    url: str
    secret: bytes | None = None    # webhook: signs the body; ntfy: signs the buttons' verdict tokens
    snapshot: bool = False     # include the JPEG of the spot (camera footage leaves the machine with it)
    kind: str = "webhook"      # "webhook" | "ntfy"
    reply_url: str = ""        # ntfy: the topic the phone's Confirm / Reject buttons post to
    max_per_hour: int = 60     # ntfy: at most this many pushes an hour (the public server has limits)


def load_owners(path: Path) -> tuple[dict[str, list[Target]], str, list[str]]:
    """config/owners.json -> ({owner: [Target]}, public_base_url, problems). A target whose url_env is not set is left
    out, and named in problems; a missing secret_env or reply_url_env is named and the target kept."""
    cfg = json.loads(path.read_text(encoding="utf-8"))
    owners, problems, names = {}, [], set()
    for owner, targets in cfg.get("owners", {}).items():
        for t in targets:
            if t["name"] in names:
                problems.append(f"{owner} / {t['name']}: the name is taken by another target: left out")
                continue
            names.add(t["name"])
            kind = t.get("type", "webhook")
            if kind not in ("webhook", "ntfy"):
                problems.append(f"{owner} / {t['name']}: unknown type {kind!r}: left out")
                continue
            url = t.get("url") or os.environ.get(t.get("url_env", ""), "")
            if not url:
                problems.append(f"{owner} / {t['name']}: no url, and {t.get('url_env')} is not set")
                continue
            secret = None
            if t.get("secret_env"):
                if not os.environ.get(t["secret_env"]):
                    problems.append(f"{owner} / {t['name']}: {t['secret_env']} is not set: "
                                    + ("verdict tokens not checked" if kind == "ntfy" else "sent unsigned"))
                else:
                    secret = os.environ[t["secret_env"]].encode()
            reply_url = ""
            if kind == "ntfy":
                reply_url = t.get("reply_url") or os.environ.get(t.get("reply_url_env", ""), "")
                if t.get("reply_url_env") and not reply_url:
                    problems.append(f"{owner} / {t['name']}: {t['reply_url_env']} is not set: no Confirm / Reject "
                                    f"buttons")
            owners.setdefault(owner, []).append(Target(t["name"], url.rstrip("/"), secret, bool(t.get("snapshot")),
                                                       kind, reply_url.rstrip("/"), int(t.get("max_per_hour", 60))))
    return owners, cfg.get("public_base_url") or "http://127.0.0.1:8765", problems


def _iso(t: float | None) -> str | None:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(timespec="seconds") if t else None


def _hms(t: float | None) -> str:
    return f"{dt.datetime.fromtimestamp(t, dt.timezone.utc):%H:%M:%S} UTC" if t else "?"


def _header(value: str) -> str:
    """An HTTP header value: as is when plain ASCII on one line, otherwise RFC 2047 (ntfy decodes it; the text keeps
    its line breaks and Hafnia's punctuation)."""
    if "\n" not in value and "\r" not in value:
        try:
            value.encode("ascii")
            return value
        except UnicodeEncodeError:
            pass
    return "=?UTF-8?B?" + base64.b64encode(value.encode("utf-8")).decode("ascii") + "?="


def _local(url: str) -> bool:
    return (urllib.parse.urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1")


def _shrink(jpeg: bytes, width: int) -> bytes:
    """The snapshot scaled to a push's width (ntfy.sh allows 20 MB of attachments a day); as is without OpenCV."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return jpeg
    img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    if img is None or img.shape[1] <= width:
        return jpeg
    small = cv2.resize(img, (width, round(img.shape[0] * width / img.shape[1])), interpolation=cv2.INTER_AREA)
    return cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 75])[1].tobytes()


def _by(via: str | None, phone: str = "from their phone") -> str:
    return phone if via == "ntfy" else "on the board"


def verdict_token(secret: bytes, incident: str, verdict: str) -> str:
    return hmac.new(secret, f"{incident}:{verdict}".encode(), hashlib.sha256).hexdigest()[:16]


def event_of(effect: dict) -> str | None:
    if "alarm" in effect:
        return "reopened" if effect.get("reopen") else "opened"
    if "close_alarm" in effect:
        return "rejected" if effect.get("reason") == "rejected" else "cleared"
    if "confirm_alarm" in effect:
        return "confirmed"
    return None


def payload(event: str, effect: dict, inc: dict, run: str, base_url: str, dry_run: bool) -> dict:
    """The JSON an owner's target receives (without the snapshot: added per target)."""
    a = inc.get("answer") or {}
    said = a.get("summary") or ""
    what = CATEGORY.get(inc["category"], inc["category"])
    where = inc["camera"].replace("_", " ")
    changed = effect.get("t_change") or inc.get("t_occurrence") or inc["t_change"]
    cam = f"camera \"{where}\""
    text = {
        "opened": f"{what} for {inc['owner']}, {cam}: the spot changed at {_hms(changed)}."
                  + (f" Hafnia: \"{said}\" (AI-generated: check the clip.)" if said else ""),
        "reopened": f"Happened again: {what}, {cam} (occurrence {inc['occurrences']}): the spot changed at "
                    f"{_hms(changed)}.",
        "cleared": f"Clear: {what.lower()}, {cam}: the spot has looked as before since "
                   f"{_hms(effect.get('t_cleared'))}. No action needed.",
        "confirmed": f"Confirmed by the operator {_by(effect.get('via'))}: {what.lower()}, {cam}, is real.",
        "rejected": f"Not an incident: the operator rejected the {what.lower()} card {_by(effect.get('via'))}, {cam}. "
                    f"Stand down.",
    }[event]
    link = f"?run={run}"
    return {
        "schema": SCHEMA, "event": event, "incident": inc["id"], "run": run, "dry_run": dry_run,
        "via": effect.get("via"),
        "owner": inc["owner"], "priority": inc["priority"], "category": inc["category"], "camera": inc["camera"],
        "occurrences": inc["occurrences"], "changed_at": _iso(changed), "at": _iso(effect.get("t")),
        "summary": {"text": said, "by": "Hafnia VLM", "ai_generated": True} if said else None,
        "text": ("[dry run] " if dry_run else "") + text,
        "links": {"board": f"{base_url}/", "clip": f"{base_url}/clips/{inc['id']}.mp4{link}" if inc.get("clip") else None,
                  "snapshot": f"{base_url}/snaps/{inc['id']}.jpg{link}"},
    }


def phone_message(msg: dict) -> tuple[str, str]:
    """(title, text) for a push notification, from the webhook payload: short, the incident id last."""
    what = CATEGORY.get(msg["category"], msg["category"])
    where = msg["camera"].replace("_", " ")
    changed = msg["changed_at"][11:19] + " UTC" if msg.get("changed_at") else "?"
    said = (msg.get("summary") or {}).get("text") or ""
    prefix = "[dry run] " if msg.get("dry_run") else ""
    event = msg["event"]
    title = {"opened": f"{what} - {msg['owner']}", "reopened": f"Again: {what} - {msg['owner']}",
             "cleared": f"Clear: {what} - {msg['owner']}", "confirmed": f"Confirmed: {what} - {msg['owner']}",
             "rejected": f"Rejected: {what} - {msg['owner']}"}[event]
    text = {
        "opened": f"Camera \"{where}\", the spot changed at {changed}."
                  + (f"\nHafnia: \"{said}\" (AI-generated, check the clip)" if said else ""),
        "reopened": f"Camera \"{where}\", again at {changed} (occurrence {msg['occurrences']}).",
        "cleared": f"Camera \"{where}\": the spot has looked as before for a minute. No action needed.",
        "confirmed": f"The operator confirmed the {what.lower()} at camera \"{where}\" as real "
                     f"({_by(msg.get('via'), 'from the phone')}).",
        "rejected": f"The operator rejected the {what.lower()} card at camera \"{where}\" "
                    f"({_by(msg.get('via'), 'from the phone')}). Stand down.",
    }[event]
    return prefix + title, f"{text}\nIncident {msg['incident']}"


class OwnerNotifier:
    def __init__(self, owners: dict[str, list[Target]], log: Callable[..., None], run: str,
                 base_url: str = "http://127.0.0.1:8765", dry_run: bool = False, out: Path | None = None):
        """owners: load_owners()'s targets. log(kind, **fields): the service's log. run: the run folder's name. out:
        the run folder; with it, the verdicts that phones send to an ntfy reply topic are appended to
        <out>/operator.jsonl for the service (NtfyReplies)."""
        self.owners, self.log, self.run, self.base_url, self.dry_run = owners, log, run, base_url, dry_run
        self.pools = {t.name: ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"notify-{t.name}")
                      for ts in owners.values() for t in ts}
        self.pending: list[Future] = []
        self.sent: dict[str, deque[float]] = {t.name: deque() for ts in owners.values() for t in ts}
        self.sent_day: deque[float] = deque()           # every ntfy push, all targets: this machine is one visitor
        self.guard_lock = threading.Lock()
        self.listeners: list[NtfyReplies] = []
        if out is not None:
            seen: dict[str, NtfyReplies] = {}
            for ts in owners.values():
                for t in ts:
                    if t.kind == "ntfy" and t.reply_url and t.reply_url not in seen:
                        seen[t.reply_url] = NtfyReplies(t.reply_url, t.secret, out / "operator.jsonl", log)
            self.listeners = list(seen.values())
            for li in self.listeners:
                li.start()

    def submit(self, effect: dict, incident: dict, evidence: dict) -> None:
        """effect: the ledger's {"alarm" | "close_alarm" | "confirm_alarm": ...}; incident: Incident.public();
        evidence: {"jpeg", "size", ...} (the snapshot the XProtect alarm gets too)."""
        event = event_of(effect)
        targets = self.owners.get(incident.get("owner") or "", [])
        if event is None or not targets:
            return
        body = payload(event, effect, incident, self.run, self.base_url, self.dry_run)
        for t in targets:
            msg = dict(body)
            jpeg = evidence.get("jpeg") if t.snapshot and event in ("opened", "reopened") else None
            if jpeg and t.kind == "webhook":
                w, h = evidence.get("size") or (None, None)
                msg["snapshot"] = {"jpeg_base64": base64.b64encode(jpeg).decode(), "width": w, "height": h}
            self.pending.append(self.pools[t.name].submit(self._deliver, t, msg, jpeg, time.time()))

    # --- one delivery ----------------------------------------------------------------------------------------------
    def _deliver(self, t: Target, msg: dict, jpeg: bytes | None, submitted: float) -> None:
        if t.kind == "ntfy":
            guard = self._guard(t, msg["event"])
            if guard:
                self.log("notify", incident=msg["incident"], owner=msg["owner"], target=t.name, event=msg["event"],
                         ok=False, status=None, error=guard, attempts=0, bytes=0, snapshot=False, seconds=0.0,
                         changed_at=msg["changed_at"])
                return
            make, size = self._ntfy_request(t, msg, jpeg)
        else:
            make, size = self._webhook_request(t, msg)
        status, error, attempt, resp = self._send(t, make)
        self.log("notify", incident=msg["incident"], owner=msg["owner"], target=t.name, event=msg["event"],
                 ok=error is None, status=status, error=error, attempts=attempt, bytes=size,
                 snapshot=jpeg is not None, seconds=round(time.time() - submitted, 2), changed_at=msg["changed_at"],
                 **({"push": resp.get("id")} if t.kind == "ntfy" and resp.get("id") else {}))

    def _guard(self, t: Target, event: str) -> str | None:
        """ntfy: skip a push past the public server's limits: max_per_hour per target, and one daily budget for all
        ntfy targets (this machine is one visitor to ntfy.sh): past NTFY_DAILY_SOFT only new and returning incidents
        go out, past NTFY_DAILY_HARD nothing. A looped incident that keeps clearing and reopening would otherwise
        flood a phone and spend the day's 250."""
        now = time.monotonic()
        with self.guard_lock:
            q, day = self.sent[t.name], self.sent_day
            while q and now - q[0] > 3600:
                q.popleft()
            while day and now - day[0] > 86400:
                day.popleft()
            if len(q) >= t.max_per_hour:
                return f"rate guard: {t.max_per_hour} pushes in the last hour"
            if len(day) >= NTFY_DAILY_HARD:
                return f"rate guard: {NTFY_DAILY_HARD} pushes in 24 h"
            if len(day) >= NTFY_DAILY_SOFT and event not in ("opened", "reopened"):
                return f"rate guard: {NTFY_DAILY_SOFT} pushes in 24 h, only new and returning incidents go out"
            q.append(now)
            day.append(now)
        return None

    def _webhook_request(self, t: Target, msg: dict):
        data = json.dumps(msg).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "Clearway", "X-Clearway-Event": msg["event"],
                   "X-Clearway-Delivery": str(uuid.uuid4())}
        if t.secret:
            headers["X-Clearway-Signature"] = "sha256=" + hmac.new(t.secret, data, hashlib.sha256).hexdigest()
        return (lambda: urllib.request.Request(t.url, data=data, headers=headers, method="POST")), len(data)

    def _ntfy_request(self, t: Target, msg: dict, jpeg: bytes | None):
        """A push: the text in headers and the snapshot as the body when there is one (ntfy attaches it), else the
        text as the body. New and returning incidents get Confirm / Reject buttons that post to the reply topic."""
        title, text = phone_message(msg)
        event = msg["event"]
        priority = NTFY_QUIET.get(event) or NTFY_PRIORITY.get(msg["priority"], 3)
        tags = ",".join(x for x in (NTFY_EVENT_TAGS.get(event, ""), NTFY_TAGS.get(msg["category"], "warning")) if x)
        headers = {"User-Agent": "Clearway", "Title": _header(title), "Priority": str(priority), "Tags": tags}
        actions = []
        if t.reply_url and event in ("opened", "reopened"):
            for verdict, label in (("confirmed", "Confirm"), ("rejected", "Reject")):
                body = {"incident": msg["incident"], "verdict": verdict}
                if t.secret:
                    body["token"] = verdict_token(t.secret, msg["incident"], verdict)
                actions.append(f"http, {label}, {t.reply_url}, method=POST, body='{json.dumps(body)}', clear=true")
        if not _local(self.base_url):
            headers["Click"] = msg["links"]["board"]
            actions.append(f"view, Board, {msg['links']['board']}")
        if actions:
            headers["Actions"] = "; ".join(actions)
        if jpeg:
            jpeg = _shrink(jpeg, NTFY_SNAPSHOT_WIDTH)
            headers.update({"Filename": f"{msg['incident']}.jpg", "Content-Type": "image/jpeg",
                            "Message": _header(text)})
            return (lambda: urllib.request.Request(t.url, data=jpeg, headers=headers, method="PUT")), len(jpeg)
        data = text.encode("utf-8")
        headers["Content-Type"] = "text/plain; charset=utf-8"
        return (lambda: urllib.request.Request(t.url, data=data, headers=headers, method="POST")), len(data)

    def _send(self, t: Target, make: Callable[[], urllib.request.Request]) -> tuple[int | None, str | None, int, dict]:
        status, error, attempt, resp = None, None, 0, {}
        for attempt, wait in enumerate((0.0, *RETRY_AFTER_S), start=1):
            time.sleep(wait)
            try:
                with urllib.request.urlopen(make(), timeout=TIMEOUT_S[t.kind]) as r:
                    status, error = r.status, None
                    raw = r.read()
                try:
                    resp = json.loads(raw) if raw else {}
                except ValueError:
                    resp = {}
                if not isinstance(resp, dict):
                    resp = {}
                break
            except urllib.error.HTTPError as e:
                status, error = e.code, f"HTTP {e.code}"
                if e.code != 429 and e.code < 500:
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                status, error = None, repr(getattr(e, "reason", e))
            except Exception as e:              # a bad URL, say: not worth retrying, and never fatal to the service
                status, error = None, repr(e)
                break
        return status, error, attempt, resp

    def drain(self) -> None:
        for f in list(self.pending):
            f.result()
        for p in self.pools.values():
            p.shutdown()
        for li in self.listeners:
            li.stop.set()


class NtfyReplies(threading.Thread):
    """Follows an ntfy reply topic (an open HTTP subscription, reconnected when it drops; outbound only) for the
    verdicts that the phones' Confirm / Reject buttons post, and appends each to <run>/operator.jsonl the way the
    board does (F7); the service reads that file every second (Service._verdicts). Replies from before the listener
    started are ignored; each ntfy message is taken once; with a secret, the token must match."""

    def __init__(self, url: str, secret: bytes | None, operator_log: Path, log: Callable[..., None],
                 since: float | None = None):
        super().__init__(name="ntfy-replies", daemon=True)
        self.url, self.secret, self.path, self.log = url, secret, operator_log, log
        self.since = str(int(since if since is not None else time.time()))   # then the last message id
        self.seen: set[str] = set()
        self.stop = threading.Event()
        self.connected = threading.Event()

    def run(self) -> None:
        while not self.stop.is_set():
            try:
                req = urllib.request.Request(f"{self.url}/json?since={self.since}", headers={"User-Agent": "Clearway"})
                with urllib.request.urlopen(req, timeout=STREAM_TIMEOUT_S) as r:
                    for line in r:
                        if self.stop.is_set():
                            break
                        self._line(line)
            except Exception as e:                   # the subscription dropped: reconnect from the last id
                if not self.stop.is_set():
                    self.log("notify_reply", ok=False, error=repr(e)[:200])
                    time.sleep(3.0)

    def _line(self, line: bytes) -> None:
        try:
            d = json.loads(line)
        except ValueError:
            return
        if d.get("event") == "open":
            self.connected.set()
        if d.get("event") != "message" or not d.get("id"):
            return
        self.since = d["id"]
        if d["id"] in self.seen:
            return
        self.seen.add(d["id"])
        try:
            v = json.loads(d.get("message") or "")
        except ValueError:
            v = {}
        incident, verdict = v.get("incident") if isinstance(v, dict) else None, v.get("verdict") if isinstance(v, dict) else None
        if not isinstance(incident, str) or not INCIDENT_ID.fullmatch(incident) or verdict not in ("confirmed", "rejected"):
            self.log("notify_reply", ok=False, reply=d["id"], error="not a verdict")
            return
        if self.secret and not hmac.compare_digest(str(v.get("token", "")), verdict_token(self.secret, incident, verdict)):
            self.log("notify_reply", ok=False, reply=d["id"], incident=incident, verdict=verdict, error="bad token")
            return
        rec = {"incident": incident, "verdict": verdict, "wall": round(time.time(), 3), "via": "ntfy", "reply": d["id"]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        self.log("notify_reply", ok=True, reply=d["id"], incident=incident, verdict=verdict,
                 since_tap_s=round(time.time() - float(d.get("time") or time.time()), 1))


# --- self-test ---------------------------------------------------------------------------------------------------
def _sample_snapshot() -> bytes:
    """A drawn stand-in for the spot's snapshot (no footage leaves the machine in a test)."""
    import cv2
    import numpy as np
    img = np.full((360, 640, 3), 70, np.uint8)
    cv2.rectangle(img, (240, 150), (400, 300), (0, 0, 255), 3)
    cv2.putText(img, "Clearway test: the spot", (150, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()


def _main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Send one sample owner notification to the configured targets")
    ap.add_argument("--test", action="store_true", help="send a sample 'opened' notification")
    ap.add_argument("--owner", default="Rail control")
    ap.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config" / "owners.json")
    ap.add_argument("--listen", type=float, default=0.0,
                    help="then follow the ntfy reply topic for this many seconds and print the verdicts received")
    args = ap.parse_args()
    if not args.test and not args.listen:
        ap.error("nothing to do: --test and/or --listen")
    owners, base_url, problems = load_owners(args.config)
    for p in problems:
        print("note:", p)
    targets = owners.get(args.owner, [])
    if not targets:
        print(f"no targets for owner {args.owner!r} (owners: {sorted(owners)})")
        return 1

    def log(kind: str, **fields) -> None:
        print(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%S} {kind}: {json.dumps(fields)}")

    out = Path(__file__).resolve().parent.parent / "run" / "notify-test"
    notifier = OwnerNotifier(owners, log, "notify-test", base_url, out=out if args.listen else None)
    if args.test:
        now = time.time()
        inc = {"id": "cw-0000", "camera": "person_on_railway_tracks", "category": "PERSON_ON_TRACKS",
               "owner": args.owner, "priority": "High", "occurrences": 1, "t_change": now - 30, "t_occurrence": now - 30,
               "clip": "", "answer": {"summary": "A person in a red jacket climbs down onto the tracks and walks "
                                                 "along them (sample text, not a real answer)."}}
        notifier.submit({"alarm": "cw-0000", "t": now, "t_change": now - 30}, inc, {"jpeg": _sample_snapshot(),
                                                                                     "size": (640, 360)})
        for f in list(notifier.pending):
            f.result()
    if args.listen:
        if not notifier.listeners:
            print("no reply topic configured (reply_url_env): nothing to listen to")
        else:
            print(f"listening {args.listen:.0f} s for Confirm / Reject taps; verdicts go to {out / 'operator.jsonl'}")
            time.sleep(args.listen)
    notifier.drain()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
