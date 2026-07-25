#!/usr/bin/env python3
"""Split an odd e3=3 mod-5 level by the exact norm-8 parity traces.

For B odd, the degree-two full-cyclotomic trace forces the base Hecke trace to
be zero modulo 5. For B even, u-1=B^5/A^3 is 2-adically positive and the
multiplicative local rule gives trace +/-9, namely 1 or 4 modulo 5. The three
eigenvalues are distinct, so the same low-memory Hecke matrix gives separate
B-odd, B-even, and complete parity-union dimensions.

The request releases the ambient space and cached HMF data before computing the
operator, releases the prime-specific quaternion precomputation before reducing
the matrix modulo 5, and forms the parity union by summing three distinct
Hecke eigenspaces instead of multiplying dense matrices. At norm 8 there are
only nine neighbors, so direct enumeration is used instead of automorphism
orbits, with greedy lattice reduction replacing theta-series hashes.
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
SetStoreModularForms(K,false);
I3 := Factorisation(3*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
I2 := Factorisation(2*OK)[1][1];
F5 := GF(5);
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,I3^{e3}*I7^{e7});
ambient:=Dimension(M0);
printf "AMBIENT_DIM=%o\n",ambient;
M:=NewSubspace(M0);
n:=Dimension(M);
printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M);
delete M0;
ClearStoredModularForms(K);
DeleteHeckePrecomputation(O);
printf "PHASE=ambient-and-cache-cleared\n";
printf "PHASE=T2-direct-neighbors-start\n";
TQ:=HeckeOperator(M,I2 : LowMemory:=true,UseLLL:=false,UseAuto:=false,ThetaPrec:=-1);
printf "PHASE=T2-rational-ready\n";
DeleteHeckePrecomputation(O,I2);
ClearStoredModularForms(K);
printf "PHASE=T2-precomputation-cleared\n";
T:=Matrix(F5,TQ);
delete TQ;
printf "PHASE=T2-mod5-ready\n";
I:=IdentityMatrix(F5,n);
Sodd:=Kernel(T);
Seven_plus:=Kernel(T-I);
Seven_minus:=Kernel(T+I);
Seven:=Seven_plus+Seven_minus;
Sunion:=Sodd+Seven;
printf "B_ODD_TRACE0_DIM=%o\n",Dimension(Sodd);
printf "B_EVEN_TRACE_PLUS1_DIM=%o\n",Dimension(Seven_plus);
printf "B_EVEN_TRACE_MINUS1_DIM=%o\n",Dimension(Seven_minus);
printf "B_EVEN_MULTIPLICATIVE_DIM=%o\n",Dimension(Seven);
printf "TRACE_UNION_DIM=%o\n",Dimension(Sunion);
printf "EVEN_DIRECT_SUM_CHECK=%o\n",Dimension(Seven_plus)+Dimension(Seven_minus)-Dimension(Seven);
printf "PARITY_DIRECT_SUM_CHECK=%o\n",Dimension(Sodd)+Dimension(Seven)-Dimension(Sunion);
printf "FINAL_DIM=%o\n",Dimension(Sunion);
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
        "schema_version": 4,
        "status": "odd e3=3 mod-5 low-memory norm-8 parity decomposition",
        "calculator": base.CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "input_bytes": len(code.encode("utf-8")),
        "parity_trace_map": {
            "B_odd": {"integer_trace": 0, "residual_trace_mod5": 0},
            "B_even": {
                "integer_traces": [-9, 9],
                "residual_traces_mod5": [1, 4],
            },
        },
        "union_implementation": "ker(T) direct-sum ker(T-1) direct-sum ker(T+1)",
        "hecke_strategy": {
            "low_memory": True,
            "use_automorphism_orbits": False,
            "lattice_reduction": "Kohel greedy reduction (ThetaPrec=-1)",
            "reason": "norm 8 has only nine neighbors",
        },
        "memory_policy": (
            "delete ambient space and HMF cache after newspace construction; delete "
            "prime-specific Hecke precomputation before reducing the rational matrix mod 5; "
            "avoid dense matrix products"
        ),
        "soundness": (
            "zero B-odd trace-zero dimension closes the B-odd part of this level; "
            "zero B-even multiplicative dimension closes the B-even part; zero union "
            "closes the complete residual level; positive dimensions are only necessary"
        ),
        "nonclaim": (
            "the B-odd full-to-base trace calculation, the B-even multiplicative local "
            "trace rule, modularity and level lowering remain imported research inputs"
        ),
    }
    output = ""
    try:
        output = base.submit(code)
        odd_dimension = parse_int(output, "B_ODD_TRACE0_DIM")
        even_plus_dimension = parse_int(output, "B_EVEN_TRACE_PLUS1_DIM")
        even_minus_dimension = parse_int(output, "B_EVEN_TRACE_MINUS1_DIM")
        even_dimension = parse_int(output, "B_EVEN_MULTIPLICATIVE_DIM")
        union_dimension = parse_int(output, "TRACE_UNION_DIM")
        even_direct_sum_error = parse_int(output, "EVEN_DIRECT_SUM_CHECK")
        parity_direct_sum_error = parse_int(output, "PARITY_DIRECT_SUM_CHECK")
        if (
            even_direct_sum_error != 0
            or parity_direct_sum_error != 0
            or even_plus_dimension + even_minus_dimension != even_dimension
            or odd_dimension + even_dimension != union_dimension
        ):
            raise base.ResearchError(
                "distinct norm-8 eigenspaces did not form the recorded direct sums"
            )
        record.update(
            {
                "request_status": "completed",
                "ambient_dimension": parse_int(output, "AMBIENT_DIM"),
                "new_dimension": parse_int(output, "NEW_DIM"),
                "b_odd_trace0_dimension": odd_dimension,
                "b_even_trace_plus1_dimension": even_plus_dimension,
                "b_even_trace_minus1_dimension": even_minus_dimension,
                "b_even_multiplicative_dimension": even_dimension,
                "trace_union_dimension": union_dimension,
                "even_direct_sum_check": even_direct_sum_error,
                "parity_direct_sum_check": parity_direct_sum_error,
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
