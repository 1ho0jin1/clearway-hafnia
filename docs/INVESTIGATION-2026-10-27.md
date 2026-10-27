# Investigation report: Clearway, 2026-10-27

An independent, critical pass over the entry three days before submission, done at the participant's request on
2026-10-27 between 03:50 and 04:30 UTC. Nothing below is taken from the project's own documents on trust: the
numbers were re-derived from the repository, the run logs, the gateway, XProtect and the machine, and where a claim
was checked the check is named. Opinions are marked as such.

## 1. Verdict in brief

1. **Progress.** The product is largely built (10 of 12 planned features, a three-hour live shift done) and
   everything is committed and pushed. What is missing is what the judges meet first: there is no README, no
   setup script, no demo video, and no automated test. The submission date is "about 2026-10-30" in three
   documents, but no firm date or time is written anywhere in the repository or the participant guide: confirm it.
2. **Goal.** Since 2026-10-22 the goal is concrete and measurable ("what is blocking a public way right now, whose
   job is it, how long has it been there"), and it maps onto three of the organizers' six idea boxes. The first
   seven of fifteen days went to two abandoned directions. One of the four claimed differentiators ("results on
   real footage") has no evidence a judge may see. Features were added ahead of the core's reliability.
3. **Accuracy.** M3's headline, 4 false cards in 33 questions, understates a defect this investigation
   confirmed with recorded frames: **the lens camera's recording does not share the publisher's clock.** The
   recorded time ran 0.3 to 9.5 s behind the wall clock, so Hafnia judged another camera's clip in at least four
   of the six wrong answers, judged a clip's empty tail in at least one NONE, and in every answer lost the first
   1.5 to 3 s of the clip (the BEFORE context the lens exists to provide). M3 therefore measured the pipeline's
   plumbing, not Hafnia. Two more problems have clear mechanisms in the code: the detector's slow background learns a
   lasting change away within about ten minutes (the "fade"), and FrameBridge makes the Recording Server transcode
   eleven full-resolution JPEG streams, which fits the 35 to 62 s alarm actions and the frame discards seen on the
   lens stream.
4. **Product.** Nothing reaches a person who is not at the machine: the owner webhooks go to a stand-in inbox on
   localhost. Outbound HTTPS from the machine works (checked: ntfy.sh and api.telegram.org answer), so phone
   delivery is hours of work, and a polling bot gives two-way confirm/reject from a phone without any inbound
   connectivity.
5. **Budget.** 248 Hafnia requests were used in twelve days, 0 so far today, 500 are available every day. About
   1,500 requests remain before submission. Evaluation has been starved by caution, not by the allowance.

## 2. Where the project stands (2026-10-27, 04:00 UTC)

| Item | State | How checked |
|---|---|---|
| Submission | "about 2026-10-30" (CLAUDE.md, PRODUCT.md, PLAN-C.md); no date, time or form of submission recorded; the participant guide names none | repo grep, guide pages 1-7 |
| Days left | about 3 | |
| Repository | 48 commits, 2026-10-15 to 2026-10-27 03:48 UTC; `main` equals `origin/main`; only run folders untracked | `git log`, `git status` |
| Code | about 9,300 lines: Python (clearway, tier0, lens, hafnia, incident, scripts), one C# bridge, two HTML pages, PowerShell scripts | `wc -l` |
| Tests | none (no `test_*.py`, no `tests/`); correctness rests on the run folders' READMEs | find |
| Front door | no `README.md`; no `setup.ps1` (PLAN-C component 10 "partly"); seven start/setup scripts exist | ls |
| Features | F1-F9 and F12 built; F10 (map) and F11 (person staying at the gate) not started | PRODUCT.md, code |
| Evidence | 60 run folders; M3 (3 h, 11 cameras, 32 answers) analysed but not audited against frames | `run/` |
| Machine | up since 2026-10-24 15:50; lens publisher, MediaMTX, board and owner inbox running since 10-25/10-26; 5.3 GB RAM free; C: 100 GB free | processes, services |
| XProtect | 13 cameras enabled (11 organizer cameras, `test_11`, `lens_1`); no alarm definitions (alarms are raised directly through REST) | MilestonePSTools |
| Gateway | 1 prompt, 0 rules; today's count 0 of 500; 248 requests this month | `GET /api/System/Information` |
| Memory pressure | documented; long runs are started detached | CLAUDE.md |

Against the schedule in `docs/PRODUCT.md`, days 3 to 6 are done. Days 7 to 9 hold: fixes for the three M3 problems,
a shorter check run, M4 on `test_11`, the report, the demo video, `setup.ps1`, the README, and a half day on Smart
Map. That is more than three days of work for one person, and the most visible deliverables (README, setup, video)
are last. Recommendation: drop Smart Map and M4-on-`test_11` (it cannot be shown anyway, licence not cleared), and
reorder so that the README and the setup script exist by the evening of Oct 28, with the demo video on Oct 29.

## 3. Is the project moving towards a concrete goal?

**Yes, since 2026-10-22, and the goal is better than most hackathon goals.** It names a user (city and transit
operators, owner teams, planners), a question, a measurable promise (few false cards, right clip on each card, no
request wasted on repeats), and honesty rules for the demo. The pitch sits in the organizers' own idea list
(`hackathon_qna.png`): intelligent alerting, smart dashboards, video summaries. The judges' stated criteria are
creativity, validity and reproducibility (participant guide, page 5: "the judges must be able to set your solution
up on a fresh machine").

Critical observations:

- **Three directions in the first week.** Plan A (verified accident alarms, Oct 16-21), plan B (near-miss
  observatory, Oct 20-21), plan C (Oct 22), then the product framing (Oct 24). The measurements from A and B still
  hold and are reused, so the time was not wasted, but the product has existed for three days and its core defects
  surfaced only on day 12 (M3). That is the cost of the pivots.
- **Breadth before depth.** F8 (shift summary), F9 (hotspots) and F12 (notifications) were built on Oct 25-26, before
  M3 showed that the lens path judges the wrong footage, that cards never close on a long run, and that XProtect
  takes minutes per alarm with eleven cameras. The board and the summary are polished; the thing they display is not
  yet trustworthy.
- **A differentiator without evidence.** CLAUDE.md lists "results on real footage as well as the synthetic loops"
  among the differentiators. The real crime clips are out of scope and disabled, the AI City video is "internal only,
  licence not cleared", and the CC0 street clips were cut from the plan. As it stands, a judge sees results on the
  organizers' synthetic loops only, which every other entry also has.
- **The answer key is wrong where it matters.** The "stand-in" that scores Hafnia live expects TAMPERING for every
  change on the gate camera, including lit pavement. Ten of Hafnia's twelve gate answers were NONE, most of them
  rightly. "Hafnia agrees with the stand-in on 14 of 32" is not a number to show anyone; the audit against frames,
  which the plan calls for, has not been done for M3.
- **Loops shape every number.** First-card times, recurrence counts, cost per camera-hour and the fade all come
  from 15 to 17 s loops. The docs say so honestly; the demo must say so too.

Verdict: the goal is concrete; the risk is not direction but time, and the order of the remaining work.

## 4. Accuracy of event alarms

### 4.1 M3 re-read from the logs

33 questions, 32 answers, 1 failed (cloud 403, free). 18 of the 33 were asked in the start-up minutes. 11 cards,
4 of them false (gate as PERSON_ON_TRACKS, bin as STALLED_VEHICLE, tracks as STALLED_VEHICLE, roadworks as
STALLED_VEHICLE). Per camera, from `summary.json`:

| Camera | Questions | Answers | Cards | Note |
|---|---|---|---|---|
| vehicle_breakdown_traffic_queue | 3 | 3 STALLED_VEHICLE | 1 | right |
| bin_pushed_over_onto_sidewalk | 6 | 3 OBSTRUCTION, 2 STALLED_VEHICLE, 1 NONE | 3 | one right card, one duplicate, one false (another camera's clip, see 4.2) |
| escooter_left_across_sidewalk | 3 | 2 OBSTRUCTION, 1 NONE | 1 | the NONE was answered on the clip's empty tail (4.2) |
| school_gate_break_in_night | 12 | 10 NONE, 1 TAMPERING, 1 PERSON_ON_TRACKS | 2 | the person trigger is missing (F11), so the lit pavement cost 12 requests; the false card came from the tracks clip (4.2) |
| person_on_railway_tracks | 4 | 2 PERSON_ON_TRACKS, 1 STALLED_VEHICLE, 1 failed | 2 | the false card came from the roadworks clip (4.2) |
| graffiti_on_standing_train | 1 | 1 OBSTRUCTION ("a large tree trunk") | 1 | wrong category, wrong owner |
| busy_street, traffic_flows | 2, 2 | NONE, NONE / NONE, STALLED_VEHICLE | 0, 1 | the roadworks false card |
| highway, condensation, vandalism | 0 | | 0 | the detector reported nothing at the real-camera setting |

The first card came 104 s after the change (median), the alarm 276 s after the card: an operator would have seen
the alarm 6 minutes after a person stepped onto the tracks.

### 4.2 Confirmed: the lens recording's time base (new finding)

The team suspected that three answers described another camera's clip and planned to check `lens_1`'s recording
before it expired today. This investigation did the check (`run/lens-check-20261027/`, frames exported with
MilestonePSTools, tiled beside the frames the publisher actually sent). Result:

| Question | Asked span (UTC) | What the recording held in that span | Offset of recorded time vs wall time |
|---|---|---|---|
| cw-0001 tracks | 14:16:36-43 | the right clip | -0.3 s |
| cw-0004 gate | 14:17:10-14 | 1 s of the gate clip's end, idle, then the tracks clip published at 14:17:21 | -3 s, then -7 s |
| cw-0009 bin | 14:17:59-18:03 | idle, then the breakdown clip published at 14:18:10 | -9.4 s |
| cw-0015 gate | 14:19:05-10 | idle only (answer: "the frame remains completely black") | -8.4 s |
| cw-0022 tracks | 14:20:46-50 | idle, then the roadworks clip published at 14:20:56 | -7.2 s |
| cw-0027 gate | 14:41:16-21 | the clip's last 3 s and idle | -1.5 s |
| cw-0032 e-scooter | 15:14:05-10 | the clip's last 2 s (scooter already gone) and idle; answer NONE | -2.2 s |

Consequences:

- Four of the six wrong answers and one "doubtful" NONE were judgements on other footage. All four false cards are
  explained this way. The card's own clip and snapshot come from the source camera, so the board looked right while
  the verdict came from another camera: the defect is invisible in the demo and visible only in the category.
- The offset was not confined to the start-up minutes: it was still 1.5 to 2.2 s in the quiet hours. Every lens
  answer in M3 lost its first 1.5 to 3 s, which is exactly the 2 s BEFORE margin, and gained idle frames at the end.
  `lens.client.span()` adds 0.3 s because "frames reach the recording about 0.2 s after they are sent" (measured on
  an idle machine on 10-21); under load the sign is the other way.
- The publisher's log is correct (`played.jsonl` spans match the asked spans within 1 s), so the discrepancy is
  between the publisher's clock and the timestamps XProtect's Universal driver gives the frames.

What is known about the mechanism: MediaMTX logged "reader is too slow, discarding N frames" on the lens path
during the preflight and the M3 start-up (bursts of 24 to 327 frames between 14:16:42 and 14:20:52); the reader is
XProtect's RTSP client, so the Recording Server was starved. The publisher resynchronises instead of bursting when it
falls more than 1 s behind, and ffmpeg stamps the raw frames by count, so under load the stream's own time falls
behind the wall clock; the driver evidently follows the stream's time (arrival stamping cannot place content before
it was written). How the offset later shrank from -9 s to -1.5 s without an ffmpeg restart or a new RTSP session is
not known. The remedy does not depend on knowing it.

### 4.3 The fade (mechanism confirmed in code, offline replay still pending)

`tier0/change.py` updates the slow background everywhere except where the fast foreground moves (`step[fg_fast] =
0`). A change that has stopped moving is, by definition, not in the fast foreground, so the slow background learns
it with time constant 600 s. Within about ten minutes a lasting change stops differing from the slow background
(threshold 25) and is no longer "static-changed": no more reports, and the "before" snapshot taken for later
reports already contains the object, so "restored" never fires. That is the M3 observation exactly: object incidents
reported 27 to 37 times in the first half hour and 0 to 6 times per half hour after, cards open all shift, the
e-scooter card open for 10,788 s. A real obstruction that stays is still an obstruction; the background must not
learn it while its change is open. The fix is local: exclude the open changes' boxes (or the ledger's open incident
boxes) from the slow update, and release them when the incident is cleared or rejected.

### 4.4 XProtect's slowness (strongly supported hypothesis, not yet measured)

FrameBridge uses `JPEGLiveSource` with `Width = 0`, so the Recording Server transcodes every camera to
full-resolution JPEG at 10 fps: eleven streams including 1920x1080 and 1280x720, on 4 vCPUs that also record thirteen
streams, serve the gateway's exports and answer the REST calls. The service resizes every frame to 640 px anyway.
`--width` is implemented in the bridge and never passed. Requesting 832 px (the incident cameras' native width)
would cut the transcoding load several times at no cost to those cameras. The Recording Server's CPU share was not
recorded during M3; record it in the next run (`Get-Counter` on `VideoOS.Recorder.Service`). This is the same
starvation that discarded lens frames.

### 4.5 Smaller accuracy observations

- The category list steers Hafnia (known since the pilot). On crops of a kerb with parked cars it says
  STALLED_VEHICLE; on the graffiti crop it saw "a large tree trunk lies across the pavement". The prompt has no
  negatives: parked at the kerb, queued behind another vehicle, or a stationary train are all NONE.
- TAMPERING at the gate is outside Hafnia's domain (1 of 12 here, 0 of 8 on real crime earlier). The product calls
  security a footnote, but the gate still costs the most requests of any camera because its person trigger (F11)
  is not built.
- Asking twice about the same span returns the same words; variety needs a different window or view.
- Every answer in M3 parsed as valid JSON (`json_ok` true in all 32 seen), so the parser is not the problem.

### 4.6 Recommendations, in order of impact per hour of work

1. **Stop routing large spots through the lens.** When the spot's box is large enough that cropping would magnify
   it less than about twice, ask about the source camera directly over the event window (2 s before the change to
   3 s after the report). `incident.verify.ask` already takes any camera and span. Requests then run in parallel
   (the gateway handled five at once in the first benchmark), there is no queue, no time-base problem, and the first
   card should come 15 to 25 s after the change instead of 104 s. The card's clip is still rendered locally from the
   source frames, as now. The pilot showed categories at 30 of 30 on full-loop and event windows of these cameras, so
   nothing is lost on the organizers' scenes.
   **Done later on 2026-10-27** (`clearway/service.py` `DIRECT_BELOW` 2.5, chosen because the pilot's full-frame
   answers were right down to 2.7x; `run/clearway-live-20261027T081803Z-direct`, 6 requests): the two direct cards
   came 13.3 and 13.4 s after the change, the four lens cards 21.8 to 47.2 s; 6 of 6 categories right, the direct
   summaries right in every claim. On M3's 33 questions the rule would have sent 13 direct, including both wrong-scene
   answers that came from large spots. A failed direct ask falls back to the lens once.
2. **Make the lens self-verifying where it is still used (small spots, `test_11`).** Burn a machine-readable
   timecode into every lens frame (a row of black and white blocks is enough), read one recorded frame back at the
   asked start before asking (MilestonePSTools `Get-Snapshot`, or a 60-line MIP tool next to FrameBridge), and shift
   the span by the measured offset. Cheap first experiment: run the publisher's ffmpeg with
   `-use_wallclock_as_timestamps 1` on the raw input and repeat the check under load. Keep the idle gap between
   clips longer than the largest offset seen, so a wrong span can only pull in idle frames, never a neighbour.
   **Done later on 2026-10-27** (`lens/code.py`, `lens/clock.py`, `lens/publisher.py`; `run/lens-check-20261027T094716Z`
   quiet with the recording read back, `run/lens-check-20261027T095146Z-load-wallclock` the loaded pair; no requests):
   the recording's frames decode to the same offset as the live feed (+0.02 s quiet), so the span is read back live
   from `lens_1`'s frames in the service's FrameBridge, no export needed. Under the eleven-camera load the
   count-stamped stream fell to 9.4 s behind with no MediaMTX discard at all: the publisher's own dropped frames,
   stamped by count, are the cause, and its catch-up bursts explain the recovery. With wall-clock stamping the same
   load gives +0.4 to +1.4 s. Every lens span is now measured and marked verified or not; a clip with no frame seen
   or a hole in the feed is played again. The idle gap stayed at 2 s: with the span measured it only needs to cover
   the whole-second rounding, and neighbouring frames inside a span are checked.
3. **Freeze the slow background inside open changes** (4.3). Then re-run one looped camera for 30 minutes offline
   with `scripts/eval_change.py` to confirm reports keep coming and spots keep closing.
   **Done later on 2026-10-27** (`tier0/change.py`; `run/change-fade-before` and `-after3`, 30-minute replays of the
   bin and e-scooter loops): before, 16 of 119 loops caught on both cameras and silence after seven minutes; after,
   119 of 119 on both with reports steady to the end. Freezing the open changes' boxes alone was not enough: the
   e-scooter stuck after 48 loops because the slow background had been learning the change's own precursor (the
   rider standing before the hold-back let the report through), so each loop's before snapshot carried a growing
   ghost until the empty spot no longer matched it, and the one open change then swallowed every later blob at its
   spot. Static-changed pixels not yet reported are now left unlearnt until they persist 60 s, "restored" is judged
   relative to the change's own contrast, and motion is judged frame to frame. Closing a change whose spot looks
   like neither its before nor itself (with re-baselining) was tried and switched off: it split every evolving
   incident into its states. `release()` lets a change the ledger dismissed or the operator rejected be learnt, and
   sets the background back to the look before when that spot is restored; `clearway/service.py` calls it.
4. **Pass `--width 832` to FrameBridge** and record the Recording Server's CPU in the next live run (4.4).
   **Done later on 2026-10-27, with a different finding** (`run/clearway-dry-20261027T121705Z-width0/README.md`
   and the two runs after it): the Recording Server uses under 2 % of the machine in every run; the hypothesis of
   4.4 was wrong. The MIP .NET library decodes the streams and makes the JPEGs inside FrameBridge (22-28 % of the
   machine), and the service itself takes more than two of the four cores (56-62 %), so the machine is saturated
   and FrameBridge delivers 4.3-4.7 of each camera's 10 fps; M3's discards were this saturation. `--width 832`
   (now the default) gains a tenth; the detector on every second frame (`DETECT_EVERY` 2, the default) gains far
   more: 7.5 frames per camera per second, the lens feed at 54 % coverage with no replay, its latency 0.23 s
   instead of 0.79. The CPU shares stay in every run's health record.
5. **Spend the allowance on confidence.** M3 used 1 request per camera-hour; 500 a day covers 11 cameras forty
   times over. For High-priority categories (person on the tracks, collision, stalled vehicle) ask twice with two
   views (the event window on the source camera and a crop, or two windows) and raise High only when both agree;
   otherwise raise a Low "unverified" alarm for the operator. This is the single cheapest cut to false High alarms.
6. **Prompt.** (**Negatives done later on 2026-10-27**: each definition says what it is not; the clean run's 14
   spans asked again, `scripts/reask.py`: the graffiti filed OBSTRUCTION became DAMAGE, the twelve right answers
   stayed; the summary-before-category variant did not fix it. The confidence field and the AlertValidation trial
   are still open.) Add explicit negatives (see 4.5), a `confidence` field whose low values feed the existing 30 s
   escalation instead of a card, and a one-line orientation ("a fixed CCTV camera; the first two seconds show the
   spot before the change"). Try Hafnia's trained AlertValidation shape and system prompt (noted in
   `docs/PLAN-near-miss.md`) on 20 to 30 requests; the gateway's Advanced Settings may be changed.
7. **Audit against the clip that was sent, not the stand-in.** The spool AVIs are the ground truth of what was
   sent; after fix 1 or 2 they are also what was seen. Score every answer against them (Opus as judge, as the plan
   says) and retire the stand-in as "expected" for the gate.
8. **One clean re-run** after fixes 1 to 4: eleven cameras, two hours, alarms and notifications on, the Recording
   Server's CPU logged, every answer audited. Those are the numbers for the report; M3's are not.

## 5. Product value

### 5.1 What a user gets today

An owner board in its own Edge window (Smart Client's HTML item cannot show it on this machine; the team proved
that carefully), one XProtect alarm per incident with a snapshot and two bookmarks, confirm/reject on the card
that teaches the memory, a shift summary with hotspots, and JSON webhooks per owner to a stand-in inbox on
127.0.0.1. All of it stops at the machine. After a reboot four processes must be started by hand. A judge who
clones the repository finds no README.

### 5.2 Getting alarms to a phone (the question asked)

Facts checked on 2026-10-27: the machine reaches the internet over HTTPS (ntfy.sh answered 200, api.telegram.org
302); nothing can reach the machine from outside except over Tailscale; the XProtect Mobile Server is installed and
running; `clearway/notify.py` already signs and retries JSON webhooks per owner with the URL from an environment
variable.

| Channel | What it gives | Work | Needs | Judgement |
|---|---|---|---|---|
| ntfy (ntfy.sh or self-hosted) | a push on any phone with the ntfy app, title, priority, snapshot attached, a tap-to-open link | 2-3 hours: a target type in `notify.py` (POST with Title/Priority/Attach headers), topic name from an env var | nothing else; a free public topic is a secret, so keep it out of git | do first: real pushes in the demo today |
| Telegram bot | the same, plus inline **Confirm / Reject** buttons; the machine polls `getUpdates`, so verdicts come back without inbound connectivity and land in `operator.jsonl` like the board's | half a day | a bot token in an env var | the strongest product step: F7 from the phone, which the TODO in `notify.py` says is impossible while the board is local; it is not |
| Slack / Teams incoming webhooks | a message in the owner team's channel | 2 hours each for the message format | a workspace | fine, one-way; do after the two above |
| XProtect Mobile push | native Milestone: the alarm appears in the XProtect Mobile app | unknown, half a day to find out | the Mobile Server's notifications enabled, the phone on the hackathon Tailscale network to register with port 8081, and confirmation that alarms raised through REST trigger pushes | worth a one-hour spike because judges are Milestone; stop if the phone cannot register |
| XProtect e-mail (notification profile) | mail with a snapshot | 1-2 hours | an SMTP account; alarms raised via REST do not pass an alarm definition, so a rule would need a user-defined event first | lowest value |

Recommendation: ntfy on Oct 27 (so the demo shows a phone buzzing when the person steps onto the tracks), the
Telegram bot on Oct 28 if the core fixes are in, Mobile push only as a spike.

Done later on 2026-10-27: the ntfy channel, with Confirm / Reject buttons that reply through a second ntfy topic the
service follows, so the Telegram bot is no longer needed for two-way (`docs/PRODUCT.md` F12,
`run/clearway-dry-20261027T044611Z-ntfy`). ntfy.sh's real limits per IP are 250 messages and 20 MB of attachments a
day, 2 MB per attachment; the notifier guards them.

### 5.3 Other product gaps, ranked

1. **README and `setup.ps1`.** Reproducibility is a stated criterion and the repository has no entry point. The
   README should open with the board, the ten-minute path to a running demo on a fresh machine (Python, the venv
   with pinned torch, the .NET SDK for FrameBridge, MediaMTX via `setup_lens.ps1`, the lens camera, the start
   scripts), the request budget of the demo, and the honesty notes. The setup script should create what is scripted
   today in pieces and print the manual steps it cannot do.
2. **Auto-start and health.** Scheduled tasks (or NSSM services) for the publisher, the service, the board and the
   inbox, with restart on failure and one `/health` page; otherwise a rebuilt machine is a dead demo.
3. **Demo video.** Optional for the organizers, decisive for "creativity" judges who will not install anything.
   Three minutes, the story in `docs/PRODUCT.md` is good; record it after fix 1 so the cards come in seconds.
4. **A real-footage number.** Inject the three CC0 street clips (one Recording Server restart, scripted) and run
   two hours at the real-camera setting: "false cards per hour on a real street" is the one claim that separates
   this entry from the others on the same loops. Drop `test_11` from the report instead; it cannot be shown.
5. **Presence inside Smart Client.** The toast sample in the kit (`xprotect-plugins`, Smart Client Toast) would pop
   each new card inside Smart Client with a day of C#; a nice-to-have after the above.
6. **Drop F10 (map) and F11 (gate dwell)** for this submission; say so in the README.

### 5.4 A plan for the three days (opinion)

| Day | Work | Requests |
|---|---|---|
| Oct 27 | Direct asks for large spots (4.6 #1); FrameBridge width (#4); freeze the background (#3) with the 30-min offline check; ntfy pushes; a 30-minute live check on six cameras, audited against the sent clips | 60 |
| Oct 28 | Two-view agreement for High alarms (#5) and prompt negatives (#6); the clean two-hour run on eleven cameras with CPU logged (#8); README and `setup.ps1`; Telegram bot if time allows | 200 |
| Oct 29 | Demo video; the report in operator terms with the audited numbers; CC0 street run if the restart is acceptable; final push | 100 |
| Oct 30 | Spare; submission | reserve |

## 6. Evidence produced by this investigation

- `run/lens-check-20261027/`: `README.md` (the offsets table), `export.ps1`, `sheets.py`, and `frames/*.jpg` (seven
  contact sheets, git-ignored as footage).
- Checks run, all read-only: `git log`/`status`; process, service, memory and disk listing; MilestonePSTools camera,
  alarm-definition and rule listing; gateway `System/Information`, `Prompts`, `Rules`, `Summaries`; the M3
  `service.jsonl` against `run/lens/played.jsonl` (asked vs played spans, all 33 within 1 s); `Get-Snapshot` on
  `lens_1` for seven spans; `curl` HEAD to ntfy.sh and api.telegram.org; the participant guide's seven pages
  extracted from the PDF.
- Not done: an offline replay for the fade, a CPU measurement of the Recording Server, any Hafnia request.
