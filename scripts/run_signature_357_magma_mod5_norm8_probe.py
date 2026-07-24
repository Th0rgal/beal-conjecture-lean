#!/usr/bin/env python3
"""Measure the mandatory norm-8 residual kernel at an odd e3=3 level.

Every hypothetical odd-branch solution has residual mod-5 Hecke trace zero at
the unique prime of norm 8.  Earlier producers attempted the complete
multi-prime sieve immediately and retained no result when construction of the
first rational Hecke matrix exhausted the calculator memory limit.

This focused probe clears the definite-Hecke precomputation accumulated while
constructing the newspace, computes only T_P2, reduces it modulo 5 immediately,
deletes the rational matrix and prime cache, and records ``dim ker(T_P2)``.  A
zero kernel eliminates the level.  A positive kernel is only a necessary
survivor and becomes the input dimension for later removed-prime and auxiliary
filters.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_357_magma_mod5_combined_semilinear as base

LEVEL_PAIRS = [(3, 0), (3, 1)]


def parse_pair(raw: str) -> tuple[int, int]:
    try:
        pair = tuple(int(value) for value in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("pair must be e3,e7") from exc
    if len(pair) != 2 or pair not in LEVEL_PAIRS:
        raise argparse.ArgumentTypeError(f"unsupported pair {raw}")
    return pair


def magma_code(e3: int, e7: int) -> str:
    return rf'''
_<x> := PolynomialRing(Rationals());
K<w> := NumberField(x^3-x^2-2*x+1); OK := Integers(K);
I3 := Factorisation(3*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
I2 := Factorisation(2*OK)[1][1];
F5 := GF(5);
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,I3^{e3}*I7^{e7});
printf "AMBIENT_DIM=%o\n",Dimension(M0);
M:=NewSubspace(M0);
n:=Dimension(M);
printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M);
DeleteHeckePrecomputation(O);
printf "PHASE=old-hecke-cache-cleared\n";
printf "PHASE=T2-rational-start\n";
TQ:=HeckeOperator(M,I2);
printf "PHASE=T2-rational-ready\n";
T:=Matrix(F5,TQ);
delete TQ;
DeleteHeckePrecomputation(O,I2);
printf "PHASE=T2-mod5-ready\n";
d:=Nullity(T);
printf "NORM8_DIM=%o\n",d;
printf "FINAL_DIM=%o\n",d;
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise base.ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", type=parse_pair, required=True)
    args = parser.parse_args()
    e3, e7 = args.pair
    code = magma_code(e3, e7)
    record: dict[str, Any] = {
        "schema_version": 1,
        "status": "odd e3=3 mod-5 low-memory norm-8 residual-kernel probe",
        "calculator": base.CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "input_bytes": len(code.encode("utf-8")),
        "necessary_condition": "a_P2=0 mod 5 at the unique prime of norm 8",
        "memory_policy": (
            "delete definite-Hecke precomputation before and after T_P2; "
            "delete the rational matrix immediately after reduction modulo 5"
        ),
        "soundness": (
            "norm8_dimension zero eliminates the entire residual level; "
            "positive dimension is only a necessary survivor"
        ),
    }
    output = ""
    try:
        output = base.submit(code)
        record.update(
            {
                "request_status": "completed",
                "ambient_dimension": parse_int(output, "AMBIENT_DIM"),
                "new_dimension": parse_int(output, "NEW_DIM"),
                "norm8_dimension": parse_int(output, "NORM8_DIM"),
                "final_dimension": parse_int(output, "FINAL_DIM"),
                "output_tail": output[-6000:],
            }
        )
    except Exception as exc:
        record.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-9000:],
            }
        )
    result = dict(record)
    result["certificate_sha256"] = base.digest(record)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
