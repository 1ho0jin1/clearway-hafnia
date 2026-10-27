# The detector on every second frame: eleven cameras, 5 minutes (2026-10-27)

The third run of the width comparison (`run/clearway-dry-20261027T121705Z-width0/README.md` has the first two and
the finding behind this one: the machine's four cores, not the Recording Server, are the bottleneck, with the
service taking 56-62 % and FrameBridge 22-28 %). Same eleven cameras, `--width 832`, and the new default
`DETECT_EVERY` 2 (`clearway/service.py`): each camera's thread runs the change detector on every second frame it
receives and keeps the others for clips and snapshots. The detector waits persist_s (1.5 s on the loops, 15 s on
real cameras) before reporting, so 5 fps loses it nothing.

| | Width 832, every frame | Width 832, every 2nd frame |
|---|---|---|
| Frames received from FrameBridge, all cameras | 51.4 per s (4.7 per camera) | 82.1 per s (7.5 per camera) |
| Frames the detector processed per camera | 4.7 per s | 3.8 per s |
| CPU: machine / Recording Server / FrameBridge / the service | 100 / 1.6 / 21.9 / 61.8 % | 100 / 1.6 / 27.3 / 51.9 % |
| Lens clock: frames per second from `lens_1`'s feed | 3.9 | 6.2 |
| Lens questions: coverage of the clip's frames (median) | 0.33, 4 of 6 replayed for holes | 0.54, 0 of 3 replayed |
| Recorded time minus the publisher's clock (lens, median) | +0.79 s | +0.23 s |
| Questions (direct / lens), cards | 15 (9 / 6), 8 | 11 (8 / 3), 7 |

The cores freed by the detector went to FrameBridge, which now delivers three quarters of every camera's frames,
and to the lens feed, whose latency fell with it. The machine is still full; the next savings would be FrameBridge
forwarding every second frame itself (the MIP library has to decode every H.264 frame, but the JPEG encoding and
the pipe halve) and the real-camera profile's 640-px working width.
