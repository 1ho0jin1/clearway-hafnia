# Phone pushes with Confirm / Reject (F12, ntfy): a four-minute dry run on three cameras (2026-10-27)

`scripts/run_clearway.py --cameras person_on_railway_tracks escooter_left_across_sidewalk bin_pushed_over_onto_sidewalk
--minutes 4 --answers standin --no-lens --alarms --close-alarms-at-end --notify`, 04:47-04:51 UTC, no Hafnia requests
(the stand-in answered). `config/owners.json` sends every owner's news to the stand-in inbox and to one ntfy topic
(`scripts/setup_ntfy.ps1`); the phone was simulated by posting the Reject button's body to the reply topic
(`tap_one.py` in the investigation's scratch folder: the same JSON the ntfy app sends when the button is tapped).

- **Cards:** 3 (the person on the tracks for rail control, the e-scooter and the bin for street services), 76 changes,
  7 questions, 24 recurrences.
- **Pushes:** every card's "opened" went to the phone 0.7 s after the ledger's effect, with the snapshot attached
  (97-107 KB), priority 5 for rail control, 4 for street services, and the two buttons; the inbox webhook got the
  same news in 0.02-0.1 s. XProtect's alarms took 0.3-1.4 s (three cameras: the machine was not starved).
- **The tap:** Reject on `cw-0001` (the tracks card), posted 04:48:21 UTC. The listener took it 0.7 s after the tap,
  the service applied it 0.9 s after (`operator`, `since_click_s` 0.9), the ledger closed the alarm with the reason,
  XProtect's alarm was closed 1.2 s after the tap, and the "rejected" acknowledgement reached the phone 1.4 s after
  the tap (and the inbox). Afterwards 13 look-alikes at that spot were skipped without a question
  (`skipped_operator` 13 in the end stats).
- **Refusals** (self-test `run/notify-test`, `python -m clearway.notify --test --listen 30`): a tap with a wrong
  token is logged `bad token` and ignored; a message that is not a verdict is logged `not a verdict`; a valid tap
  lands in `operator.jsonl` as `{"incident", "verdict", "wall", "via": "ntfy", "reply": <ntfy id>}`.
- **Readback from ntfy.sh:** the push's title, the three-line text (RFC 2047 keeps the line breaks and the quotes),
  priority, tags, the attachment URL (expires after 3 h; the message after 12 h) and both actions with their JSON
  bodies parsed as sent.

Files: `service.jsonl`, `ledger.jsonl`, `changes.jsonl`, `incidents.json`, `shift.json`, `operator.jsonl`. Not
committed: `stdout.log`, `stderr.log`, `snaps/`, `cameras/` (footage, git-ignored).

Open: the XProtect close comment still says "on the Clearway board" for a verdict from the phone (`via` is in
`operator.jsonl`); Teams and Slack formats; one topic per owner for a real deployment (`config/owners.json`, `_doc`).
