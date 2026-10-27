# Dry run, eleven cameras, 6 minutes: the count-stamped baseline (2026-10-27)

The same dry run as `run/clearway-dry-20261027T095145Z-lensclock`, 10:02-10:08 UTC, with the publisher started
`--no-wallclock` (ffmpeg stamping by count, as during M3): the load for the baseline pair
(`run/lens-check-20261027T100203Z-load-count`; the comparison is in
`run/lens-check-20261027T095146Z-load-wallclock/README.md`). 21 questions (11 direct, 10 on the lens), 8 cards. The
10 lens spans had offsets of -4.0 to -8.16 s (median -5.6 s) against the publisher's clock and drifts up to 5.9 s
within a clip; two clips had no frame seen in the feed and were assumed from the publisher's clock shifted by the
offset (-5.5 s); 9 of 10 unverified. The clock measured the defect that M3 suffered, live, and shifted the spans by
it; the wall-clock pair keeps it from arising.
