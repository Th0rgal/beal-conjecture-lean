#!/usr/bin/env python3
"""Fetch all four fixed-7 Hilbert spaces from the public LMFDB SQL mirror.

The levels are the four Pacetti--Villagra levels over Q(sqrt(5)):

    3^i * p5^j,  (i,j) in {(2,2),(2,3),(3,2),(3,3)}.

Their ideal norms are 2025, 10125, 18225 and 91125.  The output includes each
newform's coefficient-field polynomial and the complete stored Hecke-eigenvalue
array, aligned with the pinned `hmf_fields.primes` ordering.  It is a research
producer, not a theorem checker.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

import psycopg

FIELD_LABEL = "2.2.5.1"
LEVELS = [
    (2025, 2, 2),
    (10125, 2, 3),
    (18225, 3, 2),
    (91125, 3, 3),
]
EXPECTED_COUNTS = {2025: 14, 10125: 35, 18225: 111, 91125: 112}
DSN = os.environ.get(
    "LMFDB_DSN",
    "host=devmirror.lmfdb.xyz port=5432 dbname=lmfdb user=lmfdb password=lmfdb",
)


class FetchError(RuntimeError):
    pass


def normalize(value: Any) -> Any:
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    return value


def digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    level_norms = [row[0] for row in LEVELS]
    with psycopg.connect(DSN, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT primes FROM hmf_fields WHERE label = %s", (FIELD_LABEL,))
            rows = cursor.fetchall()
            if len(rows) != 1 or not isinstance(rows[0][0], list):
                raise FetchError("expected one hmf_fields row with a prime array")
            primes = rows[0][0]

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
                (FIELD_LABEL, level_norms),
            )
            form_rows = cursor.fetchall()
            labels = [row[0] for row in form_rows]

            hecke: dict[str, tuple[Any, Any]] = {}
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
                    if label in hecke:
                        raise FetchError(f"duplicate hmf_hecke row for {label}")
                    hecke[label] = (polynomial, eigenvalues)

    records_by_level: dict[int, list[dict[str, Any]]] = {
        norm: [] for norm in level_norms
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
        if label not in hecke:
            raise FetchError(f"missing hmf_hecke row for {label}")
        polynomial, eigenvalues = hecke[label]
        if not isinstance(eigenvalues, list):
            raise FetchError(f"Hecke eigenvalues are not an array for {label}")
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
                "hecke_eigenvalues": eigenvalues,
            }
        )

    levels: list[dict[str, Any]] = []
    total_records = 0
    total_dimension = 0
    for norm, exponent_3, exponent_5 in LEVELS:
        records = sorted(records_by_level[norm], key=lambda record: record["label"])
        if len(records) != EXPECTED_COUNTS[norm]:
            raise FetchError(
                f"level {norm}: expected {EXPECTED_COUNTS[norm]} packets, got {len(records)}"
            )
        dimension_sum = sum(record["dimension"] for record in records)
        total_records += len(records)
        total_dimension += dimension_sum
        levels.append(
            {
                "level_norm": norm,
                "conductor_exponents": [exponent_3, exponent_5],
                "record_count": len(records),
                "total_coefficient_field_dimension": dimension_sum,
                "records": records,
            }
        )

    body = normalize(
        {
            "schema_version": 1,
            "status": "LMFDB mirror inventory for replaying the fixed-7 elimination",
            "source": {
                "database": "LMFDB public SQL mirror",
                "tables": ["hmf_fields", "hmf_forms", "hmf_hecke"],
                "field_label": FIELD_LABEL,
                "paper_source_commit": "e88f914c577ab6cf9a45e5cdd82c1993477fb423",
            },
            "prime_ordering": primes,
            "levels": levels,
            "total_record_count": total_records,
            "total_coefficient_field_dimension": total_dimension,
        }
    )
    output = dict(body)
    output["certificate_sha256"] = digest(body)
    json.dump(output, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
