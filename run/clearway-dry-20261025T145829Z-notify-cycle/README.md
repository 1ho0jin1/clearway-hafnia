# Owner notifications: cleared and reopened (2026-10-25)

`scripts/run_clearway.py --cameras bin_pushed_over_onto_sidewalk --minutes 2 --close-after 5 --notify` (the
stand-in answering: no Hafnia requests; no XProtect alarms) with the stand-in owner inbox running. `--close-after 5`
(test harness) lets an incident's alarm close once its spot has looked as before for 5 s instead of 60 s, so the
looped bin closes and reopens it every loop, as the F3 reopen test did.

- 13 messages to Street services, all delivered within 0.02 s: "opened" with the snapshot, then "cleared" (no action
  needed) and "reopened" (happened again, occurrence n, with a new snapshot) every 15 s as the clip looped.
- That is why close_after_s is 60 s: an owner would otherwise get a stand-down and a call-out every loop. With 60 s,
  the e-scooter and the bin on their 15 s loops keep one open alarm and send one message
  (`run/clearway-dry-20261025T144944Z-notify`).
- A 2-minute try with `--close-after 8` (not kept) sent only "opened": the bin's spot never looked as before for 8 s
  between loops.
