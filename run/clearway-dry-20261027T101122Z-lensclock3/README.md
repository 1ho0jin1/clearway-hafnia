# Dry run, three cameras, 3 minutes: the final lens clock (2026-10-27)

`scripts/run_clearway.py --cameras vehicle_breakdown_traffic_queue bin_pushed_over_onto_sidewalk
escooter_left_across_sidewalk --minutes 3 --direct-below 0`, 10:11-10:15 UTC, no requests: every spot on the lens,
with the final `lens/clock.py` (the verification rule, the 0.3 s margin, holes) and the service's replay rule
(`clearway/service.py` `REPLAY_HOLE_S`), after the loaded pairs (`run/lens-check-20261027T095146Z-load-wallclock`).
The publisher stamps with the wall clock. 8 questions, 8 lens clips, 3 cards; all 8 spans verified, every frame of
every clip seen in the live feed (coverage 1.0), recorded time 0.01-0.03 s after the publisher's clock, drift within
a clip at most 0.03 s, no hole, no replay, no error; the lens queue made the wait 9-62 s. `summary.json`
(`scripts/report_clearway.py`) has the `lens` block.
