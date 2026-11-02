r"""make_video.py - the demonstration video (docs/VIDEO.md) from cards, stills, captures and narration, with ffmpeg.

    .venv\Scripts\python.exe scripts\make_video.py --render-cards --tts --build [--voice af_heart] [--out docs\video\clearway.mp4]
    .venv\Scripts\python.exe scripts\make_video.py --list                 # the scenes, their visuals and lengths

Scenes (SCENES below) each have a narration and a visual. The visual is a card (docs/video/cards/*.html, rendered
to 1920x1080 PNG by Edge headless with --render-cards), a still, or a video: a capture in docs/video/captures/
(the board filmed by scripts/record_board.py, Smart Client or the phone recorded by hand, a card's clip from the
board) when it exists, else the fallback named in the scene. Narration: the author's recording docs/video/voice/<id>.wav
when it exists, else synthetic speech into docs/video/audio/<id>.wav (--tts): Kokoro, an open model, through
scripts/narrate.py in its own environment .venv-tts (--engine kokoro, the default; requirements-tts.txt), or
Windows text-to-speech (--engine sapi, --voice Zira or David: the scratch track the first cuts were timed with).
Each scene lasts as long as its narration (at least its min_s); a video shorter than that loops, a longer one
is cut. --build encodes one segment per scene (1920x1080, 30 fps, H.264, AAC) and concatenates them. Only the
organizers' cameras and our own pages appear; never test_11. The outputs hold camera footage and are git-ignored.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FFMPEG = r"C:\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"   # as lens/publisher.py (not imported:
FFPROBE = str(Path(FFMPEG).with_name("ffprobe.exe"))                       # narrate.py's environment has no cv2)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
VIDEO = REPO / "docs" / "video"
CARDS, RENDER, AUDIO, VOICE, SEGMENTS, CAPTURES = (VIDEO / d for d in ("cards", "render", "audio", "voice",
                                                                        "segments", "captures"))

# visual: ("card", html name) | ("still", path) | ("video", capture name, fallback visual)
#       | ("text", html name, text file in captures/): the card with the file's lines as its ?t= (a terminal)
SCENES = [
    # Cut 2026-11-01 to stay under the portal's 3 minutes (the synthetic voice gives about 2.5; a slower reading
    # still fits): shorter narration everywhere, the comparison without its "to be fair" sentence (the card's foot
    # keeps it), the known limit said on the numbers scene.
    {"id": "title", "min_s": 8, "visual": ("card", "title.html"),
     "say": "Clearway watches a city's XProtect cameras for what blocks a public way, asks Hafnia V L M once per "
            "incident, and turns the answer into one alarm, one card for its owner, one push to a phone."},
    {"id": "cameras", "min_s": 5, "visual": ("video", "cameras.mp4", ("still", REPO / "docs" / "walkthrough" / "01_cameras.jpg")),
     "say": "Eleven cameras, six with a staged incident."},
    # the terminal card: the first lines the service printed in the run that was filmed (captures/plan.txt)
    {"id": "plan", "min_s": 5, "visual": ("text", "terminal.html", "plan.txt"),
     "say": "The service says what it will spend before it starts: at most this many of the day's five hundred."},
    {"id": "board", "min_s": 16, "visual": ("video", "board.mp4", ("still", RENDER / "board-final.png")),
     "say": "Within a minute every incident has a card in its owner's column: the truck for traffic operations, the "
            "person on the tracks for rail control, the bin for street services, each with the clip Hafnia judged, "
            "its verdict, the time open and its alarm."},
    {"id": "clip", "min_s": 8, "visual": ("video", "clip.mp4", ("card", "placeholder.html?t=The clip Hafnia judged")),
     "say": "The clip for the stalled truck as Hafnia saw it, and the verdict: a silver pickup stalls in the lane "
            "with its door open and smoke rising, blocking traffic."},
    # Smart Client's Alarm Manager list did not draw the alarms on this machine (2026-11-02; a screen capture
    # smartclient.mp4 was planned): the card shows them as the REST API returns them (captures/alarms.txt, JSON)
    {"id": "smartclient", "min_s": 10, "visual": ("text", "alarms.html", "alarms.txt"),
     "say": "The same incident is an XProtect alarm with the category, the owner, Hafnia's summary, a snapshot and a "
            "bookmark. It closes itself when the spot clears and reopens if it happens again."},
    {"id": "phone", "min_s": 17, "visual": ("video", "phone.mp4", ("card", "placeholder.html?t=The phone: Confirm or Reject")),
     # 17 s: the author's phone recording (the push in the shade, the app, the tap at 13 s, the acknowledgement)
     "say": "The owner gets a push with two buttons. A tap reaches the system in under a second and teaches it: a "
            "rejected look at that spot is not asked about again."},
    {"id": "decides", "min_s": 14, "visual": ("card", "decides.html"),
     "say": "Nothing asks Hafnia on a timer. A change detector notices what stayed changed, a memory skips what was "
            "already judged, and a small spot is enlarged on a magnifier camera of our own: a thirty-pixel crash the "
            "full frame called nothing is named a collision."},
    {"id": "measured", "min_s": 12, "visual": ("card", "measured.html"),
     "say": "All of it was measured, and three faults were found and fixed: the magnifier camera's clock, now proven "
            "by a code in every frame; a detector that faded after seven minutes; alarms slowed by our own load."},
    {"id": "numbers", "min_s": 12, "visual": ("card", "numbers.html"),
     "say": "Three hours on eleven cameras: thirty-three requests, one per camera-hour, and the next run had no false "
            "cards. On real streets it had never seen, waiting cars became false cards: the known limit. Everything "
            "is in the repository."},
    {"id": "compare", "min_s": 14, "visual": ("card", "compare.html"),
     "say": "The plain way asks every camera once a minute: sixty requests per camera-hour, the day's five hundred "
            "gone in forty-five minutes. Clearway spent one per camera-hour. Six times out of six, the full frame "
            "left the person on the platform; the magnified clip put them on the tracks."},
    {"id": "summary", "min_s": 7, "visual": ("still", RENDER / "summary-final.png"),
     "say": "At the end of a shift, the summary: incidents by owner, how fast, where it keeps happening."},
    {"id": "close", "min_s": 6, "visual": ("card", "close.html"),
     "say": "Clearway keeps public ways clear, and spends the model's attention only where it earns it."},
]


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"failed: {' '.join(cmd[:3])} ...\n{r.stderr[-800:]}")


def seconds(path: Path) -> float:
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def width(path: Path) -> int:
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return int(r.stdout.strip().split(",")[0] or 0)


def render_card(name: str, png: Path) -> None:
    html, _, query = name.partition("?")
    url = (CARDS / html).resolve().as_uri() + (f"?{query}" if query else "")
    run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1920,1080",
         "--virtual-time-budget=2000", f"--screenshot={png}", url])


def render_page(url: str, png: Path, budget_ms: int = 6000) -> None:
    run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1920,1080",
         f"--virtual-time-budget={budget_ms}", f"--screenshot={png}", url])


def tts(text: str, wav: Path, voice: str) -> None:
    """Windows text-to-speech (System.Speech), the scratch track."""
    script = (f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              f"$s.SelectVoice('Microsoft {voice} Desktop'); $s.Rate = 0; $s.SetOutputToWaveFile('{wav}'); "
              f"$s.Speak([string]'{text.replace(chr(39), chr(39) * 2)}'); $s.Dispose()")
    run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script])


TTS_PY = REPO / ".venv-tts" / "Scripts" / "python.exe"


def narrate_kokoro(scene_ids: list[str], voice: str, speed: float) -> None:
    """Kokoro through scripts/narrate.py in .venv-tts (see requirements-tts.txt); writes AUDIO/<id>.wav."""
    if not TTS_PY.exists():
        raise SystemExit(f"{TTS_PY} is missing: py -3.12 -m venv .venv-tts; "
                         f".venv-tts\\Scripts\\python.exe -m pip install -r requirements-tts.txt")
    r = subprocess.run([str(TTS_PY), str(REPO / "scripts" / "narrate.py"), "--voice", voice, "--speed", f"{speed}",
                        "--only", *scene_ids], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout, end="")
    if r.returncode:
        raise SystemExit(f"narrate.py failed:\n{r.stderr[-1500:]}")


def resolve(scene: dict) -> tuple[str, Path]:
    """("image" | "video", path): the capture when it exists, else the fallback."""
    v = scene["visual"]
    if v[0] == "video":
        cap = CAPTURES / v[1]
        if cap.exists():
            return "video", cap
        v = v[2]
    if v[0] == "card":
        return "image", RENDER / (v[1].split("?")[0].replace(".html", "") + ("-" + scene["id"] if "?" in v[1] else "") + ".png")
    if v[0] == "text":
        return "image", RENDER / (v[1].replace(".html", "") + "-" + scene["id"] + ".png")
    return "image", Path(v[1])


def text_card(scene: dict) -> str:
    """The ("text", html, file) visual as a card name with its ?t= query (the file's lines, or a placeholder)."""
    from urllib.parse import quote
    src = CAPTURES / scene["visual"][2]
    text = src.read_text(encoding="utf-8") if src.exists() else f"({src.name} is not there yet)"
    return scene["visual"][1] + "?t=" + quote(text.strip())


def narration(scene: dict) -> Path | None:
    own = VOICE / f"{scene['id']}.wav"
    if own.exists():
        return own
    gen = AUDIO / f"{scene['id']}.wav"
    return gen if gen.exists() else None


def build_segment(scene: dict, out: Path) -> float:
    kind, path = resolve(scene)
    wav = narration(scene)
    dur = max(scene["min_s"], seconds(wav) + 0.8 if wav else 0.0)
    audio = ["-i", str(wav)] if wav else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#0f141a,fps=30,format=yuv420p"
    if kind == "image":
        src = ["-loop", "1", "-framerate", "30", "-i", str(path)]
    else:
        src = ["-stream_loop", "-1", "-i", str(path)]
        if width(path) < 1000:                     # a small clip (a card's crop): shown at twice its size, not blown up
            vf = "scale=iw*2:ih*2:flags=lanczos," + vf.replace("scale=1920:1080:force_original_aspect_ratio=decrease,", "")
    run([FFMPEG, "-y", "-loglevel", "error", *src, *audio, "-t", f"{dur:.2f}", "-vf", vf, "-af", "apad",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
         "-ac", "2", "-shortest", str(out)])
    return dur


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--render-cards", action="store_true", help="cards to PNG (Edge headless), and the board and "
                                                                "summary of --board-url to board-final / summary-final")
    ap.add_argument("--board-url", default="http://127.0.0.1:8766", help="a board showing the run to picture")
    ap.add_argument("--tts", action="store_true", help="synthetic narration where no voice/<id>.wav exists")
    ap.add_argument("--engine", choices=("kokoro", "sapi"), default="kokoro",
                    help="kokoro: scripts/narrate.py in .venv-tts (default); sapi: Windows text-to-speech")
    ap.add_argument("--voice", help="kokoro: af_heart (default), am_michael, bm_george, ... (narrate.py --samples); "
                                    "sapi: Zira (default) or David")
    ap.add_argument("--speed", type=float, default=1.0, help="kokoro: speaking rate, 1.0 = the voice's own")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--only", nargs="*", help="scene ids to build (default all)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", type=Path, default=VIDEO / "clearway.mp4")
    args = ap.parse_args()
    for d in (RENDER, AUDIO, VOICE, SEGMENTS, CAPTURES):
        d.mkdir(parents=True, exist_ok=True)
    scenes = [s for s in SCENES if not args.only or s["id"] in args.only]
    if args.render_cards:
        for s in SCENES:
            v = s["visual"]
            card = v[1] if v[0] == "card" else (v[2][1] if v[0] == "video" and v[2][0] == "card" else None)
            if v[0] == "text":
                _, png = resolve(s)
                render_card(text_card(s), png)
                print(f"rendered {png.name}")
            elif card:
                _, png = resolve({**s, "visual": ("card", card)})
                render_card(card, png)
                print(f"rendered {png.name}")
        try:
            render_page(args.board_url + "/", RENDER / "board-final.png")
            render_page(args.board_url + "/summary", RENDER / "summary-final.png")
            print("rendered board-final.png, summary-final.png")
        except SystemExit as e:
            print(f"board not rendered: {e}")
    if args.tts:
        todo = [s for s in scenes if not (VOICE / f"{s['id']}.wav").exists()]
        if args.engine == "kokoro" and todo:
            narrate_kokoro([s["id"] for s in todo], args.voice or "af_heart", args.speed)
        else:
            for s in todo:
                tts(s["say"], AUDIO / f"{s['id']}.wav", args.voice or "Zira")
                print(f"spoken {s['id']}: {seconds(AUDIO / (s['id'] + '.wav')):.1f} s")
    if args.list or not (args.build or args.render_cards or args.tts):
        total = 0.0
        for s in SCENES:
            kind, path = resolve(s)
            wav = narration(s)
            dur = max(s["min_s"], seconds(wav) + 0.8 if wav else 0.0)
            total += dur
            print(f"{s['id']:12} {dur:5.1f} s  {kind:5} {path.relative_to(REPO) if path.is_relative_to(REPO) else path}"
                  f"  {'voice' if wav and wav.parent == VOICE else 'tts' if wav else 'silent'}")
        print(f"total {total / 60:.1f} min")
    if args.build:
        parts = []
        total = 0.0
        for s in scenes:
            seg = SEGMENTS / f"{s['id']}.mp4"
            total += build_segment(s, seg)
            parts.append(seg)
            print(f"built {seg.name}")
        lst = SEGMENTS / "list.txt"
        lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
             "-movflags", "+faststart", str(args.out)])
        print(f"wrote {args.out} ({total / 60:.1f} min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
