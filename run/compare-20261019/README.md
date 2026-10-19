# Tiered pipeline vs Hafnia-only polling, same recorded footage (2026-10-19)

`scripts/bench_tiered_vs_polling.py --out run/compare-20261019`. 7 cameras, the same 36 s of recording each
(14:27:40–14:28:16 UTC). All rows: `compare_results.json`. Hafnia cost: 47 requests (42 polling, of which 4 failed for
lack of recording and were free; 5 tiered).

The test cameras loop their clips (12–17 s), so the 36 s hold 2–3 replays of each accident: 14 impacts on 5 accident
cameras. A replay is the same accident again, so **cameras caught** is the fair recall measure; the tiered router holds
a camera after a confirmation on purpose (one accident, one alarm).

Ground truth: each impact located in the recordings by matching recorded frames to the source frame at the impact
(match ratios 0.08–0.22), the others one loop length apart. An ACCIDENT answer is correct when its window overlaps an
impact or the 6 s after it (aftermath); otherwise it is a false alarm.

## Result

| | Hafnia-only polling (6 s windows) | Tiered |
|---|---|---|
| Hafnia requests | **42** | **5** |
| Accident cameras caught | **5 of 5** | 3 of 5 |
| Impacts covered | 13 of 14 | 3 of 14 (holds after a confirmation by design) |
| Alarms raised | 21 | 3 |
| False alarms | 2 (ACCIDENT more than 6 s after an impact) | 0 |
| Normal traffic | 0 false alarms (8 NONE; 4 highway windows had no recording) | 0 candidates |
| Median impact → verdict | 9.8 s | 7.8 s (plus an unverified alarm in under 1 s, live) |

Per camera:

| Camera | Impacts | Polling answers (6 windows) | Tiered |
|---|---|---|---|
| `test_01` | 2 | ACCIDENT ×4 | missed: no tier 0 candidate (struck rider never detected) |
| `test_02` | 3 | ACCIDENT ×6 | caught, first impact |
| `test_03` | 3 | ACCIDENT ×2 | **missed: router.** First candidate 4.6 s before the impact → NONE; then 21 candidates muted as a rejected spot, 11 by the cooldown |
| `test_04` | 3 | ACCIDENT ×3 | caught, first impact |
| `test_05` | 3 | ACCIDENT ×6 | early candidate → NONE; caught at the third impact after the cooldown |
| `traffic_flows_in_the_open_lanes` | 0 | NONE ×6 | no candidates |
| `highway_traffic_overcast_weather` | 0 | NONE ×2, no recording ×4 | no candidates |

## Reading

- **Cost:** tiered used 5 requests against 42, an 8× saving here, and the saving grows with quiet footage: on the two
  normal cameras tiered spent nothing while polling spent 12. Continuous 6 s polling is 14,400 requests a day per
  camera, 29× the daily allowance.
- **Recall:** polling caught every accident camera; tiered caught 3 of 5. One miss is tier 0 (`test_01`), one is the
  router (`test_03`): after Hafnia rejects a candidate that came *before* the impact, the router mutes the spot and
  the camera, and blocks the real impact seconds later.
- **Operator load:** polling raised 21 alarms for 5 accidents (every window again) and 2 false ones; tiered raised 3,
  none false. Polling would need its own deduplication.
- **Router fix suggested by this run:** after a rejection, mute only candidates whose event time falls inside the window
  Hafnia already checked; later evidence gets its own check. That would have recovered `test_03` and caught `test_05`
  at its first impact, for a few more requests.
