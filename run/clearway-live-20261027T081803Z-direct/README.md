# Direct asks for large spots: live check, three cameras, 4 minutes, 6 requests (2026-10-27)

`scripts/run_clearway.py --cameras vehicle_breakdown_traffic_queue bin_pushed_over_onto_sidewalk
escooter_left_across_sidewalk --minutes 4 --answers hafnia --max-requests 8 --alarms --close-alarms-at-end`,
08:18-08:22 UTC, the lens on, `DIRECT_BELOW` 2.5, 3 requests at once. Today's count before: 0; after: 6. The first
Hafnia run of the routing in `clearway/service.py`: a spot the lens would magnify less than 2.5x is asked about on its
own camera's recording over the event window (whole seconds, 3 s after the window's end); a smaller spot is played on
the lens and asked about on `lens_1` as before. Dry run of the same code: `run/clearway-dry-20261027T081259Z-direct`.

| Question | Camera | View | Lens would magnify | Hafnia | Card after the change | Category (expected) |
|---|---|---|---|---|---|---|
| cw-0002 | e-scooter | direct | 2.14x | 5.3 s | 13.3 s | OBSTRUCTION (OBSTRUCTION) |
| cw-0003 | bin | direct | 1.23x | 5.5 s | 13.4 s | OBSTRUCTION (OBSTRUCTION) |
| cw-0001 | breakdown | lens, waited 8.8 s | 3.56x | 7.3 s | 21.8 s | STALLED_VEHICLE (STALLED_VEHICLE) |
| cw-0004 | e-scooter | lens, waited 14.8 s | 3.65x | 7.3 s | 32.2 s, merged | OBSTRUCTION (OBSTRUCTION) |
| cw-0005 | bin | lens, waited 26.9 s | 2.82x | 7.2 s | 43.4 s, merged | OBSTRUCTION (OBSTRUCTION) |
| cw-0006 | bin | lens, waited 35.9 s | 4.45x | 5.2 s | 47.2 s, merged | OBSTRUCTION (OBSTRUCTION) |

- 6 of 6 categories as the stand-in expected. The two direct summaries were checked against the stored crops (the
  same frames as the recording): "the electric scooter lies on its side on the pavement after the rider dismounts,
  blocking part of the sidewalk as the rider walks away" and "a person tips a green wheeled bin onto the pavement,
  leaving it lying on its side as they walk away" are right in every claim. The lens summaries also fit the clips sent
  (the machine was quiet: three cameras); two of them describe the loop restarting inside the window ("a rider later
  enters the frame", "places a small object on its lid" is the hand at the lid as the next loop starts).
- A direct card came 13.3-13.4 s after the change: the window's 3 s after the report, the 3 s settle, Hafnia's 5.3-5.5
  s. The lens cards came 21.8-47.2 s after theirs (the queue: 8.8-35.9 s waiting). M3's median was 104 s.
- No direct ask failed (both windows were recorded), so the fallback to the lens was not exercised.
- 3 cards, 3 XProtect alarms (0.2-0.9 s per action), 4 bookmarks: one on the camera for each direct card, camera and
  `lens_1` for the lens card; 0 errors. The test harness closed the alarms at the end.
- The three cameras ran at 9.9 fps with no dropped frames.

Files: `service.jsonl`, `ledger.jsonl`, `changes.jsonl`, `incidents.json`, `shift.json`, `summary.json`
(`scripts/report_clearway.py`); not committed: `stdout.log`, `stderr.log`, `snaps/`, `cameras/`.
