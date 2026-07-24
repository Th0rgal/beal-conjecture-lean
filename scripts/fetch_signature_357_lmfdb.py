#!/usr/bin/env python3
"""Fetch the LMFDB-covered candidate mod-5 levels for signature (3,5,7).

This is a research producer, not a trusted checker.  The global conductor
certificate leaves 24 levels p3^a*p7^b.  LMFDB documents complete degree-three
Hilbert-newform coverage through level norm 2059, which contains exactly the
first eight of those levels.  This script queries those eight norms and emits a
canonical inventory; an empty response is recorded as database output, never as
an arithmetic nonexistence theorem.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from typing import Any

BASE = "https://www.lmfdb.org/api/hmf_forms/"
FIELD_LABEL = "3.3.49.1"
LEVELS = sorted(
    (27**a * 7**b, a, b)
    for a in range(6)
    for b in range(4)
    if 27**a * 7**b <= 2059
)
FIELDS = [
    "label",
    "level_norm",
    "level_ideal",
    "dimension",
    "is_CM",
    "is_base_change",
    "parallel_weight",
]


class FetchError(RuntimeError):
    pass


def canonical_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FetchError("LMFDB record must be an object")
    missing = set(FIELDS) - set(value)
    if missing:
        raise FetchError(f"LMFDB record lacks fields: {sorted(missing)}")
    return {field: value[field] for field in FIELDS}


def fetch_level(level_norm: int) -> tuple[str, list[dict[str, Any]]]:
    query = {
        "field_label": FIELD_LABEL,
        "level_norm": f"i{level_norm}",
        "parallel_weight": "i2",
        "_format": "json",
        "_fields": ",".join(FIELDS),
    }
    url = BASE + "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "beal-conjecture-lean-research/1.0 "
                "(+https://github.com/Th0rgal/beal-conjecture-lean)"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise FetchError(f"unexpected LMFDB API response for level {level_norm}")
    records = sorted(
        (canonical_record(record) for record in payload["data"]),
        key=lambda record: record["label"],
    )
    return url, records


def main() -> int:
    inventories: list[dict[str, Any]] = []
    total = 0
    for level_norm, exponent_3, exponent_7 in LEVELS:
        url, records = fetch_level(level_norm)
        total += len(records)
        inventories.append(
            {
                "level_norm": level_norm,
                "exponent_pair": [exponent_3, exponent_7],
                "api_url": url,
                "record_count": len(records),
                "records": records,
            }
        )
    output = {
        "schema_version": 1,
        "status": "LMFDB coverage inventory, not a nonexistence certificate",
        "source": {
            "database": "LMFDB",
            "table": "hmf_forms",
            "field_label": FIELD_LABEL,
            "parallel_weight": 2,
            "documented_degree3_completeness_bound": 2059,
        },
        "candidate_levels_within_bound": [level for level, _a, _b in LEVELS],
        "level_count": len(LEVELS),
        "total_record_count": total,
        "levels": inventories,
    }
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
