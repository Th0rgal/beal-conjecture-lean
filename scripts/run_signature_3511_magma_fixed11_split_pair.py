#!/usr/bin/env python3
"""Test the paired split-prime trace relation for signature (3,5,11).

At a rational prime l split in K=Q(sqrt(5)), a rational specialization gives
traces at the two conjugate primes that are coefficient-field conjugates.  A
quadratic candidate polynomial X^2+c1*X+c0 therefore imposes simultaneously

    T_1+T_2=-c1,   T_1*T_2=c0,

rather than allowing either root independently at each prime.  Linear
polynomials force the same rational root at both primes.  Zero/infinity rows
use the published degree-two full-cyclotomic transform before pairing.

The semilinear identification, modularity, irreducibility and level lowering
remain imported research inputs.  A zero paired-union dimension is a candidate
level closure; a positive dimension or request failure is not.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_3511_magma_fixed11_residual as base

LEVELS = [(2, 2), (2, 3), (3, 2)]
SPLIT_PRIMES = [19, 29, 31, 41, 59, 61, 71, 79, 89, 101, 109, 131]


def parse_level(raw: str) -> tuple[int, int]:
    try:
        pair = tuple(int(value) for value in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("level must be e3,e5") from exc
    if len(pair) != 2 or pair not in LEVELS:
        raise argparse.ArgumentTypeError(f"unsupported level {raw}")
    return pair


def magma_code(e3: int, e5: int, row: str) -> str:
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); SetStoreModularForms(K,false);
I5:=Factorisation(5*OK)[1][1]; F15:=NumberField(CyclotomicPolynomial(15)); OF15:=Integers(F15);
F11:=GF(11); R11<X>:=PolynomialRing(F11); Row:={row};
Red:=function(P) return R11![F11!Coefficient(P,i):i in [0..Degree(P)]]; end function;
PairPolynomialSpace:=function(P,A,B)
  P:=Red(P); d:=Degree(P); n:=Nrows(A); I:=IdentityMatrix(F11,n);
  if d eq 1 then
    c1:=Coefficient(P,1); c0:=Coefficient(P,0); r:=-c0/c1;
    return Kernel(A-r*I) meet Kernel(B-r*I);
  elif d eq 2 then
    c2:=Coefficient(P,2); c1:=Coefficient(P,1)/c2; c0:=Coefficient(P,0)/c2;
    return Kernel(A+B+c1*I) meet Kernel(A*B-c0*I);
  end if;
  error "candidate trace polynomial has degree outside 1 or 2 after reduction";
end function;
PairedUnion:=function(row,T1,T2)
  l:=row[1]; fac:=Factorisation(l*OK); n:=Nrows(T1); I:=IdentityMatrix(F11,n);
  fK:=InertiaDegree(fac[1][1]); fF:=InertiaDegree(Factorisation(l*OF15)[1][1]);
  q:=Integers()!Norm(fac[1][1]); U1:=T1; U2:=T2;
  if fF div fK eq 2 then
    U1:=T1*T1-F11!(2*l^fK)*I; U2:=T2*T2-F11!(2*l^fK)*I;
  end if;
  V:=VectorSpace(F11,n); S:=sub<V|>;
  for P in row[2] do S+:=PairPolynomialSpace(P,T1,T2); end for;
  for P in row[3] do S+:=PairPolynomialSpace(P,U1,U2); end for;
  for P in row[4] do S+:=PairPolynomialSpace(P,U1,U2); end for;
  target:=F11!(q+1);
  for a in [-1,1] do for b in [-1,1] do
    S+:=Kernel(T1-F11!a*target*I) meet Kernel(T2-F11!b*target*I);
  end for; end for;
  S:=S meet Kernel(T1^11-T1) meet Kernel(T2^11-T2);
  return S;
end function;
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^{e3}*I5^{e5}); M:=NewSubspace(M0); n:=Dimension(M);
printf "LEVEL_EXPONENTS=[{e3},{e5}]\n"; printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
fac:=Factorisation(Row[1]*OK); assert #fac eq 2;
printf "PHASE=T1-start\n";
T1Q:=HeckeOperator(M,fac[1][1]); DeleteHeckePrecomputation(O,fac[1][1]); ClearStoredModularForms(K);
T1:=Matrix(F11,T1Q); delete T1Q;
printf "PHASE=T2-start\n";
T2Q:=HeckeOperator(M,fac[2][1]); DeleteHeckePrecomputation(O,fac[2][1]); ClearStoredModularForms(K);
T2:=Matrix(F11,T2Q); delete T2Q;
S:=PairedUnion(Row,T1,T2);
printf "AUXILIARY_PRIME=%o\n",Row[1];
printf "PAIRED_UNION_DIM=%o\n",Dimension(S);
printf "FINAL_DIM=%o\n",Dimension(S);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"(?:^|\n){re.escape(marker)}=(\d+)(?:\n|$)", output)
    if match is None:
        raise base.ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=parse_level, required=True)
    parser.add_argument("--prime", type=int, choices=SPLIT_PRIMES, required=True)
    args = parser.parse_args()
    e3, e5 = args.level
    data = base.fetch_data()
    row = base.selected_row(data, args.prime)
    source = magma_code(e3, e5, row)
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) paired split-prime residual test",
        "equation": "A^3+B^5=C^11",
        "calculator": base.CALCULATOR_URL,
        "candidate_blob_sha1": base.EXPECTED_DATA_BLOB,
        "residual_characteristic": 11,
        "coefficient_residue_field": "F_11",
        "level_exponents": [e3, e5],
        "level_norm": 3 ** (2 * e3) * 5**e5,
        "auxiliary_prime": args.prime,
        "split_in_Qsqrt5": True,
        "paired_relations": ["t1+t2=-c1", "t1*t2=c0"],
        "scalar_trace_filters": ["T1^11=T1", "T2^11=T2"],
        "multiplicative_sign_policy": "all four sign pairs retained",
        "input_bytes": len(source.encode()),
        "soundness": (
            "zero paired-union dimension eliminates every residual eigensystem at the "
            "level for this prime, conditional on imported semilinear local-global "
            "compatibility, modularity, irreducibility, conductor and level lowering"
        ),
    }
    output = ""
    try:
        output = base.submit(source)
        body.update({
            "request_status": "completed",
            "new_dimension": parse_int(output, "NEW_DIM"),
            "paired_union_dimension": parse_int(output, "PAIRED_UNION_DIM"),
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
