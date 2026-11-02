# Clearway

Clearway keeps public ways clear. It watches XProtect cameras for things that block or endanger a way (a stalled
vehicle, a person on the tracks, an e-scooter dropped across a pavement, damage to transit), asks the Hafnia VLM
about each one once, and turns the answer into one XProtect alarm, one card on an owner board and one phone push
with Confirm / Reject.

Solo entry for the Hafnia Hackathon 2026 (Milestone XProtect 2026 R1, the Hafnia VLM gateway).

## Demo video (2:57)

https://github.com/user-attachments/assets/7d4c948f-0b6c-458a-b310-14fda63504db

The storyboard and how it is built are in `docs/VIDEO.md`.

## How it works

![Clearway pipeline](docs/clearway_pipeline.svg)

- **Change detector** (`tier0/change.py`): a dual-rate background finds what changed and stayed changed. No object
  classes, no per-camera rules. YOLO11m adds one trigger: a person inside a danger zone (`config/zones.json`).
- **Incident memory** (`clearway/ledger.py`): a SigLIP 2 fingerprint of the spot decides whether to ask. A known
  look joins its incident; a rejected one is held. Only something new costs a request.
- **Lens camera** (`lens/`): Hafnia only reads XProtect recordings, so a small spot is cropped, enlarged and played
  on a camera of our own, `lens_1`. A code in every frame proves which seconds the recording holds.
- **Prompt** (`clearway/prompt.py`): one paragraph, JSON out: category, summary, evidence. The category picks the
  owner and the priority.

Step by step, with a figure and the numbers for each step: `docs/walkthrough/index.html`.

## Results

| Run | Result |
|---|---|
| Three-hour live shift, 11 cameras | 33 requests, about 1 per camera-hour (`run/clearway-live-20261026T141534Z-m3`) |
| Asking every camera once a minute instead | 60 requests per camera-hour; the person on the tracks found 0 of 6 times (`run/vanilla-20261029T0714Z-compare`) |
| 20-minute run after the fixes, 11 cameras | 14 requests, 7 incidents, none false (`run/clearway-live-20261027T124112Z-clean`) |
| **Known limit:** three real streets it had never seen | 31 of 39 ordinary scenes became false cards, mostly cars waiting at a light called stalled; not fixed (`run/holdout-20261029`) |

Every run folder under `run/` has a README with its numbers.

## Run it

On a hackathon machine (XProtect 2026 R1, the Hafnia gateway, the organizers' cameras), from a fresh clone, in an
elevated PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1      # idempotent; asks for the gateway password once
```

Then, in a new PowerShell (so it has the user-scope variables):

```powershell
# Dry run on the six incident cameras: no request, a stand-in answers
.venv\Scripts\python.exe scripts\run_clearway.py --minutes 5 --alarms --close-alarms-at-end

# Live: at most 12 requests, alarms and phone pushes
.venv\Scripts\python.exe scripts\run_clearway.py --minutes 10 --answers hafnia --max-requests 12 --alarms --notify

# The owner board, beside Smart Client
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\open_board.ps1
```

Hafnia allows 500 requests a day; the run script stops at 450.

## Reproduce the measurements

No requests, one at a time (each loads a model):

```powershell
.venv\Scripts\python.exe scripts\eval_change.py --loops 120 --only bin_pushed_over_onto_sidewalk escooter_left_across_sidewalk
.venv\Scripts\python.exe scripts\eval_ledger.py
.venv\Scripts\python.exe scripts\check_lens.py --minutes 3 --clips 4 --export
```

The real-street check (40 requests; CC0 clips from Wikimedia Commons, about 500 MB):

```powershell
py scripts\fetch_footage.py
.venv\Scripts\python.exe scripts\holdout.py detect --out run\holdout-<date>
Copy-Item run\holdout-20261029\labels.json run\holdout-<date>\
.venv\Scripts\python.exe scripts\holdout.py play run\holdout-<date>
.venv\Scripts\python.exe scripts\holdout.py ask run\holdout-<date>      # --dry-run prints the plan
.venv\Scripts\python.exe scripts\holdout.py score run\holdout-<date>
```

## Repository

| Path | What |
|---|---|
| `clearway/` | the service, incident memory, prompt, alarms, board, notifications, shift summary |
| `tier0/` | change detector, SigLIP memory, danger zones |
| `lens/` | the lens camera: publisher, frame code, clock |
| `bridge/FrameBridge/` | C# live-frame reader on the MIP SDK |
| `hafnia/`, `incident/` | gateway and XProtect REST clients |
| `scripts/` | setup, runs, evaluations, reports |
| `run/` | every measured run, with its README |

A line per file: `CLAUDE.md`, "Repository layout".

## Licences and footage

Ultralytics YOLO11 (AGPL-3.0), SigLIP 2 (Apache-2.0), MediaMTX (MIT), ffmpeg (GPL), Real-ESRGAN weights
(BSD-3-Clause, optional), spandrel (MIT), psutil (BSD), MilestonePSTools and the MIP SDK (Milestone's terms). The
organizers' camera clips stay on the hackathon machine. The street clips are CC0 on Wikimedia Commons ("Street in
Mumbai (video) 02" and "03" by Nicolas Vigier, 2016; "Straßenverkehr in Düsseldorf" by Slick, 2014). The AI City
Challenge clip used for internal tests may not be redistributed and is not in the repository.
