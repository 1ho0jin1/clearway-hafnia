# Why does Hafnia miss accidents? Window and model experiments (2026-10-18)

Follow-up to `run/bench-20261018`, where Hafnia answered NONE for `test_04` and its free descriptions missed 3 of 5
accidents with full-loop windows (12–18 s). 34 requests, all rows in `results.jsonl`; windows in `windows.json`.

## A. Event-centred 6 s windows (default model `traffic-general`)

`scripts/event_windows.ps1` located each impact in the recordings by matching recorded frames to the source frame at
the impact (`scripts/locate_event.py`; best-to-median ratios 0.08–0.22) and centred a 6 s window on it. The `test_04`
window was checked by eye: the collision is inside.

| | Full loop (bench-20261018) | Event-centred 6 s |
|---|---|---|
| One-word question, accidents | 8 of 9 answers (`test_04` NONE) | **10 of 10** |
| Description caught the accident | 2 of 5 | **4 of 5** |
| Median time to answer (descriptions) | 9.4 s | 5.2 s |

Descriptions with the 6 s window:
- `test_01` caught: "the driver ... swerves sharply to the right, striking the motorcyclist ... thrown off the bike".
- `test_02` caught: the bike "tips over, and both riders fall onto the tracks ... A train then approaches".
- `test_03` missed (hard clip, light contact): describes stopping and braking only.
- `test_04` caught (missed before): "fails to yield and collides with the cyclist ... the cyclist remains on the ground".
- `test_05` caught, cause wrong: "the scooter tips over and falls"; the collision with the parked truck is not named.

## D. Other models (full-loop windows, one answer each)

| Model | Accidents (of 5) | Normal traffic |
|---|---|---|
| `traffic-general` (default, from bench-20261018) | 4 (missed `test_04`) | 2 / 2 |
| `hafnia-traffic-eu-cr1-7b-v1` | 4 (missed `test_03`) | 2 / 2 |
| `hafnia-traffic-us-cr1-7b-v1` | 4 (missed `test_04`) | 1 / 1 (highway: recording gap, free) |
| `hafnia-traffic-us-cr3-8b-v1` | 3 (missed `test_03`, `test_04`) | 1 / 1 (highway: recording gap, free) |

## Reading

- The window matters far more than the model. Shorter, event-centred clips fixed `test_04` and turned the free
  descriptions from 2 of 5 to 4 of 5. Model differences are one clip at most: within noise for one answer per clip.
- A shorter clip both raises the sampled frame density during the impact (if the model caps frames) and the
  resolution per frame (if it caps total pixels). This experiment does not separate the two; slow-motion and crop
  variants (experiments B and C) would.
- Design consequence: tier 0 must send Hafnia a short window centred on the moment it detected, not "the last N
  seconds". That is the event-centred window hook, now measured.
