"""Owner notifications: each incident's news sent to whoever owns it, as a JSON webhook (docs/PRODUCT.md, "Who uses it").

The ledger decides (clearway/ledger.py); XProtect alarms (clearway/alarms.py) are one output, for the control room.
This is another, for the people whose job it is and who do not sit at the VMS: rail control, traffic operations,
street services, the asset owner, security. Per ledger effect, one event to each of the owner's targets:
- opened: a new card (its alarm raised): category, Hafnia's sentence (marked AI-generated), the camera, when the spot
  changed, a snapshot of the spot (targets that want it);
- reopened: it happened again after its alarm had closed;
- cleared: the spot has looked as before for the ledger's close_after_s, the alarm closed: stand down;
- confirmed / rejected: the operator's verdict on the board (F7); rejected means not an incident: stand down.
Targets come from config/owners.json. A real webhook URL usually carries its own credential, so the file names an
environment variable that holds it (url_env), and an optional signing key the same way (secret_env: HMAC-SHA256 of
the body in X-Clearway-Signature, so a receiver can check the sender). Plain URLs are for receivers on this machine
(scripts/owner_inbox.py). URLs and keys never reach the logs: deliveries are logged by target name.
Each target has its own thread, so one slow or unreachable target cannot hold the others back, and gets its events in
order. A delivery is retried on a connection error, a timeout, 429 or 5xx (after 1 s and 4 s), not on another 4xx.

One-way: the links (board, clip, snapshot) work only where the board is reachable (public_base_url; 127.0.0.1 on the
hackathon machines), so owners cannot confirm or reject from the message yet.
TODO: Microsoft Teams and Slack message formats (their incoming webhooks want their own JSON); until then a relay
turns this JSON into their message.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "clearway.notification/1"
TIMEOUT_S = 5.0
RETRY_AFTER_S = (1.0, 4.0)     # two retries
CATEGORY = {"PERSON_ON_TRACKS": "Person on the tracks", "COLLISION": "Collision", "STALLED_VEHICLE": "Stalled vehicle",
            "OBSTRUCTION": "Obstruction", "DAMAGE": "Damage", "TAMPERING": "Tampering"}


@dataclass
class Target:
    name: str                  # for the logs, instead of the URL
    url: str
    secret: bytes | None = None
    snapshot: bool = False     # include the JPEG of the spot (camera footage leaves the machine with it)


def load_owners(path: Path) -> tuple[dict[str, list[Target]], str, list[str]]:
    """config/owners.json -> ({owner: [Target]}, public_base_url, problems). A target whose url_env or secret_env is
    not set is left out, and named in problems."""
    cfg = json.loads(path.read_text(encoding="utf-8"))
    owners, problems, names = {}, [], set()
    for owner, targets in cfg.get("owners", {}).items():
        for t in targets:
            if t["name"] in names:
                problems.append(f"{owner} / {t['name']}: the name is taken by another target: left out")
                continue
            names.add(t["name"])
            url = t.get("url") or os.environ.get(t.get("url_env", ""), "")
            if not url:
                problems.append(f"{owner} / {t['name']}: no url, and {t.get('url_env')} is not set")
                continue
            secret = None
            if t.get("secret_env"):
                if not os.environ.get(t["secret_env"]):
                    problems.append(f"{owner} / {t['name']}: {t['secret_env']} is not set: sent unsigned")
                else:
                    secret = os.environ[t["secret_env"]].encode()
            owners.setdefault(owner, []).append(Target(t["name"], url, secret, bool(t.get("snapshot"))))
    return owners, cfg.get("public_base_url") or "http://127.0.0.1:8765", problems


def _iso(t: float | None) -> str | None:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(timespec="seconds") if t else None


def _hms(t: float | None) -> str:
    return f"{dt.datetime.fromtimestamp(t, dt.timezone.utc):%H:%M:%S} UTC" if t else "?"


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
        "confirmed": f"Confirmed by the operator: {what.lower()}, {cam}, is real.",
        "rejected": f"Not an incident: the operator rejected the {what.lower()} card, {cam}. Stand down.",
    }[event]
    link = f"?run={run}"
    return {
        "schema": SCHEMA, "event": event, "incident": inc["id"], "run": run, "dry_run": dry_run,
        "owner": inc["owner"], "priority": inc["priority"], "category": inc["category"], "camera": inc["camera"],
        "occurrences": inc["occurrences"], "changed_at": _iso(changed), "at": _iso(effect.get("t")),
        "summary": {"text": said, "by": "Hafnia VLM", "ai_generated": True} if said else None,
        "text": ("[dry run] " if dry_run else "") + text,
        "links": {"board": f"{base_url}/", "clip": f"{base_url}/clips/{inc['id']}.mp4{link}" if inc.get("clip") else None,
                  "snapshot": f"{base_url}/snaps/{inc['id']}.jpg{link}"},
    }


class OwnerNotifier:
    def __init__(self, owners: dict[str, list[Target]], log: Callable[..., None], run: str,
                 base_url: str = "http://127.0.0.1:8765", dry_run: bool = False):
        """owners: load_owners()'s targets. log(kind, **fields): the service's log. run: the run folder's name."""
        self.owners, self.log, self.run, self.base_url, self.dry_run = owners, log, run, base_url, dry_run
        self.pools = {t.name: ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"notify-{t.name}")
                      for ts in owners.values() for t in ts}
        self.pending: list[Future] = []

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
            if t.snapshot and event in ("opened", "reopened") and evidence.get("jpeg"):
                w, h = evidence.get("size") or (None, None)
                msg["snapshot"] = {"jpeg_base64": base64.b64encode(evidence["jpeg"]).decode(), "width": w, "height": h}
            self.pending.append(self.pools[t.name].submit(self._deliver, t, msg, time.time()))

    def _deliver(self, t: Target, msg: dict, submitted: float) -> None:
        data = json.dumps(msg).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "Clearway", "X-Clearway-Event": msg["event"],
                   "X-Clearway-Delivery": str(uuid.uuid4())}
        if t.secret:
            headers["X-Clearway-Signature"] = "sha256=" + hmac.new(t.secret, data, hashlib.sha256).hexdigest()
        status, error, attempt = None, None, 0
        for attempt, wait in enumerate((0.0, *RETRY_AFTER_S), start=1):
            time.sleep(wait)
            try:
                with urllib.request.urlopen(urllib.request.Request(t.url, data=data, headers=headers, method="POST"),
                                            timeout=TIMEOUT_S) as r:
                    status, error = r.status, None
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
        self.log("notify", incident=msg["incident"], owner=msg["owner"], target=t.name, event=msg["event"],
                 ok=error is None, status=status, error=error, attempts=attempt, bytes=len(data),
                 snapshot="snapshot" in msg, seconds=round(time.time() - submitted, 2), changed_at=msg["changed_at"])

    def drain(self) -> None:
        for f in list(self.pending):
            f.result()
        for p in self.pools.values():
            p.shutdown()
