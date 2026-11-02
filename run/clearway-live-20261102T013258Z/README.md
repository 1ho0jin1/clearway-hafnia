# Live run for the demo video, second of two: eleven cameras, 10 minutes, 15 requests (2026-11-02, 01:33-01:44 UTC)

The same command as `run/clearway-live-20261102T012136Z` (eleven cameras, the five street clips `--real`,
`--answers hafnia --max-requests 15 --minutes 10 --alarms --close-alarms-at-end --notify`). Today's count before:
15; after: 30. The board scene of the video is this run replayed on the idle machine (`scripts/replay_board.py`,
then `scripts/record_board.py` on port 8767): the recorder beside the live run got 20 frames in 10 minutes.

| | |
|---|---|
| Requests | 15 (12 answers) |
| Cards | 8, all on the six incident cameras and none on the five street cameras: the person on the tracks (High, Rail control; cleared and reopened twice as the loop repeats), the bin and the e-scooter (OBSTRUCTION, Street services), the graffiti (DAMAGE, Asset owner), the gate (TAMPERING, Security), the stalled truck (STALLED_VEHICLE, Traffic operations, twice: cw-0014 and cw-0015, its first question only at +445 s because the first minutes' requests went to the other cameras) and a second bin card (cw-0012) |
| NONE | 4, all lens clips of the gate at night |
| Recurrences carded without a request | 147 |
| Verdicts from the phone | 6 confirmations (cw-0005, cw-0006, cw-0001 twice, cw-0015, cw-0014) |
| Seconds from the service's start to the answers | 54, 59, 104, 136, 160, 169, 178, 211, 321, 356, 445, 474 |

The raw logs are git-ignored; `run/clearway-replay-20261102T014908Z` is the replay's copy (also ignored).
