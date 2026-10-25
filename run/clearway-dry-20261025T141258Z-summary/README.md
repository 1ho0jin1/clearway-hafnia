# The shift summary (F8) on a live dry run (2026-10-25)

`scripts/run_clearway.py --minutes 3` (the stand-in answering: no Hafnia requests, no alarms) with the board following
it. Halfway through, the board's `/summary` page was checked in a headless Edge screenshot ("live, so far", refreshed
every 15 s). At the end the service wrote `shift.json` (`clearway/summary.py`; `python -m clearway.summary <run>` gives
the same).

- 6 incidents, one per camera, 114 occurrences on their cards, 18 questions; 116 of 134 changes needed no question
  by the middle of the run.
- Spot changed to card: 47.5 s the first time (median; max 143 s, the breakdown, behind the lens queue), 1.4 s for a
  repeat. Alarm to clear: 31.7 s. A median occurrence lasted 11.8 s: these are the organizers' looped clips, which
  restart every 8-17 s, and the page says so.
- Recurring spots: the school gate 39 times, the bin 20, the breakdown 15, the tracks 14, the e-scooter 14, each with
  the snapshot of the spot.
- How long things lasted is not in the ledger's log alone, which logs a clearing only for an open card: a question
  still waiting for the lens when its spot cleared would last the lens queue's minute. The summary replays the
  ledger's clearing rule over its log and the detector's closings (`changes.jsonl`). Checked on three earlier runs:
  each of the 201 clearings the ledger logged is at the end of a replayed occurrence (172), or inside one where two
  pieces asked about apart overlapped (29).
- The 3 minutes of frames plus the questions finishing make a 4-minute run, and the rates per hour are a start-up
  burst's: every incident's first question comes at once. The page says that too (short run).
