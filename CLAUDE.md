# Hafnia Hackathon 2026

Our entry for the XProtect Developer Summit Hackathon 2026: a solution built on Milestone XProtect Corporate 2026 R1
and Hafnia VLM (a vision-language model reached through the Hafnia gateway on the machine). Repository:
`github.com/1ho0jin1/hafnia-hackathon-2026` (private).

**Judging includes reproducibility:** the judges must be able to set the solution up on a fresh machine from this
repository alone. Every design decision should keep that possible.

## Where things run

- The dev machine is **p021** (Windows Server 2022, UTC clock). It is rebuilt fresh on failure (about 25 min) and
  deleted after the hackathon: nothing outside this repository survives.
- You are on the machine if `hostname` prints `p021` and the service `Milestone XProtect Management Server` exists.
  Then use `localhost`. Otherwise use `http://p021` and only the XProtect REST, WebSocket and Web Client APIs work.
- The Hafnia gateway (`https://localhost:15443`, self-signed cert) is reachable **only from server-side code on the
  machine**: not from the laptop, not from browser JavaScript.
- Windows PowerShell 5.1's `Invoke-RestMethod` and `Invoke-WebRequest` cannot talk to the gateway. Use `curl.exe -k`,
  Python or C#.

## Reference docs: use the skills

The organizers' kit (`C:\HackathonKit`) is installed as skills. Load the matching one before writing code against
an API; never write XProtect or gateway paths and fields from memory.

| Topic | Skill |
|---|---|
| Machine, accounts, ports, allowance, troubleshooting | `xprotect-hackathon` |
| Smart Client, Management Client, MilestonePSTools setup scripts | `xprotect-essentials` |
| Prompts, Hafnia webhooks, gateway rules, gateway REST API | `hafnia-vlm` |
| XProtect REST, WebSocket, WebRTC APIs, receiving XProtect webhooks | `xprotect-apis` |
| MIP SDK plug-ins (C#, .NET Framework 4.8, NuGet `MilestoneSystems.VideoOS.Platform` 26.1.*) | `xprotect-plugins` |

## Hard rules

**Hafnia allowance: 500 completed requests a day, reset at 00:00 UTC.**
- Before running anything that sends Hafnia requests in a loop or on a trigger, state how many requests it will use.
- Never connect motion events to Hafnia. Never let an analytics event raised by a gateway rule (or any Hafnia result)
  start another Hafnia request: that loops until the allowance is gone.
- Automated code reads `DailySummaryCount` from `GET /api/System/Information` and stops at a fixed cap.
  A per-camera cooldown alone is not enough.
- Reuse earlier answers (`GET /api/Summaries`) while developing UI instead of asking again.

**Secrets**
- Never write passwords, tokens or API keys into code, config files, logs, commits or chat. Read them from
  environment variables (for example `HAFNIA_GW_PASSWORD`, `XP_PASSWORD`) or prompt at run time
  (`Read-Host -AsSecureString`, `getpass`).

**Do not touch on the machine**
- Tailscale (app, CLI, service), Windows Firewall, the Administrator password, the computer name, Windows Update.
- Uninstalling or upgrading XProtect, Smart Client or the Hafnia plug-in. `C:\Program Files\VideoOS\MIPPlugins`.
- The gateway's *Reset System* button, its tray-icon password reset, and its *Hafnia VLM Settings* and
  *XProtect Settings*. Only the two *Advanced Settings* sections may change.
- XProtect's default rules, recording storage and camera hardware settings.
- Do not shut the machine down (it cannot be started again). Ask before restarting services or rebooting.
  Never stop the Recording Server less than 90 s after it started.
- Keep fewer than 25 gateway prompts.

## Reproducibility conventions

- Look up cameras, prompts, events, rules and webhooks **by name**, never by hard-coded ID: IDs change on a rebuild
  or a prompt import.
- XProtect setup lives in an idempotent script in this repository (MilestonePSTools or the REST API). Each block
  checks by name first, so re-running is safe.
- Commit what the gateway does not export together: the prompts export JSON, the system prompt text, any changed
  *Advanced Settings*, and the gateway rules (recreate them through `POST /api/Rules`).
- Document every manual step a script cannot do: switching analytics events on in Management Client, and generating
  Hafnia webhook addresses in Smart Client (they embed prompt and camera IDs).
- Times sent to the gateway are UTC with `Z`; never an offset like `+02:00` (the `+` becomes a space in the URI).

## Machine facts

- Cameras (device group `Hackathon`; loops at 10 fps; record on motion; 24 h retention): `busy_street`,
  `highway_traffic_overcast_weather`, `city_street_7_condensation_inside_housing`, `vandalism`,
  `traffic_flows_in_the_open_lanes`.
- Starting state: one prompt (*Road conditions analysis*); no gateway rules, analytics events, user-defined events,
  webhooks, alarm definitions or basic users. Analytics events are disabled.
- Installed: Git, Python 3.12.10 (we installed it: python.org, all users, with the `py` launcher), the .NET 8
  runtime (no SDK), Edge, Windows PowerShell 5.1, MilestonePSTools 25.2.61.
  Not installed: Node.js, the .NET SDK, VS Code. Installers we depend on belong in the setup docs.
- The NVIDIA T4 GPU has no driver installed.
- Logs: gateway `C:\ProgramData\VideoOS\Hafnia.Vlm.Gateway\logs`; XProtect `C:\ProgramData\Milestone\<component>\Logs`.

## Repository layout

Python 3.12 (installed from python.org, `py` launcher), standard library only so far.

| Path | What |
|---|---|
| `hafnia/gateway.py` | Hafnia gateway client: session, quota, prompts by title, `ask`, `wait_all` with per-phase timing |
| `hafnia/xprotect.py` | Camera name → ID lookup through MilestonePSTools (10-30 s) |
| `scripts/bench_hafnia.py` | Latency benchmark per phase; capped by `--max-requests` and `--stop-at` |
| `scripts/report_bench.py` | Turns a run folder's `results.jsonl` into a self-contained `report.html` |
| `scripts/export_frames.ps1` | Exports 2 fps recorded JPEGs of each completed request's clip to `run/<name>/frames/` (git-ignored; same day only, 24 h retention) |
| `scripts/report_compare.py` | Hafnia vs another model on the same clips: `opus_results.jsonl` + `scores.json` → `compare.html` |
| `run/<name>/` | Model run results, committed: `results.jsonl` (Hafnia rows, with answers), `report.html`; for comparisons `opus_results.jsonl`, `scores.json`, `compare.html` |

## Commands

The gateway password lives in the user-scope environment variable `HAFNIA_GW_PASSWORD`. Shells started by Claude Code
do not inherit it, so load it first in the same command:

```powershell
$env:HAFNIA_GW_PASSWORD = [Environment]::GetEnvironmentVariable('HAFNIA_GW_PASSWORD', 'User')
py scripts\bench_hafnia.py --dry-run          # plan and allowance; costs nothing
py scripts\bench_hafnia.py --run-dir run\<name> --label <tag> ...   # several runs can share one folder
py scripts\report_bench.py run\<name>         # writes run\<name>\report.html
```
