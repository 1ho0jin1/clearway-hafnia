# The fade, reproduced offline: the detector before 2026-10-27 (freeze off)

`scripts/eval_change.py --loops 120 --only bin_pushed_over_onto_sidewalk escooter_left_across_sidewalk --no-freeze`,
2026-10-27: each clip looped 120 times (30 minutes at 10 fps), the person hold-back on, `ChangeParams.loops()` with
`freeze_open` off, which is the detector as it ran during M3 (the slow background learning everywhere the fast
foreground did not move, open changes included). No requests.

| Camera | Loops caught | Reports per 5 min | Open at the end |
|---|---|---|---|
| bin | 16 of 119 | 54, 14, 0, 1, 0, 0 | 15 of 69 reports |
| e-scooter | 16 of 119 | 19, 1, 0, 0, 0, 1 | 6 of 21 reports |

Both cameras fall silent after about seven minutes, as in M3 (`run/clearway-live-20261026T141534Z-m3`: 27-37 reports
per object incident in the first half hour, 0-6 per half hour after). The slow background (time constant 600 s)
took the lasting state of each loop in, so it stopped differing from the background. With the open changes' spots
left out of the learning (`freeze_open`): `run/change-fade-after` (the bin cured, the e-scooter still stuck by a
second mechanism); with the general fix: `run/change-fade-after2`.
