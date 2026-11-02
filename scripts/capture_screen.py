r"""capture_screen.py - film a 16:9 region of this desktop (Smart Client, the phone's mirror) with ffmpeg for the video.

    .venv\Scripts\python.exe scripts\capture_screen.py place                     # Smart Client into the 16:9 region
    .venv\Scripts\python.exe scripts\capture_screen.py record NAME --seconds 60  # the region into captures\raw\NAME.mkv
    .venv\Scripts\python.exe scripts\capture_screen.py sheet NAME [--every 2]    # a contact sheet to find the cut
    .venv\Scripts\python.exe scripts\capture_screen.py cut NAME SCENE --start 4.0 --end 16.5   # captures\SCENE.mp4

The region is the largest 16:9 rectangle of the primary screen's work area (the taskbar left out), top left. `place`
restores Smart Client's main window (Client.exe) and sizes it to that region, so what it shows fills the frame.
`record` runs ffmpeg's gdigrab on the region at 20 fps into an MKV (readable even if the recording is cut short)
for --seconds, in the foreground; it must run in the desktop session it films (an RDP session counts). `sheet`
writes raw\NAME-sheet.jpg with one frame every --every seconds, numbered by time, to pick the cut by eye. `cut`
trims and scales the cut to 1920x1080 H.264 into docs\video\captures\SCENE.mp4, where scripts\make_video.py
picks it up. No request to Hafnia; the files hold camera footage and are git-ignored.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from make_video import CAPTURES, FFMPEG, FFPROBE  # noqa: E402

RAW = CAPTURES / "raw"
PS = ["powershell", "-NoProfile", "-NonInteractive", "-Command"]


def region() -> tuple[int, int, int, int]:
    """x, y, w, h: the largest 16:9 rectangle at the top left of the work area, even-sized."""
    r = subprocess.run([*PS, "Add-Type -AssemblyName System.Windows.Forms; "
                        "$a=[System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea; "
                        "\"$($a.X) $($a.Y) $($a.Width) $($a.Height)\""], capture_output=True, text=True, check=True)
    x, y, w, h = (int(v) for v in r.stdout.split())
    h = min(h, w * 9 // 16)
    w = h * 16 // 9
    return x, y, w // 2 * 2, h // 2 * 2


def place(x: int, y: int, w: int, h: int) -> None:
    script = (
        "Add-Type @'\nusing System; using System.Runtime.InteropServices;\npublic class W {\n"
        "[DllImport(\"user32.dll\")] public static extern bool ShowWindow(IntPtr h, int n);\n"
        "[DllImport(\"user32.dll\")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int w, int cy, uint f);\n"
        "[DllImport(\"user32.dll\")] public static extern bool SetForegroundWindow(IntPtr h); }\n'@\n"
        "$p = Get-Process Client -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1\n"
        "if (-not $p) { throw 'Smart Client (Client.exe) has no window' }\n"
        "[W]::ShowWindow($p.MainWindowHandle, 9) | Out-Null\n"            # SW_RESTORE: out of maximized
        f"[W]::SetWindowPos($p.MainWindowHandle, [IntPtr]::Zero, {x}, {y}, {w}, {h}, 0x0040) | Out-Null\n"   # SWP_SHOWWINDOW
        "[W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null\n'placed ' + $p.MainWindowTitle")
    r = subprocess.run([*PS, script], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())


def record(name: str, seconds: int, fps: int) -> Path:
    x, y, w, h = region()
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{name}.mkv"
    print(f"recording {w}x{h} at ({x},{y}) for {seconds} s into {out}")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", str(fps), "-offset_x", str(x),
                    "-offset_y", str(y), "-video_size", f"{w}x{h}", "-i", "desktop", "-t", str(seconds),
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
                   check=True)
    (RAW / f"{name}.json").write_text(json.dumps({"region": [x, y, w, h], "seconds": seconds, "fps": fps}))
    return out


def seconds(path: Path) -> float:
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def sheet(name: str, every: float) -> Path:
    src = RAW / f"{name}.mkv"
    out = RAW / f"{name}-sheet.jpg"
    n = max(1, int(seconds(src) / every) + 1)
    cols = 4
    rows = (n + cols - 1) // cols
    vf = (f"fps=1/{every},scale=480:-2,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=28:fontcolor=white:"
          f"box=1:boxcolor=black@0.6,tile={cols}x{rows}")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(src), "-vf", vf, "-frames:v", "1", "-q:v", "4",
                    str(out)], check=True)
    print(f"{out}: {n} frames, one every {every} s")
    return out


def cut(name: str, scene: str, start: float, end: float) -> Path:
    src = RAW / f"{name}.mkv"
    out = CAPTURES / f"{scene}.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", str(src),
                    "-vf", "scale=1920:1080:flags=lanczos,fps=30,format=yuv420p", "-an", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "20", str(out)], check=True)
    print(f"{out}: {seconds(out):.1f} s")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("place")
    p = sub.add_parser("record"); p.add_argument("name"); p.add_argument("--seconds", type=int, default=60)
    p.add_argument("--fps", type=int, default=20)
    p = sub.add_parser("sheet"); p.add_argument("name"); p.add_argument("--every", type=float, default=2.0)
    p = sub.add_parser("cut"); p.add_argument("name"); p.add_argument("scene")
    p.add_argument("--start", type=float, default=0.0); p.add_argument("--end", type=float, required=True)
    a = ap.parse_args()
    if a.cmd == "place":
        place(*region())
    elif a.cmd == "record":
        record(a.name, a.seconds, a.fps)
    elif a.cmd == "sheet":
        sheet(a.name, a.every)
    else:
        cut(a.name, a.scene, a.start, a.end)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
