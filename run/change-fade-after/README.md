# The fade, first fix only: open changes' spots left out of the slow background (2026-10-27)

`scripts/eval_change.py --loops 120 --only bin_pushed_over_onto_sidewalk escooter_left_across_sidewalk` with the
first version of the fix in `tier0/change.py` (`freeze_open`: an open change's spot is not learnt by the slow
background; nothing else changed yet). 30 minutes per clip, no requests. Baseline: `run/change-fade-before`.

| Camera | Loops caught | Reports per 5 min | Open at the end |
|---|---|---|---|
| bin | 119 of 119 | steady (the log of this run capped reports at 200, so its later bins read 0) | 4 of 200 logged |
| e-scooter | 50 of 119 | 24, 20, 10, 0, 0, 1 | 5 of 55 |

The bin is cured. The e-scooter is caught 48 loops in a row, then a change reported at loop 49 never "restores" (its
spot never again looks like its before snapshot) and every later scooter blob overlapping it is merged into it. A
debug replay showed why: the before snapshot is the slow background at report time, and that background had been
learning the rider and scooter standing still during the seconds of each loop before the hold-back let the report
through (static-changed pixels not yet reported were still learnt), so each loop's before carried a stronger ghost
of the change's own precursor until the empty pavement no longer matched it within the restore threshold. The
general fix (no learning of static-changed pixels until they persist; a change whose spot looks like neither its
before nor itself closes as "changed" and re-baselines the spot; motion judged frame to frame): `run/change-fade-after2`.
