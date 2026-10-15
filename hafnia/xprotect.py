"""XProtect lookups through MilestonePSTools, as the logged-in Windows user (no password needed on the machine)."""
from __future__ import annotations

import json
import subprocess

_LIST_CAMERAS = (
    "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; "
    "Import-Module MilestonePSTools; "
    "Connect-Vms -ServerAddress 'http://localhost' -AcceptEula | Out-Null; "
    "@(Get-VmsCamera | Select-Object Name, Id) | ConvertTo-Json -Compress; "
    "Disconnect-Vms"
)


def cameras_by_name() -> dict[str, str]:
    """{camera name: camera id}. IDs change when the machine is rebuilt, so code looks cameras up by name.
    Takes 10-30 s: MilestonePSTools loads slowly."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", _LIST_CAMERAS],
        capture_output=True, text=True, timeout=180, check=True,
    ).stdout
    cameras = json.loads(out)
    if isinstance(cameras, dict):  # ConvertTo-Json unwraps a single-item array
        cameras = [cameras]
    return {c["Name"]: c["Id"] for c in cameras}
