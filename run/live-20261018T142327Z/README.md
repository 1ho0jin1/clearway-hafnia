# First live end-to-end run (2026-10-18, 5 minutes)

`scripts/run_live.py --cameras test_04 traffic_flows_in_the_open_lanes --minutes 5 --max-requests 10`.
All events with timestamps: `events.jsonl`. Hafnia cost: 4 requests (3 checks, 1 description).

Pipeline: FrameBridge (C#, MIP .NET library, live frames at 9.5–10.2 fps) → tier 0 per camera (YOLO11m + ByteTrack +
rules) → router → an unverified Low alarm on the camera with an annotated snapshot → Hafnia on the 6 s window centred on
the event → the alarm is raised to High (plus Hafnia's description in its history and a bookmark) or closed.

## What happened

| Time (UTC) | Camera | Step |
|---|---|---|
| 14:23:37.0 | test_04 | tier 0: motorcycle+person contact (0.55) → Low alarm after 0.6 s |
| 14:23:46.2 | test_04 | Hafnia: NONE (9.2 s after the event) → alarm closed as a false alarm |
| 14:24:09.2 | test_04 | tier 0: motorcycle+bicycle collision (0.93) → Low alarm after 0.8 s |
| 14:24:17.5 | test_04 | Hafnia: ACCIDENT (8.3 s after the event) → alarm raised to High |
| 14:24:23.0 | test_04 | Hafnia description added to the alarm history; bookmark `no.000004` |
| 14:25:39.5 | traffic_flows | tier 0: car+car contact (0.52) → Low alarm |
| 14:25:45.6 | traffic_flows | Hafnia: NONE (6.1 s after the event) → alarm closed |

| Candidates | test_04 | traffic_flows |
|---|---|---|
| From tier 0 | 304 | 1 |
| Sent to Hafnia | 2 | 1 |
| Held: incident open | 259 | – |
| Held: camera cooldown | 41 | – |
| Held: spot recently rejected | 2 | – |

- Unverified alarm 0.6–0.8 s after the event; Hafnia's verdict 6–9 s after it. Tier 0 ran 0.3–0.8 s behind live.
- Asking Hafnia about every tier 0 candidate would have cost about 305 requests in 5 minutes; the router spent 3.

## Problem found

The description of the confirmed accident contradicts the verdict on the same window: "A motorcyclist ... slows, and
stops to avoid a collision". The one-word check says ACCIDENT; the free description under-reports, as in
`run/bench-20261018`. The operator sees both in the alarm history. To fix: a description prompt that takes the
confirmed accident as given, or no free text on the alarm.
