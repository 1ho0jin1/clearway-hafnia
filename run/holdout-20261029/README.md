# Hold-out check: the detector and the prompt on real streets they were not written against (2026-10-29)

`scripts/holdout.py`, 03:43-04:30 UTC, 41 requests sent, 39 completed (today's count 0 before, 39 after; one clip
failed twice at Hafnia's end, "Transfer Assets: HTTP 403 Forbidden", and cost nothing). The question: the prompt
experiment (`run/prompt-20261028T1605Z`) and every live run so far measured Clearway on the eight looped scenes on
this machine, the same scenes the prompt's negatives and the detector's settings were tuned on. What does the
pipeline raise, and what does Hafnia answer with the service's prompt, on footage no part of Clearway has seen?
Three CC0 street clips from Wikimedia Commons (`data/footage/commons`, listed in `docs/PLAN-near-miss.md`): a Mumbai
junction from above by day (3:03), a Mumbai street at night (3:31), a tram junction in Düsseldorf by day (4:35).
Dense traffic, people crossing between moving cars and over tram rails, cars and taxis queued at lights, motorbikes
paused in the junction, stalls and parked vans on pavements: nothing blocks or endangers a way, so every candidate
is a hard negative, the kind a city deployment is full of and the looped scenes have none of.

## How

- **The detector, offline, no request** (`detect`): each clip once at 10 fps, 832 px wide (the frames the service
  gets from FrameBridge), through `tier0/change.py` with the setting the service gives real cameras
  (`ChangeParams.real`: a change must last 15 s) and, for more hard negatives, the looped-clip setting
  (`ChangeParams.loops`: 1.5 s), people found by YOLO11m holding changes back as in the service. Each report became
  the clip the service would send, by the service's own rules (`clearway/service.py`): the window from 2 s before
  the change to 3 s after the report (at most 30 s), cropped to the spot and enlarged on the lens when the lens
  would magnify it 2.5x or more, the whole frame otherwise (a direct ask on the camera's own recording in the
  service; here the frame was played on the lens too).
- **Labels by eye** (`labels.json`, from `sheets/`), written before any answer was read: all 40 NONE.
- **The lens** (`play`): the 40 candidates (all 3 real-setting reports and 37 of the 71 looped-setting ones,
  evenly sampled) played on `lens_1`, every recorded span measured from its own frames: 40 of 40 verified, offsets
  +0.01 to +0.03 s (`clips.jsonl`).
- **Hafnia** (`ask`): one request per clip with `clearway/prompt.py` as it is and the gateway's system prompt
  empty as it is (`prompt.json`); nothing was changed between or after. The answers are in `results.jsonl` and
  `answers.md`.
- **Not done:** the ledger's merging (recurrences, the verdict memory) was not replayed; with 3 real-setting
  reports in eleven minutes it would change nothing. No answer from this set was used to change the prompt or the
  detector: a fix would burn the set, and the next check would need new footage.

## Findings

1. **On real streets the service's prompt turns ordinary stopped traffic into incidents: 31 false cards in 39
   answers** (8 NONE). Of the real-camera-setting reports, the ones the service would have sent, 2 of 2 answered
   were false (the third failed twice at Hafnia's end). The same prompt was 28 of 28 on the looped scenes the day
   before: that figure was in-sample; this one is not.
2. **The failure is one habit: a vehicle waiting at a junction is "stopped in the middle of the lane, blocking
   traffic".** 20 of the 31 are STALLED_VEHICLE on taxis and cars waiting at a light or a crossing (the Düsseldorf
   estate car waiting 18 s while people cross in front of it; the queued Mumbai taxi), the lead vehicle of a queue
   as often as one behind others. The prompt's negatives ("not a vehicle parked at a kerb or queued behind
   others"; NONE for "ordinary traffic, parked vehicles") did not hold. The wording is the one the sectioned
   prompt produced on the looped scenes on 10-28 (finding 2 there): the baseline has the same habit; the loops
   contain no waiting car.
3. **Invented events and objects, as before:** 5 COLLISIONs on moving traffic in the crowded Mumbai junction
   ("collides with a black SUV, then stalls"; "a motorcycle collides with a parked vehicle, producing visible
   sparks and smoke, and the rider is thrown from the bike", on a motorbike standing at the frame's edge), and 6
   OBSTRUCTIONs, among them "a large fallen tree trunk lies across the roadway" three times (people standing at a
   pavement corner; pedestrians' legs crossing tram rails, twice): the model's standing answer for a crop it
   cannot read, seen on the organizers' dark fence on 10-26 and in the structured cells on 10-28. Two
   OBSTRUCTIONs describe real things that are not incidents (a blue cover on a cart by the railing, a car parked
   at the kerb). Every false card is a complete, fluent story; nothing in the answer tells it from a true one.
   Valid JSON 39 of 39.
4. **What the model got right, it got right from the scene, not the object:** 6 of the 8 NONE answers are
   Düsseldorf clips in which the crossing and the lights are visible ("pedestrians cross the zebra crossing while
   vehicles wait at the red light"); a crop of a single waiting car loses that context. The lens view (4 right of
   22) and the whole frame (4 of 17) did not differ beyond that.
5. **The detector at the real-camera setting raised 3 candidates in 10.7 minutes of three streets, about 17 per
   camera-hour** (the Mumbai junction from above 42, Düsseldorf 14, the Mumbai night street 0; the organizers'
   eleven looped cameras cost one request per camera-hour). The looped-clip setting raised 790 and 449 per hour:
   a real camera must have the real setting, which the service already gives it. Whether the night street's zero
   is right or a low-contrast blind spot was not tested. On the Mumbai junction each of those candidates would
   have become a false alarm, two of them High priority (stalled vehicles).

## What this means for Clearway

- **The 28 of 28, and the live runs' "none false", describe the eight looped scenes and nothing else.** The
  judge-facing text says so now and carries this run's number beside it.
- **The prompt is not where the fix is.** Its negatives already name queued and parked vehicles and ordinary
  traffic; the model overrides them on a clip of a stopped car, and 10-28 showed that adding rules adds invented
  objects. No answer from this set was used to change anything.
- **What a city deployment needs sits upstream of and beside the model:** (1) a far longer wait on a lane at a
  junction than 15 s (a light cycle, 60-120 s), or a scene's normal waiting places learnt from where things
  routinely stop; (2) the operator's rejections teaching the verdict memory (Reject on the board and the phone
  already does this), so the next taxi at the same stop line is not asked; (3) the second question with Hafnia's
  own AlertValidation shape before a High-priority alarm (strict on the looped scenes on 10-28: 0 false of 10, 10
  of 18 incidents discarded), untested on these clips; (4) showing the model the context the crop removes for a
  stopped vehicle: the whole frame with the spot marked, or crop and frame as one clip.
- **Any of these has to be checked on footage this run did not use:** this set is a tuning set from now on. The
  remaining held-out sources are the AI City crash clip (internal) and footage the user films.

## Reproduce it on another machine

The three clips are public (CC0) and `scripts/fetch_footage.py` fetches them from Wikimedia Commons with a SHA-256
check (about 500 MB; their Commons titles, authors and checksums are in the script). Everything else `setup.ps1`
installs: ffmpeg, YOLO11m, the lens camera, FrameBridge. The detector pass costs no request; `ask` costs one request
per clip, 40 with the cap as run here. Use a new run folder (the detector overwrites the candidate list of the folder
it is given) and copy this run's `labels.json` into it before `play`:

```powershell
py scripts\fetch_footage.py                                                      # the clips, verified
.venv\Scripts\python.exe scripts\holdout.py detect --out run\holdout-<date>      # candidates, clips, sheets; no request
Copy-Item run\holdout-20261029\labels.json run\holdout-<date>\
.venv\Scripts\python.exe scripts\holdout.py play run\holdout-<date> --max 40     # on lens_1, every span verified
.venv\Scripts\python.exe scripts\holdout.py ask run\holdout-<date> --dry-run     # prints the plan and today's count
.venv\Scripts\python.exe scripts\holdout.py ask run\holdout-<date>               # 40 requests
.venv\Scripts\python.exe scripts\holdout.py score run\holdout-<date>
```

What to expect: candidates are numbered in report order per clip and setting, so with the same clips and settings
the ids match this run's and the labels apply; a candidate the new pass numbers differently (YOLO's person boxes
can differ between GPUs) has no label and is listed, not scored. The spans are the new machine's own lens recording.
Hafnia's wording varies between repeats and its category rarely does (`run/prompt-20261028T1605Z`, finding 7), so
the counts should land near 31 false of 39, not on it.

Files: `detect.json` and `detect.log` (the detector pass), `candidates.jsonl` (every report with its window, box,
magnification and view), `labels.json`, `clips.jsonl` (the 40 played, with verified spans), `prompt.json`,
`results.jsonl` (every answer with timing), `answers.md`, `summary.json`, `play.log`, `ask.log`; `clips/` and
`sheets/` are git-ignored (footage; `detect` rebuilds them).

<!-- tables: written by holdout.py score; the text above is kept -->

74 candidates from the detector (0 looped-setting ones the same spot as a real-setting one), 40 played on `lens_1` (40 spans verified), 40 answered with the service's prompt. Labels by eye (`labels.json`); an ambiguous candidate (no label) is listed, not scored.

## The detector on the three streets

| Clip | Setting | Seconds scored | Reports | Per hour | Scene jumps |
|---|---|---|---|---|---|
| mumbai02 | real | 173.2 | 2 | 41.6 | 0 |
| mumbai02 | loops | 173.2 | 38 | 789.8 | 0 |
| mumbai03 | real | 201.2 | 0 | 0.0 | 2 |
| mumbai03 | loops | 201.2 | 0 | 0.0 | 2 |
| duesseldorf | real | 264.7 | 1 | 13.6 | 21 |
| duesseldorf | loops | 264.7 | 33 | 448.8 | 21 |

## Hafnia's answers

| Set | Asked | Answered | Failed | Scored | Of them NONE | Incidents | Right | False cards | Missed | Wrong category | Valid JSON |
|---|---|---|---|---|---|---|---|---|---|---|---|
| real-setting candidates (what the service would send from a real camera) | 3 | 2 | 1 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | 2 |
| looped-setting extras (things that paused 1.5 s; more hard negatives) | 37 | 37 | 0 | 37 | 37 | 0 | 8 | 29 | 0 | 0 | 37 |
| all | 40 | 39 | 1 | 39 | 39 | 0 | 8 | 31 | 0 | 0 | 39 |
| view: lens | 23 | 22 | 1 | 22 | 22 | 0 | 4 | 18 | 0 | 0 | 22 |
| view: direct | 17 | 17 | 0 | 17 | 17 | 0 | 4 | 13 | 0 | 0 | 17 |

## Every candidate asked

| # | Candidate | Setting | At (s) | View | Truth | Answer | Hafnia says |
|---|---|---|---|---|---|---|---|
| 1 | mumbai02-real-001 | real | 42.7 | lens x5.82 | NONE | failed | Transfer Assets: An error was returned from Hafnia VLM: HTTP 403 Forbidden |
| 2 | mumbai02-real-002 | real | 43.4 | lens x6.71 | NONE | OBSTRUCTION ✗ | A large tree trunk falls across the roadway, blocking the lane and forcing vehicles to stop or maneuver around it. |
| 3 | duesseldorf-real-001 | real | 29.9 | lens x4.73 | NONE | STALLED_VEHICLE ✗ | A dark station wagon is stopped in the lane with brake lights illuminated, blocking traffic; vehicles behind slow and stop, and pedestrians cross the road aroun |
| 4 | mumbai02-loops-001 | loops | 13.4 | lens x2.76 | NONE | COLLISION ✗ | A white sedan collides with a parked vehicle at the curb, then stalls in the lane and blocks traffic. |
| 5 | mumbai02-loops-002 | loops | 14.0 | lens x3.34 | NONE | STALLED_VEHICLE ✗ | A white sedan stalls in the middle of the lane, blocking traffic and forcing vehicles to merge around it. |
| 6 | mumbai02-loops-004 | loops | 16.3 | lens x2.91 | NONE | NONE ✓ | Motorcyclists and cars move through the intersection in an orderly flow, with no collisions, obstructions, or damage observed. |
| 7 | mumbai02-loops-006 | loops | 17.6 | lens x4.1 | NONE | STALLED_VEHICLE ✗ | A yellow taxi is stopped in the middle of the lane, blocking traffic, while motorcycles and other vehicles maneuver around it. |
| 8 | mumbai02-loops-008 | loops | 27.3 | lens x2.54 | NONE | STALLED_VEHICLE ✗ | A white sedan stalls in the middle of the lane, blocking traffic and forcing vehicles to maneuver around it. |
| 9 | mumbai02-loops-010 | loops | 27.8 | direct x1.0 | NONE | STALLED_VEHICLE ✗ | A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it. |
| 10 | mumbai02-loops-012 | loops | 28.2 | lens x2.82 | NONE | OBSTRUCTION ✗ | A white SUV is parked on the pavement, blocking the lane and forcing passing vehicles to slow and maneuver around it. |
| 11 | mumbai02-loops-014 | loops | 29.4 | direct x2.22 | NONE | STALLED_VEHICLE ✗ | A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it. |
| 12 | mumbai02-loops-016 | loops | 29.5 | direct x2.37 | NONE | NONE ✓ | A motorcyclist rides along the pavement at the intersection, weaving between parked cars and pedestrians while traffic moves through the junction. |
| 13 | mumbai02-loops-018 | loops | 30.1 | lens x3.34 | NONE | OBSTRUCTION ✗ | A blue tarpaulin lies across the pavement, partially blocking the pedestrian path and remaining in place throughout the video. |
| 14 | mumbai02-loops-020 | loops | 30.3 | direct x1.13 | NONE | STALLED_VEHICLE ✗ | A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it. |
| 15 | mumbai02-loops-022 | loops | 33.5 | lens x3.41 | NONE | OBSTRUCTION ✗ | A white sedan is stopped in the middle of the lane, blocking traffic and forcing vehicles and pedestrians to detour around it. |
| 16 | mumbai02-loops-024 | loops | 33.7 | direct x2.17 | NONE | COLLISION ✗ | A white sedan collides with a black SUV at the intersection, then stalls in the lane and remains there as traffic around it slows and stops. |
| 17 | mumbai02-loops-025 | loops | 33.7 | lens x2.65 | NONE | STALLED_VEHICLE ✗ | A yellow taxi is stopped in the middle of the lane, blocking traffic, while other vehicles and motorcycles maneuver around it. |
| 18 | mumbai02-loops-027 | loops | 38.1 | direct x1.26 | NONE | COLLISION ✗ | A white sedan collides with a black hatchback in the middle of the intersection, then stalls and blocks the lane. |
| 19 | mumbai02-loops-029 | loops | 46.5 | direct x2.1 | NONE | COLLISION ✗ | A white hatchback enters the intersection and collides with a black sedan, causing the hatchback to spin and stall in the lane. |
| 20 | mumbai02-loops-031 | loops | 47.3 | lens x4.87 | NONE | STALLED_VEHICLE ✗ | A white sedan is stopped in the middle of the lane, blocking traffic and causing vehicles behind to slow and stop. |
| 21 | mumbai02-loops-033 | loops | 50.9 | direct x2.29 | NONE | STALLED_VEHICLE ✗ | A white hatchback stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it. |
| 22 | mumbai02-loops-035 | loops | 134.7 | direct x1.0 | NONE | STALLED_VEHICLE ✗ | A white sedan is stopped in the middle of the intersection, blocking the lane and forcing surrounding vehicles and motorcycles to maneuver around it. |
| 23 | mumbai02-loops-037 | loops | 135.4 | lens x3.47 | NONE | COLLISION ✗ | A motorcycle collides with a parked vehicle in the lane, producing visible sparks and smoke, and the rider is thrown from the bike. |
| 24 | duesseldorf-loops-001 | loops | 12.0 | lens x3.73 | NONE | STALLED_VEHICLE ✗ | A dark blue station wagon is stopped in the lane with brake lights illuminated, blocking traffic; a blue sedan pulls up behind it and stops, while pedestrians w |
| 25 | duesseldorf-loops-003 | loops | 15.0 | direct x1.42 | NONE | STALLED_VEHICLE ✗ | A blue sedan is stopped in the middle of the intersection, blocking the lane and causing other vehicles to queue behind it. |
| 26 | duesseldorf-loops-005 | loops | 15.0 | lens x3.28 | NONE | STALLED_VEHICLE ✗ | A white sedan is stopped in the middle of the lane, blocking traffic, while other vehicles slow and maneuver around it. |
| 27 | duesseldorf-loops-007 | loops | 18.3 | direct x1.23 | NONE | STALLED_VEHICLE ✗ | A blue sedan stalls in the middle of the intersection, blocking the lane and forcing other vehicles to stop and wait. |
| 28 | duesseldorf-loops-009 | loops | 18.4 | lens x3.47 | NONE | NONE ✓ | Pedestrians cross the street while vehicles wait at a red light, with no collisions or obstructions visible. |
| 29 | duesseldorf-loops-010 | loops | 18.4 | lens x2.54 | NONE | STALLED_VEHICLE ✗ | A dark blue sedan is stopped in the lane with brake lights illuminated, blocking traffic; pedestrians wait on the pavement as the vehicle remains stationary. |
| 30 | duesseldorf-loops-012 | loops | 19.2 | direct x2.13 | NONE | STALLED_VEHICLE ✗ | A blue sedan stalls in the middle of the lane, blocking traffic and forcing other vehicles to stop and wait. |
| 31 | duesseldorf-loops-014 | loops | 20.3 | direct x2.29 | NONE | STALLED_VEHICLE ✗ | A blue sedan stalls in the middle of the lane, blocking traffic and forcing other vehicles to stop and wait. |
| 32 | duesseldorf-loops-016 | loops | 26.1 | lens x3.82 | NONE | STALLED_VEHICLE ✗ | A silver sedan is stopped in the middle of the lane, partially blocking traffic, while a red car and a pedestrian pass by. |
| 33 | duesseldorf-loops-018 | loops | 26.5 | lens x3.08 | NONE | NONE ✓ | Pedestrians cross the pavement while vehicles remain stopped or move slowly in the adjacent lane, with no collision or obstruction observed. |
| 34 | duesseldorf-loops-020 | loops | 26.6 | lens x2.67 | NONE | OBSTRUCTION ✗ | A large fallen tree trunk lies across the roadway, blocking the lane and forcing vehicles to stop and pedestrians to detour around it. |
| 35 | duesseldorf-loops-022 | loops | 26.7 | direct x1.14 | NONE | STALLED_VEHICLE ✗ | A black station wagon is stopped in the middle of the lane, blocking traffic and forcing vehicles to queue behind it. |
| 36 | duesseldorf-loops-024 | loops | 26.7 | lens x2.76 | NONE | NONE ✓ | Pedestrians cross the street at the marked crosswalk while vehicles remain stopped at the red light, maintaining orderly traffic flow. |
| 37 | duesseldorf-loops-026 | loops | 26.7 | direct x1.0 | NONE | NONE ✓ | Pedestrians cross the zebra crossing while vehicles wait at the red light, with no collisions or obstructions observed. |
| 38 | duesseldorf-loops-028 | loops | 27.3 | lens x3.14 | NONE | OBSTRUCTION ✗ | A large fallen tree trunk lies across the roadway, blocking the lane and forcing vehicles to slow and maneuver around it while pedestrians cross nearby. |
| 39 | duesseldorf-loops-030 | loops | 29.7 | direct x1.1 | NONE | NONE ✓ | Pedestrians cross the zebra crossing while vehicles wait at the red light, with no collisions or obstructions. |
| 40 | duesseldorf-loops-032 | loops | 29.7 | direct x2.11 | NONE | NONE ✓ | Pedestrians cross the zebra crossing while vehicles wait at the red light, maintaining orderly traffic flow. |
