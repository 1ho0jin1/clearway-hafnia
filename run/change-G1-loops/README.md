# Gate G1 of plan C: the change detector, offline (2026-10-23)

`scripts/eval_change.py` with `tier0/change.py`'s two settings. No Hafnia requests. Each clip is played the way its
camera plays it (loops, 10 fps); the first 10 s warm the backgrounds up and are not scored. An incident loop is caught
if a change is reported while the incident's lasting state is on screen (from when its object first comes to rest at
the incident spot until the loop restarts; spans approximate, from contact sheets). Every other report is false.
People standing in a change are held back (YOLO11m person boxes). Boxes drawn on the reporting frames: `frames/`
(git-ignored).

## Loops setting (`ChangeParams.loops()`: 320 px, blobs ≥ 0.5%, 1.5 s): this folder

| Clip | Loops caught | Report after the object comes to rest (s) | False reports (per hour) |
|---|---|---|---|
| `vehicle_breakdown_traffic_queue` | **6/6** | 1.9–3.9 | 1 (35) |
| `bin_pushed_over_onto_sidewalk` | **6/6** | 0.1–0.6 | 12 (480): at 8.8–9.7 s of the loop, while the man grips and tips the bin, just before the span starts |
| `escooter_left_across_sidewalk` | **6/6** | 1.5 | 1 (40) |
| `school_gate_break_in_night` | **6/6** | 4.2 | 26 (1040): the lit pavement as the person walks in |
| `graffiti_on_standing_train` | **6/6** | 1.7 | 0 |
| `person_on_railway_tracks` | 0/6 | – | 0: by design (a person is held back); needs the danger-zone trigger |
| `vandalism` (organizers' original) | 0/5 | – | 0: the cracked window changes too few pixels (caught only at difference 12 and 0.2%, which floods every other camera) |
| `traffic_flows_in_the_open_lanes` (roadworks all the time) | – | – | **0** |
| `highway_traffic_overcast_weather` (13 min) | – | – | **0** |
| `busy_street` (crowd) | – | – | 10 (387) |
| `city_street_7_condensation_inside_housing` (camera fogs up) | – | – | 25 (2250): camera status, out of scope |

## Real-camera setting (`ChangeParams.real()`: 640 px, blobs ≥ 0.15%, 15 s): `run/change-G1-real`

| Clip | Result | False reports (per hour) |
|---|---|---|
| `test_11` (AI City video 91, real highway, 15 min; internal only) | the crashed SUV against the median wall reported **43 s** after it came to rest | 16 (65) |
| Mumbai 02 (CC0, busy junction, daylight, 3 min) | – | 6 (125): vehicles stopping |
| Mumbai 03 (CC0, night, 3.5 min) | – | **0** |
| Düsseldorf (CC0, tram junction, 4.6 min) | – | 1 (14) |
| `busy_street` | – | **0** |

How the real setting was chosen (all at 15 s, the same detector): 320 px and 0.5% found the SUV after 101 s
(`run/change-size-320-0.005`), 320 px and 0.15% after 48 s with 312 false/h on Mumbai (`run/change-size-320-0.0015`),
640 px and 0.15% after 43 s with 125/h (`run/change-size-640-0.0015`). At 1.5 s on real footage the false rates were
48–852/h (Mumbai): real obstructions last minutes, so the real setting waits 15 s.

## Verdict

**Passed for the incidents:** 5 of 6 new incident cameras caught in every loop (the sixth, the tracks, is a person and
goes to the danger-zone trigger). Roadworks and highway: nothing. Not passed: `busy_street` at the loops setting (10 in
93 s; 0 at the real setting) and the fogging camera (out of scope). Known misses: thin damage like a cracked window.

What changed on the way (development runs not kept): a median warm-up removed ghosts (a car's starting place reported
once it drove off); holding back people removed most false reports on the synthetic clips; a 10-min slow background
stopped the looped incidents from being learnt; a per-pixel static time that pauses while something moves across a
spot fixed both occlusion (a stalled car behind passing traffic) and walking people being credited as static; the
larger working image found the small crashed SUV.

Before the live pipeline the false reports are filtered by the verdict memory (`run/memory-compare`: 45% fewer
requests, no incident skipped, against a stand-in for Hafnia).
