#!/usr/bin/env python3
"""Fetch every currently indexed HMF packet at the seven open (3,5,7) levels.

This is an internet-facing producer. LMFDB does not document completeness above
level norm 2059, so absence from this output is never interpreted as emptiness.
The output retains coefficient fields and selected Hecke eigenvalues for later
finite trace sieves.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from typing import Any

import psycopg

FIELD_LABEL = "3.3.49.1"
LEVELS = [5103, 9261, 19683, 35721, 137781, 250047, 964467]
AUXILIARY_RATIONAL_PRIMES = [2, 13, 29, 41, 43]
DSN = os.environ.get(
    "LMFDB_DSN",
    "host=devmirror.lmfdb.xyz port=5432 dbname=lmfdb user=lmfdb password=lmfdb",
)


class FetchError(RuntimeError):
    pass


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def normalize(value: Any) -> Any:
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    return value


def prime_metadata(
    primes: list[Any],
) -> tuple[list[dict[str, Any]], dict[int, list[int]]]:
    records: list[dict[str, Any]] = []
    indices: dict[int, list[int]] = {
        prime: [] for prime in AUXILIARY_RATIONAL_PRIMES
    }
    pattern = re.compile(r"^\[(\d+),\s*(\d+),")
    for index, encoded in enumerate(primes):
        if not isinstance(encoded, str):
            continue
        match = pattern.match(encoded)
        if match is None:
            continue
        norm, rational_prime = map(int, match.groups())
        if rational_prime in indices:
            indices[rational_prime].append(index)
            records.append(
                {
                    "index_zero_based": index,
                    "rational_prime": rational_prime,
                    "norm": norm,
                    "encoded_prime": encoded,
                }
            )
    if len(indices[2]) != 1 or not all(
        indices[prime] for prime in AUXILIARY_RATIONAL_PRIMES
    ):
        raise FetchError(f"selected prime indices are incomplete: {indices}")
    return records, indices


def main() -> int:
    with psycopg.connect(DSN, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT primes FROM hmf_fields WHERE label=%s", (FIELD_LABEL,)
            )
            field_rows = cursor.fetchall()
            if len(field_rows) != 1 or not isinstance(field_rows[0][0], list):
                raise FetchError(
                    "could not retrieve the unique hmf_fields prime ordering"
                )
            primes = field_rows[0][0]
            selected_primes, indices = prime_metadata(primes)

            cursor.execute(
                '''
                SELECT label, level_norm, level_ideal, dimension,
                       "is_CM", is_base_change, parallel_weight
                FROM hmf_forms
                WHERE field_label=%s
                  AND level_norm=ANY(%s)
                  AND parallel_weight=2
                ORDER BY level_norm, label
                ''',
                (FIELD_LABEL, LEVELS),
            )
            forms = cursor.fetchall()
            labels = [row[0] for row in forms]
            hecke: dict[str, tuple[Any, Any]] = {}
            if labels:
                cursor.execute(
                    '''
                    SELECT label, hecke_polynomial, hecke_eigenvalues
                    FROM hmf_hecke WHERE label=ANY(%s)
                    ''',
                    (labels,),
                )
                for label, polynomial, eigenvalues in cursor.fetchall():
                    if label in hecke:
                        raise FetchError(f"duplicate hmf_hecke row for {label}")
                    hecke[label] = (polynomial, eigenvalues)

    by_level: dict[int, list[dict[str, Any]]] = {
        level: [] for level in LEVELS
    }
    for (
        label,
        level_norm,
        level_ideal,
        dimension,
        is_cm,
        is_base_change,
        weight,
    ) in forms:
        if label not in hecke:
            raise FetchError(f"missing hmf_hecke row for {label}")
        polynomial, eigenvalues = hecke[label]
        if not isinstance(eigenvalues, list):
            raise FetchError(f"malformed eigenvalue list for {label}")
        selected: dict[str, list[dict[str, Any]]] = {}
        for rational_prime, prime_indices in indices.items():
            values: list[dict[str, Any]] = []
            for index in prime_indices:
                if index >= len(eigenvalues):
                    raise FetchError(
                        f"missing Hecke eigenvalue {index} for {label}"
                    )
                meta = next(
                    item
                    for item in selected_primes
                    if item["index_zero_based"] == index
                )
                values.append(
                    {
                        "index_zero_based": index,
                        "norm": meta["norm"],
                        "encoded_prime": meta["encoded_prime"],
                        "eigenvalue": eigenvalues[index],
                    }
                )
            selected[str(rational_prime)] = values
        by_level[int(level_norm)].append(
            {
                "label": label,
                "level_norm": int(level_norm),
                "level_ideal": level_ideal,
                "dimension": int(dimension),
                "is_CM": is_cm,
                "is_base_change": is_base_change,
                "parallel_weight": int(weight),
                "hecke_polynomial": polynomial,
                "selected_hecke_eigenvalues": selected,
            }
        )

    levels = []
    for level in LEVELS:
        records = by_level[level]
        levels.append(
            {
                "level_norm": level,
                "record_count": len(records),
                "total_coefficient_field_dimension": sum(
                    record["dimension"] for record in records
                ),
                "records": records,
            }
        )
    body = normalize(
        {
            "schema_version": 1,
            "status": (
                "LMFDB indexed high-level inventory; explicitly not a "
                "completeness certificate"
            ),
            "source": {
                "database": "LMFDB public SQL mirror",
                "tables": ["hmf_fields", "hmf_forms", "hmf_hecke"],
                "field_label": FIELD_LABEL,
                "parallel_weight": 2,
                "documented_completeness_bound": 2059,
            },
            "candidate_level_norms": LEVELS,
            "selected_prime_metadata": selected_primes,
            "level_count": len(LEVELS),
            "indexed_record_count": sum(
                level["record_count"] for level in levels
            ),
            "indexed_total_coefficient_field_dimension": sum(
                level["total_coefficient_field_dimension"] for level in levels
            ),
            "levels": levels,
            "nonclaim": (
                "zero records at a level do not prove that its "
                "Hilbert-newform space is empty"
            ),
        }
    )
    output = dict(body)
    output["certificate_sha256"] = canonical_sha256(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
