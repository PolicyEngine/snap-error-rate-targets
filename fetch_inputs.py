"""Download the pinned input from PolicyEngine/snap-qc-sim and check its hash.

``inputs/component_targets.json`` already holds a copy. Run this script to
replace it with a fresh download from the pinned commit, or pass ``--check``
to confirm the committed copy matches it.

PolicyEngine/snap-qc-sim builds the file (``analysis/build_component_targets.py``)
from the FY2024 SNAP QC public-use file and USDA's FY2024 and FY2025 payment
error rate reports, and publishes it under the Apache License 2.0.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request

from snap_targets import INPUT, INPUT_SHA256

COMMIT = "718fac92da2508ed6e04405fbd4d52d7172adeb1"
URL = (
    "https://raw.githubusercontent.com/PolicyEngine/snap-qc-sim/"
    f"{COMMIT}/analysis/component_targets.json"
)


def download() -> bytes:
    with urllib.request.urlopen(URL, timeout=60) as response:
        return response.read()


def main(argv: list[str]) -> int:
    payload = download()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != INPUT_SHA256:
        print(f"Hash mismatch for {URL}: {digest}", file=sys.stderr)
        return 1
    if "--check" in argv:
        local = hashlib.sha256(INPUT.read_bytes()).hexdigest()
        if local != digest:
            print(f"{INPUT} differs from {URL}", file=sys.stderr)
            return 1
        print(f"{INPUT.name} matches snap-qc-sim at {COMMIT[:7]}")
        return 0
    INPUT.parent.mkdir(exist_ok=True)
    INPUT.write_bytes(payload)
    print(f"Wrote {INPUT} from snap-qc-sim at {COMMIT[:7]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
