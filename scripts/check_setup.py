r"""check_setup.py - the last step of setup.ps1: what XProtect and the Hafnia gateway report, at no request.

    .venv\Scripts\python.exe scripts\check_setup.py

Prints the cameras XProtect knows (and whether lens_1 is among them), the lens publisher's spool, and today's count
on the gateway (HAFNIA_GW_PASSWORD from the environment, else the user-scope variable). Exit code 1 only when
XProtect cannot be reached: the gateway check reports its problem and goes on.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))


def main() -> int:
    from hafnia.xprotect_rest import XProtect
    try:
        cams = XProtect().cameras()
    except Exception as e:
        print(f"XProtect: cannot list cameras ({e!r}): is the API Gateway on http://localhost up, and is this a "
              f"Windows user XProtect knows?")
        return 1
    print(f"XProtect: {len(cams)} cameras; lens_1 {'present' if 'lens_1' in cams else 'MISSING (scripts/setup_lens.ps1)'}")
    spool = REPO / "run" / "lens" / "spool"
    print(f"Lens spool: {spool} ({'present' if spool.exists() else 'not yet: the publisher creates it'})")
    try:
        from hafnia.gateway import Gateway
        from lens_compare import gateway_password
        gw = Gateway()
        gw.login(gateway_password())
        q = gw.quota()
        print(f"Hafnia gateway: today's count {q['DailySummaryCount'] if q else 'unknown'} (the allowance is 500 a day)")
    except Exception as e:
        print(f"Hafnia gateway: not checked ({e!r}); set HAFNIA_GW_PASSWORD (user scope) and make sure the gateway "
              f"runs on https://localhost:15443")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
