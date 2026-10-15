"""Minimal client for the Hafnia gateway REST API (https://localhost:15443), standard library only.

Runs on the hackathon machine only: the gateway is not reachable from elsewhere. Schema reference: the gateway's
own OpenAPI document at https://localhost:15443/api/swagger/v1/swagger.json.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

DEFAULT_BASE_URL = "https://localhost:15443"
TERMINAL = ("Completed", "Failed")
PHASES = ("NotStarted", "FetchingVideo", "TransferringAssets", "RequestingSummary")

# The gateway's certificate is self-signed: certificate checks are off for this context, used only for the gateway.
_GATEWAY_TLS = ssl.create_default_context()
_GATEWAY_TLS.check_hostname = False
_GATEWAY_TLS.verify_mode = ssl.CERT_NONE


class GatewayError(Exception):
    def __init__(self, status: int, body: str, path: str):
        super().__init__(f"gateway answered {status} for {path}: {body[:300]}")
        self.status = status
        self.body = body


def video_uri(camera_id: str, start: dt.datetime, end: dt.datetime) -> str:
    """An xprotect:// clip address. Times are sent in UTC with Z: an offset's '+' would be read as a space."""
    def z(t: dt.datetime) -> str:
        return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"xprotect://localhost/cameras/{camera_id}?StartTime={z(start)}&EndTime={z(end)}"


def parse_time(value: str) -> dt.datetime:
    """Gateway times come with Z or an offset, and up to 7 fractional digits (.NET); Python takes at most 6."""
    value = re.sub(r"(\.\d{6})\d+", r"\1", value.replace("Z", "+00:00"))
    return dt.datetime.fromisoformat(value)


@dataclass
class Tracked:
    """A summary request being watched, with the time each progress state was first seen (monotonic seconds)."""
    id: str
    submitted: float
    seen: dict[str, float] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def progress(self) -> str:
        return self.summary.get("Progress", "")

    @property
    def done(self) -> bool:
        return self.progress in TERMINAL


class Gateway:
    """One gateway session. Log in once and reuse it: the machine allows 10 logins a minute in total."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session: str | None = None

    # --- plumbing -------------------------------------------------------------------------------------------------
    def _call(self, method: str, path: str, body: Any = None, query: dict[str, Any] | None = None) -> Any:
        if query:
            path += "?" + urllib.parse.urlencode(query, doseq=True)
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.session:
            req.add_header("X-Session-Id", self.session)
        try:
            with urllib.request.urlopen(req, context=_GATEWAY_TLS, timeout=self.timeout) as resp:
                text = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise GatewayError(e.code, e.read().decode("utf-8", "replace"), path) from None
        return json.loads(text) if text else None

    # --- sessions -------------------------------------------------------------------------------------------------
    def login(self, password: str | None = None, user: str = "administrator") -> None:
        """The password defaults to the HAFNIA_GW_PASSWORD environment variable; it is never stored or logged."""
        password = password or os.environ.get("HAFNIA_GW_PASSWORD")
        if not password:
            raise RuntimeError("Set HAFNIA_GW_PASSWORD to the gateway's administrator password")
        self.session = self._call("POST", "/api/Sessions/Login", {"Name": user, "Password": password})["Id"]

    def logout(self) -> None:
        if self.session:
            try:
                self._call("POST", "/api/Sessions/Logout", {"Id": self.session})
            finally:
                self.session = None

    def __enter__(self) -> "Gateway":
        if not self.session:
            self.login()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.logout()

    # --- reads ----------------------------------------------------------------------------------------------------
    def system_information(self) -> dict[str, Any]:
        return self._call("GET", "/api/System/Information")

    def quota(self) -> dict[str, Any] | None:
        """{DailySummaryQuota, DailySummaryCount, DailySummaryReset, ...}, or None when Hafnia VLM did not answer."""
        return self.system_information().get("QuotaInformation")

    def models(self) -> list[dict[str, Any]]:
        return self._call("GET", "/api/Models")

    def find_prompt(self, title: str) -> dict[str, Any] | None:
        """Prompts are found by exact title: their IDs change when prompts are imported."""
        found = self._call("GET", "/api/Prompts", query={"SearchString": title})
        return next((p for p in found.get("PageContent") or [] if p.get("Title") == title), None)

    def summary(self, summary_id: str) -> dict[str, Any]:
        return self._call("GET", f"/api/Summaries/{summary_id}")

    def summaries(self, limit: int = 20, **filters: Any) -> dict[str, Any]:
        """Newest first. Always limited: without a limit the gateway returns everything it has kept."""
        return self._call("GET", "/api/Summaries", query={"Limit": limit, **filters})

    # --- asking ---------------------------------------------------------------------------------------------------
    def ask(self, uri: str, prompt: str, prompt_id: str | None = None, model_id: str | None = None) -> dict[str, Any]:
        """Start a summary. Costs 1 of the 500 daily requests if it completes. Pass prompt_id (with the prompt's
        text in prompt) so gateway rules for that saved prompt check the answer."""
        body: dict[str, Any] = {"Prompt": prompt, "VideoUris": [uri]}
        if prompt_id:
            body["PromptId"] = prompt_id
        if model_id:
            body["AiModelId"] = model_id
        return self._call("POST", "/api/Summaries", body)

    def wait_all(self, tracked: list[Tracked], poll: float = 1.0, timeout: float = 600,
                 on_change: Callable[[Tracked], None] | None = None) -> None:
        """Poll every request until each is Completed or Failed, recording when each state is first seen.
        The gateway allows 60 s for the export and 300 s for Hafnia VLM, so 10 minutes is the outer limit."""
        deadline = time.monotonic() + timeout
        while True:
            for t in tracked:
                if t.done:
                    continue
                t.summary = self.summary(t.id)
                if t.progress not in t.seen:
                    t.seen[t.progress] = time.monotonic()
                    if on_change:
                        on_change(t)
            if all(t.done for t in tracked) or time.monotonic() > deadline:
                return
            time.sleep(poll)
