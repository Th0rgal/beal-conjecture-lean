#!/usr/bin/env python3
"""Combined odd mod-5 residual sieve with the removed-prime-7 trace.

This wrapper starts from the guarded combined semilinear producer, whose generic
HGM polynomials are evaluated in the base Hecke operator and whose
parallel-weight-2 newspace uses Magma's native fixed rational basis.  In the
conductor-drop case ``e7=0`` it additionally imposes the necessary unramified
trace condition

    a_p7 = +/-(7+1) mod 5,

encoded by ``(T_p7-8)(T_p7+8)``.  A zero final dimension is a fail-closed
residual elimination conditional on the imported local-type, monodromy,
level-lowering and semilinear-descent theorems.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

import run_signature_357_magma_mod5_combined_semilinear as base


def replace_once(source: str, old: str, new: str, description: str) -> str:
    count = source.count(old)
    if count != 1:
        raise base.ResearchError(
            f"expected one {description} fragment in generated Magma code, got {count}"
        )
    return source.replace(old, new, 1)


def magma_code(e3: int, e7: int, rows: dict[int, tuple[Any, ...]]) -> str:
    source = base.magma_code(e3, e7, rows)
    removed_block = ""
    if e7 == 0:
        removed_block = r'''
printf "PHASE=removed7-start\n";
T7:=Matrix(F5,HeckeOperator(M,I7));
Id7:=IdentityMatrix(F5,n);
S:=S meet Kernel((T7-F5!8*Id7)*(T7+F5!8*Id7));
printf "PHASE=removed7-ready\n";
'''
    source = replace_once(
        source,
        'printf "NORM8_DIM=%o\\n",Dimension(S);\nfor row in Rows do',
        (
            'printf "NORM8_DIM=%o\\n",Dimension(S);\n'
            + removed_block
            + 'printf "AFTER_REMOVED7_DIM=%o\\n",Dimension(S);\n'
            + 'if Dimension(S) ne 0 then\nfor row in Rows do'
        ),
        "norm-8-to-prime-loop",
    )
    source = replace_once(
        source,
        'end for;\nprintf "FINAL_DIM=%o\\n",Dimension(S);',
        'end for;\nend if;\nprintf "FINAL_DIM=%o\\n",Dimension(S);',
        "prime-loop terminator",
    )
    if "SetRationalBasis" in source:
        raise base.ResearchError("generated v2 code contains SetRationalBasis")
    if "EvalMatrix(Red(P),T)" not in source:
        raise base.ResearchError("generated v2 code lacks base generic-coordinate evaluation")
    if e7 == 0 and "T7-F5!8*Id7" not in source:
        raise base.ResearchError("generated v2 code lacks removed-prime-7 condition")
    return source


def parse_pair(raw: str) -> tuple[int, int]:
    return base.parse_pair(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split-data", type=pathlib.Path, required=True)
    parser.add_argument("--inert-data", type=pathlib.Path, required=True)
    parser.add_argument("--pair", type=parse_pair, required=True)
    args = parser.parse_args()

    split = json.loads(args.split_data.read_text())
    inert = json.loads(args.inert_data.read_text())
    rows = base.rows_from(inert, base.INERT_PRIMES)
    rows.update(base.rows_from(split, base.SPLIT_PRIMES))
    e3, e7 = args.pair
    source = magma_code(e3, e7, rows)

    body: dict[str, Any] = {
        "schema_version": 3,
        "status": (
            "combined odd mod-5 residual HGM, semilinear and removed-prime sieve"
        ),
        "calculator": base.CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "removed_prime7_trace_applied": e7 == 0,
        "removed_prime7_targets_mod5": [2, 3] if e7 == 0 else [],
        "inert_primes": base.INERT_PRIMES,
        "split_primes": base.SPLIT_PRIMES,
        "split_local_sha256": split.get("certificate_sha256"),
        "inert_local_sha256": inert.get("certificate_sha256"),
        "input_bytes": len(source.encode()),
        "generic_coordinate": "base Hecke trace T",
        "specialization_coordinate": (
            "full-cyclotomic transform U when degree ratio is two"
        ),
        "rational_basis_policy": (
            "native parallel-weight-2 newspace basis; no redundant conversion"
        ),
        "early_zero_exit": True,
        "soundness": (
            "zero final dimension is a fail-closed residual elimination; "
            "positive dimension is only necessary"
        ),
    }
    output = ""
    try:
        output = base.submit(source)
        dimensions = {
            prime: int(dimension)
            for prime, dimension in re.findall(r"DIM_AFTER_(\d+)=(\d+)", output)
        }
        final_dimension = base.parse_int(output, "FINAL_DIM")
        if final_dimension == 0:
            for prime in base.INERT_PRIMES + base.SPLIT_PRIMES:
                dimensions.setdefault(str(prime), 0)
        body.update(
            {
                "request_status": "completed",
                "new_dimension": base.parse_int(output, "NEW_DIM"),
                "norm8_dimension": base.parse_int(output, "NORM8_DIM"),
                "after_removed7_dimension": base.parse_int(
                    output, "AFTER_REMOVED7_DIM"
                ),
                "dimensions_after_primes": dimensions,
                "final_dimension": final_dimension,
                "output_tail": output[-5000:],
            }
        )
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-8000:],
            }
        )
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
