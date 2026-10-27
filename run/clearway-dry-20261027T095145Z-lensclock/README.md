# Dry run, eleven cameras, 6 minutes: the lens's spans read back from its own frames (2026-10-27)

`scripts/run_clearway.py` on all eleven organizer cameras (the five street clips `--real`), 09:51-09:58 UTC, no
requests: the load for the lens self-check's wall-clock pair (`run/lens-check-20261027T095146Z-load-wallclock`,
which has the comparison). The first run of `clearway/service.py` with `lens/clock.py`: `lens_1` is in the service's
FrameBridge, every lens question's span comes from the clip's own recorded frames. 28 questions (13 direct, 15 on
the lens), 8 cards; the 15 lens spans had offsets of +0.39 to +1.43 s against the publisher's clock, drift within a
clip up to 0.58 s, 12-42 % of each clip's frames in the starved live feed; `summary.json` (`scripts/report_clearway.py`)
has the `lens` block. Verification ran with the first, stricter rule (8 of 15 unverified); by the final rule 10 of 15
are verified and the 5 others had their frames seen in one part of the clip only.
