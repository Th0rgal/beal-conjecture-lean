#!/usr/bin/env python3
"""Fetch the LMFDB-covered candidate mod-5 levels for signature (3,5,7).

This internet-facing script is a research producer, not a trusted checker.  The
global conductor certificate leaves 24 levels p3^a*p7^b.  LMFDB documents
complete degree-three Hilbert-newform coverage through level norm 2059, which
contains exactly eight candidate norms.  This first-stage producer fetches only
the complete form inventory; Hecke enrichment is intentionally separate so an
API/schema failure cannot hide the basic finite enumeration.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from typing import Any

BASE = "https://www.lmfdb.org/api/hmf_forms/"
FIELD_LABEL = "3.3.49.1"
COMPLETENESS_BOUND = 2059
LEVELS = sorted(
    (27**a * 7**b, a, b)
    for a in range(6)
    for b in range(4)
    if 27**a * 7**b <= COMPLETENESS_BOUND
)
FIELDS = (
    "label",
    "level_norm",
    "level_ideal",
    "dimension",
    "is_CM",
    "is_base_change",
    "parallel_weight",
)
USER_AGENT = (
    "beal-conjecture-lean-research/1.0 "
    "(+https://github.com/Th0rgal/beal-conjecture-lean)"
)


class FetchError(RuntimeError):
    pass


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fetch_level(level_norm: int) -> tuple[list[dict[str, Any]], list[str]]:
    # LMFDB's public API uses raw text for string equality and the i-prefix for
    # integer equality (as in the repository's already working level-18225 probe).
    params = {
        "field_label": FIELD_LABEL,
        "level_norm": f"i{level_norm}",
        "parallel_weight": "i2",
        "_format": "json",
        "_fields": ",".join(FIELDS),
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    records: list[dict[str, Any]] = []
    urls: list[str] = []
    while url:
        urls.append(url)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.load(response)
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise FetchError(f"unexpected LMFDB API response for level {level_norm}")
        for value in payload["data"]:
            if not isinstance(value, dict):
                raise FetchError("LMFDB record must be an object")
            missing = set(FIELDS) - set(value)
            if missing:
                raise FetchError(
                    f"level {level_norm} record lacks fields: {sorted(missing)}"
                )
            records.append({field: value[field] for field in FIELDS})
        next_url = payload.get("next")
        if next_url is None:
            break
        if not isinstance(next_url, str):
            raise FetchError("LMFDB next link is not a string")
        url = urllib.parse.urljoin(BASE, next_url)
    records.sort(key=lambda record: record["label"])
    return records, urls


def main() -> int:
    levels: list[dict[str, Any]] = []
    query_urls: list[str] = []
    total_records = 0
    total_dimension = 0
    for level_norm, exponent_3, exponent_7 in LEVELS:
        records, urls = fetch_level(level_norm)
        query_urls.extend(urls)
        dimension_sum = sum(int(record["dimension"]) for record in records)
        total_records += len(records)
        total_dimension += dimension_sum
        levels.append(
            {
                "level_norm": level_norm,
                "exponent_pair": [exponent_3, exponent_7],
                "record_count": len(records),
                "total_coefficient_field_dimension": dimension_sum,
                "records": records,
            }
        )
    body = {
        "schema_version": 1,
        "status": "LMFDB complete-range form inventory, not a nonexistence theorem",
        "source": {
            "database": "LMFDB",
            "table": "hmf_forms",
            "field_label": FIELD_LABEL,
            "parallel_weight": 2,
            "documented_degree3_completeness_bound": COMPLETENESS_BOUND,
            "query_urls": sorted(set(query_urls)),
        },
        "candidate_levels_within_bound": [level for level, _a, _b in LEVELS],
        "level_count": len(LEVELS),
        "total_record_count": total_records,
        "total_coefficient_field_dimension": total_dimension,
        "levels": levels,
    }
    output = dict(body)
    output["certificate_sha256"] = canonical_sha256(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
