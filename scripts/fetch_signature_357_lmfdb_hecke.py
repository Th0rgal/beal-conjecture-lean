#!/usr/bin/env python3
"""Fetch norm-8 Hecke data for the LMFDB-covered signature-(3,5,7) levels.

This internet-facing producer queries the official read-only LMFDB PostgreSQL
mirror.  It emits the complete packet inventory at the eight candidate level
norms <=2059, together with each packet's Hecke polynomial and its eigenvalue at
the unique prime of K7=Q(zeta_7)^+ of norm 8.  It is research data, not a theorem.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from decimal import Decimal
from typing import Any

import psycopg2
import psycopg2.extras

FIELD_LABEL = "3.3.49.1"
COMPLETENESS_BOUND = 2059
LEVELS = sorted(
    (27**a * 7**b, a, b)
    for a in range(6)
    for b in range(4)
    if 27**a * 7**b <= COMPLETENESS_BOUND
)
DB_CONFIG = {
    "host": os.environ.get("LMFDB_HOST", "devmirror.lmfdb.xyz"),
    "port": int(os.environ.get("LMFDB_PORT", "5432")),
    "dbname": os.environ.get("LMFDB_DBNAME", "lmfdb"),
    "user": os.environ.get("LMFDB_USER", "lmfdb"),
    "password": os.environ.get("LMFDB_PASSWORD", "lmfdb"),
    "connect_timeout": 30,
    "sslmode": os.environ.get("LMFDB_SSLMODE", "require"),
}


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral() else str(value)
    raise TypeError(f"cannot encode {type(value).__name__}")


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=json_default,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    norms = [level for level, _a, _b in LEVELS]
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SET statement_timeout = 120000")
            cursor.execute(
                "SELECT primes FROM hmf_fields WHERE label=%s",
                (FIELD_LABEL,),
            )
            field_rows = cursor.fetchall()
            if len(field_rows) != 1:
                raise RuntimeError(f"expected one hmf_fields row, got {len(field_rows)}")
            primes = field_rows[0]["primes"]
            if not isinstance(primes, list):
                raise RuntimeError("hmf_fields.primes is not a list")
            norm8_indices = [
                index for index, prime in enumerate(primes)
                if isinstance(prime, str) and prime.startswith("[8,")
            ]
            if len(norm8_indices) != 1:
                raise RuntimeError(f"expected one norm-8 prime, got {norm8_indices}")
            norm8_index = norm8_indices[0]
            norm8_prime = primes[norm8_index]

            cursor.execute(
                """
                SELECT f.label, f.level_norm, f.level_ideal, f.dimension,
                       f."is_CM", f.is_base_change, f.parallel_weight,
                       h.hecke_polynomial, h.hecke_eigenvalues
                  FROM hmf_forms AS f
                  JOIN hmf_hecke AS h USING (label)
                 WHERE f.field_label=%s
                   AND f.level_norm=ANY(%s)
                   AND f.parallel_weight=2
                 ORDER BY f.level_norm, f.label
                """,
                (FIELD_LABEL, norms),
            )
            rows = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    for row in rows:
        eigenvalues = row.pop("hecke_eigenvalues")
        if not isinstance(eigenvalues, list) or norm8_index >= len(eigenvalues):
            raise RuntimeError(f"missing norm-8 eigenvalue for {row.get('label')}")
        row["hecke_eigenvalue_norm8"] = eigenvalues[norm8_index]

    by_norm: dict[int, list[dict[str, Any]]] = {norm: [] for norm in norms}
    for row in rows:
        norm = int(row["level_norm"])
        if norm not in by_norm:
            raise RuntimeError(f"unexpected level norm {norm}")
        by_norm[norm].append(row)

    levels = [
        {
            "level_norm": level_norm,
            "exponent_pair": [exponent_3, exponent_7],
            "record_count": len(by_norm[level_norm]),
            "records": by_norm[level_norm],
        }
        for level_norm, exponent_3, exponent_7 in LEVELS
    ]
    body = {
        "schema_version": 1,
        "status": "LMFDB complete-range norm-8 Hecke inventory, not a nonexistence theorem",
        "source": {
            "database": "LMFDB read-only PostgreSQL mirror",
            "tables": ["hmf_fields", "hmf_forms", "hmf_hecke"],
            "field_label": FIELD_LABEL,
            "parallel_weight": 2,
            "documented_degree3_completeness_bound": COMPLETENESS_BOUND,
        },
        "prime_ordering": {
            "norm8_index_zero_based": norm8_index,
            "norm8_prime": norm8_prime,
        },
        "candidate_levels_within_bound": norms,
        "total_record_count": len(rows),
        "levels": levels,
    }
    output = dict(body)
    output["certificate_sha256"] = canonical_sha256(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2, default=json_default)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
