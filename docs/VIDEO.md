# The demonstration video (required for the submission: under 3 minutes, public or unlisted)

Status: **storyboard, 2026-10-27.** The portal closes 2 November 12:00 CET (extended from 1 November); the video is planned for Oct 29.
**The portal form (read 2026-11-01) wants the video under 3 minutes, not the 3-5 the hackathon page recommended: the
storyboard was cut on 2026-11-01 from about 4 minutes to 2:40 with the synthetic voice (`make_video.py --list`).** Criteria it
serves (the hackathon page): real-world value, use of Hafnia VLM and XProtect with results fed back into XProtect,
technical execution, functionality, demo and user experience. The pitch is the one in `PRODUCT.md`, "What sells
it": optimization around the model, shown with numbers; the obstruction categories get one line.

## Storyboard (2:43 with the Kokoro voice and the captures of 2026-11-02; cut 2026-11-01 from about 4 minutes)

The narration below is the script in `scripts/make_video.py` (`SCENES`), the one to record; the times in the
table are the 2026-11-01 cut's and run about 6 s early from scene 6 on (the phone scene grew to 17 s; `--list`
prints the current lengths), each scene its narration plus 0.8 s or its least length. What was cut: the exact-clip
and one-sentence-verdict phrasing, the comparison's "to be fair" sentence (the card's foot keeps it), "a large spot
is asked about on its own recording", the setup script in the numbers narration (the card's foot keeps it); what
came in: the known limit, one sentence on the numbers scene.

| # | Time | On screen | Narration | Made from |
|---|---|---|---|---|
| 1 | 0:00-0:14 | Title card: **Clearway**. "What is blocking a public way right now, whose job is it, and how long has it been there?" | Clearway watches a city's XProtect cameras for what blocks a public way, asks Hafnia VLM once per incident, and turns the answer into one alarm, one card for its owner, one push to a phone. | card |
| 2 | 0:14-0:19 | The eleven cameras in Smart Client (the All cameras view). | Eleven cameras, six with a staged incident. | screen capture (`captures/cameras.mp4`, filmed 2026-11-02 with `scripts/capture_screen.py`) |
| 2b | 0:19-0:26 | A terminal: the service's first lines from the filmed run, the planned request count before anything starts. | The service says what it will spend before it starts: at most this many of the day's five hundred. | card `terminal.html` with `captures/plan.txt` (the run's own first lines) |
| 3 | 0:25-0:41 | The owner board filling: columns per owner, cards appearing 20 seconds after each change; one card opened. | Within a minute every incident has a card in its owner's column: the truck for traffic operations, the person on the tracks for rail control, the bin for street services, each with the clip Hafnia judged, its verdict, the time open and its alarm. | board footage: the second filmed run replayed at its own pace and filmed at 6x (`replay_board.py`, `record_board.py`; `captures/board.mp4`) |
| 4 | 0:41-0:52 | The stalled truck's clip as the board served it, with Hafnia's verdict. | The clip for the stalled truck as Hafnia saw it, and the verdict: a silver pickup stalls in the lane with its door open and smoke rising, blocking traffic. | `captures/clip.mp4` (there) |
| 5 | 0:52-1:05 | The alarms as XProtect holds them, read back through its REST API: time, priority, state, name (category, owner), camera, Hafnia's summary; the snapshot attached to the stalled-vehicle alarm; a foot on the close and reopen rule. | The same incident is an XProtect alarm with the category, the owner, Hafnia's summary, a snapshot and a bookmark. It closes itself when the spot clears and reopens if it happens again. | card `alarms.html` with `captures/alarms.txt` (the API's records of the filmed runs) and `captures/alarm-snapshot.jpg`. A Smart Client capture (`smartclient.mp4`) was planned: its Alarm Manager list stayed blank on this machine on 2026-11-02 (the quick filters counted New 3, Closed 15; the list below showed 0 rows under every filter, for the author and for the script), so the records are shown as the API returns them |
| 6 | 1:05-1:23 | The phone, 17 s: the push arriving in the shade, the ntfy app with Hafnia's text and the snapshot, the tap on Confirm, the acknowledgement push. | The owner gets a push with two buttons. A tap reaches the system in under a second and teaches it: a rejected look at that spot is not asked about again. | the author's phone screen recording during the first filmed run (`captures/phone.mp4`, the app header with the topic name cropped off) |
| 7 | 1:16-1:33 | "How it decides": the change detector stills, the verdict memory, the magnified crop of the 30-pixel crash the full frame called NONE. | Nothing asks Hafnia on a timer. A change detector notices what stayed changed, a memory skips what was already judged, and a small spot is enlarged on a magnifier camera of our own: a thirty-pixel crash the full frame called nothing is named a collision. | card `decides.html` (stills from `docs/walkthrough/`) |
| 8 | 1:33-1:48 | "Measured": the frame code strip and the time base, the fade replay before and after, the alarm latency before and after. | All of it was measured, and three faults were found and fixed: the magnifier camera's clock, now proven by a code in every frame; a detector that faded after seven minutes; alarms slowed by our own load. | card `measured.html` |
| 9 | 1:48-2:06 | The numbers card: 33 requests for three hours, 0 false cards in the clean run, 20-42 s to a card; the foot: the known limit on real streets, one setup script. | Three hours on eleven cameras: thirty-three requests, one per camera-hour, and the next run had no false cards. On real streets it had never seen, waiting cars became false cards: the known limit. Everything is in the repository. | card `numbers.html` |
| 10 | 2:06-2:26 | The comparison card: 60 against 1 request per camera-hour; 45 minutes until the plain way has spent the day's 500; 0 of 6 plain answers that put the person on the tracks; the foot: the smashed window the plain way reports and Clearway never asks about. | The plain way asks every camera once a minute: sixty requests per camera-hour, the day's five hundred gone in forty-five minutes. Clearway spent one per camera-hour. Six times out of six, the full frame left the person on the platform; the magnified clip put them on the tracks. | card `compare.html`; measured in `run/vanilla-20261029T0714Z-compare` (66 requests, 2026-10-29) against the 10-27 run and the 10-26 shift |
| 11 | 2:26-2:34 | The shift summary page. | At the end of a shift, the summary: incidents by owner, how fast, where it keeps happening. | `render/summary-final.png`: the second filmed run's `/summary`, rendered through a board on that run folder with a 25 s page budget (the 10-27 run's logs are gone from the repository, so the board on port 8766 renders an empty page now) |
| 12 | 2:34-2:40 | Close: the repository. | Clearway keeps public ways clear, and spends the model's attention only where it earns it. | card `close.html` |

## Additions decided 2026-10-29 (not in the cut yet)

- **Vanilla against Clearway, a rough comparison** (the user's wish): **measured 2026-10-29**
  (`run/vanilla-20261029T0714Z-compare/README.md`, "The comparison"): the organizers' example question asked about
  every camera once a minute for six minutes, 66 requests, read one by one, against Clearway's 20-minute run of
  10-27 and the three-hour shift of 10-26 on the same loops. Scene 7b and `cards/compare.html` carry it. The
  request economy is the point; the accuracy side is stated as counts of answers, not as a rate. Lesson from the
  same morning: do not run the poller beside a live run on this machine (the CPU saturates and the detector starves;
  that run's Clearway numbers are in the README as a degraded data point, not the reference).
- **The held-out check** (`run/holdout-20261029`): one line on the numbers card, as the known limit and the next
  fix (31 of 39 hard negatives on real streets became false cards). **On the card and in the narration since
  2026-11-01.** Its CC0 clips may be shown, and `scripts/fetch_footage.py` makes the check reproducible on a judge's
  machine.

## Production

`scripts/make_video.py` holds the scene list (ids, narration, visuals, least lengths) and builds the video:

```powershell
.venv\Scripts\python.exe scripts\make_video.py --render-cards --tts --build    # cards, scratch narration, the cut
.venv\Scripts\python.exe scripts\make_video.py --list                          # scenes, visuals, lengths
```

- **Cards** (`docs/video/cards/*.html`, committed; `card.css` uses fonts installed on Windows, so a render needs no
  network): rendered to 1920x1080 PNG in `docs/video/render/` with Edge headless. `placeholder.html?t=...` stands in
  for a capture that is not there yet.
- **Board footage**: `scripts/record_board.py` renders the board headless once a second (no desktop session needed)
  and makes `docs/video/board/board.mp4`; copy it to `docs/video/captures/board.mp4`. **Beside a live run on eleven
  cameras it does not work** (2026-11-02, twice): the machine is saturated and each headless Edge render takes 3 s
  or times out, so the frames stop before the first card. What works: `scripts/replay_board.py <run>` after the
  run, on the idle machine: it copies the run's snapshots, clips and scene images into `run/clearway-replay-<UTC>`,
  starts a board on port 8767 following it and appends the run's log lines at their own pace with every time
  stamp shifted to the present, so the board fills as it did (cards, Hafnia's summaries, the owners' verdicts,
  "time open"); `record_board.py --url http://127.0.0.1:8767/ --every 1 --speed 6` films that. The footage is the
  run's own data replayed, not the run itself. Without it the scene shows the board's final state
  (`render/board-final.png`).
- **Captures by hand**, into `docs/video/captures/`: `cameras.mp4` (Smart Client's All cameras view, filmed from
  this desktop with `scripts/capture_screen.py`: `place` sizes Smart Client to the largest 16:9 region of the
  screen, `record` films it with ffmpeg's gdigrab, `cut` trims and scales it), `smartclient.mp4` (the Alarm
  Manager: the alarm, the bookmark, the close), `phone.mp4` (the author's phone, screen-recorded in the ntfy app
  during the run: the push in the shade, the message with Hafnia's text and the snapshot, the tap on Confirm, the
  acknowledgement; the app's header is cropped off because it shows the topic name, which is the credential).
  `clip.mp4` is the stalled truck's clip as the board served it (`/clips/cw-0003.mp4`), already there.
- **Narration**: `docs/video/voice/<scene id>.wav` (the author's voice, one take per scene, the script in
  `make_video.py`) takes precedence; otherwise synthetic speech (`--tts`) into `docs/video/audio/`: **Kokoro**
  (`hexgrad/Kokoro-82M`, Apache-2.0, an open model that runs on the CPU at about real time) through
  `scripts/narrate.py` in its own environment `.venv-tts` (`requirements-tts.txt`; `--engine kokoro`, the default,
  `--voice af_heart` unless another is chosen, `--speed`), or Windows text-to-speech (`--engine sapi`, Zira or David:
  the machine-sounding scratch track the first cuts were timed with, replaced on 2026-11-01). `narrate.py --samples`
  speaks the title line in eight Kokoro voices into `docs/video/audio/samples/` to choose one by ear. Kokoro's
  phonemizer reads "Hafnia" and "XProtect" as expected; "V L M" is spelled out in the script. A scene lasts as long
  as its narration plus 0.8 s, at least its `min_s`; Kokoro's pace is SAPI's within a second per scene (2:35 in all).
- **Assembly**: one segment per scene in `docs/video/segments/` (1920x1080, 30 fps, H.264, AAC), concatenated into
  `docs/video/clearway.mp4`. A video shorter than its narration loops; a capture smaller than 1000 px wide is shown
  at twice its size, not blown up. The poster (`docs/video/poster.jpg`, the title frame) is
  committed; the finished cut is not (removed 2026-11-02: the README's player is GitHub's upload of it), and
  everything else under `docs/video/` but the cards and this file is git-ignored (camera footage, intermediate
  renders).
- **Size**: the assembler's output (CRF 20) is about 14 MB for 2:43; the uploaded `clearway.mp4` is that file
  re-encoded at CRF 26 with 96 kbit/s audio (8.5 MB) so it stays under GitHub's 10 MB attachment limit for the
  README's inline player; the CRF 20 cut is kept beside it as `clearway-hq.mp4` (git-ignored):
  `ffmpeg -i clearway-hq.mp4 -c:v libx264 -preset slow -crf 26 -c:a aac -b:a 96k -movflags +faststart clearway.mp4`.
- **Footage shown**: only the organizers' cameras (on every machine), the three CC0 street clips
  (`scripts/fetch_footage.py`) and our own pages; never `test_11` (the AI City licence forbids redistribution).
- **Requests**: the live run recorded for scenes 2-5 costs about 15 (today's count 41 of 500 after the day's work).

**State (2026-10-27):** a first cut of 2.6 minutes exists with the scratch narration, the cards, the walkthrough
stills, the stalled truck's clip, the board's and the summary's final state, and placeholders for the three captures
by hand. (Done on 2026-11-02, see the end of this paragraph; the author's own narration is the one thing not made,
Kokoro's voice stands.) **2026-10-29:** the comparison scene added (7b); the board recording
made beside the comparison run is 6 s long (the recorder starved with the poller running) and is not usable: film
the board again during the live run for scenes 2-6, with nothing else asking Hafnia at the time. **2026-11-01:** the
narration cut for the portal's 3-minute limit: 2:40 with the synthetic voice, so a reading up to 12 % slower still
fits; if the recorded voice runs longer, the comparison's second sentence and the measured scene's list are the
next cuts. Later that day the Windows voice (plainly machine-made) was replaced by Kokoro, an open model, in the
same pace: the cut is 2:35 (`clearway.mp4`; the SAPI cut kept beside it as `clearway-sapi.mp4`, git-ignored),
voice `af_heart` until one is chosen from the samples. The author's own recording still takes precedence per
scene if made. **2026-11-02, 01:00-02:00 UTC, the placeholders filled:** the cameras scene filmed in Smart Client;
scene 2 split so the terminal card shows the filmed run's own first lines; two live runs of 10 minutes on the
eleven cameras (`run/clearway-live-20261102T012136Z` and `...T013258Z`, 15 requests each, 12 answers each,
today's count 30 after; a first attempt, `...T011422Z`, died at FrameBridge's start without a request and was not
explained: the same launch worked twice after) with alarms and phone pushes, the author tapping Confirm / Reject
on the phone (six verdicts in each run, each applied in XProtect within 0.1 s); the phone scene from the author's screen
recording (17 s); the board scene from the second run replayed (`scripts/replay_board.py`), because filming the
live board starved beside eleven cameras.
