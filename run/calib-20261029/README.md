# The calibrated floor: square metres instead of a share of the frame (2026-10-29)

**The question.** The change detector's size floor is a share of the frame, the same on every camera (0.5 % on
the looped scenes, 0.15 % on real cameras). Could a scale per camera, taken from the objects in view (a person is
about 1.7 m tall, a car's box about 1.5 m high), set the floor in square metres instead, so that a cracked pane on a
close camera and a waiting rickshaw on a far one are measured with one yardstick? And would it help on the Mumbai
junction, where the hold-out (`run/holdout-20261029`) turned 31 of 39 hard negatives into false cards? Tested
instead of argued, on the user's request. The service is unchanged; the detector got an optional per-row floor
(`ChangeParams.min_area_fn`, `None` in the service) for the test.

**What was done.**

1. **A scale per camera and row** (`scripts/scale_fit.py`, boxes from `collect_dets.py` in `dets.json`): YOLO11m
   boxes of people and cars on sampled frames of all fourteen clips, their pixels per metre fitted against the row
   the box stands on (one straight line per camera, the flat-ground assumption; robust; clamped to 0.3 to 3 times
   the camera's median so the floor cannot vanish at the horizon). `scales.json`; the table below.
2. **Every blob of the baseline runs in square metres**: the true cards of the clean live run of 10-27, the
   hold-out's 74 candidates with Hafnia's answers, the cracked pane.
3. **The floor in both directions.** *Raise only* (the frame-share floor stays, and a blob must also cover X m² at
   its row) is scored exactly from the baseline runs, no run needed (`scripts/calib_raise.py`, `raise.md`). *Pure*
   (X m² at the blob's row and nothing else) needs the detector run again: the three streets at both settings
   (`holdout.py detect --world-floor 0.25 --scales ... --baseline run/holdout-20261029`, `holdout-pure-0.25/`) and
   the staged loops (`eval_change.py --world-floor 0.25`, `eval-pure-0.25/`, against `eval-baseline/` made the same
   hour). The new street candidates were played on `lens_1` and asked with the service's prompt; a candidate at the
   same spot and time as a hold-out candidate inherits that answer instead of a second request.
   X = 0.25 m²: the smallest true card of the live run after the school gate at night (the person on the tracks,
   0.31 m²; the gate's own blobs are 0.03 to 0.04 m², as small as the pane).

**Findings.**

1. **In square metres the incidents and the false cards overlap over the whole range.** True cards: 0.03 m² (the
   gate at night) to 2.5 m² (the person on the tracks), the bin 0.7, the stalled truck 1.4, the scooter 1.6. The
   hold-out's false cards: 0.38 to 119 m², median 3.9. Its NONE answers: 1 to 139 m², median 31. Hafnia said NONE
   to the big blobs and made cards of the car-sized ones. No floor in square metres separates them: the first
   false card goes at 0.38 m², after the gate (0.03), the pane (0.04) and the person on the tracks (0.31) are gone.
2. **Raise only.** At 0.5 m², 4 of the 31 false cards are gone and the graffiti is lost (5 of 5 loops to 0 of 5).
   At 1 m², 10 of 31 and the graffiti. At 2 m², 12 of 31, the graffiti and the gate. The two real-setting false
   cards, the ones the service would have sent, are 1.3 and 3.9 m² and go only with the graffiti and the gate.
3. **Pure.** On the junction the service's own setting goes from 2 candidates in 173 s to 23 (42 to 478 per hour),
   the looped setting from 38 to 825 (790 to 17,148 per hour); Düsseldorf from 1 to 2 and from 33 to 429; the
   Mumbai night street stays at 0. The new candidates are specks in the far rows, 40 to 280 pixels, which the lens
   would magnify 11 to 46 times (`sheets/grid-mumbai02-real-*.jpg`). On the staged loops the same incidents are
   caught and the false reports rise everywhere: the stalled truck's camera 212 to 3,473 per hour, the open lanes
   0 to 2,700, the condensation 2,250 to 16,200, the highway 0 to 28. The pane is still not raised (0.04 to 0.10
   m² at its row).
4. **Hafnia on the new candidates: 38 of 40 said NONE.** 40 requests (today's count 169 to 209): the 22 new
   real-setting candidates (21 at the junction, 1 in Düsseldorf) and 18 of the 1,182 new looped-setting ones,
   evenly sampled, all played on `lens_1` with verified spans. The magnified specks come back as "a dark,
   out-of-focus view with no discernible vehicles" or as a pavement with people walking: 0 false cards of 22 at
   the service's setting, 2 of 18 at the looped one (an invented collision on a x5 crop of moving cars; a
   hatchback waiting at a light called stalled). So the floor does not add false cards at the junction; it adds
   requests. At the service's setting the three streets go from 17 candidates an hour to 141, eight times the
   requests, with the false cards per hour where they were (16.9 before and after, both resting on the same two
   baseline candidates). At the looped setting, 400 to 7,064 candidates an hour and false cards from 314 to about
   1,070. The tables below carry the estimate and every answer.

**Why.** The scale turns a few dozen far pixels into a quarter of a square metre, but a far row's noise does not
scale with the world: it is pixels, from compression, flicker and passers-by. The frame-share floor was never a
world measure; it is a noise floor, and the noise is per scene, not per pose (the gate at night 1,200 false
reports an hour and the vandalism camera 0 at the same share). Hafnia kept the test free of new false cards by
calling the unreadable crops NONE, which is a property of magnifying 40 pixels twenty times, not of the floor: a
sharper camera would hand the same specks over readable, and the hold-out shows what the model does with readable
waiting cars. Either way a floor can only trade the gate and the pane against the junction's standing people, and
Clearway's purpose is to spend few requests; this spends eight times more to learn nothing new.

**What it does not touch.** The junction's false cards are car-sized things that stopped for a while (median 3.9
m²). The scale confirms they are cars; it cannot say they block nothing. That is the queue-moves rule the hold-out
README names as the next fix, and it is upstream of the floor.

**Where the scale is still useful.** Perspective inside one camera is bigger than the difference between cameras
(a person is 65 % of the frame height near and 10 % far on the bin camera). A scale per row could decide when a spot
is small in the world rather than in the frame (the lens), tell the prompt how big the thing is, and feed priority.
None of that is a floor.

**Reproduce** (offline; the ask step spends one request per clip):

```powershell
.venv\Scripts\python.exe run\calib-20261029\collect_dets.py run\calib-20261029\dets.json
.venv\Scripts\python.exe scripts\scale_fit.py fit run\calib-20261029\dets.json run\calib-20261029\scales.json
.venv\Scripts\python.exe scripts\eval_change.py --loops 6 --only <the eleven loops> --out run\calib-20261029\eval-baseline
.venv\Scripts\python.exe scripts\eval_change.py --loops 6 --only <the eleven loops> --scales run\calib-20261029\scales.json --world-floor 0.25 --out run\calib-20261029\eval-pure-0.25
.venv\Scripts\python.exe scripts\calib_raise.py run\calib-20261029 --floors 0.05 0.1 0.25 0.5 1 2
.venv\Scripts\python.exe scripts\holdout.py detect --out run\calib-20261029\holdout-pure-0.25 --scales run\calib-20261029\scales.json --world-floor 0.25 --baseline run\holdout-20261029
.venv\Scripts\python.exe scripts\holdout.py play run\calib-20261029\holdout-pure-0.25 --max 40
.venv\Scripts\python.exe scripts\holdout.py ask run\calib-20261029\holdout-pure-0.25
.venv\Scripts\python.exe scripts\calib_compare.py run\calib-20261029
```

<!-- tables: written by calib_compare.py; the text above is kept -->

## The scale per camera

Pixels per metre in the 832-pixel frame, from the people (1.7 m) and cars (box 1.5 m high) YOLO11m found, fitted against the row the box stands on; clamped to 0.3 to 3 times the camera's median.

| Camera | Boxes used | At 1/4 height | At 1/2 | At 3/4 | At the bottom |
|---|---|---|---|---|---|
| vehicle_breakdown_traffic_queue | 294 of 326 | 20.3 | 37.3 | 54.3 | 66.0 |
| bin_pushed_over_onto_sidewalk | 287 of 343 | 5.4 | 34.0 | 54.0 | 54.0 |
| escooter_left_across_sidewalk | 265 of 323 | 4.8 | 33.7 | 48.0 | 48.0 |
| school_gate_break_in_night | 27 of 27 | 48.0 | 48.0 | 48.0 | 396.7 |
| person_on_railway_tracks | 108 of 109 | 11.1 | 51.4 | 111.2 | 111.2 |
| graffiti_on_standing_train | 34 of 54 | 18.7 | 51.9 | 82.9 | 82.9 |
| vandalism | 10 of 10 | 65.1 | 92.7 | 120.2 | 147.8 |
| traffic_flows_in_the_open_lanes | 103 of 118 | 16.8 | 32.6 | 47.0 | 47.0 |
| city_street_7_condensation_inside_housing | 88 of 88 | 6.0 | 36.8 | 60.0 | 60.0 |
| busy_street | 8 of 10 | 31.3 | 31.3 | 31.3 | 109.9 |
| highway_traffic_overcast_weather | 71 of 74 | 10.5 | 34.3 | 58.2 | 80.0 |
| mumbai02 | 1928 of 2060 | 19.1 | 35.1 | 51.1 | 67.1 |
| mumbai03 | 1466 of 1485 | 18.2 | 24.0 | 83.3 | 142.5 |
| duesseldorf | 906 of 920 | 8.5 | 8.5 | 68.4 | 84.7 |

## What the detector's blobs measure in square metres

A blob is the pixels that stayed changed, usually a part of the object, so these are smaller than the objects. The true cards of the clean live run of 10-27 (the change asked about, at its row):

| Camera | Card | State | m² |
|---|---|---|---|
| school_gate_break_in_night | TAMPERING | open | 0.03 |
| school_gate_break_in_night | TAMPERING | merged | 0.04 |
| person_on_railway_tracks | PERSON_ON_TRACKS | merged | 0.31 |
| bin_pushed_over_onto_sidewalk | OBSTRUCTION | open | 0.71 |
| school_gate_break_in_night | TAMPERING | merged | 0.97 |
| bin_pushed_over_onto_sidewalk | OBSTRUCTION | merged | 1.21 |
| vehicle_breakdown_traffic_queue | STALLED_VEHICLE | open | 1.43 |
| graffiti_on_standing_train | OBSTRUCTION | open | 1.5 |
| escooter_left_across_sidewalk | OBSTRUCTION | merged | 1.54 |
| escooter_left_across_sidewalk | OBSTRUCTION | open | 1.59 |
| person_on_railway_tracks | PERSON_ON_TRACKS | open | 2.5 |
| person_on_railway_tracks | PERSON_ON_TRACKS | cleared | 4.98 |
| bin_pushed_over_onto_sidewalk | OBSTRUCTION | merged | 18.84 |

The hold-out's false cards (hard negatives Hafnia confirmed): 31: 0.38 to 118.85, median 3.91 m². Its NONE answers: 8: 1.01 to 138.93, median 31.2 m². The cracked pane on the vandalism camera: 0.04 m² at the man's scale beside it (0.10 m² by the row fit, which assumes the ground plane).

## The three streets with the calibrated floor: pure-0.25

Floor 0.25 m² at the blob's row, never below 0.0 of the frame. A candidate at the same spot and time as a baseline candidate inherits that answer; the new ones were played on `lens_1` and asked with the service's prompt.

| Clip | Setting | Baseline per hour | Calibrated per hour | Same as baseline | New | New asked | New answered | New false cards | Inherited false cards | Inherited NONE |
|---|---|---|---|---|---|---|---|---|---|---|
| mumbai02 | real | 41.6 (2) | 478.1 (23) | 2 | 21 | 21 | 21 | 0 | 1 | 0 |
| mumbai02 | loops | 789.8 (38) | 17147.8 (825) | 38 | 787 | 12 | 12 | 1 | 19 | 4 |
| mumbai03 | real | 0.0 (0) | 0.0 (0) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| mumbai03 | loops | 0.0 (0) | 0.0 (0) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| duesseldorf | real | 13.6 (1) | 27.2 (2) | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| duesseldorf | loops | 448.8 (33) | 5834.5 (429) | 34 | 395 | 6 | 6 | 1 | 14 | 4 |

False cards per hour, estimated: the new candidates' rate times the share of false cards among the new ones answered, plus the rate of those at a baseline spot times the share among their inherited answers (the baseline: its rate times its own share).

| Setting | Baseline candidates per hour | Baseline false cards per hour | Calibrated candidates per hour | Calibrated false cards per hour | Behind it |
|---|---|---|---|---|---|
| real | 16.9 | 16.9 (2 of 2 answered) | 140.8 | 16.9 | new 124/h at 0% (0 of 22), same spot 17/h at 100% (2 of 2) |
| loops | 399.9 | 313.5 (29 of 37 answered) | 7063.7 | 1066.2 | new 6658/h at 11% (2 of 18), same spot 406/h at 80% (33 of 41) |

New candidates: 1204, sizes 1204: 0.0 to 18.45, median 0.54 m²; asked 40, answered 40, false cards 2.

| Candidate | Setting | View | m² | Answer | Hafnia says |
|---|---|---|---|---|---|
| mumbai02-real-001 | real | lens x18.09 | 0.28 | NONE | The scene shows a dark, blurry view with no clear vehicles, pedestrians, or obstructions visible; the footage appears to be of a non-eventua |
| mumbai02-real-002 | real | lens x20.29 | 0.57 | NONE | A stationary train remains on the platform throughout the clip with no movement or incident. |
| mumbai02-real-003 | real | lens x26.0 | 0.29 | NONE | The scene shows a dark, out-of-focus view with no discernible vehicles, pedestrians, or obstructions, indicating no incident or anomaly. |
| mumbai02-real-004 | real | lens x16.64 | 0.57 | NONE | The scene shows a blurred view of a pavement with no visible people, vehicles, obstructions, or damage. |
| mumbai02-real-005 | real | lens x20.29 | 0.44 | NONE | The scene shows a dark, out-of-focus view with no discernible vehicles, people, or obstructions, indicating no incident or anomaly. |
| mumbai02-real-006 | real | lens x12.06 | 1.88 | NONE | Pedestrians walk along the pavement while vehicles pass on the adjacent road, with no collisions, obstructions, or damage observed. |
| mumbai02-real-007 | real | lens x18.09 | 0.44 | NONE | A stationary train remains at the platform throughout the clip with no movement or incident. |
| mumbai02-real-008 | real | lens x21.33 | 0.29 | NONE | The scene shows a blurred pavement with no visible people, vehicles, obstructions, or damage; the camera remains steady and no events occur. |
| mumbai02-real-009 | real | lens x12.06 | 0.44 | NONE | A train remains stationary at the platform throughout the clip with no visible movement or incident. |
| mumbai02-real-010 | real | lens x11.4 | 0.67 | NONE | Pedestrians walk along the pavement at night, with no collisions, obstructions, or damage visible. |
| mumbai02-real-011 | real | lens x30.81 | 0.22 | NONE | The scene shows a dark, out-of-focus view with no discernible vehicles, pedestrians, or obstructions, indicating no incident or anomaly. |
| mumbai02-real-014 | real | lens x23.11 | 0.22 | NONE | Pedestrians walk along the pavement in daylight, with no collisions, obstructions, or vehicle incidents visible. |
| mumbai02-real-015 | real | lens x41.6 | 0.36 | NONE | The scene shows a dark, indistinct view with no visible vehicles, pedestrians, or obstructions, and no discernible movement or incident. |
| mumbai02-real-016 | real | lens x15.41 | 0.26 | NONE | The scene shows a dark, blurry view with no discernible vehicles, pedestrians, or clear road markings, indicating no active traffic or incid |
| mumbai02-real-017 | real | lens x46.22 | 0.44 | NONE | The scene shows a blurred, indistinct view with no clear vehicles, people, or obstructions visible; the footage appears to be out of focus o |
| mumbai02-real-018 | real | lens x11.4 | 1.1 | NONE | Pedestrians walk along the pavement in the dimly lit scene, with no collisions, obstructions, or damage visible. |
| mumbai02-real-019 | real | lens x16.64 | 0.24 | NONE | The scene shows a dark, blurry view with no clear vehicles, pedestrians, or obstructions visible; the footage appears to be of a non-traffic |
| mumbai02-real-020 | real | lens x36.17 | 0.44 | NONE | A person walks along the pavement, passing parked vehicles and a bus stop, with no collisions or obstructions visible. |
| mumbai02-real-021 | real | lens x23.11 | 1.07 | NONE | A stationary train remains on the platform throughout the clip with no movement or incident. |
| mumbai02-real-022 | real | lens x14.6 | 0.72 | NONE | A motorcycle is stopped in the lane, with a rider standing beside it and another person nearby. |
| mumbai02-real-023 | real | lens x30.81 | 0.27 | NONE | The scene shows a dark, indistinct view with no visible vehicles, pedestrians, or obstructions, indicating no incident or anomaly. |
| mumbai02-loops-001 | loops | lens x41.6 | 0.35 | NONE | The scene shows a dark, out-of-focus view with no discernible objects, people, or vehicles, and no observable events or incidents. |
| mumbai02-loops-069 | loops | lens x18.09 | 0.44 | NONE | A motorcycle is stopped in the lane, remaining stationary throughout the clip with no movement or interaction visible. |
| mumbai02-loops-137 | loops | lens x46.22 | 0.44 | NONE | The scene shows a dark, out-of-focus view with no discernible objects, people, or vehicles, and no observable events or incidents. |
| mumbai02-loops-206 | loops | lens x30.81 | 0.32 | NONE | The scene shows a dark, out-of-focus view with no discernible vehicles, pedestrians, or obstructions, indicating no incident or anomaly. |
| mumbai02-loops-272 | loops | lens x16.0 | 0.88 | NONE | The scene shows a dark, out-of-focus view of a train passing by, with no visible people, vehicles, obstructions, or damage. |
| mumbai02-loops-341 | loops | lens x13.0 | 2.64 | NONE | The camera pans across a quiet station platform with no visible people, vehicles, obstructions, or damage. |
| mumbai02-loops-413 | loops | lens x16.0 | 0.48 | NONE | Two pedestrians walk along the pavement, one in dark clothing and one in lighter clothing, moving steadily without incident. |
| mumbai02-loops-486 | loops | lens x5.01 | 0.71 | COLLISION | The silver hatchback is struck by a black SUV and a red hatchback, causing it to spin and slide across the lane before exiting the frame. |
| mumbai02-loops-554 | loops | lens x41.6 | 0.3 | NONE | The scene shows a dark, out-of-focus view with no discernible vehicles, pedestrians, or obstructions, indicating no active incident or anoma |
| mumbai02-loops-624 | loops | lens x30.81 | 0.43 | NONE | The scene shows a dark, out-of-focus view with no discernible vehicles, people, or obstructions, indicating no incident occurs. |
| mumbai02-loops-689 | loops | lens x26.84 | 0.43 | NONE | A stationary train remains on the platform throughout the clip with no movement or incident. |
| mumbai02-loops-757 | loops | lens x20.29 | 0.29 | NONE | A white car enters the frame from the right, moves forward along the lane, and exits the frame to the left. |
| duesseldorf-real-001 | real | lens x46.22 | 0.0 | NONE | The scene shows a blurred, dark view with no discernible objects, people, or clear activity; no events or incidents are visible. |
| duesseldorf-loops-004 | loops | lens x11.4 | 0.46 | STALLED_VEHICLE | A dark blue hatchback is stopped in the lane with its brake lights illuminated, remaining stationary as a blue car passes on the right. |
| duesseldorf-loops-070 | loops | lens x55.47 | 0.54 | NONE | The scene shows a blurred, indistinct view with no discernible vehicles, people, or objects, indicating no specific event or anomaly. |
| duesseldorf-loops-138 | loops | lens x15.13 | 1.63 | NONE | No incident occurs; the scene shows a quiet street with parked cars and a pedestrian on the pavement, no collisions or obstructions visible. |
| duesseldorf-loops-210 | loops | lens x46.22 | 0.54 | NONE | The scene shows a blurred, indistinct view with no discernible vehicles, pedestrians, or specific objects, indicating no notable event or an |
| duesseldorf-loops-283 | loops | lens x46.22 | 0.54 | NONE | The scene shows a blurred view of a train station platform with no visible people, vehicles, obstructions, or damage; the camera remains sta |
| duesseldorf-loops-351 | loops | lens x13.0 | 1.63 | NONE | The scene shows a blurred urban view with no visible person on tracks, collision, stalled vehicle, obstruction, damage, or tampering; the pa |

## The staged loops: incidents caught and false reports

| Camera | baseline: caught, delay s, false/h | pure-0.25: caught, delay s, false/h |
|---|---|---|
| vehicle_breakdown_traffic_queue | 5/5, 3.9,3.9,3.9, 211.8 | 5/5, 0.3,0.3,0.3, 3472.9 |
| bin_pushed_over_onto_sidewalk | 5/5, 0.2,0.2,0.2, 336.0 | 5/5, 0.2,0.2,0.2, 672.0 |
| escooter_left_across_sidewalk | 5/5, 0.6,0.6,0.6, 48.0 | 5/5, 0.6,0.6,0.6, 624.0 |
| school_gate_break_in_night | 5/5, 4.2,4.2,4.2, 1200.0 | 5/5, 6.0,6.0,6.0, 1536.0 |
| person_on_railway_tracks | 0/5, -, 0.0 | 0/5, -, 0.0 |
| graffiti_on_standing_train | 5/5, 1.7,1.7,1.7, 0.0 | 5/5, 1.7,1.7,1.7, 0.0 |
| vandalism | 0/4, -, 0.0 | 0/4, -, 0.0 |
| traffic_flows_in_the_open_lanes | -, -, 0.0 | -, -, 2700.0 |
| city_street_7_condensation_inside_housing | -, -, 2250.0 | -, -, 16200.0 |
| busy_street | -, -, 418.1 | -, -, 1765.2 |
| highway_traffic_overcast_weather | -, -, 0.0 | -, -, 28.1 |
