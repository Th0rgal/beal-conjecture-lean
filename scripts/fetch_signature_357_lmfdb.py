#!/usr/bin/env python3
"""Fetch all LMFDB-covered mod-5 levels for signature (3,5,7).

This is an internet-facing research producer, not a trusted checker.  The global
conductor certificate leaves 24 levels p3^a*p7^b.  LMFDB documents complete
degree-three Hilbert-newform coverage through level norm 2059, containing eight
of those levels.  For every form at those levels this script also fetches the
Hecke polynomial and the eigenvalue at the unique prime of norm 8.

The output is canonical JSON.  Empty database responses are recorded as database
output, never interpreted as arithmetic nonexistence without the separately
cited completeness statement.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from typing import Any

API_ROOT = "https://www.lmfdb.org/api/"
FIELD_LABEL = "3.3.49.1"
COMPLETENESS_BOUND = 2059
LEVELS = sorted(
    (27**a * 7**b, a, b)
    for a in range(6)
    for b in range(4)
    if 27**a * 7**b <= COMPLETENESS_BOUND
)
FORM_FIELDS = (
    "label",
    "level_norm",
    "level_ideal",
    "dimension",
    "is_CM",
    "is_base_change",
    "parallel_weight",
)
HECKE_FIELDS = ("label", "hecke_polynomial", "hecke_eigenvalues")
USER_AGENT = (
    "beal-conjecture-lean-research/1.0 "
    "(+https://github.com/Th0rgal/beal-conjecture-lean)"
)


class FetchError(RuntimeError):
    pass


def fetch_payload(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise FetchError(f"unexpected LMFDB API response at {url}")
    return payload


def query_all(
    table: str,
    filters: dict[str, str],
    fields: tuple[str, ...],
) -> tuple[list[dict[str, Any]], list[str]]:
    params = dict(filters)
    params["_format"] = "json"
    params["_fields"] = ",".join(fields)
    url = API_ROOT + table + "/?" + urllib.parse.urlencode(params)
    records: list[dict[str, Any]] = []
    urls: list[str] = []
    while url:
        urls.append(url)
        payload = fetch_payload(url)
        for value in payload["data"]:
            if not isinstance(value, dict):
                raise FetchError(f"non-object record returned by {table}")
            missing = set(fields) - set(value)
            if missing:
                raise FetchError(
                    f"{table} record lacks fields {sorted(missing)}: {value!r}"
                )
            records.append({field: value[field] for field in fields})
        next_url = payload.get("next")
        if next_url is None:
            break
        if not isinstance(next_url, str):
            raise FetchError("LMFDB next link is not a string")
        url = urllib.parse.urljoin(API_ROOT, next_url)
    return records, urls


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    field_rows, query_urls = query_all(
        "hmf_fields",
        {"label": "s" + FIELD_LABEL},
        ("label", "primes"),
    )
    if len(field_rows) != 1 or field_rows[0]["label"] != FIELD_LABEL:
        raise FetchError(f"expected exactly one hmf_fields row for {FIELD_LABEL}")
    primes = field_rows[0]["primes"]
    if not isinstance(primes, list) or any(not isinstance(p, str) for p in primes):
        raise FetchError("hmf_fields.primes is not a string array")
    norm8_indices = [index for index, prime in enumerate(primes) if prime.startswith("[8,")]
    if len(norm8_indices) != 1:
        raise FetchError(f"expected one prime of norm 8, got {norm8_indices}")
    norm8_index = norm8_indices[0]
    norm8_prime = primes[norm8_index]

    inventories: list[dict[str, Any]] = []
    total = 0
    total_dimension = 0
    for level_norm, exponent_3, exponent_7 in LEVELS:
        forms, urls = query_all(
            "hmf_forms",
            {
                "field_label": "s" + FIELD_LABEL,
                "level_norm": f"i{level_norm}",
                "parallel_weight": "i2",
            },
            FORM_FIELDS,
        )
        query_urls.extend(urls)
        forms.sort(key=lambda record: record["label"])
        enriched: list[dict[str, Any]] = []
        for form in forms:
            label = form["label"]
            if not isinstance(label, str):
                raise FetchError("form label is not a string")
            hecke_rows, urls = query_all(
                "hmf_hecke",
                {"label": "s" + label},
                HECKE_FIELDS,
            )
            query_urls.extend(urls)
            if len(hecke_rows) != 1 or hecke_rows[0]["label"] != label:
                raise FetchError(f"expected exactly one hmf_hecke row for {label}")
            hecke = hecke_rows[0]
            eigenvalues = hecke["hecke_eigenvalues"]
            if not isinstance(eigenvalues, list) or norm8_index >= len(eigenvalues):
                raise FetchError(f"missing norm-8 Hecke eigenvalue for {label}")
            enriched.append(
                {
                    **form,
                    "hecke_polynomial": hecke["hecke_polynomial"],
                    "hecke_eigenvalue_norm8": eigenvalues[norm8_index],
                }
            )
        record_count = len(enriched)
        dimension_sum = sum(int(record["dimension"]) for record in enriched)
        total += record_count
        total_dimension += dimension_sum
        inventories.append(
            {
                "level_norm": level_norm,
                "exponent_pair": [exponent_3, exponent_7],
                "record_count": record_count,
                "total_coefficient_field_dimension": dimension_sum,
                "records": enriched,
            }
        )

    body = {
        "schema_version": 2,
        "status": "LMFDB complete-range inventory, not a standalone nonexistence theorem",
        "source": {
            "database": "LMFDB",
            "tables": ["hmf_fields", "hmf_forms", "hmf_hecke"],
            "field_label": FIELD_LABEL,
            "parallel_weight": 2,
            "documented_degree3_completeness_bound": COMPLETENESS_BOUND,
            "query_urls": sorted(set(query_urls)),
        },
        "prime_ordering": {
            "norm8_index_zero_based": norm8_index,
            "norm8_prime": norm8_prime,
        },
        "candidate_levels_within_bound": [level for level, _a, _b in LEVELS],
        "level_count": len(LEVELS),
        "total_record_count": total,
        "total_coefficient_field_dimension": total_dimension,
        "levels": inventories,
    }
    output = dict(body)
    output["certificate_sha256"] = canonical_sha256(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
