# Hafnia Hackathon 2026

Our entry for the XProtect Developer Summit Hackathon 2026: a solution built on Milestone XProtect Corporate 2026 R1
and Hafnia VLM (a vision-language model reached through the Hafnia gateway on the machine). Repository:
`github.com/1ho0jin1/hafnia-hackathon-2026` (private).

**Judging weighs creativity and validity most** (organizer Q&A). Reproducibility counts too, but a best-effort
setup script plus documented manual steps is enough. Deliverable: this repository; a demo video is optional.
The current plan and schedule are in `docs/PLAN-C.md` (decided 2026-10-22): keep it current. Earlier plans, kept for
reference: `docs/PLAN.md` (verified accident alarms) and `docs/PLAN-near-miss.md` (near-miss observatory; also the
research on Hafnia's trained formats, earlier and competing entries, and footage sources with licence notes).

## Project direction (decided 2026-10-22: plan C, right-of-way incidents)

- Solo entry, submission around 2026-10-30.
- **Scope: right-of-way incidents**, things that block or endanger a public way, for city and transit operators: a
  person on the tracks, a vehicle stalled in a lane, an object lying across a pavement, damage to transit. Security
  (break-ins) is a footnote: Hafnia scored 0 of 8 on real crime CCTV (`run/bench-20261018`), although it reads the
  organizers' synthetic scenes (`run/probe-20261022T054342Z`). Camera-status checks stay out of scope.
- Concept: tier 0 notices that **something changed and stayed changed** (dual background model, no object classes, no
  per-scenario rules), plus stalled vehicles and a person in a danger zone. The **lens** shows Hafnia the change:
  centred on the moment, cropped to the spot, with BEFORE and AFTER views. Hafnia names it in JSON; a ledger item and
  an XProtect alarm go to the owner; tier 0 closes the item, without a request, when the spot is restored.
- **No frontier model in the product**, and no local VLM tier (nothing performant fits a T4). Opus (Claude Code) is
  used **offline only**, as a judge: scoring tests, tuning prompts, auditing answers claim by claim.
- Differentiators: no per-scenario rules; the lens, measured against Hafnia's time-order and prior errors; results on
  real footage as well as the synthetic loops; claim-level audits.
- Own clips are allowed (participant confirmed).
- Superseded: verified traffic-incident alarms (plan A, 2026-10-16 to 10-21) and the near-miss observatory (plan B,
  2026-10-20 to 10-21). Their measured findings below still hold.

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
- XProtect's default rules, recording storage, and the hardware settings of the five organizer cameras (our own
  test cameras, added with `scripts/add_test_camera.ps1`, are ours to change).
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
- Repository text files are UTF-8. Never rewrite them with Windows PowerShell 5.1's `Get-Content -Raw` /
  `Set-Content` (they use the legacy codepage and garble `–`, `→`, `×`); use the Edit tool or Python with
  `encoding="utf-8"`.

## Machine facts

- Organizer cameras (device group `Hackathon`; loops at 10 fps; record on motion; 24 h retention): `busy_street`,
  `highway_traffic_overcast_weather`, `city_street_7_condensation_inside_housing`, `vandalism`,
  `traffic_flows_in_the_open_lanes`; and since 2026-10-21 six synthetic 832×480 clips of 15–17 s, on every machine:
  `vehicle_breakdown_traffic_queue`, `bin_pushed_over_onto_sidewalk`, `escooter_left_across_sidewalk`,
  `school_gate_break_in_night`, `person_on_railway_tracks`, `graffiti_on_standing_train` (scenes described in
  `C:\HackathonKit\xprotect-hackathon\SKILL.md`, "Your cameras"). The bin and e-scooter clips show the same street.
- Starting state: one prompt (*Road conditions analysis*); no gateway rules, analytics events, user-defined events,
  webhooks, alarm definitions or basic users. Analytics events are disabled.
- Installed: Git, Python 3.12.10 (we installed it: python.org, all users, with the `py` launcher), the .NET 8
  runtime (no SDK), Edge, Windows PowerShell 5.1, MilestonePSTools 25.2.61.
  Not installed: Node.js, the .NET SDK, VS Code. Installers we depend on belong in the setup docs.
- ffmpeg 9.0.2 (gyan.dev essentials build, SHA-256 checked), portable at
  `C:\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin` (not on PATH).
- The NVIDIA T4 GPU has its driver (GRID 596.86) and `nvidia-smi`; XProtect also uses it for video decoding.
- Tier 0 Python environment: `.venv` (git-ignored) with torch 2.11.0+cu128, Ultralytics 8.4.182; see
  `requirements.txt`. YOLO weights download to `models/` (git-ignored).
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
| `scripts/add_test_camera.ps1` | Injects a clip as a new StableFPS test camera (organizers' procedure); restarts the Recording Server only with `-RestartRecordingServer`; ends a hung service process instead of needing a reboot |
| `scripts/annexb_normalize.py` | Rewrites ffmpeg's Annex B output into the layout StableFPS accepts (run after every conversion) |
| `scripts/report_recognition.py` | One-word classification vs ground truth (confusion matrix) and judged descriptions → `recognition.html` |
| `scripts/event_windows.ps1`, `scripts/locate_event.py` | Find when a looped clip's event was recorded (frame matching) and write event-centred windows for `bench_hafnia.py --windows` |
| `tier0/` | Tier 0: `source.py` (frames from a video file, streamed, looped), `pipeline.py` (YOLO + ByteTrack), `rules.py` (track features, collision / fall / sudden-stop rules, incident merging) |
| `scripts/eval_tier0.py` | Offline tier 0 evaluation (recall on accident clips, false candidates on normal traffic); `--set`, `--imgsz`, `--conf`, `--cap-negatives` for tuning |
| `bridge/FrameBridge/` | C# (.NET Framework 4.8, MIP SDK 26.1.*) live frame bridge; build: `dotnet build -c Release` in that folder (needs the .NET 8 SDK, installed 2026-10-18) |
| `hafnia/xprotect_rest.py` | XProtect REST client (Windows-auth token via PowerShell): cameras, JpegGetLive, alarms (trigger, update, snapshot), bookmarks |
| `incident/` | Live pipeline: `bridge.py` (read FrameBridge), `router.py` (cooldown, open incident, rejected spots, budget), `verify.py` (Hafnia check + description) |
| `scripts/run_live.py` | The end-to-end pipeline on live cameras; logs to `run/live-<UTC>/events.jsonl` |
| `lens/` | The lens camera: `publisher.py` (one RTSP stream through ffmpeg to MediaMTX: idle frames, then each queued clip in real time; logs the UTC span each clip played), `client.py` (queue a clip; crop, slow motion, marks), `mediamtx.yml` (RTSP on 127.0.0.1:8554 only, TCP only) |
| `scripts/setup_lens.ps1`, `scripts/start_lens.ps1` | Install MediaMTX (pinned, SHA-256 checked) and camera `lens_1` (Universal 1 channel driver, our rule "Lens: record lens_1 always"); start MediaMTX and the publisher detached (logs in `run/lens/`) |
| `scripts/lens_compare.py` | One looped event asked about plainly and through the lens (crop, crop in slow motion): finds the event live by frame matching; 3 Hafnia requests |
| `data/clips.json` | Incident clips: neutral camera name, source file, length, label, ground truth; organizer cameras as controls |
| `run/<name>/` | Model run results, committed: `results.jsonl` (Hafnia rows, with answers), `report.html`; for comparisons `opus_results.jsonl`, `scores.json`, `compare.html` |
| `data/` | Source videos (`*.mp4`) and converted clips (`data/clips/`), both git-ignored: too large, and judges must download them from their source |

## Commands

The gateway password lives in the user-scope environment variable `HAFNIA_GW_PASSWORD`. Shells started by Claude Code
do not inherit it, so load it first in the same command:

```powershell
$env:HAFNIA_GW_PASSWORD = [Environment]::GetEnvironmentVariable('HAFNIA_GW_PASSWORD', 'User')
py scripts\bench_hafnia.py --dry-run          # plan and allowance; costs nothing
py scripts\bench_hafnia.py --run-dir run\<name> --label <tag> ...   # several runs can share one folder
py scripts\report_bench.py run\<name>         # writes run\<name>\report.html
```

Inject a clip as a test camera (convert first; see the script's header for the ffmpeg line):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\add_test_camera.ps1 -Clip data\clips\<W>x<H>_<name> -Port 105
# exit code 3 = copied and revision bumped, Recording Server restart needed: ask the participant, then add -RestartRecordingServer
```

## Findings so far

**Latency** (`run/bench-20261015`, 12 requests): median 5.3 s from submit to answer (range 4.1–13.3 s); Hafnia's own
answer phase about 3–4 s; 5 requests at once all finish within 7 s (parallel, no queueing); clip length 5 → 30 s barely
changes latency, and every clip costs 1 request. The one 13.3 s outlier was a cold first export.

**Quality vs Opus** (same 12 clips, blind Opus agents on 2 fps stills, answer key from the frames; `compare.html`):
Opus 24/24 key facts, Hafnia 17.5/24. Hafnia missed lens condensation twice ("clear, dry"), the cracked window in the
5 s vandalism clip (the event *is* in that clip), and called fog "rainy". It ties on traffic and roadworks scenes.
Default model: "The latest general traffic model (recommended)". Hafnia never noticed the clips loop; Opus did.
Caveats: 5 distinct scenes, one generic prompt, Opus judged its own answers. Targeted keyword prompts are untested.

**Incident recognition** (`run/bench-20261018/recognition.html`, 39 requests; 10 incident clips as neutral cameras
`test_01`–`test_10`, 5 organizer cameras as controls; ground truth in `data/clips.json`):
- **Every Hafnia model is a traffic model**, per the gateway's own `GET /api/Models` (descriptions: "specialized in
  multimodal traffic analysis"): `traffic-general` (default) plus three variants named "(deprecated)". Their IDs
  contain `7b`/`8b`, which may mean parameter counts: unconfirmed. The kit documents only the endpoint, not the models.
  There is no security model.
- **Accidents, asked directly** ("reply with exactly one word"): 8 of 9 answers correct, including a subtle light
  contact. **Accidents in a free description:** only 2 of 5 caught, and twice it wrote "no collisions" for a visible
  crash. For detection, always ask a targeted keyword question; never parse free descriptions.
- **Crime: 0 of 8** (robberies, shootings) answered NONE or ACCIDENT; descriptions missed masks and weapons (a man
  collapsing after a shooting became "slips on the slick pavement"). The `vandalism` control was NONE both times,
  although a generic description on 2026-10-15 did describe the broken window.
- Normal-traffic controls: 8 of 8 NONE (no false alarms). Same answer on both repeats: 13 of 14 clips.
- Median 8.4 s per request with 5 at once. One export failed inside XProtect ("Index was out of range"): free.
- All missed incidents were verified to lie inside the window Hafnia received (1 fps frames of each window).
- **Event-centred windows fix most misses** (`run/bench-20261018b/README.md`, 34 requests): a 6 s window centred on the
  impact (located in the recordings by `scripts/event_windows.ps1`) gave 10 of 10 accident answers and 4 of 5 caught
  descriptions, against 8 of 9 and 2 of 5 with full 12–18 s loops; median 5.2 s. The three older traffic models were
  no better than the default (3–4 of 5 accidents). The window matters far more than the model; whether through frame
  sampling or resolution is not yet separated (experiments B, slow motion, and C, crop).
- Implication: Hafnia is a strong, cheap traffic-incident verifier; security incidents need tier 0 evidence and
  rules of our own, or must be reported honestly as out of Hafnia's domain.

**Tier 0, offline** (`run/tier0-20261018/README.md`; `tier0/`, `scripts/eval_tier0.py`, venv in `.venv`): YOLO11m
at 640 px + ByteTrack + rules (collision = contact plus a sharp stop; fall = person box upright → lying; sudden stop).
4 of 5 accident impacts found; 0.74 false candidates/min on normal traffic, from 2 spots repeating every loop; none on
the 13-min highway or the crowd. 22.3 frames/s on the T4 (about 2 cameras at 10 fps). `test_01` is missed because the
struck rider is never detected (small, occluded); 1280 px and a relative speed drop were tried and were worse.
The GPU driver is installed (596.86; done by someone else between 2026-10-15 and 10-18), no reboot needed.
Long evaluations: launch them as a detached process (`Start-Process ... -RedirectStandardOutput`, `python -u`) so
they survive a Claude Code session ending, then poll the process.

**Live end to end** (`run/live-20261018T142327Z/README.md`; `scripts/run_live.py`, `incident/`, `bridge/FrameBridge`):
the REST task JpegGetLive returns keyframes only (1 per second), so live frames come from **FrameBridge**, a .NET
Framework 4.8 console app on the MIP .NET library (`JPEGLiveSource`, Windows login, no password) that streams binary
records to Python at 9.5–10.2 fps. First 5-min run: unverified Low alarm 0.6–0.8 s after the event, Hafnia's verdict
6–9 s after it; one accident confirmed (alarm → High, description, bookmark), two false candidates closed; 3 checks
plus 1 description instead of ~305 requests for every tier 0 candidate. Open problem: the free description contradicted
the confirmed verdict.
XProtect REST quirks found: alarm PATCH needs every field (read the alarm first); "Reasons for Closing" is off, so
reasonForClosing must be empty; bookmarks need timeTriggered and return a `reference`, not an id; JpegGetLive needs
width and height; task responses are wrapped in `result`, alarm reads in `data`; reads lag writes by about a second.

**Tiered vs Hafnia-only, measured** (`run/compare-20261019/README.md`, same 36 s of recording on 7 cameras): polling
42 requests, 5 of 5 accident cameras, 21 alarms (2 false); tiered 5 requests, 3 of 5 cameras, 3 alarms (0 false),
median verdict 7.8 s vs 9.8 s. Tiered misses: `test_01` (tier 0) and `test_03` (router: a rejected pre-impact candidate
muted the spot and camera, blocking the real impact 4.6 s later). Clips loop, so count cameras caught, not impacts.

**Tiered vs Hafnia-only (computed 2026-10-19, before the measured run):** without tier 0
the only trigger is polling. Continuous 6 s polling costs 600 requests an hour per camera (14,400 a day: 29× the daily
allowance for one camera); 15 s polling 5,760 a day. The live run cost 4 requests for 2 cameras in 5 minutes, against
100 for 6 s polling. Accuracy: tiered recall is bounded by tier 0 (4 of 5 accidents offline; `test_01` missed), while
Hafnia found `test_01` with a full-loop window, so polling would catch it. Hafnia was 10 of 10 on accidents with
event-centred 6 s windows and 8 of 9 with longer ones; unaligned polling windows can split an impact (unmeasured).
False alarms reaching the operator: none seen tiered. Tiered gives an unverified alarm in under 1 s and a verdict in
6–9 s; polling gives no early alarm and a verdict about window length plus 5–9 s after the event.

**Plan C tier 0, offline** (`run/change-G1-loops/README.md`, `run/memory-compare/README.md`, no requests): the change
detector (`tier0/change.py`) catches the breakdown, bin, e-scooter and graffiti in every loop (0.1–4.2 s after the
object comes to rest); people are held back by design, so the tracks and the gate need person triggers (the gate's
apparent catches were lit pavement and shadow beside the person); a cracked window is too subtle. Two settings: `ChangeParams.loops()` for the synthetic clips, `.real()` (640 px, 0.15%, 15 s) for real
cameras: the crashed SUV in `test_11` after 43 s, 14–125 false reports per hour on real streets. The SigLIP 2 verdict
memory (`tier0/memory.py`) cuts requests by 45% with no incident skipped against a stand-in for Hafnia; plan A's
spot muting would have skipped 20 of 56 incidents.

**Lens camera, first test** (`run/lens-test_11-20261021T144445Z/README.md`, 6 requests): on `test_11`'s distant crash
(the SUV is about 30 px long), the plain 6 s window got NONE twice; the same window cropped and enlarged on `lens_1`
got ACCIDENT twice, in slow motion too. One event: an anecdote that motivates E6 in `docs/PLAN-near-miss.md`. Lens
recordings match send times within about 10 ms; after a publisher restart XProtect resumes recording about 10 s later.

**Clip windows:** cameras record on motion, so a window can have no recording ("Fetch Video: ... No recordings
available within the provided time range"). Such a failure costs nothing; pick recorded spans or retry slightly earlier.

**How video reaches Hafnia:** the gateway accepts only `xprotect://` URIs. It resolves video sources through
plug-ins, and the only one installed is `Plugins\Hafnia.Vlm.Gateway.Plugins.XProtect.dll`. So any footage must be
recorded by XProtect, i.e. played as a camera. Calling the Hafnia cloud API directly would need the key stored in the
gateway: off limits (house rules); ask the organizers if ever needed.

**Injecting footage as a camera** (StableFPS driver, inside the Recording Server):
- Clips: H.264 Annex B, no extension, named `<W>x<H>_<name>`, 10 fps like the organizer cameras, in
  `C:\Program Files (x86)\Milestone\XProtect Recording Server\Drivers\NativeDrivers\StableFPS_DATA\Video\H264`.
  The 32-bit driver keeps all clips in RAM, 1.7 GB in total.
- The driver reads its **file list** only when the Recording Server starts, so a new file needs the `versionid` in
  `...\NativeDrivers\resources\StableFPS.xml` bumped and the Recording Server restarted.
- **Which clip a camera plays** is a hardware setting (`VideoH264Files`, `FileName`) that applies live, without a
  restart. Plan: convert a batch of clips, restart once, then test by swapping the clip on a "test bench" camera.
- Each camera is one StableFPS hardware on its own port: organizer cameras use `http://127.0.0.1:100`–`104`, ours
  start at `105`. The record-on-motion rule covers All Cameras, so new cameras record automatically.
- **Recording Server restart** = stop and start the Windows service `Milestone XProtect Recording Server` only (not a
  reboot). For 2–3 minutes all cameras have no live video and no recording, and Hafnia exports fail (free). Stored
  recordings, the Management and Event Servers, the gateway, RDP and Tailscale are unaffected. Never stop it within
  90 s of its start. Push to GitHub before restarting, in case the machine needs a rebuild.

**Clip format pitfall (2026-10-18):** ffmpeg's Annex B output (SPS/PPS before every keyframe, an x264 SEI, some
3-byte start codes) makes the Recording Server log "Unable to add one or more frames to the frame collector. Error
code = 5" and the camera stays black. Always run `scripts/annexb_normalize.py` after ffmpeg: SPS/PPS once, no SEI,
4-byte start codes, like the organizer clips. Replacing a clip's content needs another Recording Server restart.

**Current state (2026-10-21):** camera `test_11` (port 116) plays AI City 2021 Track 4 training video 91 (15 min,
800×410; a crash at about 602 s; licence not cleared for the entry: internal tests only; source in `data/aicity21/`,
git-ignored). Camera `lens_1` (Universal driver, `rtsp://127.0.0.1:8554/lens1`) shows lens clips; it needs MediaMTX and
`lens.publisher` running (`scripts/start_lens.ps1`); both run detached and do not survive a reboot. MediaMTX v1.21.2
is in `C:\tools\mediamtx\v1.21.2`.

**Earlier state (2026-10-18):** cameras `test_01`–`test_10` (ports 106–115, device group Hackathon) play the
incident clips listed in `data/clips.json`; the Recording Server was restarted twice today. The construction clip is
in the driver folder (normalized) but has no camera.

**Earlier state (2026-10-17):** `data/construction_aeria_footage.mp4` (27.8 s drone footage of a construction site;
**source and licence not yet recorded: TODO**) is converted to `data/clips/1920x1080_construction_aerial` and copied
into the driver folder; `StableFPS.xml` revision bumped 2.26 → 3.26. **The Recording Server restart is pending** (the
participant chose to wait), so the camera on port 105 does not exist yet. To do: give `add_test_camera.ps1` the
organizers' hung-service fallback (end the process, start the service) and batch support with a clip-swap command.
