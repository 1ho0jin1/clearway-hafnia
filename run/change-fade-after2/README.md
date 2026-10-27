# The fade, second attempt: the "changed" closing overshoots (2026-10-27)

`scripts/eval_change.py --loops 120 --only bin_pushed_over_onto_sidewalk escooter_left_across_sidewalk` with the
second version of the fix in `tier0/change.py`: open changes' spots left out of the slow background, static-changed
pixels not learnt until they persist 60 s (no ghost of a change's precursor in its before), motion judged frame to
frame, and a change whose spot looked like neither its before nor the change itself for 3 s closed as "changed"
with the spot re-baselined to its current look. 30 minutes per clip, no requests. Baseline `run/change-fade-before`,
first attempt `run/change-fade-after`.

| Camera | Loops caught | Reports | Closed as restored / changed / open | Reports per 5 min |
|---|---|---|---|---|
| bin | 119 of 119 | 743 (6.2 per loop) | 349 / 387 / 7 | 123, 147, 142, 131, 100, 100 |
| e-scooter | 119 of 119 | 363 (3 per loop) | 58 / 302 / 3 | 63, 60, 60, 60, 60, 60 |

No fade and no stuck change, but three to six reports per loop where one is right. The e-scooter's reports come at
fixed loop phases (0, 1, 4, 8, 10, 12 s): the incident evolves within a loop (the rider stands, lays the scooter
down, the scooter lies), each state is a "third look" to the change reported before it, so the change is closed as
"changed", the spot re-baselined to that transient state, and the next state reported as a change of its own. A
real incident that evolves (a person who collapses after standing) would be closed the same way. The "changed"
closing is therefore off by default in the final version, whose net under a contaminated or drifted before is a
restore test relative to the change's own contrast: `run/change-fade-after3`.
