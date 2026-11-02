r"""replay_board.py - replay a finished run's logs into a copy, line by line at their own pace, so the board shows the
cards arriving as they did, for filming with scripts\record_board.py on an idle machine (no request).

    .venv\Scripts\python.exe scripts\replay_board.py run\clearway-live-<UTC> [--speed 1] [--skip 60] [--port 8767]

The live board could not be filmed during the run itself: with eleven cameras the machine is saturated and the
headless Edge renders time out (2026-11-02). This makes a run folder run\clearway-replay-<UTC> with the run's
snapshots, clips and scene images copied, starts a board on --port following it, and appends the run's
ledger.jsonl, service.jsonl and operator.jsonl lines in wall-clock order, --speed times faster than they were
written, with every time stamp shifted to the present so the board's "time open" reads as it did. --skip drops
the first seconds after the service's start (the warm-up, when nothing happens). Film it beside this with:

    .venv\Scripts\python.exe scripts\record_board.py --url http://127.0.0.1:8767/ --minutes M --every 1 --speed 6

The board is stopped at the end. The replay folder is git-ignored like every run folder's logs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOGS = ("ledger.jsonl", "service.jsonl", "operator.jsonl")
COPY = ("snaps", "clips", "cameras")
STAMP = re.compile(r"\b(17\d{8})(\.\d+)?\b")    # Unix seconds in 2024-2026, as the logs write them


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run", type=Path)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--skip", type=float, default=0.0, help="seconds after the service's start line to skip")
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    out = args.out or REPO / "run" / f"clearway-replay-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
    out.mkdir(parents=True)
    for d in COPY:
        if (args.run / d).exists():
            shutil.copytree(args.run / d, out / d)
    lines: list[tuple[float, str, str]] = []
    for name in LOGS:
        if (args.run / name).exists():
            for line in (args.run / name).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    lines.append((json.loads(line).get("wall", 0.0), name, line))
    lines.sort(key=lambda x: x[0])
    t_start = next(w for w, n, l in lines if n == "service.jsonl" and '"kind": "start"' in l) + args.skip
    t_now0 = time.time()

    def shifted(line: str) -> str:
        """Every stamp moved to the replay's own clock: the start is now, later ones --speed times nearer."""
        return STAMP.sub(lambda m: f"{t_now0 + (float(m.group(0)) - t_start) / args.speed:.3f}", line)

    files = {name: (out / name).open("a", encoding="utf-8") for name in LOGS}
    for wall, name, line in lines:          # everything before the start (and the skipped seconds): at once
        if wall <= t_start:
            files[name].write(shifted(line) + "\n")
    for f in files.values():
        f.flush()
    board = subprocess.Popen([sys.executable, "-u", "-m", "clearway.board", "--run", str(out), "--port",
                              str(args.port)], cwd=REPO)
    print(f"board on http://127.0.0.1:{args.port}/ following {out}; replaying from +{args.skip:g} s at "
          f"{args.speed:g}x", flush=True)
    t0 = time.monotonic()
    try:
        for wall, name, line in lines:
            if wall <= t_start:
                continue
            due = t0 + (wall - t_start) / args.speed
            while time.monotonic() < due:
                time.sleep(min(0.2, due - time.monotonic()))
            files[name].write(shifted(line) + "\n")
            files[name].flush()
            if name == "ledger.jsonl" and '"kind": "answer"' in line:
                print(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%S} +{wall - t_start:5.0f} s  answer "
                      f"{json.loads(line).get('incident')}", flush=True)
        print("replay done", flush=True)
        time.sleep(5)
    finally:
        for f in files.values():
            f.close()
        board.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
