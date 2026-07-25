#!/usr/bin/env python3
"""Fetch low-norm Hecke traces for the four complete-range mod-5 survivors.

This internet-facing research producer queries the public LMFDB PostgreSQL
mirror. It emits the common prime ordering and the first stored eigenvalues for
the four rational packets surviving the norm-8 congruence. The output is input
to later auxiliary-prime and two-Frey searches; it is not a theorem certificate.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

import psycopg

FIELD_LABEL = "3.3.49.1"
LABELS = [
    "3.3.49.1-49.1-a",
    "3.3.49.1-189.1-a",
    "3.3.49.1-729.1-b",
    "3.3.49.1-1323.1-a",
]
SAMPLE_SIZE = 40
DSN = os.environ.get(
    "LMFDB_DSN",
    "host=devmirror.lmfdb.xyz port=5432 dbname=lmfdb user=lmfdb password=lmfdb",
)


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    with psycopg.connect(DSN, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT primes FROM hmf_fields WHERE label = %s", (FIELD_LABEL,))
            rows = cursor.fetchall()
            if len(rows) != 1 or not isinstance(rows[0][0], list):
                raise RuntimeError("could not retrieve the K7 prime ordering")
            primes = rows[0][0][:SAMPLE_SIZE]

            cursor.execute(
                """
                SELECT label, hecke_polynomial, hecke_eigenvalues
                  FROM hmf_hecke
                 WHERE label = ANY(%s)
                 ORDER BY label
                """,
                (LABELS,),
            )
            form_rows = cursor.fetchall()

    if [row[0] for row in form_rows] != sorted(LABELS):
        raise RuntimeError("LMFDB did not return exactly the four requested packets")

    records: list[dict[str, Any]] = []
    for label, polynomial, eigenvalues in form_rows:
        if not isinstance(eigenvalues, list) or len(eigenvalues) < len(primes):
            raise RuntimeError(f"insufficient Hecke data for {label}")
        records.append(
            {
                "label": label,
                "hecke_polynomial": polynomial,
                "eigenvalues": eigenvalues[: len(primes)],
            }
        )

    body = {
        "schema_version": 1,
        "status": "LMFDB public-mirror trace sample; research data only",
        "source": {
            "database": "LMFDB public SQL mirror",
            "tables": ["hmf_fields", "hmf_hecke"],
            "field_label": FIELD_LABEL,
            "sample_size": len(primes),
        },
        "primes": primes,
        "records": records,
    }
    output = dict(body)
    output["certificate_sha256"] = canonical_sha256(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
