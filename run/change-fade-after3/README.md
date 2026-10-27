# The fade, fixed: the final detector, 30 minutes per looped camera (2026-10-27)

`scripts/eval_change.py --loops 120 --only bin_pushed_over_onto_sidewalk escooter_left_across_sidewalk`, the person
hold-back on, no requests. The final `tier0/change.py`: an open change's spot is left out of the slow background
(`freeze_open`); static-changed pixels not yet reported are not learnt until they have persisted
`learn_static_after_s` (60 s); "restored" is judged within `restored_diff` or within `restored_ratio` (0.25) of the
change's own contrast to its before; motion is judged frame to frame; the "changed" closing of the second attempt
is off (`changed_s` 0). Earlier states: `run/change-fade-before` (the detector before the fix), `-after` (freeze
only), `-after2` (with the "changed" closing).

| Camera | Loops caught | Reports | Per loop | Closed | Reports per 5 min |
|---|---|---|---|---|---|
| bin | 119 of 119 | 362 | 3: the tipped bin, the bin with the person, the bin's base (the pieces the ledger merges into one incident) | 357 restored, 5 open at the end | 62, 60, 60, 60, 60, 60 |
| e-scooter | 119 of 119 | 241 | 2: the rider and scooter standing (phase 7 s), the scooter lying (phase 9 s) | 237 restored, 4 open | 41, 40, 40, 40, 40, 40 |

Against the detector before the fix (16 of 119 loops on both cameras, silent after seven minutes) and the freeze
alone (the bin cured, the e-scooter stuck after 48 loops by the ghost its precursor left in the before snapshot).
The eval's "false" count (reports outside the annotated incident seconds: 121 for the bin) is the piece reported
when the person is still pushing the bin, two seconds before the annotation's start; it was the same in the first
attempt and is merged by the ledger live. The four and five changes open at the end are spots whose state at report
time recurs for most of each loop (the rider's standing place), which is what an open change should be.
