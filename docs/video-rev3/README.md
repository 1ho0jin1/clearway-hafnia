# Clearway video materials, rev. 3 (2026-11-02)

Everything needed to build the rev. 3 cut of the Clearway demo video (11 scenes, under 3:00) with a text-to-speech
voice or with human takes. The earlier cut's materials are in `../clearway-video-materials-20261102/`.

## Build it with TTS (Kokoro)

```bash
python -m venv .venv-tts
.venv-tts/bin/pip install -r tools/requirements-tts.txt -r tools/requirements.txt   # Python 3.10-3.12 (Kokoro)
sudo apt install ffmpeg espeak-ng                                                     # or put them on PATH
.venv-tts/bin/python tools/narrate.py --voice af_heart        # -> audio/<scene>.wav + audio/<scene>.lines.json
.venv-tts/bin/python tools/build_video.py --list              # timings and the total, nothing encoded
.venv-tts/bin/python tools/build_video.py                     # -> clearway-rev3.mp4 (about 3 min of encoding)
```

On Windows use `.venv-tts\Scripts\python.exe`, and `--ffmpeg C:\path\to\ffmpeg.exe` if ffmpeg is not on PATH.
`narrate.py --samples` speaks the title in eight voices into `audio/samples/` to choose one; `--speed 0.95` slows
the reading.

Another TTS engine works too: write `audio/<scene>.wav` per scene (any format ffmpeg reads) and, so the flowchart
moves land on the right words, `audio/<scene>.lines.json` as `{"lines": [{"start": s, "end": s}, ...]}`, one entry
per line of `script.json`. Without it the build finds the lines from the pauses, then from the word counts.

## Build it with human takes

Open `recorder.html` in Edge or Chrome, connect the `voice/` folder, record each scene. A file in `voice/` wins over
the TTS file of the same scene, so a mix of both works.

## What is here

| Path | What |
|---|---|
| `script.json` | The script and the scene list: per scene its minimum length, its visual, and per line the words, what is on screen, and the pause after it (used by the TTS step). The source of truth. |
| `SCRIPT.md` | The same script as a table, for reading. |
| `tools/narrate.py` | Kokoro TTS from `script.json`, line by line, with exact line timings. |
| `tools/build_video.py` | The cut: trims each take, places the lines, renders the flowchart camera moves, encodes one segment per scene into `segments/`, joins them. |
| `tools/camera.py` | The camera moves and spotlights over a chart still (used by the build). |
| `visuals/` | The cards (`title.png`, `numbers.png`, `compare.png`, `close.png`, `measured.png`, `alarms-smartclient.png`), the captures (`cameras.mp4`, `board.mp4`, `clip.mp4`, `phone.mp4`), the finished board (`board-final.png`), the two flowcharts as SVG and as dark renders (`pipeline@3x.png`, `verdict@2x.png`), and `operator_reject.svg` (the earlier Reject-only chart, not in the cut). |
| `visuals/shots/` | Camera keyframes per line for `spoiler`, `pipeline` and `verdict`. |
| `recorder.html`, `recorder-thumbs/`, `preview/` | The recording page for human takes, its scene stills, and silent previews of the three animated scenes (their timing is guessed; the build times the moves to the narration). |
| `voice/`, `audio/` | Empty: human takes go in `voice/`, TTS output in `audio/`. |

## Scenes

1. `title` (title card) 2. `spoiler` (the finished owner board, the view moving to each card) 3. `pipeline` (the
pipeline flowchart) 4. `board` (Smart Client's eleven cameras, then the owner board filling) 5. `clip` (the stalled
truck's clip) 6. `smartclient` (the alarms as XProtect holds them) 7. `phone` (the push and the tap) 8. `verdict`
(the Confirm / Reject flowchart) 9. `numbers` 10. `compare` 11. `close`. Optional: `measured` (`--with-optional`).

## Checked

`build_video.py` was run end to end on 2026-11-02 with stand-in audio (tones timed like speech, one scene as a
"human" take without line timings, so both timing paths ran): 11 segments, 1920x1080 30 fps H.264 with AAC 48 kHz
stereo, 2:49.6 at a Kokoro-like pace. `narrate.py` is the earlier cut's Kokoro script with only its input changed to
`script.json` and line-by-line timing added; it was not run here (Kokoro needs Python 3.10-3.12).

Footage: only the organizers' cameras and Clearway's own pages appear; never `test_11`.
