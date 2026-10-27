# Lens self-check on a quiet machine: the frame code and wall-clock stamping (2026-10-27)

`scripts/check_lens.py --minutes 3 --clips 4 --export`, 09:47-09:50 UTC, no requests. The publisher had been
restarted at 09:46:19 with the new `lens/publisher.py`: every frame carries the frame code of `lens/code.py` (job
number, frame index, wall time) and ffmpeg stamps the raw frames with the wall clock instead of by count. Nothing
else was running but the board and the owner inbox. The check reads `lens_1`'s live frames through FrameBridge (the
Recording Server's frame times) with `lens/clock.py`, plays four synthetic 6 s clips, measures each clip's recorded
span from its own frames, and then reads the recording itself back (`scripts/export_window.ps1`, MilestonePSTools)
over each measured span.

## Result

| | |
|---|---|
| Recorded time minus the publisher's wall time | median +0.02 s over 3 min (single frames -0.07 to +0.12 s) |
| Readable frames in the live feed | 1767 of 1767, 0 dropped |
| Clips verified (first and last frames seen, no neighbour inside the span) | 4 of 4, 70 of 70 frames seen each, drift within a clip 0.00-0.01 s |
| Frames exported from the recording over each measured span (+1 s each side, 2 fps) | 18 per clip, all readable |
| Of the frames inside each measured span | 14 of 14 belong to that clip; 0 of another clip, 0 idle |
| Offset in the recording's own frames | +0.02 s, the same as the live feed's |

So the live feed's frame times are the recording's (the one assumption behind reading the span back live rather
than from the recording), and with wall-clock stamping an idle machine's recording sits 20 ms after the publisher's
clock. On 2026-10-26 the same recording ran 1.5-2.2 s behind when quiet and up to 9.5 s under load
(`run/lens-check-20261027`); the loaded case is `run/lens-check-20261027T095*-load-wallclock` beside a dry run of
the service on all eleven cameras.

Files: `offsets.jsonl` (the clock's stats every second), `clips.jsonl` (per clip: the publisher's span, the measured
span, the clock's info), `recorded.json` (the exported frames' codes), `summary.json`; `recorded/` holds the
exported frames (our own synthetic clips, git-ignored like other exported frames).
