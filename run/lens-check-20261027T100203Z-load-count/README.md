# Lens self-check under load, the count-stamped baseline (2026-10-27)

`scripts/check_lens.py --minutes 6 --clips 8`, 10:02-10:08 UTC, beside a dry run of the service on all eleven cameras
(`run/clearway-dry-20261027T100202Z-lensclock-count`), with the publisher started `--no-wallclock` (ffmpeg stamping
the raw frames by count, as during M3). The comparison with wall-clock stamping, and what it shows, is written up in
`run/lens-check-20261027T095146Z-load-wallclock/README.md`. In short: the recording fell from +0.02 s to -9.36 s
behind the publisher's clock within four minutes and recovered to -0.5 s two minutes after the load ended, without a
single frame discarded by MediaMTX; the clock measured and followed it (spans shifted by up to 8 s), and marked 6 of
the 8 clips unverified for their drift (up to 3.7 s within one clip).
