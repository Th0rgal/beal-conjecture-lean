#!/usr/bin/env python3
"""Run the fixed-7 level-(3,3) residual test without a redundant basis conversion.

Parallel-weight newspaces already have a fixed rational basis in Magma. The
previous producer called SetRationalBasis again before printing any marker and
therefore failed closed on the public calculator. This wrapper removes that
conversion, restricts the auxiliary Hecke operator with Magma's native Restrict
intrinsic, and retains raw output whenever a request fails.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

import run_signature_357_magma_fixed7_residual_space as base


def repaired_code(row: str) -> str:
    code = base.make_code(row)
    code = code.replace(
        "M := NewSubspace(M0); SetRationalBasis(M);",
        "M := NewSubspace(M0);",
    )
    code = code.replace(
        "TS := Matrix(F7,d,d,&cat[Coordinates(S,S.i*T) : i in [1..d]]);",
        "TS := Restrict(T,S);",
    )
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prime", type=int, choices=base.PRIMES, required=True)
    args = parser.parse_args()

    row = base.selected_row(base.fetch_data(), args.prime)
    code = repaired_code(row)
    record: dict[str, Any] = {
        "schema_version": 2,
        "status": "fixed-7 level-(3,3) residual test with native stable-subspace restriction",
        "calculator": base.CALCULATOR_URL,
        "candidate_blob_sha1": base.EXPECTED_DATA_BLOB,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "auxiliary_prime": args.prime,
        "input_bytes": len(code.encode("utf-8")),
        "rational_basis_policy": "NewSubspace parallel weight 2; no redundant SetRationalBasis call",
        "restriction_method": "Magma Restrict(T,S)",
        "soundness": (
            "gcd degree zero eliminates every superspecial residual eigensystem; "
            "positive degree is only a necessary survivor"
        ),
    }
    output = ""
    try:
        output = base.submit(code)
        record.update(
            {
                "request_status": "completed",
                "new_dimension": base.parse_int(output, "NEW_DIM"),
                "superspecial_dimension": base.parse_int(
                    output, "SUPERSPECIAL_DIM"
                ),
                "union_polynomial_degree": base.parse_int(
                    output, "UNION_POLYNOMIAL_DEGREE"
                ),
                "restricted_charpoly_degree": base.parse_int(
                    output, "RESTRICTED_CHARPOLY_DEGREE"
                ),
                "gcd_degree": base.parse_int(output, "GCD_DEGREE"),
                "output_tail": output[-4000:],
            }
        )
    except Exception as exc:
        record.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-8000:],
            }
        )

    body = dict(record)
    result = dict(body)
    result["certificate_sha256"] = base.canonical_sha256(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
