#!/usr/bin/env python3
"""Test fixed-7 level (3,3) first at the cheapest auxiliary prime 11.

The full superspecial computation first constructs T_7 on a 1024-dimensional
newspace and exceeds the public calculator memory limit.  This fail-closed
probe instead applies only the necessary local HGM condition at the split
rational prime 11.  It deliberately omits the superspecial and semilinear
conditions, so a zero result is still decisive while a positive result is only
an enlarged necessary survivor space.

To reduce memory pressure, the producer:

* clears stored definite-Hecke precomputation before T_11;
* reduces the rational Hecke matrix modulo 7 immediately;
* deletes the rational matrix and the prime-11 precomputation;
* factors the permitted trace polynomial over F_7;
* computes kernels factor-by-factor.  At prime 11 every squarefree factor has
  degree at most two, so only T and T^2 are required.
"""
from __future__ import annotations

import json
import re
from typing import Any

import run_signature_357_magma_fixed7_combined_residual as base

PRIME = 11


def magma_code(row: str) -> str:
    return rf'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
F15 := NumberField(CyclotomicPolynomial(15)); OF15 := Integers(F15);
F7 := GF(7); R7<X> := PolynomialRing(F7);
Row := {row};
Red := function(P)
  return R7![F7!Coefficient(P,i) : i in [0..Degree(P)]];
end function;
UnionPolynomial := function(row)
  l:=row[1]; I:=Factorisation(l*OK)[1][1];
  fK:=InertiaDegree(I); fF:=InertiaDegree(Factorisation(l*OF15)[1][1]);
  q:=Integers()!Norm(I); U:=X;
  if fF/fK eq 2 then U:=X^2-F7!(2*l^fK); end if;
  P:=R7!1;
  for Q in row[2] do P *:= Red(Q); end for;
  for Q in row[3] do P *:= Evaluate(Red(Q),U); end for;
  for Q in row[4] do P *:= Evaluate(Red(Q),U); end for;
  P *:= (X-F7!(q+1))*(X+F7!(q+1));
  return P;
end function;
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^3*I5^3);
M:=NewSubspace(M0);
n:=Dimension(M); V:=VectorSpace(F7,n);
printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M);
DeleteHeckePrecomputation(O);
printf "PHASE=old-hecke-cache-cleared\n";
I:=Factorisation(Row[1]*OK)[1][1];
printf "PHASE=T11-rational-start\n";
TQ:=HeckeOperator(M,I);
printf "PHASE=T11-rational-ready\n";
T:=Matrix(F7,TQ);
delete TQ;
DeleteHeckePrecomputation(O,I);
printf "PHASE=T11-mod7-ready\n";
P:=UnionPolynomial(Row);
Fs:=Factorisation(P);
printf "UNION_POLYNOMIAL_DEGREE=%o\n",Degree(P);
printf "UNION_FACTOR_COUNT=%o\n",#Fs;
maxdeg:=Maximum([Degree(pair[1]) : pair in Fs]);
printf "MAX_FACTOR_DEGREE=%o\n",maxdeg;
if maxdeg gt 2 then error "prime-11 union has a factor of degree above two"; end if;
Id:=IdentityMatrix(F7,n); T2:=T*T;
S:=sub<V|>;
for index in [1..#Fs] do
  Q:=Fs[index][1]; d:=Degree(Q);
  if d eq 1 then
    A:=Coefficient(Q,1)*T+Coefficient(Q,0)*Id;
  else
    A:=Coefficient(Q,2)*T2+Coefficient(Q,1)*T+Coefficient(Q,0)*Id;
  end if;
  KQ:=Kernel(A);
  printf "FACTOR|%o|%o|%o\n",index,d,Dimension(KQ);
  S:=S+KQ;
  delete A; delete KQ;
end for;
printf "LOCAL_CANDIDATE_DIM=%o\n",Dimension(S);
printf "FINAL_DIM=%o\n",Dimension(S);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise base.ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    rows = base.rows_by_prime(base.fetch_data())
    code = magma_code(rows[PRIME])
    record: dict[str, Any] = {
        "schema_version": 1,
        "status": "fixed-7 level-(3,3) low-memory prime-11 marginal residual sieve",
        "calculator": base.CALCULATOR_URL,
        "candidate_blob_sha1": base.EXPECTED_DATA_BLOB,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "auxiliary_prime": PRIME,
        "input_bytes": len(code.encode("utf-8")),
        "conditions_applied": ["complete fixed-7 local HGM trace union at prime 11"],
        "conditions_deliberately_omitted": [
            "superspecial T_7 kernel",
            "semilinear relation between the two primes above 11",
        ],
        "memory_policy": (
            "delete definite-Hecke precomputation before and after T_11; "
            "delete the rational matrix immediately after reduction modulo 7"
        ),
        "soundness": (
            "final dimension zero eliminates the entire fixed-7 level-(3,3) "
            "residual frontier; positive dimension is only an enlarged necessary survivor"
        ),
    }
    output = ""
    try:
        output = base.submit(code)
        factors = [
            {
                "index": int(index),
                "degree": int(degree),
                "kernel_dimension": int(dimension),
            }
            for index, degree, dimension in re.findall(
                r"FACTOR\|(\d+)\|(\d+)\|(\d+)", output
            )
        ]
        record.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "union_polynomial_degree": parse_int(
                    output, "UNION_POLYNOMIAL_DEGREE"
                ),
                "union_factor_count": parse_int(output, "UNION_FACTOR_COUNT"),
                "maximum_factor_degree": parse_int(output, "MAX_FACTOR_DEGREE"),
                "factor_kernel_dimensions": factors,
                "final_dimension": parse_int(output, "FINAL_DIM"),
                "output_tail": output[-6000:],
            }
        )
        if len(factors) != record["union_factor_count"]:
            raise base.ResearchError("factor record count mismatch")
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
