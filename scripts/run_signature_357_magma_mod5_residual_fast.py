#!/usr/bin/env python3
"""Run the mod-5 residual Hecke-module test without recomputing a rational basis.

The base producer called SetRationalBasis on a parallel-weight newspace. Magma's
Hilbert-modular-form API already gives such a newspace a fixed rational basis;
forcing the conversion again is expensive and prevented the public calculator
from reaching the first residual marker. This wrapper removes that call, uses
the native Restrict intrinsic on the stable kernel, and retains raw output on
failure.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import run_signature_357_magma_mod5_residual_spaces as base


def repaired_code(e3: int, e7: int, row: tuple[Any, ...]) -> str:
    code = base.make_code(e3, e7, row)
    code = code.replace(
        "M := NewSubspace(M0); SetRationalBasis(M);",
        "M := NewSubspace(M0);",
    )
    code = code.replace(
        "TS := Matrix(F5,d,d,&cat[Coordinates(S,S.i*T) : i in [1..d]]);",
        "TS := Restrict(T,S);",
    )
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-data", type=pathlib.Path, required=True)
    parser.add_argument("--pair", type=base.parse_pair, required=True)
    parser.add_argument("--prime", type=int, choices=base.PRIMES, required=True)
    args = parser.parse_args()

    local = json.loads(args.local_data.read_text(encoding="utf-8"))
    e3, e7 = args.pair
    code = repaired_code(e3, e7, base.candidate_row(local, args.prime))
    record: dict[str, Any] = {
        "schema_version": 3,
        "status": "public-Magma residual Hecke-module test with native stable-subspace restriction",
        "calculator": base.CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "source_local_data_sha256": local["certificate_sha256"],
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "auxiliary_prime": args.prime,
        "input_bytes": len(code.encode("utf-8")),
        "rational_basis_policy": "NewSubspace parallel weight 2; no redundant SetRationalBasis call",
        "restriction_method": "Magma Restrict(T,S)",
        "soundness": (
            "gcd degree zero eliminates every norm-8 residual eigensystem; "
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
                "norm8_dimension": base.parse_int(output, "NORM8_DIM"),
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
