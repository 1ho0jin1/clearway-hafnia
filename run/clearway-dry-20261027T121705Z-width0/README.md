# FrameBridge width, full against 832 px: eleven cameras, 5 minutes each (2026-10-27)

Two dry runs of `scripts/run_clearway.py` on all eleven organizer cameras (the five street clips `--real`), the lens
on, no requests, one after the other: this folder with `--width 0` (each camera's own width, as every run until
today: 832x480 for the six incident cameras, 1280x720 and 1920x1080 for the street clips and `lens_1`), then
`run/clearway-dry-20261027T122305Z-width832` with `--width 832` (now the default, `clearway/service.py`
`BRIDGE_WIDTH`). The health record carries, every 15 s, the CPU shares of the machine, the Recording Server,
FrameBridge and the service (psutil, percent of all four cores; medians below leave out the first two records, the
model loading).

| | Width 0 | Width 832 |
|---|---|---|
| Frames received from FrameBridge, all cameras | 47.7 per s (4.3 per camera, of 10) | 51.4 per s (4.7 per camera) |
| CPU, whole machine | 100 % | 100 % |
| CPU, Recording Server (`VideoOS.Recorder.Service`) | 1.4 % (max 1.8) | 1.6 % (max 1.9) |
| CPU, FrameBridge | 28.4 % | 21.9 % |
| CPU, the service | 56.2 % | 61.8 % |
| Lens clock: readable frames, rate | 100 %, 3.3 per s | 100 %, 3.9 per s |
| Lens questions: coverage of the clip's frames in the feed (median) | 0.30 (1 question) | 0.33 (6 questions) |
| MediaMTX frames discarded | 0 | 0 |
| Questions (direct / lens) | 8 (7 / 1) | 15 (9 / 6) |

What it shows:

- **The Recording Server is not the bottleneck.** The investigation of 2026-10-27
  assumed it transcoded every camera to JPEG; it uses under 2 % of the machine. The MIP .NET library decodes the
  H.264 streams and makes the JPEGs inside FrameBridge, which takes about a core, and the service's own work
  (decoding, the detector at 320 or 640 px for eleven cameras, YOLO, SigLIP) takes more than two of the four. The
  machine is saturated, so FrameBridge delivers less than half the frames and `lens_1`'s feed with them.
- 832 px saves a quarter of FrameBridge's share and raises the delivered rate by a tenth, at no cost to the six
  incident cameras (their own width) and `test_11` (800 px). It stays the default.
- The next step was the service's own rate: the detector needs no more than every second frame (`DETECT_EVERY` 2,
  now the default). With it (`run/clearway-dry-20261027T123136Z-detect2`), FrameBridge delivered 7.5 frames per
  camera per second instead of 4.7, the lens feed carried 54 % of each clip's frames instead of 33 % with no
  replay, and its delivery latency fell from 0.79 to 0.23 s; the service's share fell to 52 %.
- M3's MediaMTX discards (XProtect's RTSP reader of the lens stream "too slow") were the same saturation: the
  Recording Server's threads were not scheduled in time, not short of work.
