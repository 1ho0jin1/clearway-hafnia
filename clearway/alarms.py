"""XProtect alarms and bookmarks for the ledger's incidents (docs/PRODUCT.md, F3): one alarm per incident.

The ledger decides (clearway/ledger.py: raise, reopen, close); XProtectAlarms carries it out through XProtect's REST
APIs (hafnia/xprotect_rest.py), on one thread, in order:
- raise: an alarm on the incident's camera, named for the category and the owner ("Clearway: OBSTRUCTION, Street
  services"), with the category's priority, Hafnia's summary in the message (marked as AI-generated), a snapshot of the
  spot (the last frame of the clip Hafnia judged, the spot boxed), and two bookmarks: the event window on the camera
  and the clip Hafnia judged on lens_1 (recorded always; the organizers' cameras record on motion);
- reopen (a closed incident happened again): the same alarm back to New, with a comment, a snapshot and a bookmark
  on the new occurrence;
- close (the incident stayed cleared for the ledger's close_after_s, or an operator rejected it): state Closed, the
  reason in the comment (Reasons for Closing are off on the hackathon machines, so the comment carries it).
XProtect applies an update about a second later (2026-10-25), and update_alarm reads the alarm back for the fields it
does not change, so every update here names the state and the priority it wants: a comment sent just after a close
must not read the old state back and reopen the alarm.
"""
from __future__ import annotations

import datetime as dt
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

from hafnia.xprotect_rest import XProtect

BEFORE_S, AFTER_S = 2.0, 3.0   # the event window around an occurrence, as the lens clip (clearway/service.py)


def _utc(t: float) -> dt.datetime:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc)


class XProtectAlarms:
    def __init__(self, camera_ids: dict[str, str], lens_id: str | None, log: Callable[..., None],
                 xp: XProtect | None = None, label: str = ""):
        """camera_ids: camera name -> XProtect id. lens_id: lens_1's id (None: no lens bookmark). log(kind, **fields):
        the service's log. label: prefixed to alarm names (a dry run marks its alarms)."""
        self.xp = xp or XProtect()
        self.camera_ids, self.lens_id, self.log, self.label = camera_ids, lens_id, log, label
        self.alarm: dict[str, str] = {}       # incident -> XProtect alarm id
        self.is_open: dict[str, bool] = {}    # incident -> its alarm is open
        self.priority: dict[str, str] = {}
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.pending: list[Future] = []

    def submit(self, effect: dict, incident: dict, evidence: dict) -> None:
        """effect: the ledger's {"alarm": ...} or {"close_alarm": ...}; incident: Incident.public(); evidence:
        {"jpeg", "size", "span"} (snapshot, its size, lens_1's span of the clip Hafnia judged)."""
        self.pending.append(self.pool.submit(self._run, effect, incident, evidence))

    def _run(self, effect: dict, inc: dict, ev: dict) -> None:
        t0 = time.monotonic()
        try:
            if "alarm" in effect:
                done = self._reopen(effect, inc, ev) if inc["id"] in self.alarm else self._raise(effect, inc, ev)
            elif "close_alarm" in effect:
                done = self._close(inc["id"], self._close_comment(effect))
            else:
                return
            self.log("xprotect", incident=inc["id"], seconds=round(time.monotonic() - t0, 2), **done)
        except Exception as e:                # XProtect trouble must not stop the service
            self.log("xprotect_error", incident=inc["id"], effect=effect, error=repr(e))

    # --- actions ---------------------------------------------------------------------------------------------------
    def _raise(self, effect: dict, inc: dict, ev: dict) -> dict:
        cam = self.camera_ids[inc["camera"]]
        when = _utc(effect["t_change"])
        alarm = self.xp.trigger_alarm(f"{self.label}Clearway: {inc['category']}, {inc['owner']}"[:100],
                                      self._message(inc, ev)[:1000], cam, when, priority=inc["priority"],
                                      tag=f"clearway/{inc['id']}")
        self.alarm[inc["id"]], self.is_open[inc["id"]], self.priority[inc["id"]] = alarm, True, inc["priority"]
        out = {"action": "raise", "alarm": alarm, "priority": inc["priority"], "camera": inc["camera"]}
        out.update(self._evidence(alarm, inc, ev, effect, first=not effect.get("recurrence")))
        return out

    def _reopen(self, effect: dict, inc: dict, ev: dict) -> dict:
        alarm = self.alarm[inc["id"]]
        when = _utc(effect["t_change"])
        self.xp.update_alarm(alarm, f"Happened again: the spot changed at {when:%H:%M:%S} UTC (occurrence "
                                    f"{inc['occurrences']}). Reopened by Clearway.",
                             priority=inc["priority"], state="New")
        self.is_open[inc["id"]] = True
        out = {"action": "reopen", "alarm": alarm}
        out.update(self._evidence(alarm, inc, ev, effect, first=False))
        return out

    def _close(self, incident_id: str, comment: str) -> dict:
        alarm = self.alarm.get(incident_id)
        if alarm is None:
            return {"action": "close", "alarm": None, "note": "no XProtect alarm for this incident"}
        self.xp.update_alarm(alarm, comment, priority=self.priority[incident_id], state="Closed")
        self.is_open[incident_id] = False
        return {"action": "close", "alarm": alarm, "comment": comment}

    def close_all(self, comment: str) -> None:
        """Test harness: close every alarm still open (a test run's incidents are not real)."""
        for iid in [i for i, o in self.is_open.items() if o]:
            self.pending.append(self.pool.submit(
                lambda iid=iid: self.log("xprotect", incident=iid, **self._close(iid, comment))))

    def drain(self) -> None:
        for f in list(self.pending):
            f.result()
        self.pool.shutdown()

    # --- content ---------------------------------------------------------------------------------------------------
    def _message(self, inc: dict, ev: dict) -> str:
        a = inc.get("answer") or {}
        if a.get("summary"):
            said = f"{a['summary']} [AI-generated by Hafnia VLM: check the clip.]"
        elif a.get("standin"):
            said = "[Dry run: answered by the test stand-in, not by Hafnia.]"
        else:
            said = ""
        span = ev.get("span")
        lens = f" Clip Hafnia judged: lens_1 {span[0]:%H:%M:%S}-{span[1]:%H:%M:%S} UTC." if span else ""
        return (f"{said} Incident {inc['id']} on {inc['camera']}: {inc['category']}, for {inc['owner']}. The spot "
                f"changed at {_utc(inc['t_change']):%H:%M:%S} UTC.{lens}").strip()

    def _close_comment(self, effect: dict) -> str:
        if effect.get("reason") == "rejected":
            return "Rejected by the operator. Closed by Clearway."
        since = f" since {_utc(effect['t_cleared']):%H:%M:%S} UTC" if effect.get("t_cleared") else ""
        return f"Cleared: the spot has looked as before{since}. Closed by Clearway (no request)."

    def _evidence(self, alarm: str, inc: dict, ev: dict, effect: dict, first: bool) -> dict:
        """Snapshot and bookmarks; each failure is noted and the rest still tried."""
        out: dict = {"bookmarks": [], "errors": []}
        if ev.get("jpeg"):
            try:
                w, h = ev["size"]
                self.xp.attach_snapshot(alarm, ev["jpeg"], w, h)
                out["snapshot"] = True
            except Exception as e:
                out["errors"].append(f"snapshot: {e!r}")
        cam = self.camera_ids[inc["camera"]]
        if first:   # the occurrence Hafnia judged: the clip's window
            begin, end = inc["t_change"] - BEFORE_S, inc["t_report"] + AFTER_S
        else:       # a later occurrence: its own window
            begin, end = effect["t_change"] - BEFORE_S, effect["t"] + AFTER_S
        description = self._message(inc, ev if first else {})[:1000]
        marks = [(cam, f"Clearway {inc['category']} {inc['id']}", _utc(begin), _utc(end), _utc(effect["t_change"]))]
        if first and self.lens_id and ev.get("span"):
            s, e = ev["span"]
            marks.append((self.lens_id, f"Clearway lens {inc['category']} {inc['id']}", s, e, s))
        for device, header, b, e, trig in marks:
            try:
                out["bookmarks"].append(self.xp.create_bookmark(device, header, description, b, e, trig))
            except Exception as err:
                out["errors"].append(f"bookmark: {err!r}")
        if not out["errors"]:
            del out["errors"]
        return out
