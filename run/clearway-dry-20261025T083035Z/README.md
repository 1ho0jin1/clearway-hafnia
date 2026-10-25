# The Clearway service, dry run (F2, 2026-10-25)

`scripts/run_clearway.py --minutes 5` on the organizers' six incident cameras: the live service with the offline
replay's stand-in answering instead of Hafnia (no requests; each camera's loop phase found by matching frames to the
clip). The last of five dry runs; what the earlier ones found is in `run/clearway-live-20261025T083623Z/README.md`.

| Camera | Questions | Card | Occurrences | Change → card (first) | Recurrence → card | Offline replay (no guard): requests, cards |
|---|---|---|---|---|---|---|
| Breakdown | 2 | 1 | 7 | 117 s | 2.3 s | 2, 1 |
| Bin | 5 | 1 | 24 | 62 s | 1.4 s | 3, 1 |
| E-scooter | 2 | 1 | 12 | 24 s | 2.3 s | 2, 1 |
| Gate | 4 | 1 | 39 | 34 s | 1.7 s | 2, 2 |
| Tracks | 1 | 1 | 2 | 44 s | 1.6 s | 1, 1 |
| Graffiti | 1 | 1 | 19 | 53 s | 1.4 s | 1, 1 |
| **Total** | **15** | **6** | | | | **11, 7** |

No errors, no question unanswered, 9.8–9.9 fps per camera. Live gives a few more questions than the replay (pieces of
a first occurrence reported more than 3 s apart are asked separately) and slow first cards (the single lens camera
plays the questions' clips in turn).
