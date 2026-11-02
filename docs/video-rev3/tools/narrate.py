r"""narrate.py - the narration with Kokoro (open TTS, hexgrad/Kokoro-82M, Apache-2.0), from script.json.

    python tools/narrate.py                         # every scene -> audio/<id>.wav + audio/<id>.lines.json
    python tools/narrate.py --voice am_michael --speed 0.95 --only title pipeline
    python tools/narrate.py --samples               # the title in eight voices -> audio/samples/, to choose one

Setup (its own environment is best; it pulls a CPU torch of about 250 MB, and the model, about 330 MB, downloads
to the Hugging Face cache on first use):
    python -m venv .venv-tts && .venv-tts/bin/pip install -r tools/requirements-tts.txt     (Windows: .venv-tts\Scripts\pip)
Kokoro also needs espeak-ng for words outside its lexicon (apt install espeak-ng; on Windows the espeak-ng MSI).

Each line of a scene is spoken separately, then joined with the line's pause_after_s of silence (script.json), so
the start of every line is known exactly: audio/<id>.lines.json, which tools/build_video.py uses to move the view
in the flowchart scenes. Scenes with a human take in voice/<id>.wav are skipped unless --force.
Another TTS engine works the same way: write audio/<id>.wav, and audio/<id>.lines.json as
{"lines": [{"start": seconds, "end": seconds, "say": "..."}, ...]}; without it the build finds the lines from the pauses.
"""
from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
RATE = 24000
GAP_S = 0.12                 # silence between sentences inside one line
SAMPLE_VOICES = ["af_heart", "af_bella", "af_nicole", "am_michael", "am_fenrir", "bf_emma", "bm_george", "bm_lewis"]


def pipeline(voice: str):
    warnings.filterwarnings("ignore")
    from kokoro import KPipeline
    return KPipeline(lang_code="b" if voice.startswith("b") else "a", repo_id="hexgrad/Kokoro-82M")


def speak(pipe, text: str, voice: str, speed: float) -> np.ndarray:
    parts: list[np.ndarray] = []
    for _, _, audio in pipe(text, voice=voice, speed=speed):
        if parts:
            parts.append(np.zeros(int(GAP_S * RATE), np.float32))
        parts.append(np.asarray(audio, dtype=np.float32))
    return np.concatenate(parts) if parts else np.zeros(0, np.float32)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--only", nargs="*", help="scene ids (default all, optional ones included)")
    ap.add_argument("--force", action="store_true", help="also scenes with a human take in voice/")
    ap.add_argument("--samples", action="store_true")
    args = ap.parse_args()
    cfg = json.loads((ROOT / "script.json").read_text(encoding="utf-8"))
    audio_dir = ROOT / "audio"
    audio_dir.mkdir(exist_ok=True)
    if args.samples:
        (audio_dir / "samples").mkdir(exist_ok=True)
        text = " ".join(l["say"] for l in cfg["scenes"][0]["lines"])
        pipes = {}
        for v in SAMPLE_VOICES:
            pipe = pipes.setdefault(v[0], pipeline(v))
            sf.write(audio_dir / "samples" / f"{v}.wav", speak(pipe, text, v, args.speed), RATE)
            print(f"sample {v}")
        return 0
    pipe = pipeline(args.voice)
    for s in cfg["scenes"]:
        if args.only and s["id"] not in args.only:
            continue
        if any((ROOT / "voice").glob(f"{s['id']}.*")) and not args.force:
            print(f"{s['id']}: a human take is in voice/, skipped")
            continue
        t0, chunks, marks, pos = time.time(), [], [], 0
        for i, line in enumerate(s["lines"]):
            a = speak(pipe, line["say"], args.voice, args.speed)
            marks.append({"start": round(pos / RATE, 3), "end": round((pos + len(a)) / RATE, 3), "say": line["say"]})
            chunks.append(a)
            pos += len(a)
            if i < len(s["lines"]) - 1:
                gap = np.zeros(int(max(line.get("pause_after_s", cfg.get("default_pause_s", 0.25)), GAP_S) * RATE), np.float32)
                chunks.append(gap)
                pos += len(gap)
        audio = np.concatenate(chunks)
        sf.write(audio_dir / f"{s['id']}.wav", audio, RATE)
        (audio_dir / f"{s['id']}.lines.json").write_text(json.dumps({"voice": args.voice, "speed": args.speed,
                                                                     "lines": marks}, indent=1), encoding="utf-8")
        print(f"spoken {s['id']} ({args.voice}): {len(audio) / RATE:.1f} s, in {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
