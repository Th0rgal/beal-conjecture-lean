#!/usr/bin/env python3
"""One-shot LMFDB fetcher for the lowest candidate mod-5 level.

This is a research producer, not a trusted checker.  It emits only canonical
query fields and sorted records, stripping volatile API metadata so that a
GitHub Actions producer can commit the result once without creating a loop.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from typing import Any

BASE = "https://www.lmfdb.org/api/hmf_forms/"
FIELDS = [
    "label",
    "level_norm",
    "level_ideal",
    "dimension",
    "is_CM",
    "is_base_change",
    "parallel_weight",
]
QUERY = {
    "field_label": "s3.3.49.1",
    "level_norm": "i729",
    "parallel_weight": "i2",
    "_format": "json",
    "_fields": ",".join(FIELDS),
}


class FetchError(RuntimeError):
    pass


def canonical_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FetchError("LMFDB record must be an object")
    missing = set(FIELDS) - set(value)
    if missing:
        raise FetchError(f"LMFDB record lacks fields: {sorted(missing)}")
    return {field: value[field] for field in FIELDS}


def main() -> int:
    url = BASE + "?" + urllib.parse.urlencode(QUERY)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "beal-conjecture-lean-research/1.0 (+https://github.com/Th0rgal/beal-conjecture-lean)"
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise FetchError("unexpected LMFDB API response structure")
    records = sorted(
        (canonical_record(record) for record in payload["data"]),
        key=lambda record: record["label"],
    )
    output = {
        "schema_version": 1,
        "source": {
            "database": "LMFDB",
            "table": "hmf_forms",
            "api_url": url,
            "field_label": "3.3.49.1",
            "level_norm": 729,
            "parallel_weight": 2,
        },
        "record_count": len(records),
        "records": records,
    }
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
