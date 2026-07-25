#!/usr/bin/env python3
"""Fetch the pinned Pacetti--Villagra fixed-7 candidate data.

This is a research producer.  It downloads `Outputs/Data.txt` from the exact
public source commit and verifies the Git blob SHA before writing the bytes.
"""

from __future__ import annotations

import hashlib
import pathlib
import sys
import urllib.request

URL = (
    "https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/"
    "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Outputs/Data.txt"
)
EXPECTED_GIT_BLOB_SHA1 = "9c96357834f2298b4d91ab97812c38e84b8ef7a2"


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    request = urllib.request.Request(
        URL,
        headers={
            "User-Agent": (
                "beal-conjecture-lean-research/1.0 "
                "(+https://github.com/Th0rgal/beal-conjecture-lean)"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
    actual = git_blob_sha1(data)
    if actual != EXPECTED_GIT_BLOB_SHA1:
        raise RuntimeError(
            f"source blob mismatch: expected {EXPECTED_GIT_BLOB_SHA1}, got {actual}"
        )
    sys.stdout.buffer.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
