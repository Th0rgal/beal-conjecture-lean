#!/usr/bin/env python3
"""Probe public LMFDB coverage for the fixed-7 level-(3,2) search.

This is a research inventory helper, not a theorem checker. It reads the exact
API URL pinned in Research/Signature357/lmfdb_level18225_query.txt, downloads the
JSON response with the standard library, and emits a compact summary. Network or
coverage failure is reported explicitly; an empty response is never interpreted
as arithmetic nonexistence.
"""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
QUERY = ROOT / "Research" / "Signature357" / "lmfdb_level18225_query.txt"


def main() -> int:
    url = QUERY.read_text(encoding="utf-8").strip()
    if not url.startswith("https://www.lmfdb.org/api/hmf_forms/"):
        raise ValueError("unexpected LMFDB query endpoint")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "beal-conjecture-lean research certificate probe"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    records = payload.get("data", [])
    if not isinstance(records, list):
        raise ValueError("LMFDB response has no data array")
    summary = {
        "query": url,
        "record_count": len(records),
        "labels": [record.get("label") for record in records],
        "records": records,
        "interpretation": (
            "coverage inventory only; zero records is not a nonexistence theorem"
        ),
    }
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
