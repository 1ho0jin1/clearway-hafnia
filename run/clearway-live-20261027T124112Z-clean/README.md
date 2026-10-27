# Clean live run under the day's fixes: eleven cameras, 20 minutes, 14 requests (2026-10-27)

`scripts/run_clearway.py` on all eleven organizer cameras (the five street clips `--real`), 12:41-13:01 UTC,
`--answers hafnia --max-requests 40 --alarms --close-alarms-at-end --notify`, the stand-in answering beside Hafnia as
`expected`. Today's count before: 6; after: 20. The first live run with everything fixed today: direct asks for
large spots, the lens's span read back from its own frames, the detector that does not fade, FrameBridge at 832 px
and the detector on every second frame. Per camera: `summary.json` (`scripts/report_clearway.py --xprotect`).

| | This run | M3 (2026-10-26, 3 h) |
|---|---|---|
| Questions | 14 (10 direct, 4 on the lens), 12 of them in the start-up minutes | 33, 26 in the first 10 minutes |
| Cards | 7 on the six incident cameras, 0 on the five street cameras | 11, 4 of them false |
| Categories as the stand-in expected | 12 of 14 | 24 of 32 fit the scene |
| Seconds from the change to its card | direct 19.5-31 s, lens 42-72 s | median 104 s |
| Recurrences carded without a request | 331 (79-83 occurrences per card over 20 min) | the object incidents faded after half an hour |
| Lens spans | offsets +0.29 to +0.47 s, 3 of 4 verified, 0 replayed | assumed; 0.3-9.5 s off |
| Frames received per camera | 7.5-8.1 per s | 3-5 per s |
| XProtect alarm actions | 7 raised, 7 closed, 8 bookmarks, 0 errors; 14-71 s per raise (median 19 s) | 35-62 s |

The two disagreements: cw-0008, the graffiti, described exactly ("uses a spray paint can to apply graffiti on the
side of a stationary train") but filed as OBSTRUCTION instead of DAMAGE, so its card went to Street services; and
cw-0009, the gate at night on the lens, answered NONE on a clip whose feed had a 0.7 s hole (under the 1 s replay
threshold; the gate's later question, cw-0010, got TAMPERING). One more flaw not in the score: cw-0006, the
e-scooter on the lens, got the right category for the wrong object ("a large tree branch lies across the pavement";
the clip's feed carried a third of its frames, the span verified). No answer described another camera's scene.
The tracks camera has two cards: the person's first spot and, 20 s later, a second spot further along the tracks
(cw-0014), cleared when they left the frame.

CPU (health, medians after the first two records): the machine 100 %, the service 54 %, FrameBridge 29 %, the
Recording Server 1.6 %. The alarm actions' latency is the next thing to cut: each raise is several REST calls through
the API Gateway on a saturated machine. The service and FrameBridge now run below normal priority, so that
XProtect's services are scheduled first: on the same cameras the raises took 0.16-0.23 s
(`run/clearway-dry-20261027T134043Z-priority`).

**The prompt asked again** (`scripts/reask.py`, 21 requests, `reask-negatives.jsonl` and
`reask-summary_first.jsonl`): the same 14 spans with two variants of the prompt. With each category's definition
saying what it is not ("negatives"), the graffiti became DAMAGE, the twelve right answers stayed, the gate's
wrong-seconds clip stayed NONE (both variants describe a person walking past the fence: the clip never showed the
tampering), and the ambiguous scooter crop went from a right label for a wrong object to NONE: 13 of 14 as expected
against 12. Asking for the summary before the category ("summary_first", 7 spans) left the graffiti OBSTRUCTION
and made the scooter crop STALLED_VEHICLE. The negatives prompt is the service's since (`clearway/prompt.py`).

Files: `service.jsonl`, `ledger.jsonl`, `changes.jsonl`, `incidents.json`, `shift.json`, `summary.json`,
`reask-*.jsonl`; not committed: `snaps/`, `cameras/`, `clips/`.
