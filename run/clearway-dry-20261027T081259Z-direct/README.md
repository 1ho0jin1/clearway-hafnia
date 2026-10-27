# Direct asks for large spots: dry run, three cameras, 3 minutes (2026-10-27)

`scripts/run_clearway.py --cameras person_on_railway_tracks bin_pushed_over_onto_sidewalk escooter_left_across_sidewalk
--minutes 3 --answers standin --alarms --close-alarms-at-end`, 08:13-08:16 UTC, no Hafnia requests, the lens on. First
run of the routing in `clearway/service.py` (`DIRECT_BELOW` 2.5): a spot the lens would magnify less than 2.5x is
asked about on its own camera's recording over the event window, and its crop is only stored for the board's card; a
smaller spot is played on the lens as before. Made after `run/lens-check-20261027` showed the lens recording's time
base 0.3-9.5 s behind the publisher.

- 7 questions: 4 direct (tracks 1.1x and 1.41x, e-scooter 2.14x, bin 1.23x), 3 on the lens (e-scooter 3.65x, bin
  2.82x and 4.45x).
- The stand-in answered the direct questions 11.6-12.2 s after the report (its own 8 s latency plus the window's 3 s
  after the report; no lens wait), the lens ones 24.1-45.6 s (lens waits of 12.6, 24.8 and 34.2 s: the queue).
- 3 cards (tracks, High, rail control; e-scooter and bin, Medium, street services): XProtect alarms 0.2-0.9 s after
  the effect, each with one bookmark on its own camera (a direct ask gets no lens bookmark). The stored crops
  (`run/lens/spool/<id>.avi` without a job file, so the publisher never played them) convert to the board's MP4
  (`clips/cw-0001.mp4`, `clips/cw-0004.mp4` checked).
- The test harness closed the alarms at the end.

Files: `service.jsonl`, `ledger.jsonl`, `changes.jsonl`, `incidents.json`, `shift.json`; not committed: `stdout.log`,
`stderr.log`, `snaps/`, `cameras/`, `clips/`.
