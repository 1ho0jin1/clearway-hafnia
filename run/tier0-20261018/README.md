# Tier 0, first offline evaluation (2026-10-18)

`scripts/eval_tier0.py` with the defaults in `tier0/rules.py` (YOLO11m at 640 px, confidence 0.25, ByteTrack).
Full results with every candidate: `tier0_results.json`. Costs no Hafnia requests.

**Setup.** Positives: the 5 accident clips, each played twice back to back like a looped camera; only the second pass
is scored, so the tracker has history before every impact. A hit is a candidate within ±2.5 s of the impact time in
`data/clips.json`. Negatives: the 4 organizer normal-traffic clips, looped to at least 60 s (the highway clip is 13 min
long by itself).

## Result

| Metric | Value |
|---|---|
| Accident impacts found | **4 of 5** |
| Extra candidates on the accident clips | 5 (about one per clip, in the aftermath) |
| False candidates on normal traffic | 12 in 16.2 min (0.74/min), from **2 spots** that repeat every loop |
| Throughput | 22.3 frames/s on the T4: about 2 cameras at 10 fps |

| Clip | Candidates (clip time, kind, score) | Impact |
|---|---|---|
| `test_01` | none: **missed** | 10.5 s |
| `test_02` | 3.6 s collision+sudden_stop 1.0 · 7.2 s collision 0.51 | 6.5 s |
| `test_03` | 4.1 s collision+sudden_stop 1.0 · 11.1 s collision 1.0 | 3.2 s |
| `test_04` | 2.6 s collision+fall 0.81 · 7.4 s collision 0.81 · 12.8 s collision 0.65 | 1.2 s |
| `test_05` | 4.0 s collision 0.63 · 9.8 s collision 0.65 | 2.5 s |
| `busy_street` (62 s) | none | – |
| `highway_traffic_overcast_weather` (780 s) | none | – |
| `city_street_7_condensation_inside_housing` (64 s) | 4 × collision 0.67, the same spot every loop | – |
| `traffic_flows_in_the_open_lanes` (64 s) | 8 × collision 0.51, the same spot every loop | – |

## What was tried

| Variant | Impacts | False on 4 normal clips × 60 s | Verdict |
|---|---|---|---|
| Collision needs a full stop (default) | 4 of 5 | 11 | kept |
| Collision also on a 60 % speed drop (`decel_drop=0.6`) | 4 of 5 | 18 | more false candidates, no gain |
| Inference at 1280 px | 3 of 5 | more (crowd) | worse |

Two bugs found on the way: candidate clusters chained across the loop boundary and took the strongest candidate's
time, which hid the `test_04` hit (now anchored at the first candidate, whose time is the incident time); and the
evaluation kept a minute of 1080p frames in memory (now streamed).

## Known limit

`test_01`: YOLO tracks the auto-rickshaw (as "truck") but never detects the motorcyclist it hits, who is small and
hidden behind it at the moment of impact, nor the rider thrown off. With one party invisible no contact rule can fire.
A larger inference size did not help. Not tuned around: one clip.

## Reading

Tier 0 is tuned for recall; Hafnia (tier 1) rejects false candidates, which it did reliably on normal traffic (8 of 8
NONE in `run/bench-20261018`). Each candidate costs one Hafnia request, so the router must deduplicate repeating spots
and, with learned trust, stop asking about a spot Hafnia keeps rejecting.
