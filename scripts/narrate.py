r"""narrate.py - the video's narration with Kokoro (open TTS, Apache-2.0) instead of Windows text-to-speech.

    .venv-tts\Scripts\python.exe scripts\narrate.py [--voice af_heart] [--speed 1.0] [--only title board]
    .venv-tts\Scripts\python.exe scripts\narrate.py --samples        # the title line in several voices, to choose one

Runs in its own environment (.venv-tts, git-ignored), so the project's pinned one is untouched:

    py -3.12 -m venv .venv-tts
    .venv-tts\Scripts\python.exe -m pip install -r requirements-tts.txt

Reads the scenes from scripts/make_video.py (SCENES) and writes docs/video/audio/<id>.wav (24 kHz mono) for every
scene that has no recording of the author's in docs/video/voice/. make_video.py --tts calls this script
(--engine kokoro, the default) and then builds the cut. The model (hexgrad/Kokoro-82M, about 330 MB) and the
voices download to the Hugging Face cache on first use; synthesis runs on the CPU at about real time.
Voices: Kokoro's English set, American (af_*, am_*) and British (bf_*, bm_*); af_heart is the one graded best.
"""
from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from make_video import AUDIO, SCENES, VOICE  # noqa: E402

RATE = 24000
GAP_S = 0.12                 # silence between the sentences Kokoro synthesises one by one
SAMPLE_VOICES = ["af_heart", "af_bella", "af_nicole", "am_michael", "am_fenrir", "bf_emma", "bm_george", "bm_lewis"]


def pipeline(voice: str):
    warnings.filterwarnings("ignore")
    from kokoro import KPipeline
    return KPipeline(lang_code="b" if voice.startswith("b") else "a", repo_id="hexgrad/Kokoro-82M")


def speak(pipe, text: str, voice: str, speed: float) -> np.ndarray:
    gap = np.zeros(int(GAP_S * RATE), dtype=np.float32)
    parts: list[np.ndarray] = []
    for _, _, audio in pipe(text, voice=voice, speed=speed):
        if parts:
            parts.append(gap)
        parts.append(np.asarray(audio, dtype=np.float32))
    return np.concatenate(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--only", nargs="*", help="scene ids (default all)")
    ap.add_argument("--force", action="store_true", help="also scenes that have the author's recording in voice/")
    ap.add_argument("--samples", action="store_true", help=f"the title line in {len(SAMPLE_VOICES)} voices into "
                                                           "docs/video/audio/samples/")
    args = ap.parse_args()
    AUDIO.mkdir(parents=True, exist_ok=True)
    if args.samples:
        out = AUDIO / "samples"
        out.mkdir(exist_ok=True)
        text = SCENES[0]["say"]
        pipes = {}
        for voice in SAMPLE_VOICES:
            pipe = pipes.setdefault(voice[0], pipeline(voice))
            sf.write(out / f"{voice}.wav", speak(pipe, text, voice, args.speed), RATE)
            print(f"sample {voice}: {out / (voice + '.wav')}")
        return 0
    pipe = pipeline(args.voice)
    for s in SCENES:
        if args.only and s["id"] not in args.only:
            continue
        if (VOICE / f"{s['id']}.wav").exists() and not args.force:
            print(f"{s['id']}: the author's recording is used")
            continue
        t = time.time()
        audio = speak(pipe, s["say"], args.voice, args.speed)
        sf.write(AUDIO / f"{s['id']}.wav", audio, RATE)
        print(f"spoken {s['id']} ({args.voice}): {len(audio) / RATE:.1f} s, in {time.time() - t:.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
