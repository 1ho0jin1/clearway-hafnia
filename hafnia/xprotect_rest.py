"""XProtect REST APIs through the API Gateway on the machine (http://localhost/api/rest/v1), standard library only.

Logs in with Windows authentication as the current user (grant_type=windows_credentials, as the kit's tour script
does): the token comes from PowerShell's -UseDefaultCredentials, so no password is stored anywhere. Paths and fields
follow Milestone's OpenAPI files for the Configuration, Alarms and Bookmarks REST APIs.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE = "http://localhost/api/rest/v1"
_TOKEN_PS = (
    "$ProgressPreference='SilentlyContinue';"
    "Invoke-RestMethod -Method Post -Uri 'http://localhost/IDP/connect/token' -UseDefaultCredentials "
    "-Body @{ grant_type='windows_credentials'; client_id='GrantValidatorClient' } | ConvertTo-Json -Compress"
)


class XProtectError(Exception):
    def __init__(self, status: int, body: str, path: str):
        super().__init__(f"XProtect answered {status} for {path}: {body[:300]}")
        self.status = status


class XProtect:
    def __init__(self, base: str = BASE, timeout: float = 30):
        self.base, self.timeout = base.rstrip("/"), timeout
        self._token, self._expires = "", 0.0

    def _auth(self) -> str:
        if time.monotonic() > self._expires - 60:   # renew a minute before expiry
            out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _TOKEN_PS],
                                 capture_output=True, text=True, timeout=60, check=True).stdout
            tok = json.loads(out)
            self._token, self._expires = tok["access_token"], time.monotonic() + int(tok["expires_in"])
        return self._token

    def call(self, method: str, path: str, body: Any = None, query: dict | None = None) -> Any:
        url = self.base + path + ("?" + urllib.parse.urlencode(query) if query else "")
        req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode())
        req.add_header("Authorization", "Bearer " + self._auth())
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                text = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise XProtectError(e.code, e.read().decode("utf-8", "replace"), path) from None
        return json.loads(text) if text else None

    # --- configuration ----------------------------------------------------------------------------------------------
    def cameras(self) -> dict[str, str]:
        """{name: id}. IDs change on a rebuild: look cameras up by name."""
        return {c["name"]: c["id"] for c in self.call("GET", "/cameras").get("array", [])}

    def jpeg_live(self, camera_id: str, width: int = 1920, height: int = 1080) -> tuple[dt.datetime, bytes]:
        """One live JPEG (camera task JpegGetLive) and its frame time. Width and height are maximums; the spec marks
        them optional, but the server answers 400 "Required property 'Width' not found" without them."""
        r = self.call("POST", f"/cameras/{camera_id}", {"width": width, "height": height}, {"task": "JpegGetLive"})
        data = r["result"]   # task responses are wrapped in "result"
        when = dt.datetime.fromisoformat(_trim_fraction(data["frameDateTime"]))
        return when.astimezone(dt.timezone.utc), base64.b64decode(data["jpegDataAsBase64"])


    # --- alarms (Alarms REST API) -----------------------------------------------------------------------------------
    def _named(self, path: str, name: str) -> str:
        """ID of an alarm priority or state by name ("Low", "High", "Closed", ...): IDs differ between systems."""
        cache = self.__dict__.setdefault("_named_cache", {})
        if path not in cache:
            r = self.call("GET", path)
            cache[path] = {i["name"].lower(): i["id"] for i in r.get("array", r)}
        return cache[path][name.lower()]

    def trigger_alarm(self, name: str, message: str, camera_id: str, when: dt.datetime, priority: str = "High",
                      tag: str = "") -> str:
        """Raise an alarm on a camera, without an alarm definition. Returns the alarm's id."""
        body = {"name": name, "message": message, "source": f"cameras/{camera_id}",
                "time": _z(when), "priority": self._named("/alarmPriorities", priority), "tag": tag}
        r = self.call("POST", "/alarms", body)
        return _unwrap(r)["id"]

    def update_alarm(self, alarm_id: str, comment: str, priority: str | None = None, state: str | None = None) -> None:
        """PATCH needs every field (comment, priority, state, assignedTo.displayName, reasonForClosing), so the current
        values are read first and only the given ones change. reasonForClosing stays empty: "Reasons for Closing" is
        off on the hackathon machines and any other value is refused; the comment (alarm history) carries the reason."""
        cur = _unwrap(self.call("GET", f"/alarms/{alarm_id}"))
        body: dict[str, Any] = {
            "comment": comment,
            "priority": self._named("/alarmPriorities", priority) if priority else cur["priority"]["id"],
            "state": self._named("/alarmStates", state) if state else cur["state"]["id"],
            "assignedTo.displayName": (cur.get("assignedTo") or {}).get("displayName", ""),
            "reasonForClosing": "",
        }
        self.call("PATCH", f"/alarms/{alarm_id}", body)

    def attach_snapshot(self, alarm_id: str, jpeg: bytes, width: int, height: int, overlay: bool = True) -> None:
        """Store a JPEG with the alarm (shown in Smart Client's alarm preview)."""
        self.call("POST", f"/alarms/{alarm_id}/snapshots",
                  {"image": base64.b64encode(jpeg).decode(), "width": width, "height": height,
                   "sizeInBytes": len(jpeg), "timeOffset": 0, "hasOverlay": overlay})

    # --- bookmarks (Bookmarks REST API) -------------------------------------------------------------------------------
    def create_bookmark(self, camera_id: str, header: str, description: str, begin: dt.datetime, end: dt.datetime,
                        triggered: dt.datetime) -> str:
        """Returns the bookmark's reference (e.g. "no.000003"). Header: Smart Client shows at most 50 characters.
        timeTriggered is required in practice (without it: 400 "Parameter name: tagTime")."""
        r = self.call("POST", "/bookmarks", {
            "header": header[:50], "description": description, "timeBegin": _z(begin), "timeEnd": _z(end),
            "timeTriggered": _z(triggered), "devicePath": {"type": "cameras", "id": camera_id}})
        return _unwrap(r).get("reference", "")


def _z(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _unwrap(r: Any) -> dict:
    """REST answers wrap the object in "data" or "result" depending on the API."""
    if isinstance(r, dict):
        for k in ("data", "result"):
            if isinstance(r.get(k), dict):
                return r[k]
    return r


def _trim_fraction(s: str) -> str:
    """.NET gives 7 fractional digits; Python takes at most 6."""
    import re
    return re.sub(r"(\.\d{6})\d+", r"\1", s.replace("Z", "+00:00"))
