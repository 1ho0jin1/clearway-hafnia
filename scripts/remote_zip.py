r"""remote_zip.py - list or fetch single files from a large remote zip with HTTP range requests (no full download).

    py -I scripts\remote_zip.py URL list [--filter SUBSTRING]
    py -I scripts\remote_zip.py URL get OUT_DIR NAME [NAME ...]

Several footage sources ship as one huge zip (NGSIM videos 7-15 GB, MERL Street Scene 49 GB, AI City 15 GB); their
servers answer range requests, so the zip's directory and single members can be read on their own. Standard library
only. Files are saved flat in OUT_DIR under their base name; a file already there with the right size is skipped.
"""
from __future__ import annotations

import argparse
import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

UA = "hafnia-hackathon-2026 remote_zip (+https://github.com/1ho0jin1/hafnia-hackathon-2026)"


class RangeFile(io.RawIOBase):
    """A read-only, seekable file over HTTP range requests."""

    def __init__(self, url: str):
        self.url, self.pos, self.requests = url, 0, 0
        self.size = int(self._get(0, 0)[1].split("/")[-1])

    def _get(self, start: int, end: int) -> tuple[bytes, str]:
        # A descriptive User-Agent: Zenodo refuses a generic browser one (403).
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}", "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            self.requests += 1
            if r.status != 206:
                raise RuntimeError(f"the server ignored the range request (status {r.status})")
            return r.read(), r.headers["Content-Range"]

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, off: int, whence: int = 0) -> int:
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def readinto(self, b) -> int:
        if self.pos >= self.size:
            return 0
        n = min(len(b), self.size - self.pos)
        data, _ = self._get(self.pos, self.pos + n - 1)
        b[:len(data)] = data
        self.pos += len(data)
        return len(data)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--filter", default="")
    get = sub.add_parser("get")
    get.add_argument("out", type=Path)
    get.add_argument("names", nargs="+")
    args = ap.parse_args()

    raw = RangeFile(args.url)
    zf = zipfile.ZipFile(io.BufferedReader(raw, buffer_size=1 << 20))
    if args.cmd == "list":
        infos = [i for i in zf.infolist() if args.filter in i.filename]
        print(f"{len(zf.infolist())} entries ({len(infos)} shown), archive {raw.size:,} bytes")
        for i in infos:
            print(f"{i.file_size:>15,}  {i.filename}")
        return
    args.out.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        dest = args.out / Path(name).name
        if dest.exists() and dest.stat().st_size == zf.getinfo(name).file_size:
            print(f"have {dest.name}")
            continue
        with zf.open(name) as src, dest.open("wb") as dst:
            shutil.copyfileobj(src, dst, 8 << 20)
        print(f"got {dest.name} ({dest.stat().st_size:,} bytes)", flush=True)


if __name__ == "__main__":
    main()
