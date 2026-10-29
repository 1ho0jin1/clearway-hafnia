r"""fetch_footage.py - the three CC0 street clips the held-out check runs on (run/holdout-20261029), fetched from
Wikimedia Commons into data/footage/commons and checked against their SHA-256.

    py scripts\fetch_footage.py                 # fetch what is missing (about 500 MB), verify everything
    py scripts\fetch_footage.py --check         # verify only, no download
    py scripts\fetch_footage.py --only mumbai02 duesseldorf

Standard library only, so the system Python (py) or .venv both run it. Idempotent: a file whose checksum matches is
left alone; a wrong or partial file is fetched again (a .part file resumes where it stopped). Commons answers a burst
of requests with HTTP 429; the script waits and retries. Exit code 0 when every clip is present and verified.

The clips are CC0 (Creative Commons Zero, public domain dedication: no attribution required; the authors are named
anyway). Their Commons records were read on 2026-10-29 and the local files matched the originals' SHA-1 exactly.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "data" / "footage" / "commons"
USER_AGENT = "ClearwayFootageFetch/1.0 (hafnia-hackathon-2026 entry; fetches three CC0 clips once per machine)"
CHUNK = 1 << 20

# local name: Commons file title, original-file URL, size in bytes, SHA-256, what it is, author, filmed, licence
CLIPS = {
    "mumbai02.webm": {
        "title": "File:Street in Mumbai (video) 02.webm",
        "url": "https://upload.wikimedia.org/wikipedia/commons/6/66/Street_in_Mumbai_%28video%29_02.webm",
        "size": 80541087,
        "sha256": "3913782ffdfa9ce1f340b334db4ae0c6291d2a393f878898d1fd5ba8c30865c8",
        "what": "a Mumbai junction from above by day, 3:03, 960x540",
        "author": "Nicolas Vigier", "filmed": "2016-03-29", "licence": "CC0",
    },
    "mumbai03.webm": {
        "title": "File:Street in Mumbai (video) 03.webm",
        "url": "https://upload.wikimedia.org/wikipedia/commons/9/96/Street_in_Mumbai_%28video%29_03.webm",
        "size": 90336151,
        "sha256": "b5a201daa435381642613a1248446226ba99e28b8b166af02fbe27cf6b002a4e",
        "what": "a Mumbai street at night, street level, 3:31, 960x540",
        "author": "Nicolas Vigier", "filmed": "2016-03-29", "licence": "CC0",
    },
    "duesseldorf.ogv": {
        "title": "File:Straßenverkehr in Düsseldorf.ogv",
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/84/Stra%C3%9Fenverkehr_in_D%C3%BCsseldorf.ogv",
        "size": 324905336,
        "sha256": "bf63e9fcdf42fa429617d5e991f183baff619d06dd8aafdc97f76c13d22cc5eb",
        "what": "a tram junction in Duesseldorf (Worringer Platz) by day, 4:35, 1280x720",
        "author": "Slick (Wikimedia Commons user)", "filmed": "2014-03-08", "licence": "CC0",
    },
}


def page_url(title: str) -> str:
    return "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def verified(path: Path, spec: dict) -> bool:
    return path.is_file() and path.stat().st_size == spec["size"] and sha256_of(path) == spec["sha256"]


def download(spec: dict, part: Path, attempts: int = 6) -> None:
    """Fetch spec["url"] into part, resuming a partial file; waits and retries on HTTP 429 and 5xx."""
    for attempt in range(1, attempts + 1):
        have = part.stat().st_size if part.exists() else 0
        if have >= spec["size"]:
            return
        req = urllib.request.Request(spec["url"], headers={"User-Agent": USER_AGENT})
        if have:
            req.add_header("Range", f"bytes={have}-")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if have and r.status != 206:        # the server ignored the range: start over
                    have = 0
                mode = "ab" if have else "wb"
                t0, got = time.monotonic(), have
                with part.open(mode) as f:
                    while True:
                        chunk = r.read(CHUNK)
                        if not chunk:
                            break
                        f.write(chunk)
                        got += len(chunk)
                        if got % (32 * CHUNK) < CHUNK or got >= spec["size"]:
                            el = time.monotonic() - t0
                            rate = (got - have) / el / 1e6 if el else 0.0
                            print(f"    {got / 1e6:7.1f} of {spec['size'] / 1e6:.1f} MB  {rate:.1f} MB/s", flush=True)
            return
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < attempts:
                wait = e.headers.get("Retry-After")
                wait_s = float(wait) if wait and wait.isdigit() else 15.0 * attempt
                print(f"    HTTP {e.code}; waiting {wait_s:.0f} s before attempt {attempt + 1}", flush=True)
                time.sleep(wait_s)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < attempts:
                print(f"    {e}; retrying in {10 * attempt} s", flush=True)
                time.sleep(10 * attempt)
                continue
            raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="folder for the clips (default data\\footage\\commons)")
    ap.add_argument("--only", nargs="+", choices=[n.split(".")[0] for n in CLIPS], help="a subset, by name")
    ap.add_argument("--check", action="store_true", help="verify what is there; download nothing")
    ap.add_argument("--force", action="store_true", help="fetch again even when the checksum matches")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")    # a console codepage without "ß" must not stop a download
    wanted = {n: s for n, s in CLIPS.items() if not args.only or n.split(".")[0] in args.only}
    args.out.mkdir(parents=True, exist_ok=True)
    ok = 0
    for name, spec in wanted.items():
        path = args.out / name
        print(f"{name}: {spec['what']}; {spec['licence']}, {spec['author']}, {spec['filmed']}; {page_url(spec['title'])}")
        if not args.force and verified(path, spec):
            print(f"    present and verified ({spec['size'] / 1e6:.1f} MB, SHA-256 matches)")
            ok += 1
            continue
        if args.check:
            print("    MISSING or wrong" if path.exists() else "    missing")
            continue
        part = path.with_suffix(path.suffix + ".part")
        if path.exists():
            print("    present but its size or checksum differs: fetching again")
            path.unlink()
        if part.exists() and part.stat().st_size > spec["size"]:
            part.unlink()
        print(f"    fetching {spec['size'] / 1e6:.1f} MB from {spec['url']}")
        download(spec, part)
        if part.stat().st_size != spec["size"]:
            print(f"    FAILED: {part.stat().st_size} bytes, expected {spec['size']}; run again to resume")
            continue
        digest = sha256_of(part)
        if digest != spec["sha256"]:
            part.unlink()
            print(f"    FAILED: SHA-256 {digest} differs from the expected {spec['sha256']}; the file was discarded")
            continue
        part.replace(path)
        print("    fetched and verified")
        ok += 1
    print(f"{ok} of {len(wanted)} clips present and verified in {args.out}")
    return 0 if ok == len(wanted) else 1


if __name__ == "__main__":
    raise SystemExit(main())
