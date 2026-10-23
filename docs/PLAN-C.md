# Plan C: right-of-way incidents (decided 2026-10-22)

Status: **current plan.** Supersedes `docs/PLAN.md` (verified accident alarms) and `docs/PLAN-near-miss.md` (near-miss
observatory); both stay as reference, and their parts are reused below. Submission about 2026-10-30. Judging weighs
creativity and validity most; reproducibility counts.

**In one paragraph.** City and transit operators need to know when something blocks or endangers a public way: a
vehicle broken down in a lane, an e-scooter or a bin lying across a pavement, a person on the tracks, damage to a train.
Tier 0 watches every camera for free and notices that *something changed and stayed changed*, without knowing what it
is (no per-scenario rules, no object classes). The lens shows Hafnia that change the way a VLM can read it: centred on
the moment, cropped to the spot, with the scene before and after. Hafnia names what changed and whose job it is. Each
confirmed change becomes an item in a ledger and an XProtect alarm for the owner; tier 0 closes the item, without
another request, when the spot looks as it did before.

## Why this direction (evidence, 2026-10-19 to 10-22)

- **The organizers' six new cameras** (2026-10-21; synthetic, 15–17 s loops, on every machine) are incidents in public
  ways: a breakdown with a queue, a bin tipped over and an e-scooter left across a pavement, a person on railway tracks,
  graffiti on a train, a school-gate break-in. They were added because participants asked for them, so many entries
  will demo "detect this scenario" on the same clips. Named-scenario detection on these loops will be crowded.
- **Hafnia can read these scenes** (`run/probe-20261022T054342Z`, 18 requests): one-word class 7 of 9 right,
  descriptions 51 of 64 claims right. **Its errors are structural** (`audit.md`): stories told in the order of a loop
  cut (time reversed: the e-scooter "mounted and ridden away"), traffic and weather priors ("wet pavement" on dry
  ground, vehicles in a pedestrian crowd), an invented outcome ("successfully cut the lock"). Most come from a window
  that is not centred on the event; that is what the lens fixes.
- **The lens works** (`run/lens-test_11-20261021T144445Z`): on a distant crash the plain window got NONE twice; the
  same window cropped and enlarged got ACCIDENT twice.
- **Real footage keeps us honest:** on real crime CCTV Hafnia scored 0 of 8 (`run/bench-20261018`); synthetic clips are
  easier. We report on both, and stay in the road-and-public-space domain where Hafnia is competent; security
  (break-in) is a footnote, not the product.
- **Prior and competing entries** are application work (`docs/PLAN-near-miss.md`, "What earlier and current entries
  did"); the 2026 "Scene Contracts" entry uses fixed per-camera templates (property damage, roadway visibility). Ours
  needs no per-camera rules and measures what it claims.

## Who it is for

| What changed | Where | Owner | Alarm priority |
|---|---|---|---|
| Person on the tracks | rail track, platform edge | rail control (stop trains) | High, urgent |
| Vehicle stopped in a traffic lane (breakdown, crash aftermath) | road lane | traffic operations, towing | High |
| Object lying across a pavement or path (e-scooter, bin, debris) | pavement, cycle path | micromobility operator, sanitation, street maintenance; an accessibility hazard for wheelchair users and blind people | Medium |
| Damage to transit or street assets (graffiti, broken window) | train, building, street furniture | asset owner | Low |
| Lock or gate tampered with | gate | security (footnote: outside Hafnia's strength) | Low |

## Pipeline

```
FrameBridge (live, 10 fps)
  └► tier 0: "changed and stayed changed" (dual background) + stopped vehicle in a lane + person in a danger zone
       └► candidate: camera, region, time of change, kind of trigger
            └► router: one candidate per region and change, daily budget, priority by trigger
                 └► lens: clip centred on the change, cropped to the region, with BEFORE and AFTER views
                      └► Hafnia: structured answer (category, object, where, still present?)
                           └► ledger item opened → XProtect alarm (owner, priority) + bookmark
                                └► tier 0 watches the region → restored → item closed, alarm closed (no request)
```

## Components

| # | Component | Reuse | New work |
|---|---|---|---|
| 1 | Change detector (`tier0/change.py`) | FrameBridge frames | Dual-rate background (after Porikli et al., "Robust abandoned object detection using dual foregrounds", 2008): a slow and a fast background model; pixels foreground to the slow model but not to the fast one are a *static* change (something arrived and stopped, or left). Blob size and persistence thresholds; ignore changes covering most of the frame (light); detect loop cuts and scene jumps (global frame difference spike) and reset. Records when the region first changed (the window centre) and a frame from before it (the BEFORE view). No object classes, no per-camera rules. |
| 2 | Stopped vehicle in a lane | `tier0/rules.py` tracks and `sharp_decel` | A vehicle track with near-zero speed for ≥ N s that had been moving (excludes parked cars). Covers the breakdown clip and crash aftermaths. |
| 3 | Person in a danger zone | YOLO person tracks | One polygon per camera that has a danger zone (tracks), in a small JSON by camera name; a person's feet inside it for ≥ 1 s. The only per-camera setting, and optional. |
| 4 | Router | `incident/router.py` | Keyed by camera and region (not camera alone: the `test_03` lesson); one request per change; daily cap from `DailySummaryCount`; urgent triggers first. |
| 5 | Lens: centred, cropped, before/after | `lens/` (publisher, client, `lens_1`) | A renderer that composes the clip from the frame buffer: BEFORE still, the change in real time (or slow motion), AFTER still, each captioned; layout chosen by the pilot (M1). |
| 6 | Prompt and parser | `incident/verify.py`, gateway client | Structured answer in JSON (Hafnia was trained on JSON answers): `category` (`PERSON_ON_TRACKS`, `STALLED_VEHICLE`, `OBSTRUCTION`, `DAMAGE`, `TAMPERING`, `NONE`), `object`, `where` (`track`, `lane`, `pavement`, `platform`, `other`), `still_present`. Questions about observable states only (audit point 3). Parsed and checked in code. |
| 7 | Ledger and XProtect | `hafnia/xprotect_rest.py` (alarms, bookmarks) | One JSONL item per change: open/closed times, category, owner, answer, alarm id, bookmark. Alarm priority by category, owner in the alarm text, the lens clip's span bookmarked; closed when tier 0 sees the region restored. |
| 8 | Ledger page (served from the machine) | the pipeline page in `scripts/viz_pipeline.py` | Open and closed items with BEFORE/AFTER thumbnails, time to open and to close, owner, requests used today. |
| 9 | Setup | `scripts/setup_lens.ps1`, `scripts/add_test_camera.ps1` | `setup.ps1` for a fresh machine; real CC0 footage fetched by script from Wikimedia Commons. |

## Cameras and footage

All on every machine unless noted, so judges can reproduce the main results without our data.

| Camera | Role |
|---|---|
| `vehicle_breakdown_traffic_queue` | Stalled vehicle in a lane (High) |
| `bin_pushed_over_onto_sidewalk`, `escooter_left_across_sidewalk` | Obstruction on a pavement (Medium); the same street and bin: one view, two incidents |
| `person_on_railway_tracks` | Person in a danger zone (urgent) |
| `graffiti_on_standing_train`, `vandalism` | Damage (Low) |
| `school_gate_break_in_night` | Tampering (footnote) |
| `traffic_flows_in_the_open_lanes` | Roadworks present all the time: must *not* open an item (nothing changes) |
| `busy_street`, `highway_traffic_overcast_weather`, `city_street_7_condensation_inside_housing` | Negatives: crowds, fog, a camera fogging up (the detector must not call a whole-frame change an incident) |
| `test_11` (ours, AI City video 91; internal only, licence not cleared) | Real crash aftermath: an SUV stopped against the median wall |
| Mumbai 02 and 03, Düsseldorf (ours, Wikimedia Commons, CC0; to inject) | Real busy streets: false items per hour |

Loops: an incident's lasting state ends when its clip restarts (after about 3–8 s). The detector treats the restart
as a scene reset; each loop is one more trial of the same incident, and the ledger counts it once per loop.

## Measurements (validity)

- **M1 Lens.** On the six new cameras: full-loop window (the probe's baseline) vs centred vs centred and cropped vs
  before/after. 3 repeats each. Category accuracy and key-fact recall with 95% intervals, plus a claim-level audit
  like `audit.md` for one repeat. About 6 × 4 × 3 = 72 requests.
- **M2 Detector, offline.** Every camera's clip (and the CC0 clips): incidents caught per loop, time from the change to
  the candidate, false candidates per hour on the negatives. No requests.
- **M3 End to end, live.** All incident cameras for an hour or more: items opened and closed per loop, precision and
  recall, time from change to alarm, time to close, requests per hour and cameras one 500-a-day allowance covers.
- **M4 Real footage.** `test_11` and the earlier real accident cameras (aftermaths), the CC0 streets: does the same
  pipeline hold outside synthetic loops? False items per hour, misses, audited answers.

## Gates

| Gate | Test | Requests | Pass | If it fails |
|---|---|---|---|---|
| G1 Detector | M2 on all clips | 0 | the incident caught on ≥ 5 of 6 incident cameras in every loop; nothing on `traffic_flows`, `highway`, `busy_street` | **Passed for the object incidents 2026-10-23** (`run/change-G1-loops`): breakdown, bin, e-scooter, graffiti in every loop; the two person incidents (tracks, gate) need person triggers (the gate's apparent catches were lit pavement and shadow beside the person); nothing on roadworks or highway; `busy_street` 10 false reports in 93 s at the loops setting, 0 at the real-camera setting. The verdict memory then cuts requests by 45% with no incident skipped (`run/memory-compare`) |
| G2 Lens | M1 pilot (1 repeat first, about 24 requests) | 24 | centred or before/after beats the full-loop baseline on category accuracy | **Not decidable 2026-10-23** (`run/pilot-20261023T162040Z`, 29 requests): with the JSON prompt every category was right in every view (29/29). Summaries: the full loop again reverses the gate across the loop cut; super-resolution no different from bicubic on these large synthetic objects; BEFORE/AFTER stills one regression. Default: event window + JSON prompt; SR to be tested on small, distant objects |

## Schedule

The allowance resets at 00:00 UTC (the machine's clock); stay under `--stop-at` each day.

| Day | Date | Work | Requests |
|---|---|---|---|
| 1 | Oct 22 | This plan. Machine restart (the organizers ask for one; participant). Change detector offline on all clips (G1). BEFORE/AFTER renderer. | 0 |
| 2 | Oct 23 | Lens pilot and M1; choose the layout and the JSON prompt (G2). | 75 |
| 3 | Oct 24 | Live pipeline: FrameBridge → triggers → router → lens → Hafnia → ledger, alarm, bookmark; auto-close. | 30 |
| 4 | Oct 25 | M3 live runs on all cameras; fixes. | 150 |
| 5 | Oct 26 | M4: inject the CC0 clips (Recording Server restart: ask first); real-footage runs. | 100 |
| 6 | Oct 27 | Ledger page; alarm definitions and priorities in XProtect. | 20 |
| 7 | Oct 28 | Final measurements, report with charts and audits. | 150 |
| 8 | Oct 29 | `setup.ps1`, README, demo video. | 30 |
| 9 | Oct 30 | Spare; submission. | |

## Risks

| Risk | Fallback |
|---|---|
| The before/after layout confuses Hafnia (unusual for a model trained on CCTV clips) | Centred and cropped clip without composition; M1 reports which works |
| The change detector fires on light changes, shadows, parked cars | Persistence and size thresholds, whole-frame changes ignored, YOLO tracks to explain moving things; Hafnia's NONE closes the rest (that is its job) |
| States last only 3–8 s in the loops | Short persistence threshold for the demo; state it plainly; real footage (M4) shows longer states |
| Synthetic clips flatter the results | Report synthetic and real separately; audit claims, not only labels |
| Hafnia misses tampering (as with real crime) | Footnote it; the product is right-of-way, not security |
| The lens stream drops | Keep the publisher running; plain centred windows still work |

## What carries over

From plan A: FrameBridge, tier 0 tracking and rules, the router, the gateway and XProtect clients (alarms, bookmarks),
the measured findings in `CLAUDE.md` (event-centred windows, latency, describe vs classify). From the lens work:
`lens/`, `lens_1`, the setup and start scripts. From plan B: the footage survey and the CC0 clips. Dropped: near-miss
counting and its statistics (no near misses in the shared footage, too little real footage, 8 days left).

## Sources

- Organizer note and kit (2026-10-21): `C:\HackathonKit\xprotect-hackathon\SKILL.md`, "Your cameras"
- Probe and audit: `run/probe-20261022T054342Z/README.md`, `audit.md`
- Lens test: `run/lens-test_11-20261021T144445Z/README.md`
- Dual-foreground abandoned-object detection: F. Porikli, Y. Ivanov, T. Haga, "Robust abandoned object detection using
  dual foregrounds", EURASIP Journal on Advances in Signal Processing, 2008
- Hafnia's trained formats and earlier research: `docs/PLAN-near-miss.md`, "Why consider a change"
