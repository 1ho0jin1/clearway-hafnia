# Phone pushes (F12, ntfy): a Confirm tap, three minutes on two cameras (2026-10-27)

Second check after `run/clearway-dry-20261027T044611Z-ntfy` (which tested Reject): `scripts/run_clearway.py --cameras
person_on_railway_tracks escooter_left_across_sidewalk --minutes 3 --answers standin --no-lens --alarms
--close-alarms-at-end --notify`, 04:56-04:59 UTC, no Hafnia requests. The snapshot is now scaled to 640 px for the
push (44-49 KB instead of 97-107 KB) and verdicts carry where they came from (`via`: board or ntfy).

- Two cards (the tracks for rail control, the e-scooter for street services); both pushed to the phone 0.6 s after
  the ledger's effect, with the snapshot and the two buttons; XProtect alarms raised in 0.2-0.7 s.
- **Confirm** tapped on `cw-0001` (simulated phone, the button's exact JSON): the listener took it 0.8 s after the tap,
  the ledger applied it at 0.8 s (`operator`, `via: ntfy`), XProtect put the alarm **In progress** 0.9 s after the tap
  with the comment "Confirmed by the operator from their phone (ntfy)", and the acknowledgement reached the phone
  1.2 s after the tap.
- The test harness closed both alarms at the end.

Files: `service.jsonl`, `ledger.jsonl`, `changes.jsonl`, `incidents.json`, `shift.json`, `operator.jsonl`; not
committed: `stdout.log`, `stderr.log`, `snaps/`, `cameras/`.
