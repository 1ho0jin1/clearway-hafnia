# The demonstration video (required for the submission: 3-5 minutes)

Status: **storyboard, 2026-10-27.** The portal closes 2 November 12:00 CET (extended from 1 November); the video is planned for Oct 29. Criteria it
serves (the hackathon page): real-world value, use of Hafnia VLM and XProtect with results fed back into XProtect,
technical execution, functionality, demo and user experience. The pitch is the one in `PRODUCT.md`, "What sells it
against the field": optimization around the model, shown with numbers; the obstruction categories get one line.

## Storyboard (about 4 minutes)

| # | Time | On screen | Narration (draft) | Made from |
|---|---|---|---|---|
| 1 | 0:00-0:15 | Title card: **Clearway**. "What is blocking a public way right now, whose job is it, and how long has it been there?" | Clearway watches a city's XProtect cameras for things that block or endanger a public way, asks the Hafnia VLM once about each, and turns the answer into one alarm, one card for its owner, and one push to a phone. | card |
| 2 | 0:15-0:35 | The eleven cameras in Smart Client (a view), then the service starting in a terminal: the planned request count printed before anything starts. | Eleven cameras, six of them with a staged incident each. The service announces what it will spend before it starts: at most this many requests of the day's five hundred. | screen capture |
| 3 | 0:35-1:15 | The owner board filling: columns per owner, cards appearing 20 seconds after each change; one card opened: the clip Hafnia judged, its summary, the alarm state, the time open. | Within a minute every incident has a card in its owner's column: the stalled truck for traffic operations, the person on the tracks for rail control, the tipped bin for street services. Each card shows the exact clip Hafnia judged and its one-sentence verdict. | board footage (headless render, 1 frame per second) or screen capture |
| 4 | 1:15-1:40 | Smart Client's Alarm Manager: the alarm named with the category, the owner and Hafnia's summary; the bookmark on the camera; the alarm closing by itself when the spot clears. | The same incident is an XProtect alarm, with a snapshot and a bookmark on the camera, closed by itself when the spot clears and reopened when it happens again. | screen capture (Smart Client) |
| 5 | 1:40-2:00 | The phone: the push with the snapshot and Confirm / Reject; a tap; the board's card marked confirmed within a second. | The owner gets a push with two buttons. A tap reaches the ledger in under a second, and teaches it: a rejected look at that spot is not asked about again. | phone screen recording |
| 6 | 2:00-2:50 | "How it decides": the change detector stills (something arrived and stopped; a person held back; fog and light not objects), the verdict memory, the lens: the 30-pixel crash the full frame called NONE and the crop named; the frame code strip and the measured time base; the fade replay (silent after 7 minutes, steady after the fix). | Nothing asks Hafnia on a timer. A change detector notices what stayed changed; a memory skips what was already judged; a small spot is cropped and enlarged on a lens camera of our own, and the lens frames carry a code that proves which seconds the recording holds. Every one of these was measured, and two of them were found wrong and fixed on the way. | stills from `docs/walkthrough/`, cards with numbers |
| 7 | 2:50-3:30 | The numbers card: M3 three hours (33 requests, 11 cards, the 4 false traced to one cause), the clean run (14 requests, 7 cards, none false, 20-42 s), one request per camera-hour, every run folder with its README, one setup script. | Three hours on eleven cameras cost 33 requests, one per camera-hour. The four false cards it produced were traced to one cause and fixed; the next run had none. Everything is in the repository: the runs, their numbers, and a single setup script for a fresh machine. | card |
| 7b | 3:30-4:05 | The comparison card (`compare.html`): 60 against 1 request per camera-hour; 45 minutes until the plain way has spent the day's 500 on eleven cameras; 0 of 6 plain answers that put the person on the tracks; the foot: the smashed window the plain way reports and Clearway never asks about. | The plain way asks every camera on a timer. Once a minute on eleven cameras is sixty requests per camera-hour, the day's five hundred gone in forty-five minutes, and a paragraph to read per request. Clearway spent one request per camera-hour over a three-hour shift. Six times out of six, the plain way's full frame left the person on the platform; the magnified clip put them on the tracks. To be fair, the plain way reports the smashed window every minute, and Clearway never asks about it, because nothing stays changed. | card; measured in `run/vanilla-20261029T0714Z-compare` (66 requests, 2026-10-29) against the 10-27 run and the 10-26 shift |
| 8 | 4:05-4:25 | Close: the repository, what is next (owners' own channels, the application layer). | Clearway keeps public ways clear, and spends the model's attention only where it earns it. | card |

## Additions decided 2026-10-29 (not in the cut yet)

- **Vanilla against Clearway, a rough comparison** (the user's wish): **measured 2026-10-29**
  (`run/vanilla-20261029T0714Z-compare/README.md`, "The comparison"): the organizers' example question asked about
  every camera once a minute for six minutes, 66 requests, read one by one, against Clearway's 20-minute run of
  10-27 and the three-hour shift of 10-26 on the same loops. Scene 7b and `cards/compare.html` carry it. The
  request economy is the point; the accuracy side is stated as counts of answers, not as a rate. Lesson from the
  same morning: do not run the poller beside a live run on this machine (the CPU saturates and the detector starves;
  that run's Clearway numbers are in the README as a degraded data point, not the reference).
- **The held-out check** (`run/holdout-20261029`): one line on the numbers card, as the known limit and the next
  fix (31 of 39 hard negatives on real streets became false cards). Its CC0 clips may be shown, and
  `scripts/fetch_footage.py` makes the check reproducible on a judge's machine.

## Production

`scripts/make_video.py` holds the scene list (ids, narration, visuals, least lengths) and builds the video:

```powershell
.venv\Scripts\python.exe scripts\make_video.py --render-cards --tts --build    # cards, scratch narration, the cut
.venv\Scripts\python.exe scripts\make_video.py --list                          # scenes, visuals, lengths
```

- **Cards** (`docs/video/cards/*.html`, committed; `card.css` uses fonts installed on Windows, so a render needs no
  network): rendered to 1920x1080 PNG in `docs/video/render/` with Edge headless. `placeholder.html?t=...` stands in
  for a capture that is not there yet.
- **Board footage**: `scripts/record_board.py --minutes 10 --speed 4` beside a live run renders the board headless
  once a second (no desktop session needed) and makes `docs/video/board/board.mp4`; copy it to
  `docs/video/captures/board.mp4`. Without it the scene shows the board's final state (`render/board-final.png`,
  from the board instance on port 8766 that shows the clean live run).
- **Captures by hand**, into `docs/video/captures/`: `cameras.mp4` (Smart Client's view of the eleven cameras and the
  terminal starting the service), `smartclient.mp4` (the Alarm Manager: the alarm, the bookmark, the close),
  `phone.mp4` (the push, the tap, the card confirmed). `clip.mp4` is the stalled truck's clip as the board served it
  (`/clips/cw-0003.mp4`), already there.
- **Narration**: `docs/video/voice/<scene id>.wav` (the author's voice, one take per scene, the script in
  `make_video.py`) takes precedence; otherwise Windows text-to-speech (`--tts`, Zira by default) into
  `docs/video/audio/`. A scene lasts as long as its narration plus 0.8 s, at least its `min_s`.
- **Assembly**: one segment per scene in `docs/video/segments/` (1920x1080, 30 fps, H.264, AAC), concatenated into
  `docs/video/clearway.mp4`. A video shorter than its narration loops; a capture smaller than 1000 px wide is shown
  at twice its size, not blown up. Everything but the cards and this file is git-ignored (camera footage).
- **Footage shown**: only the organizers' cameras (on every machine), the three CC0 street clips
  (`scripts/fetch_footage.py`) and our own pages; never `test_11` (the AI City licence forbids redistribution).
- **Requests**: the live run recorded for scenes 2-5 costs about 15 (today's count 41 of 500 after the day's work).

**State (2026-10-27):** a first cut of 2.6 minutes exists with the scratch narration, the cards, the walkthrough
stills, the stalled truck's clip, the board's and the summary's final state, and placeholders for the three captures
by hand. Still to do: the recorded live run with the board filmed and the three captures, the author's narration,
then the cut again (expected 3.5-4 minutes). **2026-10-29:** the comparison scene added (7b); the board recording
made beside the comparison run is 6 s long (the recorder starved with the poller running) and is not usable: film
the board again during the live run for scenes 2-5, with nothing else asking Hafnia at the time.
