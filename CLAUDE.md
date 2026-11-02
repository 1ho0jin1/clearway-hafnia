# Hafnia Hackathon 2026

Our entry for the XProtect Developer Summit Hackathon 2026: a solution built on Milestone XProtect Corporate 2026 R1
and Hafnia VLM (a vision-language model reached through the Hafnia gateway on the machine). Repository:
`github.com/1ho0jin1/hafnia-hackathon-2026` (private).

**Judging weighs creativity and validity most** (organizer Q&A). Reproducibility counts too, but a best-effort
setup script plus documented manual steps is enough. Deliverable: this repository; a demo video is optional.
The product, its scope and the schedule are in `docs/PRODUCT.md` (2026-10-24: Clearway, an owner board for
right-of-way incidents); the pipeline step by step in `docs/walkthrough/`. Keep both current. The earlier plans
(verified accident alarms, a near-miss observatory) and plan C's design document were removed on 2026-11-02; their
findings are below.

## Project direction (decided 2026-10-22: plan C, right-of-way incidents)

- Solo entry; the submission portal closes **2026-11-02 12:00 CET** (extended from 11-01, told on 2026-10-29; open from Oct 26; a demo video **under 3 minutes**, public
  or unlisted, is required by the portal form read 2026-11-01, not the 3-5 min the hackathon page had recommended; see
  `docs/PRODUCT.md` for the criteria), plan to submit on Oct 30.
- **Selling point (2026-10-27):** optimization, not detection. The README, video and pitch lead with how Clearway
  decides when to ask, what to show, and measures and fixes the answers (`docs/PRODUCT.md`, "What sells it"). The
  obstruction categories get one line.
- **Scope: right-of-way incidents**, things that block or endanger a public way, for city and transit operators: a
  person on the tracks, a vehicle stalled in a lane, an object lying across a pavement, damage to transit. Security
  (break-ins) is a footnote: Hafnia scored 0 of 8 on real crime CCTV (`run/bench-20261018`), although it reads the
  organizers' synthetic scenes (`run/probe-20261022T054342Z`). Camera-status checks stay out of scope.
- Concept: tier 0 notices that **something changed and stayed changed** (dual background model, no object classes, no
  per-scenario rules), plus stalled vehicles and a person in a danger zone. The **lens** shows Hafnia the change:
  centred on the moment, cropped to the spot (BEFORE and AFTER stills and super-resolution were measured and left
  out, `run/pilot-20261023T162040Z`). Hafnia names it in JSON; a ledger item and
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
  *Advanced Settings*, and the gateway rules (recreate them through `POST /api/Rules`). The system prompt is empty
  by decision: every system prompt tried made the answers worse (`run/prompt-20261028T1605Z`).
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

Python 3.12 (installed from python.org, `py` launcher). The gateway and XProtect clients use only the standard
library; tier 0, the lens and the verdict memory run in `.venv` (`requirements.txt`). The pipeline as a flow
diagram (Mermaid, current): `docs/walkthrough/flow.mermaid`, rendered in `docs/walkthrough/index.html`; the README's figure is
`docs/clearway_pipeline.svg`.

| Path | What |
|---|---|
| `hafnia/gateway.py` | Hafnia gateway client: session, quota, prompts by title, `ask`, `wait_all` with per-phase timing; settings groups and the system prompt (`system_prompt`, `set_system_prompt`: the gateway validates the whole group on a PUT, so every setting of the group is sent) |
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
| `incident/` | Live pipeline: `bridge.py` (read FrameBridge; `width` asks the Recording Server for frames that wide, the service's `BRIDGE_WIDTH` 832), `router.py` (cooldown, open incident, rejected spots, budget), `verify.py` (Hafnia check + description) |
| `scripts/run_live.py` | The end-to-end pipeline on live cameras; logs to `run/live-<UTC>/events.jsonl` |
| `lens/` | The lens camera: `publisher.py` (one RTSP stream through ffmpeg to MediaMTX, frames stamped with the wall clock: idle frames, then each queued clip in real time, starting on a whole second; every frame carries the frame code; logs the UTC span, job number and frames sent per clip), `code.py` (the frame code: 64 blocks in the bottom 16 px, job number, frame index, wall time, CRC; `stamp`, `read`), `clock.py` (`LensClock`: lens_1's recorded time base read back from its own frames through FrameBridge; `span_for` a played clip, `offset`, `stats`), `client.py` (queue a clip; `crop`, `zoom`, `slow`, `mark`, `before_after`, `replay`, `span` as the assumed fallback), `enhance.py` (Real-ESRGAN super-resolution via spandrel; measured, not in the default), `mediamtx.yml` (RTSP on 127.0.0.1:8554 only, TCP only) |
| `scripts/setup_lens.ps1`, `scripts/start_lens.ps1` | Install MediaMTX (pinned, SHA-256 checked) and camera `lens_1` (Universal 1 channel driver, our rule "Lens: record lens_1 always"); start MediaMTX and the publisher detached (logs in `run/lens/`) |
| `scripts/check_lens.py` | Measure `lens_1`'s recorded time base against the publisher's clock through the frame code (`--minutes`, `--clips` synthetic clips, `--export` reads the recording itself back with `export_window.ps1`); no requests |
| `README.md`, `setup.ps1`, `scripts/check_setup.py` | The entry's README (what it is, the numbers, how to run and reproduce it); the one-script, idempotent setup of a hackathon machine from a fresh clone (Python 3.12, `.venv`, ffmpeg, the .NET 8 SDK and FrameBridge, MilestonePSTools, the lens camera, the model weights, the gateway password as a user-scope variable, `-Ntfy` for the phone, the board); its last step, a check at no request (cameras, `lens_1`, today's count) |
| `docs/VIDEO.md`, `docs/video/cards/`, `scripts/make_video.py`, `scripts/record_board.py` | The demonstration video: the storyboard and production notes; the title and number cards (HTML, the board's palette, Windows fonts); the assembler (cards and the board rendered with Edge headless, narration from `docs/video/voice/` or synthetic: Kokoro-82M through `scripts/narrate.py` in `.venv-tts` (`requirements-tts.txt`, git-ignored; `--samples` for choosing a voice) or Windows text-to-speech (`--engine sapi`, the old scratch track), one ffmpeg segment per scene, concatenated into `docs/video/clearway.mp4`, git-ignored); the board filmed headless during a run |
| `scripts/capture_screen.py`, `scripts/replay_board.py` | Video captures (2026-11-02): `capture_screen.py` films the largest 16:9 region of this desktop with ffmpeg's gdigrab from the same RDP session (`place` sizes Smart Client into it, `record NAME --seconds N`, `sheet` a contact sheet to pick the cut, `cut NAME SCENE --start --end` into `docs/video/captures/SCENE.mp4`); `replay_board.py <run>` replays a finished run's logs into a copy at their own pace (stamps shifted to the present) under a board on port 8767, for `record_board.py` to film on the idle machine, because filming the live board beside eleven cameras starves (renders 3 s or time out) |
| `docs/video-rev3/` | The rev. 3 video kit (2026-11-02, from the author's reorganized materials; replaces the `make_video.py` cut): `script.json` is the script (per line the words, what is on screen, the pause after it), `tools/narrate.py` speaks it with Kokoro in `.venv-tts` (plus Pillow) with exact line timings, `tools/build_video.py --ffmpeg <ffmpeg.exe>` cuts the visuals to the narration (camera moves over the chart stills from `visuals/shots/*.json`, `tools/camera.py`) into `clearway-rev3.mp4`, 2:53.5; a take in `voice/<id>.wav` (`recorder.html`) wins over the Kokoro file; the footage, narration, segments and cuts are git-ignored |
| `docs/walkthrough/`, `scripts/viz_walkthrough.py` | The walkthrough (renewed 2026-10-28): fifteen steps, each a claim, a figure from the real cameras and its numbers, with the operator's Confirm / Reject path (what a verdict changes and what it does not); `flow.mermaid` is the concise flowchart of the whole pipeline, embedded in `index.html` (Mermaid from cdnjs; the source text shows offline); the figures are made by the script (`--only fade lens_code pages` for the three added on 2026-10-28: the fade replays, a lens frame with its code read back, the board and summary renders). The page speaks the judges' words, not ours: "the incident memory" is the ledger, "a fingerprint" a SigLIP look, "on hold" held, "part of an incident" a piece, "the magnifier camera" the lens, "asked on the camera's own recording" a direct ask, "the lens recording's clock" its time base, "incident" the unit of counting ("card" only for the tile on the board), "the three-hour shift on Oct 26" M3 and "the 20-minute run after the fixes" the clean run; FrameBridge is introduced as our own MIP SDK reader (it is not an XProtect name) |
| `scripts/lens_compare.py` | One looped event asked about plainly and through the lens (`--variants crop crop_slow2 crop_sr`, `--prompt classify|json`, `--asks N`): finds the event live by frame matching; (1 + variants) × asks requests |
| `scripts/lens_pilot.py` | Plan C's lens pilot (M1): each synthetic incident camera, five views (full loop, event window, crop, crop + SR, BEFORE/AFTER), one JSON prompt (`clearway/prompt.py`); 5 requests per camera |
| `scripts/prompt_experiment.py` | The prompt experiment (2026-10-28): 28 clips the service had sent (lens spool AVIs, labelled by eye) played once more on `lens_1` with verified spans (`play`), asked in cells of system prompt × user prompt with the gateway's system prompt switched through its Settings API and cleared at the end (`ask`, resumable, one request per clip and cell), scored into the run's README (`score`, the hand-written findings above the marker are kept); `restore` clears the system prompt |
| `scripts/holdout.py` | The held-out check (2026-10-29): the change detector on the three CC0 street clips (`data/footage/commons`, never used for tuning) with the real-camera and the looped-clip settings (`detect`, no request: candidates, the clips the service would send built with the service's own window and crop rules, contact sheets for labelling by eye into `labels.json`), the clips played on `lens_1` with verified spans (`play`), asked once each with the service's prompt and the empty system prompt (`ask`, resumable, capped), scored into the run's README (`score`, hand-written text above the marker kept) |
| `scripts/fetch_footage.py` | The three CC0 street clips of the held-out check fetched from Wikimedia Commons into `data/footage/commons` with a SHA-256 check (standard library only, so `py` runs it; resumable; waits on HTTP 429; `--check` verifies without downloading); their Commons titles, authors and checksums are in the script, read from the Commons records on 2026-10-29 |
| `scripts/vanilla_poll.py` | The plain way to use Hafnia, measured for the comparison in the demo video (2026-10-29): the organizers' example question ("Describe what happens in this video.", a 30 s clip ending 5 s ago, as the kit's `ask_hafnia.py`) asked about every named camera every `--every` seconds for `--minutes`, as a recurring XProtect rule with a Hafnia webhook would (`run`: the plan and today's count first, `--dry-run`, `--max-requests`); `score` writes the run's README below the marker (per camera, which answers name an incident by keyword, the interval's arithmetic: requests per camera-hour, coverage, how long 500 last), `answers.md`, `summary.json`. Clearway's side is a live run over the same minutes |
| `scripts/second_question.py` | The AlertValidation shape as a second question (2026-10-29): the first answer's category put to Hafnia as the upstream alert on the same recorded span, cell D's prompt otherwise (`plan` from the hold-out's false cards and the prompt experiment's cell A incidents; `ask`, resumable, the system prompt must be empty; `score` into the run's README below the marker, `answers.md`, `summary.json`) |
| `scripts/scale_fit.py` | The calibrated-floor test (2026-10-29): a scale per camera and row in pixels per metre, fitted from YOLO11m boxes of people (1.7 m) and cars (box 1.5 m high) against the row they stand on (`fit DETS OUT`, `show`); helpers `ppm`, `floor_share`, `world_m2` for `eval_change.py --scales --world-floor` and `holdout.py detect --scales --world-floor --baseline` (the detector's optional `ChangeParams.min_area_fn`, `None` in the service) |
| `scripts/calib_raise.py`, `scripts/calib_compare.py` | The calibrated floor scored: `calib_raise.py` the raise-only form from the baseline runs alone (which candidates a floor of X m² would drop, which loops it would lose); `calib_compare.py` the run folder's README below the marker and `summary.json` (scales, blobs in m², the three streets baseline against calibrated with inherited answers, the loops) |
| `clearway/ledger.py` | The ledger (product F1): incidents, pieces, recurrences (no request), provisional skips with escalation, same-category merge, one alarm per incident (closed once it stayed cleared 60 s, reopened when it recurs), clearing, failed questions, operators' verdicts (F7: a rejection teaches the card's looks as harmless at its spot, answers about what was rejected join the rejected card; a confirmation overrules Hafnia's rejections there); returns actions, logs events (JSONL), `Ledger.replay()` |
| `clearway/alarms.py` | XProtect alarms and bookmarks for the ledger's incidents (F3): raise on the incident's camera (category priority, owner in the name, Hafnia's summary marked AI-generated, snapshot, bookmarks on the camera and, for a crop shown on the lens, on `lens_1`), reopen, close, confirm (In progress); one thread, in order |
| `clearway/service.py`, `clearway/prompt.py` | The Clearway service (F2): FrameBridge → change detector (a thread per camera) → SigLIP look → ledger → the crop (a spot the lens would magnify less than `DIRECT_BELOW` is asked about on its own camera's recording, the crop only stored for the board; a small one is played on the lens) → `HafniaAnswers` (run cap, daily count, `PARALLEL` requests at once; a failed direct ask is asked once more on the lens) → ledger; logs `service.jsonl`, `ledger.jsonl`, `changes.jsonl` (replayable); takes operators' verdicts from `operator.jsonl` (F7) every second. The JSON prompt and its parser |
| `scripts/run_clearway.py`, `scripts/report_clearway.py` | Run the service on live cameras: `--answers standin` (dry run, no requests; loop phase by frame matching; detectors start at a loop start) or `--answers hafnia --max-requests N`; summarise a run per camera beside the offline replay, scoring Hafnia against the stand-in, with operators' verdicts and the later decisions they changed |
| `scripts/eval_ledger.py` | The ledger replayed offline against a stand-in for Hafnia: requests, cards, occurrences, alarms, misses; saves each clip's event stream, `--from-events` replays them without the detector |
| `tier0/change.py`, `tier0/memory.py` | Plan C tier 0: the change detector (`ChangeParams.loops()` / `.real()`; an open change's spot is left out of the slow background so a lasting change does not fade, `release()` lets it in for a change the ledger judged harmless) and the SigLIP 2 verdict memory (`Embedder`, `VerdictMemory`) |
| `clearway/board.py`, `clearway/board.html` | The owner board (F4): a standard-library web server on 127.0.0.1:8765 following a run folder (`--latest` by default): cards by owner with the lens clip (MP4 made from the spool on first view), snapshot, summary, time open, recurrences, alarm state, Confirm / Reject (F7: `POST /api/operator`, board's own page only, appended to the run's `operator.jsonl`); JSON at `/api/board` |
| `clearway/summary.py`, `clearway/summary.html` | The shift summary (F8), from a run's logs (no requests): incidents by owner and category, false cards, change to card (first and repeat), card to XProtect alarm, alarm to clear, clear to alarm closed, time open and longest occurrence (the ledger's clearing rule replayed over its log and the detector's closings), recurring spots with snapshots, cost per camera-hour and cameras per 500-a-day allowance, operator verdicts; hotspots (F9): per camera, the ledger's spots with their counts and the heat of every reported change over the camera's scene image (`<run>/cameras/`, the detector's slow background, written by the service every 10 min and at the end; the board serves it at `/cameras/<camera>.jpg`); `shift.json` (written by the service at the end, or `python -m clearway.summary <run>`) and the board's `/summary` page; logs are read incrementally |
| `clearway/notify.py`, `config/owners.json` | Owner notifications: each ledger effect (opened, reopened, cleared, confirmed, rejected) to the incident's owner as a JSON webhook (`clearway.notification/1`) or as a push on their phone (`"type": "ntfy"`: title, text, priority from the incident's, the snapshot attached, Confirm / Reject buttons that post a signed verdict to a reply topic; `NtfyReplies` follows that topic, outbound only, and appends verdicts to the run's `operator.jsonl` like the board, F7; `max_per_hour` guard); targets per owner, real URLs and keys from environment variables (`url_env`, `reply_url_env`, `secret_env`: HMAC-SHA256 of the body for webhooks, of the verdict tokens for ntfy), a thread per target, retries; logged by target name, never URL; `run_clearway.py --notify`; self-test `python -m clearway.notify --test [--listen N]` |
| `scripts/setup_ntfy.ps1` | Phone pushes: creates the ntfy topic, reply topic and verdict secret once (user-scope `CLEARWAY_NTFY_URL`, `CLEARWAY_NTFY_REPLY_URL`, `CLEARWAY_NTFY_SECRET`; the topic name is the credential: never in git, chat or slides), shows the topic to subscribe to in the ntfy app (`-Show`), sends a sample push (`-Test`, `-Listen N` waits for a tap) |
| `scripts/owner_inbox.py`, `scripts/owner_inbox.html`, `scripts/start_inbox.ps1` | A stand-in for the owners' channels on 127.0.0.1:8770: receives the notifications (checks signatures with `CLEARWAY_HOOK_SECRET` set) and shows a feed per owner; keeps them in `run/inbox/` (git-ignored) |
| `scripts/start_board.ps1`, `scripts/open_board.ps1` | Start the board detached (logs in `run/board/`); open it as an Edge app window beside Smart Client |
| `scripts/start_smartclient.ps1` | Start Smart Client not elevated (Medium integrity) from the built-in Administrator; did not make HTML page items use Edge here |
| `tier0/zones.py`, `config/zones.json` | Person triggers (F5): a person's feet inside a camera's danger-zone polygon for 1 s, reported to the ledger like a change; the polygons, by camera name, in image shares (the only per-camera setting) |
| `scripts/eval_change.py`, `scripts/eval_memory.py` | Offline checks, no requests: the detector on every clip as its camera plays it (`--profile`, gate G1); the memory against a stand-in for Hafnia (`RULES`: none, spot, spot unless confirmed, appearance, SigLIP) |
| `scripts/probe_cameras.py` | Neutral description and one-word class per camera over one loop (cameras × 2 requests) |
| `scripts/inspect_footage.py`, `scripts/remote_zip.py` | Candidate footage: contact sheet and YOLO road-user counts; single files out of huge remote zips by HTTP range requests |
| `data/clips.json` | Incident clips: neutral camera name, source file, length, label, ground truth; organizer cameras as controls |
| `run/<name>/` | Model run results: the README and rendered reports (`report.html`, `compare.html`) are committed; the raw logs (`*.json`, `*.jsonl`, `*.log`, `*.pkl`, `*.npz`) were removed before the repository went public (2026-11-02) and are git-ignored, except `run/holdout-20261029/labels.json` (hand-made labels the reproduce steps copy) |
| `data/` | Source videos (`*.mp4`) and converted clips (`data/clips/`), both git-ignored: too large, and judges must download them from their source |

## Commands

The gateway password lives in the user-scope environment variable `HAFNIA_GW_PASSWORD`. Shells started by Claude Code
do not inherit it, so load it first in the same command:

```powershell
$env:HAFNIA_GW_PASSWORD = [Environment]::GetEnvironmentVariable('HAFNIA_GW_PASSWORD', 'User')
foreach ($n in 'CLEARWAY_NTFY_URL', 'CLEARWAY_NTFY_REPLY_URL', 'CLEARWAY_NTFY_SECRET') {   # phone pushes (--notify)
    Set-Item -Path "env:$n" -Value ([Environment]::GetEnvironmentVariable($n, 'User')) }
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

**Lens pilot (plan C, M1)** (`run/pilot-20261023T162040Z/README.md`, 30 answers; `run/lens-test_11-20261023T165151Z`, 9):
with a JSON prompt that defines each category, Hafnia named all six synthetic incidents right in all five views
(30/30), even over a full loop. Summaries checked against the frames: the full loop still tells the gate backwards
across the loop cut; event windows do not. Real-ESRGAN super-resolution gave the bicubic answer word for word, on the
large synthetic objects and on test_11's 30-px crash; BEFORE/AFTER stills turned a lying scooter into "parked". Both
stay out of the default lens. The category list steers the whole answer: without a crash category the crash was
STALLED_VEHICLE nine times and never named in a summary (COLLISION to add, gate G3). Tool types are invented
("chainsaw", "lockpicks" for bolt cutters). Asking again about the same span returns the same answer, word for
word: repeats need different events or windows (2026-10-28: the same category every time, but the words differ in
about a third of repeats, `run/prompt-20261028T1605Z`). Hafnia's cloud refused one specific clip twice ("Transfer Assets: …
HTTP 403 Forbidden"); the same window shifted by 1 s worked; failures are not counted.

**Ledger, offline** (`run/ledger-F1/README.md`, no requests; stand-in for Hafnia): six incident cameras over 5 min cost
9 requests instead of 190, one card per incident, every later occurrence recognised (card in 1.4–2.6 s), no incident
change lost. On real `test_11` the memory once skipped the crash as a look-alike of a harmless change at the same
spot (similarity 0.947: the road dominates small crops); skips are now provisional (asked after 30 s if the change
stays), so the crash is carded 60 s after it began and real footage saves little (18 of 21 requests). Long replays
were stopped twice by Claude Code for low machine memory: event streams are saved per clip (`--from-events`).

**Clearway service, live (F2)** (`run/clearway-live-20261025T083623Z/README.md`, 10 requests; dry run
`run/clearway-dry-20261025T083035Z`): on the six incident cameras the whole pipeline runs live at 9.8–9.9 fps per
camera (a thread each); one card per incident, all six categories right, Hafnia agreeing with the stand-in on 9 of 10
answers (the tenth, a gate crop showing only the fence, is NONE: the gate needs its person trigger); later
occurrences carded in 1.4–2.5 s without a request. First cards come 36–85 s after the change: Hafnia takes about
10 s, the rest is the single lens camera playing every question's clip in turn. Fixed on the way: float32 times
(steps of 128 s at Unix time) in the change detector, a 2× faster detector (identical reports), the ledger forgetting
an incident's rarer spots (diverse looks; merges take the box), lens-client races on Windows, and a failed question
leaving its incident pending (`Ledger.on_failed`). Test harness: looped cameras' detectors start at a loop start (a
mid-loop start put part of the incident in the warm-up background); the gate's stream never delivers its loop's
first 5 frames.

**XProtect alarms (F3)** (`run/clearway-dry-20261025T090255Z/README.md`, no requests): one alarm per incident on its
camera, named for the category and owner, the category's priority, a snapshot of the spot, bookmarks on the camera
(event window) and on `lens_1` (the clip Hafnia judged); 6 of 6 right on the incident cameras, 0 errors. The ledger
keeps an incident's alarm open while it recurs and closes it once it has stayed cleared for 60 s (replaces the 5-min
quiet period; same replay counts); a closed incident that recurs reopens the same alarm (state New), tested live with
a 5 s delay. XProtect applies alarm updates about 1 s later, so every update names its state and priority (a comment
right after a close would otherwise read the old state back and reopen the alarm).

**Person on the tracks (F5)** (`run/clearway-live-20261025T092317Z-tracks/README.md`, 2 requests): the change detector
holds people back, so it saw the person on the tracks in 1–2 of 20 loops; a danger-zone trigger (feet, the bottom
centre of YOLO's box at 5 fps, inside the polygon for 1 s) reports them in every loop (feet inside from 6.2 s into the loop, reported at 7.2 s;
offline, 4 of 4 loops). The polygon is
everything beyond the near platform's yellow tactile strip ("stay behind the yellow line"), the strip's edge fitted by
colour. Live: one card with 12 occurrences in 3 min (1.0 s each, no request), Hafnia PERSON_ON_TRACKS 2 of 2, a High
alarm for rail control with Hafnia's summary. XProtect calls take 20–60 ms idle (0.8 s for a whole alarm with one
camera running) but 0.5–4 s each with six cameras running (`run/clearway-dry-20261025T092705Z-timing`): an alarm with
its snapshot and bookmarks takes 2–8 s (13 s median in one run) after its card; the machine's 4 cores are busy.

**Owner board (F4) and Smart Client** (`run/clearway-dry-20261025T094247Z-board`): the board runs live beside the
service and on finished runs; clips play, new cards are highlighted, the questions waiting for the lens show above
the columns. Smart Client 2026 R1 cannot show it here: its HTML page item (plugin `VideoOS.RemoteClient.Plugin.HtmlViewItem`)
shows standard display mode with the Windows Community Toolkit's `WebViewCompatible` (legacy Edge, EdgeHTML) and
otherwise falls back to Internet Explorer in IE 7 mode (user agent `MSIE 7.0; Trident/7.0`; IE Enhanced Security
blocks its scripts). As the built-in Administrator it says standard mode cannot run elevated; started without the
Administrators group, and at Medium integrity (`scripts/start_smartclient.ps1`), with either `renderingEngine` value in
the view item (0 or 1, set with `Set-VmsView`), it still fell back. The WebView2 runtime is not what it uses
(installed for a test on 2026-10-25, 156.0.4314.42, and removed again). The board is its own Edge app window
(`scripts/open_board.ps1`). Views by script: `New-VmsViewGroup` (a top-level group cannot hold views: add a child
group) and `New-VmsView`; an HTML page item's definition is `VideoOS.RemoteClient.Plugin.HtmlViewItem.HtmlViewItem`
with `iteminfo url=...` and a `renderingEngine` property (the test view group Clearway › Board was removed again).
The Web Client (port 8081) shows camera views only. **Smart Client's Alarm Manager list drew nothing on 2026-11-02**
(its quick filters counted New 3, Closed 15; the list showed 0 rows under every filter, for the author and for a
scripted click, with the machine busy and idle), while `GET /alarms` on the REST API returned the same alarms with
name, priority, state, source camera and message: the video's alarm scene shows those (`docs/video/cards/alarms.html`).

**Operator verdicts (F7)** (`run/clearway-dry-20261025T133738Z-operator`, no requests): Confirm and Reject on each
card; the board appends the verdict to the run's `operator.jsonl` (JSON from its own page only), the service reads it
every second (applied 0.1-0.5 s after the click) and the ledger takes it. Reject: the alarm closes with the reason and
the card's looks are rejected at its spot, so later look-alikes are skipped (26 on the bin in 3 min). Confirm: the
alarm goes to In progress and Hafnia's rejections there that look like the card are overruled. First test
(`run/clearway-dry-20261025T132833Z-operator-inflight`): the rejected bin card came back, because two pieces of its
first occurrence were still in the lens queue and their answers became new cards. Answers about what the operator
rejected (asked before the verdict, or about a held look-alike) now join the rejected card when they name the same
category; another category still gets a card. Escalated look-alikes of a rejected card still cost a request each (2
in 3 min on the bin). Verdicts live in the run's ledger: a new run starts without them. The board's media URLs carry
the run (`?run=`): ids restart every run and the browser had shown a previous run's snapshot.

**Shift summary (F8)** (`run/clearway-dry-20261025T141258Z-summary`, no requests): `clearway/summary.py` builds it from
a run's logs (the board's `/summary`, refreshed every 15 s while live; `shift.json` written by the service at the end).
How long things lasted is not in the ledger's log alone (it logs a clearing only for an open card), so the summary
replays the ledger's clearing rule over its log and the detector's closings: all 201 clearings the ledger logged on
three runs fall at the end of a replayed occurrence (172) or inside one where two pieces asked about apart overlapped
(29). A union of each change's own interval was wrong: on loops small pieces never close, and every incident lasted the
whole run. On the loops a median occurrence lasts 7.6-11.8 s and a repeat is carded in 1.4 s; the first card takes
38-62 s (median), the lens queue. The page names looped cameras and short runs, whose per-hour rates are a start-up
burst's. The looks (768 numbers a line) are cut out before parsing: 0.03 s instead of 0.12 s for 5 min of logs.

**Hotspots (F9) and eleven cameras** (`run/clearway-dry-20261026T140810Z-preflight11`, no requests): the summary page
draws each camera's spots over its scene image: cards outlined in their owner's priority colour with their counts,
what was not an incident (Hafnia's NONE, the operator's rejection, with the look-alikes the memory skipped) dashed
grey, and the heat of every change the detector reported, card or not, on one scale for all cameras. The scene image
is the detector's slow background, so a looped incident is not in it. Six category colours fail the all-pairs
colour check (yellow and orange too close), so boxes take the owner's priority colour and the category is in the
label. Eleven cameras at once: FrameBridge delivers 4.0-5.0 fps per camera (about 45 fps in all; 9.8-9.9 with six),
and the service processes every frame; for the first 3 minutes, while everything starts, XProtect calls are slow
(the first alarm took 116 s, later ones 0.2-0.3 s). The five street cameras at the real-camera setting report
nothing: a change must last 15 s, longer than their 8-15.5 s loops.

**Three-hour live shift (M3)** (`run/clearway-live-20261026T141534Z-m3/README.md`, 32 requests; judged from Hafnia's
summaries, not yet audited against the frames): eleven cameras for 3 h, 11 cards, 4 of them false (0.12 per
camera-hour), all from answers asked in the first 6 minutes, when 26 questions came at once; 24 of 32 answers fit the
scene. Three wrong answers describe another camera's scene (the gate "walks along the railway tracks"), matching the
clip the lens played about 10 s after the asked span: `lens_1`'s recording lagged the publisher (confirmed 2026-10-27
with exported frames, `run/lens-check-20261027`: recorded time 0.3-9.5 s behind the publisher's clock under load,
1.5-2.2 s when quiet; four of the six wrong answers judged other cameras' clips and every lens answer lost its first
1.5-3 s; see **Direct asks for large spots** and **Lens self-check**, which found the cause). The looped object incidents faded: the detector reported them in the
first half hour and hardly after (the slow background, τ 600 s, probably takes in a state present for most of each
loop), so their cards stayed open all shift and questions stopped after 70 minutes; the person triggers did not fade.
XProtect was slow all shift with eleven cameras (35-62 s per alarm action, bookmarks about 30 s; a card's alarm 276 s
after it), not only at start-up; 12 calls timed out on one alarm. The stand-in is no answer key for the gate: it
expects TAMPERING for the lit pavement, which Hafnia rightly calls NONE.

**Owner notifications (F12)** (`run/clearway-dry-20261025T144944Z-notify`, `...145829Z-notify-cycle`, no requests): the
ledger's effects go to the incident's owner as JSON webhooks (`clearway/notify.py`) beside the XProtect alarms; the
stand-in owner inbox (`scripts/owner_inbox.py`, 127.0.0.1:8770) shows a feed per owner. Live: 8 messages (6 opened, a
confirmed, a rejected), all delivered within 0.6 s of the effect; owners told 59.9 s after the spot changed (median),
within a second of the card. With `--close-after 5` the looped bin sent cleared and reopened every 15 s, which is what
the 60 s close prevents. Real webhook URLs and signing keys come from environment variables named in
`config/owners.json`; deliveries are logged by target name, never URL. One-way while the board is reachable only on the
machine; Teams and Slack formats are TODO.

**Phone pushes (F12, ntfy)** (`run/clearway-dry-20261027T044611Z-ntfy`, no requests; self-test `run/notify-test`):
each owner's news also goes to a phone through an ntfy topic (`clearway/notify.py` `"type": "ntfy"`,
`scripts/setup_ntfy.ps1`): title, text, priority 5 for High (rings through), the snapshot attached, Confirm / Reject
buttons that post a signed verdict to a reply topic the service follows (outbound only). Live on three cameras: three
cards, each pushed 0.7 s after its effect with the snapshot (97-107 KB); a Reject tapped on a simulated phone reached
the listener 0.7 s after the tap, the ledger 0.9 s, XProtect closed the alarm 1.2 s after the tap and the phone had
the acknowledgement at 1.4 s; 13 later look-alikes at the spot were skipped. The listener refuses a wrong token and a
message that is not a verdict. ntfy.sh's limits per IP (its Limitations table): 250 messages a day, 2 MB per
attachment and 20 MB of attachments a day, 60 requests then one per 5 s; a message is kept 12 h, its attachment 3 h.
Guards: one daily budget for all ntfy targets (past 170 only new and returning incidents go out, past 230 nothing),
60 an hour per target, snapshots scaled to 640 px wide (about 40 KB). RFC 2047 headers carry the text with its line
breaks and Hafnia's punctuation. The topic name is the credential: user-scope
environment variables, never in git, chat or slides; `setup_ntfy.ps1 -Show` prints it for the phone.

**Direct asks for large spots** (`run/clearway-live-20261027T081803Z-direct/README.md`, 6 requests; dry run
`run/clearway-dry-20261027T081259Z-direct`): a spot the lens would magnify less than `DIRECT_BELOW` (2.5x; the
pilot's full-frame answers were right down to 2.7x) is asked about on its own camera's recording over the event
window (whole seconds, 3 s after the window's end); its crop is stored in the spool without a job file, for the
board's card; the lens is kept for small spots (test_11's crash, about 6x). FrameBridge's frame times come from the
Recording Server, so the camera's recording has the service's own time base: no offset and no queue; at most
`PARALLEL` (3) requests at once. Live on three cameras: 2 of 6 questions direct (e-scooter 2.14x, bin 1.23x), Hafnia
answered them in 5.3-5.5 s and their cards came 13.3-13.4 s after the change (lens questions 21.8-47.2 s; M3's median
104 s); 6 of 6 categories as expected, both direct summaries right in every claim against the frames. On M3's 33
questions the rule would have sent 13 direct, among them both wrong-scene answers that came from large spots (cw-0009,
cw-0022). A failed direct ask (no recording over the window: the organizers' cameras record on motion) is asked once
more on the lens while the window's frames are kept (not seen yet). Alarms: a direct card gets one bookmark, on its
camera; the message names the camera and span Hafnia judged. `--direct-below 0` keeps every spot on the lens;
`--no-lens` makes every question direct.

**Lens self-check** (`run/lens-check-20261027T094716Z`: quiet machine, the recording read back;
`run/lens-check-20261027T095146Z-load-wallclock/README.md`: the eleven-camera load, wall-clock against count
stamping; no requests): every lens frame carries the frame code of `lens/code.py` (64 blocks in the bottom 16 px:
job number, frame index, the publisher's wall time, CRC; readable at any width after H.264 and JPEG); `lens_1` is in
the service's FrameBridge and `lens/clock.py` reads the code from its frames, whose times are the Recording Server's,
so each clip's recorded span is measured from its own frames (a line through the frames seen, 0.3 s margin, whole
seconds, neighbouring clips' frames checked) instead of assumed from the publisher's clock. The live feed's times
are the recording's: frames exported from the recording decode to the same offset (+0.02 s on a quiet machine). The
cause of M3's lag was found with it: ffmpeg stamped the raw frames by count, the publisher drops frames when the
busy machine holds its loop, and XProtect records by the stream's time; under the eleven-camera load the recording
fell to 9.4 s behind within four minutes with no frame discarded by MediaMTX, and recovered through the publisher's
catch-up bursts (M3's unexplained recovery). The publisher now stamps frames with the wall clock
(`-use_wallclock_as_timestamps 1`, the demuxer's `-framerate`, `-fps_mode cfr`; `--no-wallclock` for comparison):
the same load gives +0.4 to +1.4 s (the delivery latency) and drift within a clip under 0.6 s. The service's live
JPEG feed of `lens_1` carries only 12-42 % of the frames under that load while the recording takes the whole stream,
so a clip is verified when frames were seen from its first and last quarters, the drift is under 1 s, no neighbour
and no hole lie in the span (a hole: readable frames whose send times are more than 2 s apart, as MediaMTX's
discards leave, and they are not recorded either); a clip with no frame seen or a hole of `REPLAY_HOLE_S` (1 s) is
played once more. `lens` events log `offset_s`, `seen`, `sent`, `coverage`, `drift_s`, `hole_s`, `verified`; health
logs the clock's stats; `scripts/report_clearway.py` prints the `lens` block; `scripts/check_lens.py` repeats the
measurement (`--export` reads the recording back).

**The fade** (`run/change-fade-before`, `-after`, `-after2`, `-after3/README.md`: 30-minute offline replays of the
bin and e-scooter loops, no requests): the detector before 2026-10-27 caught 16 of 119 loops on both cameras and
fell silent after seven minutes, which is M3's fade: the slow background (τ 600 s) learnt everywhere the fast
foreground did not move, lasting changes included. Three general changes in `tier0/change.py`: an open change's spot
is left out of the slow background (`freeze_open`); static-changed pixels not yet reported are not learnt until they
have persisted `learn_static_after_s` (60 s), because the precursor of each loop's change (the rider standing before
the hold-back let the report through) had left a growing ghost in the before snapshot until the empty spot no longer
matched it (with the freeze alone the e-scooter stuck after 48 loops: one open change swallowed every later blob at
its spot); and "restored" is judged within `restored_ratio` (0.25) of the change's own contrast as well as within
`restored_diff`, with motion judged frame to frame (the fast background lags a cut by half a second). A fourth,
closing a change whose spot looks like neither its before nor itself and re-baselining the spot (`changed_s`), is off:
it split every evolving incident into its states (3-6 reports per loop) and would close a real incident that
evolves. Final replay: 119 of 119 loops on both cameras, reports steady for 30 minutes (bin 3 per loop, e-scooter
2: the pieces the ledger merges), all but 4-5 changes closed. The service releases a dismissed or rejected incident's
changes (`ChangeDetector.release`), so their spots are learnt and set back to their before when restored.

**Where the CPU goes with eleven cameras** (`run/clearway-dry-20261027T121705Z-width0/README.md` and
`-122305Z-width832`, `-123136Z-detect2`: three 5-minute dry runs, no requests; the health record now carries the
CPU shares of the machine, the Recording Server, FrameBridge and the service, from psutil): the Recording Server is
not the bottleneck the investigation assumed (4.4): it uses under 2 % of the machine, because the MIP .NET library
decodes the H.264 streams and makes the JPEGs inside FrameBridge (22-28 %), and the service's own work takes more
than two of the four cores (56-62 %); the machine is at 100 %, so FrameBridge delivered 4.3-4.7 of each camera's 10
fps and `lens_1`'s feed with it (M3's MediaMTX discards were the same saturation). `--width 832` (`BRIDGE_WIDTH`,
the default: the incident cameras' own width) saves a quarter of FrameBridge's share and gains a tenth of the
frames. `DETECT_EVERY` 2 (the detector sees every second frame; it waits persist_s before reporting anyway) gains
far more: 7.5 frames per camera per second delivered, the lens feed's coverage 0.54 instead of 0.33 with no
replay, its latency 0.23 s instead of 0.79, the service at 52 %. Still open: FrameBridge forwarding every second
frame itself, the real-camera profile's 640-px working width.

**Clean live run under the day's fixes** (`run/clearway-live-20261027T124112Z-clean/README.md`, 14 requests; eleven
cameras, 20 minutes, alarms and phone pushes): 7 cards on the six incident cameras and none on the five street
cameras (M3: 4 false), 12 of 14 categories as the stand-in expected (the graffiti described exactly but filed
OBSTRUCTION; the gate's first lens clip NONE with a 0.7 s hole in its feed), cards 19.5-31 s after the change for
direct asks and 42-72 s through the lens (M3 median 104 s), 331 recurrences carded without a request (79-83
occurrences per card: the fade fix at work), lens offsets +0.29 to +0.47 s with 3 of 4 spans verified, no answer
about another camera's scene. One wrong object with the right category: the lying scooter's crop called "a large
tree branch". XProtect alarm actions still 14-71 s per raise (median 19 s): the API Gateway on a saturated machine;
the service and FrameBridge now run below normal priority (`Service(below_normal=True)`, `--normal-priority` to
compare) so XProtect's services are scheduled first: `run/clearway-dry-20261027T134043Z-priority/README.md`, the
same eleven cameras, raises 0.16-0.23 s (median 0.2 s; M3's 35-62 s were this), our frame rate unchanged (7.0-7.7
per camera), the lens recording's delivery latency gone (+0.01 s under load). The lens publisher stays at normal
priority: it is a camera.

**Prompt negatives** (`scripts/reask.py`; `run/clearway-live-20261027T124112Z-clean/reask-negatives.jsonl` and
`reask-summary_first.jsonl`, 21 requests): the clean run's 14 spans asked again with two variants. With each
category's definition saying what it is not (OBSTRUCTION "not someone painting, breaking or forcing something",
DAMAGE "choose this even if the damaged thing is next to a path", NONE "ordinary traffic, people walking, parked
vehicles, a stationary train", ...), the graffiti became DAMAGE, the twelve right answers stayed, the clip of the
wrong seconds stayed NONE, and the ambiguous scooter crop went from a right label for a wrong object ("a large
tree branch") to NONE: 13 of 14 as expected against 12. Asking for the summary before the category did not fix the
graffiti and made that crop STALLED_VEHICLE. The negatives prompt is `clearway/prompt.py`'s since; `reask.py`
keeps the original as a variant. The sample is one run's spans: the pilot's thirty answers (`run/pilot-*`) have
expired from the recordings and were not re-checked.

**Prompt experiment: a system prompt and structured prompts** (`run/prompt-20261028T1605Z/README.md`,
`scripts/prompt_experiment.py`, 267 requests on 2026-10-28): the gateway's *System Prompt* setting had never been
set on this machine (no stored value; nothing in the repository sets one). 28 clips the service had sent on 10-26
and 10-27 (the spool AVIs: crops, the former false cards, the "tree branch" scooter crop; 18 incidents, 10 with
none, labelled by eye) were played once more on `lens_1` with verified spans and asked in every cell. **The
service's one-paragraph prompt with negatives kept all 28 answers in both runs; every variant lost some.** Read it
as a comparison between prompts, not as an accuracy (2026-10-29): the 28 clips are the machine's eight looped
scenes (six staged incidents seen 2-5 times each: the five bolt-cutter clips are one act at one gate; the negatives
are quiet moments of the same loops, nothing that looks like an incident without being one), and clips 18-28 are
the very spans `reask.py` had re-asked on 10-27 to choose the negatives, so the baseline had two tuning passes on
this material and the variants none. The repeat shows stability (the category never changed; the words differ in
about a third), not generalisation; the held-out check on real streets is the hold-out paragraph below. Every
variant was worse: the same content in
sections lost 7 (cars driving through became "stopped in the middle of the lane"); sections plus context, rules
and a `confidence` field lost 7, all false cards ("a large fallen tree trunk" on an empty pavement at night; the
rule against guessing objects produced them); Hafnia's trained system prompt lost 4 (the graffiti twice: "a person
stands beside a stationary train"); our own system prompt lost 5 (four false OBSTRUCTIONs), and with the structured
prompt 10, every empty clip called an incident. The trained AlertValidation shape is a strict verifier: 0 false,
10 of 18 incidents discarded ("a routine disposal action"), everything it confirmed right, the five High-priority
clips among them: a candidate second question for High alarms, untested beyond these clips. Confidence was 0.9-1.0
on every answer, right or wrong: not a signal. No latency difference between cells (Hafnia's phase 2-3 s). The
trained text, as system prompt or in the user prompt, makes the JSON come fenced in ```` ```json ````; the
baseline is fenced about half the time already, never with prose around it, and the parser's `{...}` search was
right every time. Decisions: keep `clearway/prompt.py` as it is, leave the system prompt empty (the setup script
sets none), do not add a confidence field; escalation must come from a second view or window, not from the model.
The gateway's Settings API: `GET/PUT /api/Settings/{group}` with the group key URL-encoded (`##local##.Advanced`),
the PUT carrying every setting of the group (`Gateway.save_settings`).

**Hold-out check: the detector and the prompt on real streets** (`run/holdout-20261029/README.md`,
`scripts/holdout.py`, 2026-10-29, 41 requests sent, 39 completed): the user's worry that the 28 of 28 was
over-fitted was right. The three CC0 street clips (`data/footage/commons`: a Mumbai junction from above by day,
a Mumbai street at night, a Düsseldorf tram junction; never used for tuning) went through the detector offline
(no request) with the real-camera setting the service gives real cameras and, for more hard negatives, the
looped-clip setting; each report became the clip the service would send by its own rules (`clearway/service.py`'s
window and crop, the lens from x2.5, the whole frame below); 40 were played on `lens_1` with verified spans and
asked once with the prompt and the empty system prompt as they are. Labels by eye, all NONE: queued taxis and cars
waiting at lights or crossings, people crossing tram rails, motorbikes paused in the junction, parked cars, stalls,
facades. **Result: 8 NONE, 31 false cards of 39 answers** (one clip failed twice at Hafnia, HTTP 403, free): 20
STALLED_VEHICLE on waiting cars ("stopped in the middle of the lane, blocking traffic", lead vehicle or not), 5
COLLISIONs invented on moving traffic ("sparks and smoke, the rider is thrown"), 6 OBSTRUCTIONs with "a large fallen
tree trunk" three times (a pavement corner; pedestrians' legs over tram rails). The prompt's negatives already name
queued and parked vehicles and ordinary traffic: they did not hold. 6 of the 8 right answers are Düsseldorf clips
where the crossing and the lights are in view; the lens view and the whole frame did not differ otherwise. The
detector at the real setting raised 3 candidates in 10.7 minutes (about 17 per camera-hour: Mumbai day 42,
Düsseldorf 14, the night street 0, untested whether a blind spot); the loops setting 450-790 per hour. Decisions:
the judge-facing numbers carry this result beside the looped ones; the prompt is not changed (its negatives are
overridden, and 10-28 showed rules add invented objects); the set is a tuning set from now on, so any fix is
checked on new footage. Where a fix would sit: a longer wait on a lane at a junction (a light cycle), the
operator's rejections teaching the memory, the AlertValidation shape as a second question before a High alarm
(39 requests to test on these spans), the whole frame with the spot marked for a stopped vehicle. **Reproducible on
another machine since 2026-10-29:** `scripts/fetch_footage.py` fetches the clips (CC0, SHA-256 checked, about
500 MB); the run README's "Reproduce it on another machine" gives the commands (a new run folder, this run's
`labels.json` copied in, 40 requests) and what to expect (ids match when the candidates do; the counts land near 31
of 39, not on it).

**The second question tested** (`run/validate-20261029/README.md`, `scripts/second_question.py`, 2026-10-29, 49
requests, today's count 88 after): the AlertValidation shape with the first answer's category as the upstream alert
(cell D's prompt otherwise, pre-registered, one shot) on the hold-out's 31 false cards and the prompt experiment's
18 true incidents. **Discards 19 of 31 false cards (all 5 invented COLLISIONs; 11 of 20 waiting cars, the whole-frame
clips 11 of 13, the lens crops 8 of 18), confirms 15 of 18 incidents; as the gate before High alarms it stops 16 of
25 false Highs and holds 2 of 5 true ones, both person-on-the-tracks clips** (cell D had confirmed all three with a
generic alert; three clips cannot tell form from variation). Confidence 0.95 on all 49. Decision: not a hard gate on
High alarms; possible as a signal (a discard lowers the priority and says why, the card stays), not built. The
whole frame is the better second look for a stalled-vehicle crop (candidate fix 4), to be measured on footage
neither run used. The reasons it gives are not evidence (a right discard "a stationary train at a platform" in
Mumbai).

**The plain way measured for the video** (`run/vanilla-20261029T0714Z-compare/README.md`, `scripts/vanilla_poll.py`,
2026-10-29, 66 requests; today's count 169 after, with the live run's 15): the organizers' example question about
every camera once a minute for six minutes, read one by one. 60 requests per camera-hour, half the time looked at,
the day's 500 gone in 45 minutes for eleven cameras; the staged incident in 24 of 36 answers (the person on the
tracks 0 of 6, "sits on the edge of the platform, calm, orderly"; the scooter 1 of 6), each reported again every
minute; nothing invented on the four ordinary street cameras (24 of 24); the `vandalism` window smash reported 6 of
6, which Clearway never asks about (an event, not a change that stays). The video's scene 7b and
`docs/video/cards/compare.html` set it against the 10-27 run (14 requests, 7 incidents, none false) and the 10-26
shift (1 per camera-hour). **Lesson:** running Clearway beside the poller on this machine starved it
(`run/clearway-live-20261029T071314Z-compare`: CPU 100 %, the service 4-47 %, 0-2.5 fps per camera, three cameras
without frames, 5 of 20 questions over the 15 cap, 6 cards; the board recorder got 23 frames in ten minutes): never
run a second Hafnia-asking process beside a live run, and film the board in a run of its own.

**The calibrated floor tested** (`run/calib-20261029/README.md`, `scripts/scale_fit.py`, `calib_raise.py`,
`calib_compare.py`, 2026-10-29, 40 requests; today's count 209 after): the user's proposal that a scale from object
sizes (a person 1.7 m, a car 1.5 m high) should set the detector's floor in square metres instead of a share of the
frame, tested rather than argued. A scale per camera and row from YOLO boxes; every baseline blob in m². **In
square metres the true cards (the gate at night 0.03, the person on the tracks 0.31, the bin 0.7, the truck 1.4)
and the hold-out's false cards (0.38 to 119, median 3.9) overlap entirely**, so no floor separates them: raised
only, 0.5 m² drops 4 of 31 false cards and the graffiti, 2 m² drops 12 and the gate; pure, 0.25 m² at the blob's
row multiplies the junction's candidates 8 times at the service's setting (17 to 141 an hour) and 18 times at the
looped one, the staged loops' false reports 3 to 16 times, and Hafnia says NONE to 38 of 40 of the magnified
specks, so the false cards per hour stay where they were and the requests are 8 times more. The pane (0.04 m²) is
still not raised. Decision: the floor stays a share of the frame; the noise floor is per scene (the gate at night
1,200 false reports an hour and the vandalism camera 0 at the same share), not per pose; a scale per row could
serve the lens, the prompt or the priority, not the floor; the junction's false cards are car-sized and want the
queue-moves rule. `tier0/change.py` carries the optional per-row floor hook for the test, off in the service.

**Crash category (gate G3)** (`run/lens-test_11-20261024T110155Z`, 3 requests): with COLLISION in the JSON prompt the
cropped view of test_11's crash says COLLISION ("loses control … veers sharply"), the full frame STALLED_VEHICLE; the
same split as on 2026-10-21 with the one-word list (crop ACCIDENT, full frame NONE). On a small, distant event the crop
decides the answer; super-resolution adds nothing; the summary invents a second vehicle. Regression check
(`run/pilot-20261024T111134Z`, 6 requests): the six synthetic incidents keep their categories with COLLISION in the
list; summary details vary between loop occurrences (two wrong this time), categories do not.

**Lens camera, first test** (`run/lens-test_11-20261021T144445Z/README.md`, 6 requests): on `test_11`'s distant crash
(the SUV is about 30 px long), the plain 6 s window got NONE twice; the same window cropped and enlarged on `lens_1`
got ACCIDENT twice, in slow motion too. One event: an anecdote, not a measurement. Lens
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
- Each camera is one StableFPS hardware on its own port: organizer cameras use `http://127.0.0.1:100`–`110` (since
  their update of 2026-10-21, which put six new cameras on 105–110 and removed our `test_01`–`test_05` there); ours
  use `111` and up: pick the next free port, and expect organizer updates to claim ports. The record-on-motion rule
  covers All Cameras, so new cameras record automatically.
- **Recording Server restart** = stop and start the Windows service `Milestone XProtect Recording Server` only (not a
  reboot). For 2–3 minutes all cameras have no live video and no recording, and Hafnia exports fail (free). Stored
  recordings, the Management and Event Servers, the gateway, RDP and Tailscale are unaffected. Never stop it within
  90 s of its start. Push to GitHub before restarting, in case the machine needs a rebuild.

**Clip format pitfall (2026-10-18):** ffmpeg's Annex B output (SPS/PPS before every keyframe, an x264 SEI, some
3-byte start codes) makes the Recording Server log "Unable to add one or more frames to the frame collector. Error
code = 5" and the camera stays black. Always run `scripts/annexb_normalize.py` after ffmpeg: SPS/PPS once, no SEI,
4-byte start codes, like the organizer clips. Replacing a clip's content needs another Recording Server restart.

**Disk and memory (2026-10-24):** XProtect's recordings (`C:\MediaDatabase`, 24 h, size limit 1,000 GB: more than the
300 GB disk; house rules: do not change storage) held 198 GB and left 5 GB free on C:; our `test_06`–`test_10` (crime
clips, out of scope) were 75 GB of it and are now **disabled** (hardware disabled; re-enable with `Set-VmsHardware
-Enabled $true`). Long offline replays were stopped twice by Claude Code for low RAM while the session was idle (XProtect
about 4.9 GB, VS Code, Edge and Claude Code about 4 GB, plus YOLO, SigLIP and decoding): run long jobs detached
(`Start-Process`) and check free memory. During M3 (eleven cameras, 2026-10-26) the service held about 4.5 GB and
2.8 GB of 15.7 GB stayed free; Claude Code stopped its own background waiter for low memory, the detached run went on.

**Current state (2026-10-24):** our cameras: `test_06`–`test_10` (ports 111–115) disabled; `test_11` (port 116) plays AI City 2021 Track 4 training video 91 (15 min,
800×410; a crash at about 602 s; licence not cleared for the entry: internal tests only; source in `data/aicity21/`,
git-ignored). Camera `lens_1` (Universal driver, `rtsp://127.0.0.1:8554/lens1`) shows lens clips; it needs MediaMTX and
`lens.publisher` running (`scripts/start_lens.ps1`); both run detached and do not survive a reboot. MediaMTX v1.21.2
is in `C:\tools\mediamtx\v1.21.2`.

**Earlier state (2026-10-18):** cameras `test_01`–`test_10` (ports 106–115, device group Hackathon) played the
incident clips listed in `data/clips.json` (`test_01`–`test_05` removed by the organizers' update of 2026-10-21); the Recording Server was restarted twice today. The construction clip is
in the driver folder (normalized) but has no camera.

**Earlier state (2026-10-17):** `data/construction_aeria_footage.mp4` (27.8 s drone footage of a construction site;
**source and licence not yet recorded: TODO**) is converted to `data/clips/1920x1080_construction_aerial` and copied
into the driver folder; `StableFPS.xml` revision bumped 2.26 → 3.26. **The Recording Server restart is pending** (the
participant chose to wait), so the camera on port 105 does not exist yet. To do: give `add_test_camera.ps1` the
organizers' hung-service fallback (end the process, start the service) and batch support with a clip-swap command.
