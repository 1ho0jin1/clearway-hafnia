# Clearway demo video: the narration script, scene by scene

Record one take per scene and save it as `voice/<id>.wav` (any sample rate, mono or stereo; WAV).
`scripts/make_video.py --build` uses `docs/video/voice/<id>.wav` when it exists and the Kokoro track in
`audio/<id>.wav` otherwise. A scene lasts as long as its narration plus 0.8 s, at least its least length;
a longer narration simply stretches the scene (a video loops, a card holds). The whole cut must stay under
3:00 (the portal's limit); it is 2:43 with the synthetic voice, so about 17 s of slack in all.

| # | id | Save as | Least length | Now (Kokoro) | On screen | Narration |
|---|---|---|---|---|---|---|
| 1 | title | `voice/title.wav` | 8 s | 14.2 s | `docs\video\render\title.png` (image) | Clearway watches a city's XProtect cameras for what blocks a public way, asks Hafnia V L M once per incident, and turns the answer into one alarm, one card for its owner, one push to a phone. |
| 2 | cameras | `voice/cameras.wav` | 5 s | 5.0 s | `docs\video\captures\cameras.mp4` (video) | Eleven cameras, six with a staged incident. |
| 3 | plan | `voice/plan.wav` | 5 s | 6.7 s | `docs\video\render\terminal-plan.png` (image) | The service says what it will spend before it starts: at most this many of the day's five hundred. |
| 4 | board | `voice/board.wav` | 16 s | 16.0 s | `docs\video\captures\board.mp4` (video) | Within a minute every incident has a card in its owner's column: the truck for traffic operations, the person on the tracks for rail control, the bin for street services, each with the clip Hafnia judged, its verdict, the time open and its alarm. |
| 5 | clip | `voice/clip.wav` | 8 s | 10.7 s | `docs\video\captures\clip.mp4` (video) | The clip for the stalled truck as Hafnia saw it, and the verdict: a silver pickup stalls in the lane with its door open and smoke rising, blocking traffic. |
| 6 | smartclient | `voice/smartclient.wav` | 10 s | 13.2 s | `docs\video\render\alarms-smartclient.png` (image) | The same incident is an XProtect alarm with the category, the owner, Hafnia's summary, a snapshot and a bookmark. It closes itself when the spot clears and reopens if it happens again. |
| 7 | phone | `voice/phone.wav` | 17 s | 17.0 s | `docs\video\captures\phone.mp4` (video) | The owner gets a push with two buttons. A tap reaches the system in under a second and teaches it: a rejected look at that spot is not asked about again. |
| 8 | decides | `voice/decides.wav` | 14 s | 17.8 s | `docs\video\render\decides.png` (image) | Nothing asks Hafnia on a timer. A change detector notices what stayed changed, a memory skips what was already judged, and a small spot is enlarged on a magnifier camera of our own: a thirty-pixel crash the full frame called nothing is named a collision. |
| 9 | measured | `voice/measured.wav` | 12 s | 14.6 s | `docs\video\render\measured.png` (image) | All of it was measured, and three faults were found and fixed: the magnifier camera's clock, now proven by a code in every frame; a detector that faded after seven minutes; alarms slowed by our own load. |
| 10 | numbers | `voice/numbers.wav` | 12 s | 16.5 s | `docs\video\render\numbers.png` (image) | Three hours on eleven cameras: thirty-three requests, one per camera-hour, and the next run had no false cards. On real streets it had never seen, waiting cars became false cards: the known limit. Everything is in the repository. |
| 11 | compare | `voice/compare.wav` | 14 s | 18.4 s | `docs\video\render\compare.png` (image) | The plain way asks every camera once a minute: sixty requests per camera-hour, the day's five hundred gone in forty-five minutes. Clearway spent one per camera-hour. Six times out of six, the full frame left the person on the platform; the magnified clip put them on the tracks. |
| 12 | summary | `voice/summary.wav` | 7 s | 7.0 s | `docs\video\render\summary-final.png` (image) | At the end of a shift, the summary: incidents by owner, how fast, where it keeps happening. |
| 13 | close | `voice/close.wav` | 6 s | 6.3 s | `docs\video\render\close.png` (image) | Clearway keeps public ways clear, and spends the model's attention only where it earns it. |

Total now: 163 s (2:43).

## Folder contents

- `clearway.mp4` the current cut (CRF 26, 8.5 MB, the one in the repository and on GitHub); `clearway-hq.mp4` the
  same at CRF 20; `clearway-sapi.mp4` the 2026-11-01 cut with the Windows voice.
- `captures/` what is shown in the video scenes: `cameras.mp4` (Smart Client, 12 s), `board.mp4` (the second
  run replayed, 22 s at 6x), `clip.mp4` (the stalled truck's clip as the board served it), `phone.mp4` (the
  author's phone, cropped, 17 s), `plan.txt` (the terminal card's lines), `alarms.txt` and
  `alarm-snapshot.jpg` (the alarms card's data); `captures/raw/` the uncut screen recording and its contact
  sheet; `captures/phone/` the author's original phone screenshots and recording.
- `cards/` the HTML cards and `card.css`; `render/` the cards rendered to 1920x1080 PNG, the board's and
  the summary's final state.
- `audio/` the Kokoro narration per scene, `audio/samples/` the title line in eight voices, `audio/sapi/` the
  Windows voice; `voice/` is where the author's takes go.
- `segments/` one encoded MP4 per scene (what the cut concatenates); `board/` the replay's frames, its MP4
  and the summary page render.
- `VIDEO.md` the storyboard and production notes; `scripts/` the assembler (`make_video.py`), the narration
  (`narrate.py`), the screen capture, the board recorder and the board replay.
- `walkthrough/01_cameras.jpg` the still the cameras scene fell back to before it was filmed.
