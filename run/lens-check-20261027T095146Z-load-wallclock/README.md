# Lens self-check under load, wall-clock against count stamping (2026-10-27)

Two 6-minute pairs, no requests. In each, `scripts/run_clearway.py` ran a dry run on all eleven organizer cameras
(the M3 load: full-resolution JPEG for every camera, the detectors, the stand-in) with the lens on, so its own clock
(`lens/clock.py`, fed from the service's FrameBridge) measured every lens question's span; beside it
`scripts/check_lens.py --minutes 6 --clips 8` read `lens_1` through a FrameBridge of its own and played eight
synthetic clips. The publisher (`lens/publisher.py`, frame code in every frame) stamped ffmpeg's raw frames with the
**wall clock** in the first pair (the new default) and **by count** in the second (`--no-wallclock`, the way M3 ran).
The quiet baseline is `run/lens-check-20261027T094716Z` (offset +0.02 s, recording read back).

| | Wall clock (this folder, service `run/clearway-dry-20261027T095145Z-lensclock`) | Count (`run/lens-check-20261027T100203Z-load-count`, service `run/clearway-dry-20261027T100202Z-lensclock-count`) |
|---|---|---|
| Recorded time minus the publisher's clock, 10 s medians over the 6 min | +0.02 to +1.1 s (median +0.59) | +0.03 down to -5.75 s (median -2.4); single frames to -9.36 s |
| The same at the service's 15 / 10 lens questions | +0.39 to +1.43 s (median +0.7) | -4.0 to -8.16 s (median -5.6), 2 clips with no frame seen (assumed from the publisher's clock shifted by -5.5 s) |
| Change of the offset within one clip (drift) | at most 0.19 s (check), 0.58 s (service) | up to 3.73 s (check), 5.9 s (service): a 10.7 s clip occupied 18 s of the recording |
| Frames of each check clip seen in its live feed | 70, 67, 70, 45, 63, 30, 53, 54 of 70 | 70, 70, 56, 56, 50, 41, 50, 49 of 70 |
| Check clips verified | 7 of 8 by the rule of that hour, 8 of 8 by the final rule (frames seen from the first and last quarters, drift under 1 s, no neighbour, no hole) | 2 of 8 (the drift) |
| Service clips verified (final rule, from the logged fields) | 10 of 15; the 5 others had their frames seen in part of the clip only (one, cw-0008, inside MediaMTX's discard of 71 frames at 09:53:25) | 1 of 10 |
| MediaMTX "reader is too slow, discarding N frames" | 71 (09:53:25) and 197 (09:54:37) | none |
| Lens queue: the service's wait per lens question | median 40 s, max 68 s | median 58 s, max 84 s |

What the pair shows:

- **The count-stamped stream reproduces M3's defect without any help from MediaMTX.** No frame was discarded in the
  second pair, yet the recording fell 9.4 s behind. The publisher drops frames when the busy machine holds its loop
  more than 1 s (it resynchronises instead of bursting), ffmpeg stamps by count, so every dropped frame pulls the
  stream's time 0.1 s behind the wall clock, and XProtect's Universal driver records by the stream's time. It also
  explains M3's unexplained recovery (-9 s at 14:18 to -1.5 s at 14:41): when the publisher is less than 1 s behind
  it writes without sleeping, and each of those frames advances the count-stamped stream 0.1 s while the wall clock
  advances less, so the stream catches up once the machine quietens (here from -9.4 s at 10:05:48 to -0.5 s at
  10:07:46).
- **Wall-clock stamping keeps the stream on the wall clock**: a dropped frame leaves a gap that ffmpeg fills with a
  duplicate (`-fps_mode cfr`), so the offset under the same load is the delivery latency, +0.4 to +1.4 s, and a clip
  drifts less than 0.6 s. The spans the clock measured held the clips either way; with count stamping they were
  shifted by up to 8 s and widened by the drift, and marked unverified.
- **The service's live JPEG feed of `lens_1` starves under eleven cameras**: it carried 12-42 % of the frames (mean
  26 %), the standalone check's feed 43-100 %. The recording takes the H.264 stream whole, so a thin feed still pins
  the clip (a line through the frames seen places its first and last frame); only a hole (readable frames whose send
  times are more than 2 s apart, as MediaMTX's discards leave) marks footage missing from the recording as well.
  The final clock tracks holes; this pair ran before that and before the final verification rule.
- The offsets of the service's clock and the check's agree within 0.2 s at the same minutes: one feed is enough.

Files in each check folder: `offsets.jsonl` (the clock's stats every second), `clips.jsonl` (per clip: the
publisher's span, the measured span, the clock's info), `summary.json`. The service folders hold the usual run files
(`service.jsonl` with the `lens` events' `offset_s`, `seen`, `sent`, `first_idx`, `last_idx`, `drift_s`, `verified`;
`summary.json` from `scripts/report_clearway.py` with its `lens` block).
