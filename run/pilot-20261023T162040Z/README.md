# Lens pilot, plan C M1 / gate G2 (2026-10-23)

`scripts/lens_pilot.py --repeat 1`: the six synthetic incident cameras, five views of the same moment each, one JSON
prompt (in `results.json`) asking for `category`, `object`, `where`, `still_present` and a one-sentence `summary`.
30 requests sent, 29 completed and counted (one failed while uploading to Hafnia, "HTTP 403 Forbidden", not counted).
Frames sent: `frames/` (git-ignored). One answer per cell: differences of one answer are anecdotes.

Event windows: from 2 s before the change started to 3 s after it was reported (5.0–8.1 s; `events` in
`results.json`). Spots from the change detector; for the tracks and the gate, YOLO's person box at a fixed moment.

| View | What Hafnia got |
|---|---|
| `full_loop` | the camera's recording, one loop long, centred on the event window (contains the loop cut) |
| `centred` | the camera's recording, the event window |
| `crop` | the event window cropped to the spot, enlarged bicubically, on `lens_1` |
| `crop_sr` | the same, enlarged with Real-ESRGAN (`lens/enhance.py`) |
| `before_after` | `crop` with the spot's first and last frames held 2 s each, captioned BEFORE / AFTER |

## Category: at the ceiling

All 29 completed answers name the right category (breakdown STALLED_VEHICLE, bin and e-scooter OBSTRUCTION, gate
TAMPERING, tracks PERSON_ON_TRACKS, graffiti DAMAGE), in valid JSON. The views cannot be told apart on category.
For comparison, the probe's one-word list (no definitions, unaligned windows) got 7 of 9 (`run/probe-20261022T054342Z`).

## Summaries: claim check against the frames

Judged by Claude (Opus) from the frames of each window (`frames/*-centred.jpg`) and the clips' contact sheets.

| View | Wrong claims | Key facts missed |
|---|---|---|
| `full_loop` | gate: "person with chainsaw", "walks away without cutting the gate", `still_present` false (he walks *in* after the loop cut: time order again); tracks: `still_present` false (he is still on the tracks) | – |
| `centred` (5 answers) | breakdown: "traffic ahead … slows and stops" (minor) | breakdown: the smoke |
| `crop` | tracks: "crawls along … remaining on the tracks" (he sits on the platform edge, legs on the track); e-scooter: "tips over" (he lays it down; minor) | breakdown: the driver |
| `crop_sr` | gate: "lock-picking tools" (bolt cutters) | – |
| `before_after` | e-scooter: "parked on the pavement" (it lies across it); gate: "lockpicks"; tracks: "sits on the railway tracks" (on the edge) | e-scooter: lying |

Other observations: tool types are invented (chainsaw, lockpicks; the bolt cutters are never named) in 3 views;
`where` for the graffiti is `track` on the full frame and `pavement` on the crops (the person stands on a platform).

## Reading

1. **The structured prompt with definitions is today's largest effect:** every category right in every view, even
   the full loop. (Not a controlled comparison with the probe: windows and prompt both changed.)
2. **Event windows still matter for the narrative:** the full loop again tells the gate backwards across the loop cut
   (as in the probe audit); the event-window views do not.
3. **Super-resolution vs bicubic: no measurable difference here.** These synthetic objects are large and clean; the
   one SR error (tool type) also appears in the bicubic `before_after`. SR has to be tested where it should matter:
   small, distant objects (`test_11`, real streets).
4. **BEFORE/AFTER stills: no gain, one regression** (the lying e-scooter read as "parked"). Held still frames may read
   as a stationary scene. Not the default.

**Gate G2 as written** ("centred or before/after beats full_loop on category accuracy"): **not decidable**, the
category is at the ceiling. On the summaries the event-window views beat the full loop (no loop-cut reversal).
Decisions: event window + JSON prompt as the default; crop where the spot is small; SR pending a small-object test;
before/after dropped from the default.
