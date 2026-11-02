r"""build_video.py - the Clearway demo video (rev. 3) from script.json, the visuals and one narration file per scene.

    python tools/build_video.py                       # every scene that is not optional -> clearway-rev3.mp4
    python tools/build_video.py --list                # timings only, nothing encoded
    python tools/build_video.py --with-optional       # also the optional scenes (measured)
    python tools/build_video.py --only pipeline       # one scene's segment (for checking); no final cut

Narration per scene, first found: voice/<id>.wav (a human take), then audio/<id>.wav (text-to-speech, see
tools/narrate.py). Any format ffmpeg reads works. Leading and trailing silence is trimmed. Line timings (when the
view moves, in the flowchart scenes, and when the board scene cuts from the cameras to the board) come from
audio/<id>.lines.json when the TTS step wrote one, otherwise from the pauses in the take, otherwise from the words.

A scene lasts lead_s + its speech + tail_s, at least its min_s (script.json). Visual kinds:
  image     a still (visuals/*.png)
  video     a capture, looped or cut to the scene's length; one narrower than 1000 px is shown at twice its size
  per_line  one capture per line, cut where the next line starts (board: the cameras, then the board)
  camera    camera moves over a chart still, one keyframe list per line (tools/camera.py, visuals/shots/*.json)
Output: 1920x1080, 30 fps, H.264 CRF 20, AAC 160 kbit/s; segments in segments/, the cut in the package root.
Needs ffmpeg and ffprobe (on PATH, or --ffmpeg C:\path\ffmpeg.exe), Python 3.10+, numpy and Pillow.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
RATE = 48000
WIN = 0.02
VF = ("scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#0f141a,"
      "setsar=1,fps=30,format=yuv420p")
FF = {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"}


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"failed: {' '.join(map(str, cmd[:4]))} ...\n{r.stderr[-1500:]}")


def probe(path: Path, entry: str, stream: bool = False) -> str:
    cmd = [FF["ffprobe"], "-v", "error"] + (["-select_streams", "v:0", "-show_entries", f"stream={entry}"] if stream
                                           else ["-show_entries", f"format={entry}"]) + ["-of", "csv=p=0", str(path)]
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split(",")[0]


def decode(path: Path) -> np.ndarray:
    r = subprocess.run([FF["ffmpeg"], "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(RATE), "-"],
                       capture_output=True)
    if r.returncode:
        raise SystemExit(f"cannot read {path}: {r.stderr.decode(errors='replace')[-400:]}")
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def voiced(pcm: np.ndarray) -> tuple[np.ndarray, float]:
    """Per 20 ms window: speech or not; and the threshold used."""
    w = int(RATE * WIN)
    n = len(pcm) // w
    rms = np.sqrt((pcm[: n * w].reshape(n, w) ** 2).mean(axis=1)) if n else np.zeros(0)
    top = np.sort(rms)[::-1][max(0, int(n * 0.1))] if n else 0.0
    th = max(0.006, float(top) * 0.08)
    return rms > th, th


def narration(scene: dict) -> tuple[Path | None, str]:
    for folder, kind in (("voice", "voice"), ("audio", "tts")):
        for ext in (".wav", ".m4a", ".mp3", ".flac", ".ogg", ".webm"):
            p = ROOT / folder / f"{scene['id']}{ext}"
            if p.exists():
                return p, kind
    return None, "none"


def line_times(scene: dict, pcm: np.ndarray, start: float, end: float, src: Path | None, kind: str) -> tuple[list[float], str]:
    """Start of each line, in seconds from the trimmed speech start."""
    lines = scene["lines"]
    speech = end - start
    if len(lines) == 1:
        return [0.0], "one line"
    if kind == "tts" and src is not None:
        lj = src.with_suffix(".lines.json")
        if lj.exists():
            st = [max(0.0, float(x["start"]) - start) for x in json.loads(lj.read_text(encoding="utf-8"))["lines"]]
            if len(st) == len(lines):
                return st, "lines.json"
    v, _ = voiced(pcm)
    a, b = int(start / WIN), int(end / WIN)
    gaps, i = [], a
    while i < b:                                 # runs of silence inside the speech
        if not v[i]:
            j = i
            while j < b and not v[j]:
                j += 1
            if (j - i) * WIN >= 0.18:
                gaps.append(((j - i) * WIN, j * WIN - start))
            i = j
        else:
            i += 1
    need = len(lines) - 1
    if len(gaps) >= need:
        cuts = sorted(t for _, t in sorted(gaps, reverse=True)[:need])
        return [0.0] + cuts, "pauses"
    words = [len(l["say"].split()) for l in lines]
    tot, acc, out = sum(words), 0, []
    for w in words:
        out.append(speech * acc / tot)
        acc += w
    return out, "words"


def write_wav(path: Path, pcm: np.ndarray) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes())


def plan(scene: dict, cfg: dict, allow_silent: bool) -> dict:
    src, kind = narration(scene)
    lead, tail = cfg.get("lead_s", 0.25), cfg.get("tail_s", 0.55)
    if src is None:
        if not allow_silent:
            raise SystemExit(f"{scene['id']}: no narration (voice/{scene['id']}.wav or audio/{scene['id']}.wav); "
                             f"run tools/narrate.py, or pass --allow-silent")
        words = sum(len(l["say"].split()) for l in scene["lines"])
        speech_pcm, speech, starts, how = np.zeros(int(words / 2.6 * RATE), np.float32), words / 2.6, None, "silent"
        starts, _ = line_times(scene, speech_pcm, 0, speech, None, "none")
        how = "silent, by words"
    else:
        pcm = decode(src)
        v, _ = voiced(pcm)
        idx = np.flatnonzero(v)
        if not len(idx):
            raise SystemExit(f"{scene['id']}: {src.name} is silent")
        start = max(0.0, idx[0] * WIN - 0.05)
        end = min(len(pcm) / RATE, (idx[-1] + 1) * WIN + 0.08)
        speech_pcm = pcm[int(start * RATE): int(end * RATE)]
        speech = len(speech_pcm) / RATE
        starts, how = line_times(scene, pcm, start, end, src, kind)
    dur = max(scene["min_s"], lead + speech + tail)
    return {"src": src, "kind": kind, "pcm": speech_pcm, "speech": speech, "dur": dur, "lead": lead,
            "starts": [lead + s for s in starts], "timing": how}


def camera_shots(spec: dict, p: dict) -> list[dict]:
    starts, end_speech = p["starts"], p["lead"] + p["speech"]
    bounds = starts[1:] + [end_speech]
    shots = [{"t": 0.0, **spec["start"]}]
    for i, keys in enumerate(spec["lines"]):
        if i >= len(starts):
            break
        for k in keys:
            t = starts[i] + k.get("at", 0) * (bounds[i] - starts[i]) - spec.get("lead_s", 0.4)
            t = max(t, shots[-1]["t"] + 0.3 if len(shots) > 1 else 0.0)
            shots.append({"t": t, "box": k["box"], "hi": k["hi"]})
    if end_speech + 0.3 < p["dur"]:
        shots.append({"t": max(end_speech + 0.3, shots[-1]["t"] + 0.6), **spec["end"]})
    return shots


def build_scene(scene: dict, p: dict, seg_dir: Path) -> Path:
    sid, dur, vis = scene["id"], p["dur"], scene["visual"]
    wav = seg_dir / f"{sid}.audio.wav"
    total = int(round(dur * RATE))
    pcm = np.zeros(total, np.float32)
    a = int(p["lead"] * RATE)
    pcm[a: a + len(p["pcm"])] = p["pcm"][: total - a]
    write_wav(wav, pcm)
    out = seg_dir / f"{sid}.mp4"
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-t", f"{dur:.3f}", "-movflags", "+faststart"]

    def vf_for(path: Path) -> str:
        try:
            narrow = int(probe(path, "width", stream=True) or 0) < 1000
        except ValueError:
            narrow = False
        return ("scale=iw*2:ih*2:flags=lanczos," if narrow else "") + VF

    if vis["kind"] == "image":
        run([FF["ffmpeg"], "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(ROOT / vis["src"]),
             "-i", str(wav), "-vf", VF, *enc, str(out)])
    elif vis["kind"] == "video":
        src = ROOT / vis["src"]
        run([FF["ffmpeg"], "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src), "-i", str(wav),
             "-map", "0:v", "-map", "1:a", "-vf", vf_for(src), *enc, str(out)])
    elif vis["kind"] == "per_line":
        srcs = [ROOT / s for s in vis["src"]]
        cuts = [0.0] + [max(0.0, t - 0.15) for t in p["starts"][1:len(srcs)]] + [dur]
        ins, parts = [], []
        for i, s in enumerate(srcs):
            ins += ["-stream_loop", "-1", "-i", str(s)]
            parts.append(f"[{i}:v]trim=duration={cuts[i + 1] - cuts[i]:.3f},setpts=PTS-STARTPTS,{vf_for(s)}[v{i}]")
        fc = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(srcs))) + f"concat=n={len(srcs)}:v=1:a=0[v]"
        run([FF["ffmpeg"], "-y", "-loglevel", "error", *ins, "-i", str(wav), "-filter_complex", fc,
             "-map", "[v]", "-map", f"{len(srcs)}:a", *enc, str(out)])
    elif vis["kind"] == "camera":
        import camera
        spec = json.loads((ROOT / vis["spec"]).read_text(encoding="utf-8"))
        shots = camera_shots(spec, p)
        silent = seg_dir / f"{sid}.video.mp4"
        camera.FFMPEG = FF["ffmpeg"]
        camera.render(ROOT / vis["image"], shots, dur, silent, scale=spec["scale"], oy=spec["oy"],
                      canvas=tuple(spec["canvas"]), move=spec.get("move", 1.4), fade=spec.get("fade", 0.8))
        run([FF["ffmpeg"], "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-t", f"{dur:.3f}",
             "-movflags", "+faststart", str(out)])
        silent.unlink(missing_ok=True)
        (seg_dir / f"{sid}.shots.json").write_text(json.dumps(shots, indent=1), encoding="utf-8")
    else:
        raise SystemExit(f"{sid}: unknown visual kind {vis['kind']!r}")
    wav.unlink(missing_ok=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--script", type=Path, default=ROOT / "script.json")
    ap.add_argument("--out", type=Path, default=ROOT / "clearway-rev3.mp4")
    ap.add_argument("--only", nargs="*", help="scene ids: build just these segments, no final cut")
    ap.add_argument("--with-optional", action="store_true", help="include optional scenes (measured)")
    ap.add_argument("--list", action="store_true", help="print the timings and stop")
    ap.add_argument("--allow-silent", action="store_true", help="a scene without narration is built silent, "
                                                                "timed by its words (for checking the visuals)")
    ap.add_argument("--ffmpeg", default=os.environ.get("FFMPEG", "ffmpeg"), help="path to ffmpeg (ffprobe beside it)")
    args = ap.parse_args()
    FF["ffmpeg"] = args.ffmpeg
    if args.ffmpeg != "ffmpeg":
        fp = Path(args.ffmpeg)
        FF["ffprobe"] = str(fp.with_name(fp.name.replace("ffmpeg", "ffprobe")))
    cfg = json.loads(args.script.read_text(encoding="utf-8"))
    scenes = [s for s in cfg["scenes"] if (args.with_optional or not s.get("optional"))
              and (not args.only or s["id"] in args.only)]
    plans, total = {}, 0.0
    print(f"{'scene':12} {'length':>7} {'speech':>7}  narration         line timing")
    for s in scenes:
        p = plans[s["id"]] = plan(s, cfg, args.allow_silent)
        total += p["dur"]
        src = f"{p['kind']}:{p['src'].name}" if p["src"] else "none"
        print(f"{s['id']:12} {p['dur']:6.1f}s {p['speech']:6.1f}s  {src:17} {p['timing']}"
              + (f"  lines at {', '.join(f'{t:.1f}' for t in p['starts'])}" if len(s["lines"]) > 1 else ""))
    limit = cfg.get("limit_s", 180)
    print(f"total {int(total // 60)}:{total % 60:04.1f}" + (f"  OVER the {limit // 60}:{limit % 60:02d} limit by "
                                                          f"{total - limit:.1f} s" if total > limit else ""))
    if args.list:
        return 0
    seg_dir = ROOT / "segments"
    seg_dir.mkdir(exist_ok=True)
    parts = []
    for s in scenes:
        parts.append(build_scene(s, plans[s["id"]], seg_dir))
        print(f"built segments/{s['id']}.mp4")
    if args.only:
        return 0
    lst = seg_dir / "list.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    run([FF["ffmpeg"], "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         "-movflags", "+faststart", str(args.out)])
    print(f"wrote {args.out} ({float(probe(args.out, 'duration')):.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
