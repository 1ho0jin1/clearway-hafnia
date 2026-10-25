# The owner board (F4), on a live dry run (2026-10-25)

`scripts/run_clearway.py --minutes 3` (the stand-in answering: no Hafnia requests) with the board following it
(`python -m clearway.board --latest`, now `scripts/start_board.ps1`), checked with headless Edge screenshots at
1920×1080. The service now writes each question's snapshot (`snaps/`, git-ignored with `clips/`: footage).

- Cards appeared per owner as the stand-in answered (new ones highlighted), each with the lens clip playing (MP4
  made from the spool on first view: 0.4 s, then cached), the camera's view with the spot boxed in the corner, time
  open since the current occurrence began, "nth time at this spot" and the alarm state.
- The strip above the columns showed up to 9 questions waiting for the lens at once during the start-up burst
  (oldest 1:41): the single lens camera's queue, made visible.
- The same page shows a finished run (the six-camera live run `run/clearway-live-20261025T083623Z`, with Hafnia's
  summaries): timers stop at the run's end and a notice says so.
- 17 questions, 6 cards, no errors.

Inside XProtect Smart Client it does not run on this machine (its HTML page item falls back to Internet Explorer;
`CLAUDE.md`), so the board is its own Edge app window beside Smart Client: `scripts/open_board.ps1`.
