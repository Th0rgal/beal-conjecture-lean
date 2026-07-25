#!/usr/bin/env python3
"""Apply inert-prime scalar trace filters to the twisted odd mod-5 levels.

At 11 and 23 the unique prime of K7 is fixed by Gal(K7/Q), so semilinear
Galois symmetry forces the residual trace into F5. Both primes split in the
quadratic cyclotomic untwist, hence the twisted packet trace is unchanged. The
local trace-union polynomial is therefore intersected with X^5-X before
comparison with the residual Hecke module.

The generated Magma code is first routed through the guarded fast repair, so it
never reintroduces the redundant ``SetRationalBasis`` conversion or the manual
stable-subspace coordinate construction.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import run_signature_357_magma_mod5_residual_fast as fast
import run_signature_357_magma_mod5_residual_spaces as base

PRIMES = [11, 23]
LEVEL_PAIRS = [(2, 1), (3, 0), (3, 1)]


def scalar_code(e3: int, e7: int, row: tuple[Any, ...]) -> str:
    code = fast.repaired_code(e3, e7, row)
    old = "  return P;\nend function;"
    new = (
        "  P:=GreatestCommonDivisor(P,X^5-X);\n"
        "  return P;\nend function;"
    )
    count = code.count(old)
    if count != 1:
        raise base.ResearchError(
            f"expected one local-union return fragment, got {count}"
        )
    code = code.replace(old, new, 1)
    if "SetRationalBasis(M);" in code:
        raise base.ResearchError("generated inert code still contains SetRationalBasis")
    if "TS := Restrict(T,S);" not in code:
        raise base.ResearchError("generated inert code lacks native restriction")
    if "GreatestCommonDivisor(P,X^5-X)" not in code:
        raise base.ResearchError("generated inert code lacks scalar-trace filter")
    return code


def parse_pair(raw: str) -> tuple[int, int]:
    try:
        pair = tuple(int(value) for value in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("pair must be e3,e7") from exc
    if len(pair) != 2 or pair not in LEVEL_PAIRS:
        raise argparse.ArgumentTypeError(f"unsupported pair {raw}")
    return pair


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-data", type=pathlib.Path, required=True)
    parser.add_argument("--pair", type=parse_pair, required=True)
    parser.add_argument("--prime", type=int, choices=PRIMES, required=True)
    args = parser.parse_args()

    local = json.loads(args.local_data.read_text(encoding="utf-8"))
    e3, e7 = args.pair
    row = base.candidate_row(local, args.prime)
    code = scalar_code(e3, e7, row)
    record: dict[str, Any] = {
        "schema_version": 2,
        "status": (
            "twisted odd mod-5 inert-prime residual Hecke-module test with "
            "guarded fast repair"
        ),
        "calculator": base.CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "source_local_data_sha256": local["certificate_sha256"],
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "auxiliary_prime": args.prime,
        "prime_inert_in_K7": True,
        "cyclotomic_untwist_value": 1,
        "input_bytes": len(code.encode("utf-8")),
        "local_union_policy": "gcd with X^5-X",
        "rational_basis_policy": (
            "parallel weight 2 and NewSubspace already fix a rational basis; "
            "SetRationalBasis is removed exactly once"
        ),
        "restriction_method": "Magma Restrict(T,S)",
        "repair_guards": True,
        "soundness": (
            "gcd degree zero eliminates every norm-8 twisted residual eigensystem; "
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
                "output_tail": output[-5000:],
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
