# Live run for the demo video, first of two: eleven cameras, 10 minutes, 15 requests (2026-11-02, 01:22-01:33 UTC)

`scripts/run_clearway.py` on the eleven organizer cameras (the five street clips `--real`), `--answers hafnia
--max-requests 15 --minutes 10 --alarms --close-alarms-at-end --notify`, the author on the phone with the ntfy app.
Today's count before: 0; after: 15. Filmed for `docs/VIDEO.md` (the phone scene comes from this run); the board
recorder beside it starved (its frames stop one second before the first card) and the board scene was taken from
the second run, replayed (`scripts/replay_board.py`). The raw logs are git-ignored; these numbers are from them.

| | |
|---|---|
| Requests | 15, all spent in the first 6 minutes (12 answers, the rest refused by Hafnia or unanswered at the cap) |
| Cards | 7: stalled vehicle (cw-0001, direct) and a second stalled-vehicle card from the lens (cw-0009, rejected by the author), the bin (OBSTRUCTION), the gate (TAMPERING), the person on the tracks (PERSON_ON_TRACKS, High), the e-scooter (OBSTRUCTION), and one false card: `traffic_flows_in_the_open_lanes` called PERSON_ON_TRACKS (a worker bent over in roadworks, "on the railway tracks"; cw-0011, rejected by the author from the phone) |
| NONE | 5 (the gate's lens clips twice, the scooter's and the bin's lens clips, a street camera) |
| Recurrences carded without a request | 98 |
| Verdicts from the phone | 6: rejected cw-0009 and cw-0011, confirmed cw-0014, cw-0006, cw-0002, cw-0007; each applied in XProtect within 0.1 s of arriving |
| Alarm actions | raises 0.2-0.3 s each once the first (33 s, the API Gateway's cold start) was through; closes and confirms 0.05-0.09 s |

A first launch of this run (`run/clearway-live-20261102T011422Z`) ended after 3 s: FrameBridge exited at its start
before any frame and before the service could sample its CPU; no request was spent; the cause was not found (the
same command, launched the same way, streamed all twelve cameras in a dry run and in this run minutes later).
