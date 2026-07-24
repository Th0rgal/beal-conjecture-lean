#!/usr/bin/env python3
"""Query the public LMFDB SQL mirror for the complete low-level HMF frontier.

This is an internet-facing research producer. It queries the three underlying
LMFDB tables directly so that API rate limiting or browser challenges cannot
silently turn a complete enumeration into an empty response.

The only non-stdlib dependency is psycopg 3, installed by the dedicated research
workflow. The emitted JSON is canonical and includes a SHA-256 digest; a later
offline checker must validate any modular elimination based on it.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

import psycopg

FIELD_LABEL = "3.3.49.1"
COMPLETENESS_BOUND = 2059
# The current optimized conductor program uses p3^3*p7^3.  Exponents >=4 at p3
# already have level norm >2059, so this choice does not affect the complete
# low-level inventory produced here.
LEVELS = sorted(
    (27**a * 7**b, a, b)
    for a in range(4)
    for b in range(4)
    if 27**a * 7**b <= COMPLETENESS_BOUND
)
DSN = os.environ.get(
    "LMFDB_DSN",
    "host=devmirror.lmfdb.xyz port=5432 dbname=lmfdb user=lmfdb password=lmfdb",
)


class FetchError(RuntimeError):
    pass


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize(value: Any) -> Any:
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    return value


def main() -> int:
    level_values = [level for level, _a, _b in LEVELS]
    with psycopg.connect(DSN, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT primes FROM hmf_fields WHERE label = %s", (FIELD_LABEL,))
            field_rows = cursor.fetchall()
            if len(field_rows) != 1:
                raise FetchError(f"expected one hmf_fields row, got {len(field_rows)}")
            primes = field_rows[0][0]
            if not isinstance(primes, list):
                raise FetchError("hmf_fields.primes did not decode as a list")
            norm8_indices = [
                index
                for index, prime in enumerate(primes)
                if isinstance(prime, str) and prime.startswith("[8,")
            ]
            if len(norm8_indices) != 1:
                raise FetchError(f"expected one norm-8 prime, got {norm8_indices}")
            norm8_index = norm8_indices[0]
            norm8_prime = primes[norm8_index]

            cursor.execute(
                """
                SELECT label, level_norm, level_ideal, dimension,
                       "is_CM", is_base_change, parallel_weight
                FROM hmf_forms
                WHERE field_label = %s
                  AND level_norm = ANY(%s)
                  AND parallel_weight = 2
                ORDER BY level_norm, label
                """,
                (FIELD_LABEL, level_values),
            )
            form_rows = cursor.fetchall()

            labels = [row[0] for row in form_rows]
            hecke_by_label: dict[str, tuple[Any, Any]] = {}
            if labels:
                cursor.execute(
                    """
                    SELECT label, hecke_polynomial, hecke_eigenvalues
                    FROM hmf_hecke
                    WHERE label = ANY(%s)
                    """,
                    (labels,),
                )
                for label, polynomial, eigenvalues in cursor.fetchall():
                    if label in hecke_by_label:
                        raise FetchError(f"duplicate hmf_hecke row for {label}")
                    hecke_by_label[label] = (polynomial, eigenvalues)

    records_by_level: dict[int, list[dict[str, Any]]] = {
        level: [] for level in level_values
    }
    for (
        label,
        level_norm,
        level_ideal,
        dimension,
        is_cm,
        is_base_change,
        parallel_weight,
    ) in form_rows:
        if label not in hecke_by_label:
            raise FetchError(f"missing hmf_hecke row for {label}")
        polynomial, eigenvalues = hecke_by_label[label]
        if not isinstance(eigenvalues, list) or norm8_index >= len(eigenvalues):
            raise FetchError(f"missing norm-8 Hecke eigenvalue for {label}")
        records_by_level[int(level_norm)].append(
            {
                "label": label,
                "level_norm": int(level_norm),
                "level_ideal": level_ideal,
                "dimension": int(dimension),
                "is_CM": is_cm,
                "is_base_change": is_base_change,
                "parallel_weight": int(parallel_weight),
                "hecke_polynomial": polynomial,
                "hecke_eigenvalue_norm8": eigenvalues[norm8_index],
            }
        )

    levels: list[dict[str, Any]] = []
    total_records = 0
    total_dimension = 0
    for level, exponent_3, exponent_7 in LEVELS:
        records = sorted(records_by_level[level], key=lambda record: record["label"])
        dimension_sum = sum(record["dimension"] for record in records)
        total_records += len(records)
        total_dimension += dimension_sum
        levels.append(
            {
                "level_norm": level,
                "exponent_pair": [exponent_3, exponent_7],
                "record_count": len(records),
                "total_coefficient_field_dimension": dimension_sum,
                "records": records,
            }
        )

    body = normalize(
        {
            "schema_version": 2,
            "status": (
                "LMFDB public-mirror complete-range inventory; database data, "
                "not a standalone nonexistence theorem"
            ),
            "source": {
                "database": "LMFDB public SQL mirror",
                "tables": ["hmf_fields", "hmf_forms", "hmf_hecke"],
                "field_label": FIELD_LABEL,
                "parallel_weight": 2,
                "documented_degree3_completeness_bound": COMPLETENESS_BOUND,
                "global_level_bound": "p3^3*p7^3",
            },
            "prime_ordering": {
                "norm8_index_zero_based": norm8_index,
                "norm8_prime": norm8_prime,
            },
            "candidate_levels_within_bound": level_values,
            "level_count": len(LEVELS),
            "total_record_count": total_records,
            "total_coefficient_field_dimension": total_dimension,
            "levels": levels,
        }
    )
    output = dict(body)
    output["certificate_sha256"] = canonical_sha256(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
