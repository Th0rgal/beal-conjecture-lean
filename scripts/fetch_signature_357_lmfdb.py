#!/usr/bin/env python3
"""Inventory the LMFDB-covered mod-5 levels for signature (3,5,7).

The legacy public web API is now protected by an interactive CAPTCHA.  LMFDB's
read-only PostgreSQL mirror remains its documented machine interface (and is the
backend of the official LMFDB MCP server).  This research producer queries that
mirror directly.  It is not a trusted theorem checker.
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
    sql = """
        SELECT label, level_norm, level_ideal, dimension,
               "is_CM", is_base_change, parallel_weight
          FROM hmf_forms
         WHERE field_label = %s
           AND level_norm = ANY(%s)
           AND parallel_weight = 2
         ORDER BY level_norm, label
    """
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SET statement_timeout = 120000")
            cursor.execute(sql, (FIELD_LABEL, norms))
            rows = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    by_norm: dict[int, list[dict[str, Any]]] = {norm: [] for norm in norms}
    for row in rows:
        norm = int(row["level_norm"])
        if norm not in by_norm:
            raise RuntimeError(f"database returned unexpected level norm {norm}")
        by_norm[norm].append(row)

    levels: list[dict[str, Any]] = []
    total_dimension = 0
    for level_norm, exponent_3, exponent_7 in LEVELS:
        records = by_norm[level_norm]
        dimension_sum = sum(int(record["dimension"]) for record in records)
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
        "schema_version": 2,
        "status": "LMFDB complete-range form inventory, not a nonexistence theorem",
        "source": {
            "database": "LMFDB read-only PostgreSQL mirror",
            "table": "hmf_forms",
            "field_label": FIELD_LABEL,
            "parallel_weight": 2,
            "documented_degree3_completeness_bound": COMPLETENESS_BOUND,
            "query": "SELECT forms over 3.3.49.1 of parallel weight 2 at the eight candidate level norms <=2059",
        },
        "candidate_levels_within_bound": norms,
        "level_count": len(LEVELS),
        "total_record_count": len(rows),
        "total_coefficient_field_dimension": total_dimension,
        "levels": levels,
    }
    output = dict(body)
    output["certificate_sha256"] = canonical_sha256(body)
    json.dump(output, sys.stdout, sort_keys=True, indent=2, default=json_default)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
