#!/usr/bin/env python3
"""Intersect several fixed-11 local trace conditions on one residual newspace.

This is the multi-prime refinement of ``run_signature_3511_magma_fixed11_residual``.
All Hecke operators commute, so the allowed kernels can be intersected in the
fixed coordinates of the complete mod-11 newspace.  Each local union is first
intersected with X^11-X: the Frey representation has coefficient residue field
F_11 because 11 splits in Q(sqrt(5)), so every congruent Hecke trace is an F_11
scalar even if the newform coefficient field is larger.

A zero final dimension eliminates the complete level conditional on the imported
modularity, irreducibility, conductor and level-lowering inputs. Positive dimension
is only a necessary residual survivor.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_3511_magma_fixed11_residual as base

PRIMES = [13, 17, 19, 31, 41]
LEVELS = [(2, 2), (2, 3), (3, 2)]


def encode_rows(data: bytes) -> str:
    return "[" + ",".join(base.selected_row(data, prime) for prime in PRIMES) + "]"


def magma_code(e3: int, e5: int, rows: str) -> str:
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); SetStoreModularForms(K,false);
I5:=Factorisation(5*OK)[1][1]; F15:=NumberField(CyclotomicPolynomial(15)); OF15:=Integers(F15);
F11:=GF(11); R11<X>:=PolynomialRing(F11); Rows:={rows};
Red:=function(P) return R11![F11!Coefficient(P,i):i in [0..Degree(P)]]; end function;
AllowedPolynomial:=function(row)
  l:=row[1]; I:=Factorisation(l*OK)[1][1];
  fK:=InertiaDegree(I); fF:=InertiaDegree(Factorisation(l*OF15)[1][1]);
  q:=Integers()!Norm(I); U:=X;
  if fF div fK eq 2 then U:=X^2-F11!(2*l^fK); end if;
  P:=R11!1;
  for Q in row[2] do P*:=Red(Q); end for;
  for Q in row[3] do P*:=Evaluate(Red(Q),U); end for;
  for Q in row[4] do P*:=Evaluate(Red(Q),U); end for;
  P*:=(X-F11!(q+1))*(X+F11!(q+1));
  return GreatestCommonDivisor(SquarefreePart(P),X^11-X);
end function;
EvalMatrix:=function(P,T)
  n:=Nrows(T); A:=ZeroMatrix(F11,n,n); Q:=IdentityMatrix(F11,n);
  for i in [0..Degree(P)] do
    A+:=F11!Coefficient(P,i)*Q;
    if i lt Degree(P) then Q:=Q*T; end if;
  end for;
  return A;
end function;
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^{e3}*I5^{e5}); M:=NewSubspace(M0); n:=Dimension(M);
printf "LEVEL_EXPONENTS=[{e3},{e5}]\n"; printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
V:=VectorSpace(F11,n); S:=V;
for row in Rows do
  l:=row[1]; Iell:=Factorisation(l*OK)[1][1]; P:=AllowedPolynomial(row);
  printf "PHASE=T%o-start\n",l;
  TQ:=HeckeOperator(M,Iell); DeleteHeckePrecomputation(O,Iell); ClearStoredModularForms(K);
  T:=Matrix(F11,TQ); delete TQ;
  S:=S meet Kernel(EvalMatrix(P,T)); delete T;
  printf "ALLOWED_DEGREE_%o=%o\n",l,Degree(P);
  printf "DIM_AFTER_%o=%o\n",l,Dimension(S);
  if Dimension(S) eq 0 then break; end if;
end for;
printf "FINAL_DIM=%o\n",Dimension(S);
'''


def parse_level(raw: str) -> tuple[int, int]:
    try:
        pair = tuple(int(value) for value in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("level must be e3,e5") from exc
    if len(pair) != 2 or pair not in LEVELS:
        raise argparse.ArgumentTypeError(f"unsupported level {raw}")
    return pair


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"(?:^|\n){re.escape(marker)}=(\d+)(?:\n|$)", output)
    if match is None:
        raise base.ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=parse_level, required=True)
    args = parser.parse_args()
    e3, e5 = args.level
    data = base.fetch_data()
    source = magma_code(e3, e5, encode_rows(data))
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) fixed-11 multi-prime residual chain",
        "equation": "A^3+B^5=C^11",
        "calculator": base.CALCULATOR_URL,
        "candidate_blob_sha1": base.EXPECTED_DATA_BLOB,
        "residual_characteristic": 11,
        "coefficient_residue_field": "F_11",
        "level_exponents": [e3, e5],
        "level_norm": 3 ** (2 * e3) * 5**e5,
        "auxiliary_primes": PRIMES,
        "scalar_trace_filter": "gcd with X^11-X",
        "input_bytes": len(source.encode()),
        "soundness": (
            "zero final dimension eliminates the complete residual newspace at the level, "
            "conditional on imported modularity, absolute irreducibility, conductor and "
            "level-lowering results; positive dimension is only necessary"
        ),
    }
    output = ""
    try:
        output = base.submit(source)
        dimensions = {
            int(prime): int(dimension)
            for prime, dimension in re.findall(r"DIM_AFTER_(\d+)=(\d+)", output)
        }
        allowed_degrees = {
            int(prime): int(degree)
            for prime, degree in re.findall(r"ALLOWED_DEGREE_(\d+)=(\d+)", output)
        }
        body.update({
            "request_status": "completed",
            "new_dimension": parse_int(output, "NEW_DIM"),
            "allowed_degrees": allowed_degrees,
            "dimensions_after_primes": dimensions,
            "final_dimension": parse_int(output, "FINAL_DIM"),
            "output_tail": output[-9000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-12000:],
        })
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
