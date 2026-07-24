#!/usr/bin/env python3
"""Fetch every current LMFDB Hilbert packet at level norm 10125 over Q(sqrt(5))."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

import psycopg

DSN = os.environ.get(
    "LMFDB_DSN",
    "host=devmirror.lmfdb.xyz port=5432 dbname=lmfdb user=lmfdb password=lmfdb",
)
FIELD = "2.2.5.1"
LEVEL = 10125


def canonical(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def normalize(value: Any) -> Any:
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    return value


def main() -> int:
    with psycopg.connect(DSN, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT primes FROM hmf_fields WHERE label=%s", (FIELD,))
            field_rows = cursor.fetchall()
            if len(field_rows) != 1:
                raise RuntimeError("missing unique hmf_fields row")
            primes = field_rows[0][0]
            cursor.execute(
                '''
                SELECT label, level_norm, level_ideal, dimension,
                       "is_CM", is_base_change, parallel_weight
                FROM hmf_forms
                WHERE field_label=%s AND level_norm=%s AND parallel_weight=2
                ORDER BY label
                ''',
                (FIELD, LEVEL),
            )
            forms = cursor.fetchall()
            labels = [row[0] for row in forms]
            hecke: dict[str, tuple[Any, Any]] = {}
            if labels:
                cursor.execute(
                    '''
                    SELECT label, hecke_polynomial, hecke_eigenvalues
                    FROM hmf_hecke
                    WHERE label=ANY(%s)
                    ''',
                    (labels,),
                )
                for label, polynomial, eigenvalues in cursor.fetchall():
                    hecke[label] = (polynomial, eigenvalues)
    records = []
    for label, norm, ideal, dimension, is_cm, is_bc, weight in forms:
        polynomial, eigenvalues = hecke.get(label, (None, None))
        records.append(
            {
                "label": label,
                "level_norm": int(norm),
                "level_ideal": ideal,
                "dimension": int(dimension),
                "is_CM": is_cm,
                "is_base_change": is_bc,
                "parallel_weight": int(weight),
                "hecke_polynomial": polynomial,
                "hecke_eigenvalues": eigenvalues,
            }
        )
    body = normalize(
        {
            "schema_version": 1,
            "status": "focused current LMFDB SQL inventory for fixed7 level 10125",
            "source": {"database": "LMFDB public SQL mirror", "tables": ["hmf_fields", "hmf_forms", "hmf_hecke"]},
            "field_label": FIELD,
            "level_norm": LEVEL,
            "prime_ordering": primes,
            "record_count": len(records),
            "total_dimension": sum(record["dimension"] for record in records),
            "records": records,
            "nonclaim": "database inventory alone does not identify Magma packet indices and is not interpreted as a theorem",
        }
    )
    output = dict(body)
    output["certificate_sha256"] = canonical(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
