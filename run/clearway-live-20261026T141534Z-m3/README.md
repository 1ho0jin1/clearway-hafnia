# M3: a three-hour live shift on all eleven cameras (2026-10-26)

`scripts/run_clearway.py` on all eleven organizer cameras (the six synthetic incident clips at the loops setting, the
five street clips at the real-camera setting, `--real`), 14:16-17:16 UTC, `--answers hafnia --max-requests 120
--alarms --close-alarms-at-end --notify`, the stand-in answering beside Hafnia as `expected`. Today's count was 0 at
the start. Per camera: `scripts/report_clearway.py <run> --xprotect` (writes `summary.json`); the shift summary:
`shift.json` (written by the service at the end), the board's `/summary`. Analysed 2026-10-27 from the logs; the
answers were judged from Hafnia's summaries against each camera's known scene, **not yet audited against the frames**.

- **Requests:** 33 questions, 32 answers, 1 failed (`HTTP 403 Forbidden` from Hafnia's cloud, free). 26 of the 33 came
  in the first 10 minutes (every camera's first changes at once), 7 in the next hour, none in the last 110 minutes
  (see "The looped incidents faded"). 1.0 request per camera-hour; the shift summary's "21.5 cameras per allowance" is
  inflated by that fade and is not a claim. The gate cost 12 (its lit pavement: 10 NONE answers, 7 of them look-alikes
  the memory held and escalated after 30 s).
- **Cards:** 11. Right: the e-scooter, the person on the tracks, the bin, the breakdown, the gate's tampering (5). A
  second card for the bin (`cw-0019`, OBSTRUCTION: the first bin card had cleared and a later occurrence was not
  matched to it). The graffiti carded as OBSTRUCTION ("a large tree trunk lies across the pavement"; DAMAGE expected).
  **False cards: 4**, all from answers asked in the first 6 minutes: the gate as PERSON_ON_TRACKS, the bin as
  STALLED_VEHICLE, the tracks as STALLED_VEHICLE, the roadworks (`traffic_flows_in_the_open_lanes`) as STALLED_VEHICLE.
  0.12 false cards per camera-hour (4 in 33), but all of them during the start-up burst. No operator at the board
  during the run, so the shift summary's operator-based "false cards" reads 0.
- **Hafnia's answers:** 24 of 32 fit the camera's scene (judged from the summaries), 6 wrong, 2 doubtful (the gate's
  crouching person called NONE at 15:05; the e-scooter street called NONE at 15:14). The stand-in agrees on 14 of 32,
  but it is wrong on the gate: it expects TAMPERING whenever the gate reports, and 10 of Hafnia's 12 gate answers were
  NONE, most of them about the lit pavement, rightly.
- **Wrong scenes (suspected, unverified):** three of the six wrong answers describe another camera's scene: the gate
  question "a person in a red coat walks along the railway tracks", the bin question "a silver pickup truck ... smoke
  rising from the engine" (the breakdown), the tracks question "a white van is stopped in the lane" (the roadworks).
  The lens publisher's log (`run/lens/played.jsonl`) shows each clip played alone, in the span that was asked about.
  In those cases the scene described matches the clip played about 10 s *after* the asked span, and one gate answer
  says "the frame remains completely black" (perhaps the publisher's dark-grey idle frames, which played about 10 s
  after that span; the gate is a night scene, though). This fits `lens_1`'s recording being about
  10 s behind the publisher's clock during the start-up minutes. It does not fit every answer (`cw-0010`). **TODO:**
  export `lens_1`'s recorded frames for those spans (`Get-Snapshot`; recordings are kept 24 h, so from about 14:16 UTC
  2026-10-27 they are gone) and compare them with the clips that were sent.
- **The looped incidents faded:** the detector's reports for the object incidents fell after the first half hour
  (per half hour: breakdown 29, 0, 3, 3, 3, 5; bin 27, 1, 3, 6, 2, 3; e-scooter 6, 1, 1, 0, 0, 0; graffiti 37, 2, 0, 0, 0,
  0). The person triggers did not fade (the tracks' danger zone about 110 per half hour; the gate's lit pavement
  490-640). The e-scooter's changes never closed, so its card stayed open the whole shift (longest open 10,788 s), as
  did the breakdown's and the false bin card. Likely cause, unverified: the slow background (τ 600 s) takes in a looped
  incident that is present for most of each loop within about 10 minutes, and then its spot no longer differs. A real
  incident does not loop. **TODO:** replay one incident clip offline for 30+ minutes (`scripts/eval_change.py`) to
  confirm.
- **Frames:** 4.3-5.1 fps per camera, as in the preflight; 7 frames dropped on the bin in 3 hours.
- **Times:** first card 103.5 s after the change (median of 11, max 213 s: the start-up burst waiting for the one lens
  camera, up to 167 s per clip); repeats carded in 1.1 s (952); an occurrence lasts 7.3 s (median of 968); owners told
  107 s after the change (median), 0.7-3.6 s after the card.
- **XProtect was slow all shift:** a raised alarm (trigger, snapshot, two bookmarks) took 39-112 s, bookmarks about
  30 s of it; every half hour's median action took 35-62 s (0.2-0.3 s after start-up in the 3-minute preflight
  `run/clearway-dry-20261026T140810Z-preflight11`). The alarm thread works in order, so a card's alarm came 276 s after
  it (median). Cause not found (11 streams, the models and XProtect on 4 cores; 2.8 GB of RAM free). 11 alarms raised,
  33 reopened, 50 closed, 55 bookmarks, 36 snapshots. 12 calls timed out, all on one alarm (`cw-0022`, the tracks'
  false card; its snapshot had answered 404 when raised): it was left New, 10 of 11 alarms in the expected state.
- **Owners:** 98 notifications, 0 failed (traffic operations 75, from the breakdown's and two false cards' clear and
  reopen cycles).
- **Street cameras:** at the real-camera setting `busy_street` reported 5 times (2 questions, NONE both), the
  roadworks 2 (one NONE, one false card), the other three nothing.

Files: `service.jsonl`, `ledger.jsonl`, `changes.jsonl` (31 MB), `incidents.json`, `shift.json`, `summary.json`.
Not committed: `stdout.log`, `stderr.log`, `cameras/` and `snaps/` (footage, git-ignored).
