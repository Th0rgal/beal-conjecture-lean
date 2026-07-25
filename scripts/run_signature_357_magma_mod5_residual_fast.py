#!/usr/bin/env python3
"""Run the mod-5 residual Hecke-module test without recomputing a rational basis.

The base producer calls ``SetRationalBasis`` on a parallel-weight-2 newspace.
Magma already permanently fixes a rational basis for such spaces, and also for
spaces returned by ``NewSubspace``. Repeating the conversion is expensive and
prevented the public calculator from reaching the first residual marker.

This wrapper removes that call with fail-closed replacement guards, uses the
native ``Restrict`` intrinsic on the stable kernel, and accepts both the
untwisted and cyclotomic-untwisted level pairs used by the active workflows.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import run_signature_357_magma_mod5_residual_spaces as base

LEVEL_PAIRS = [(2, 1), (3, 0), (2, 2), (3, 1), (3, 2)]


def replace_once(code: str, old: str, new: str, description: str) -> str:
    """Replace one generated-code fragment and reject silent producer drift."""
    count = code.count(old)
    if count != 1:
        raise base.ResearchError(
            f"expected one {description} fragment in generated Magma code, got {count}"
        )
    return code.replace(old, new, 1)


def repaired_code(e3: int, e7: int, row: tuple[Any, ...]) -> str:
    code = base.make_code(e3, e7, row)
    code = replace_once(
        code,
        "SetRationalBasis(M);\n",
        "",
        "redundant SetRationalBasis",
    )
    code = replace_once(
        code,
        "TS := Matrix(F5,d,d,&cat[Coordinates(S,S.i*T) : i in [1..d]]);",
        "TS := Restrict(T,S);",
        "manual stable-subspace restriction",
    )
    if "SetRationalBasis(M);" in code:
        raise base.ResearchError("generated code still contains SetRationalBasis")
    if "TS := Restrict(T,S);" not in code:
        raise base.ResearchError("generated code lacks native stable-subspace restriction")
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
    parser.add_argument("--prime", type=int, choices=base.PRIMES, required=True)
    args = parser.parse_args()

    local = json.loads(args.local_data.read_text(encoding="utf-8"))
    e3, e7 = args.pair
    code = repaired_code(e3, e7, base.candidate_row(local, args.prime))
    record: dict[str, Any] = {
        "schema_version": 4,
        "status": (
            "public-Magma residual Hecke-module test with guarded native "
            "stable-subspace restriction"
        ),
        "calculator": base.CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "source_local_data_sha256": local["certificate_sha256"],
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "auxiliary_prime": args.prime,
        "input_bytes": len(code.encode("utf-8")),
        "rational_basis_policy": (
            "parallel weight 2 and NewSubspace already fix a rational basis; "
            "SetRationalBasis is removed exactly once"
        ),
        "restriction_method": "Magma Restrict(T,S)",
        "repair_guards": True,
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
