# Owner notifications (F12) on a live dry run (2026-10-25)

`scripts/run_clearway.py --minutes 5 --alarms --close-alarms-at-end --notify` (the stand-in answering: no Hafnia
requests; XProtect alarms named "[dry run]", closed at the end), with the board following it, the stand-in owner inbox
running (`scripts/start_inbox.ps1`, http://127.0.0.1:8770/) and a test script confirming the e-scooter card and
rejecting the bin card on the board (F7). Every owner in `config/owners.json` pointed at the inbox, with snapshots;
unsigned (no `CLEARWAY_HOOK_SECRET` set). Signatures, a wrong key (401, not retried) and an unreachable target
(retried twice, logged as failed) were tested in-process.

- 8 messages, all delivered on the first attempt within 0.6 s of the ledger's effect: 6 "opened" (one per card), the
  bin's "rejected" (stand down) and the e-scooter's "confirmed". The largest, with the snapshot, was 145 KB.
- Owners were told 59.9 s after their spot changed (median); the card itself took 62.3 s (the lens queue and the
  stand-in's answer), so the owner hears within a second of the card. The XProtect alarm followed 2.5 s after the card.
- The board's cards say "owner told" (red "owner not reached" when a delivery failed); the shift summary counts the
  messages and times "change to owner told".
- No webhook URL in the service's log: deliveries are logged by target name.
- XProtect: 6 alarms raised, 1 set to In progress, 6 closed (the bin's by the rejection, the rest by the test harness
  at the end), 0 errors, 6 of 6 in the expected state.
- No "cleared" or "reopened" messages: on the looped clips an incident recurs within the 60 s an alarm waits before
  it closes. They are shown in `run/clearway-dry-20261025T145829Z-notify-cycle` (`--close-after 5`).
