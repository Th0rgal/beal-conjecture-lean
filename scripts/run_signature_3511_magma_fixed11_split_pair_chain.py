#!/usr/bin/env python3
"""Intersect paired split-prime trace relations for signature (3,5,11)."""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_3511_magma_fixed11_residual as base
import run_signature_3511_magma_fixed11_split_pair as pair

LEVELS = [(2, 2), (2, 3), (3, 2)]
PRIMES = [19, 29, 31, 41]


def parse_level(raw: str) -> tuple[int, int]:
    try:
        value = tuple(int(x) for x in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("level must be e3,e5") from exc
    if len(value) != 2 or value not in LEVELS:
        raise argparse.ArgumentTypeError(f"unsupported level {raw}")
    return value


def magma_code(e3: int, e5: int, rows: list[str]) -> str:
    encoded = ",".join(rows)
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); SetStoreModularForms(K,false);
I5:=Factorisation(5*OK)[1][1]; F15:=NumberField(CyclotomicPolynomial(15)); OF15:=Integers(F15);
F11:=GF(11); R11<X>:=PolynomialRing(F11); Rows:=[{encoded}];
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
  error "candidate trace polynomial has degree outside 1 or 2";
end function;
PairedUnion:=function(row,T1,T2)
  l:=row[1]; fac:=Factorisation(l*OK); n:=Nrows(T1); I:=IdentityMatrix(F11,n);
  fK:=InertiaDegree(fac[1][1]); fF:=InertiaDegree(Factorisation(l*OF15)[1][1]);
  q:=Integers()!Norm(fac[1][1]); U1:=T1; U2:=T2;
  if fF div fK eq 2 then
    U1:=T1*T1-F11!(2*l^fK)*I; U2:=T2*T2-F11!(2*l^fK)*I;
  end if;
  V:=VectorSpace(F11,n); W:=sub<V|>;
  for P in row[2] do W+:=PairPolynomialSpace(P,T1,T2); end for;
  for P in row[3] do W+:=PairPolynomialSpace(P,U1,U2); end for;
  for P in row[4] do W+:=PairPolynomialSpace(P,U1,U2); end for;
  target:=F11!(q+1);
  for a in [-1,1] do for b in [-1,1] do
    W+:=Kernel(T1-F11!a*target*I) meet Kernel(T2-F11!b*target*I);
  end for; end for;
  return W meet Kernel(T1^11-T1) meet Kernel(T2^11-T2);
end function;
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^{e3}*I5^{e5}); M:=NewSubspace(M0); n:=Dimension(M);
printf "LEVEL_EXPONENTS=[{e3},{e5}]\n"; printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
V:=VectorSpace(F11,n); S:=V;
for row in Rows do
  l:=row[1]; fac:=Factorisation(l*OK); assert #fac eq 2;
  printf "PHASE=prime-%o-first\n",l;
  T1Q:=HeckeOperator(M,fac[1][1]); DeleteHeckePrecomputation(O,fac[1][1]); ClearStoredModularForms(K);
  T1:=Matrix(F11,T1Q); delete T1Q;
  printf "PHASE=prime-%o-second\n",l;
  T2Q:=HeckeOperator(M,fac[2][1]); DeleteHeckePrecomputation(O,fac[2][1]); ClearStoredModularForms(K);
  T2:=Matrix(F11,T2Q); delete T2Q;
  W:=PairedUnion(row,T1,T2); S:=S meet W;
  printf "PAIRED_UNION_%o=%o\n",l,Dimension(W);
  printf "DIM_AFTER_%o=%o\n",l,Dimension(S);
  delete T1; delete T2;
  if Dimension(S) eq 0 then break; end if;
end for;
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
    args = parser.parse_args()
    e3, e5 = args.level
    data = base.fetch_data()
    rows = [base.selected_row(data, prime) for prime in PRIMES]
    source = magma_code(e3, e5, rows)
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) paired split-prime residual chain",
        "equation": "A^3+B^5=C^11",
        "calculator": base.CALCULATOR_URL,
        "candidate_blob_sha1": base.EXPECTED_DATA_BLOB,
        "residual_characteristic": 11,
        "level_exponents": [e3, e5],
        "level_norm": 3 ** (2 * e3) * 5**e5,
        "auxiliary_primes": PRIMES,
        "paired_relations": ["t1+t2=-c1", "t1*t2=c0"],
        "input_bytes": len(source.encode()),
        "soundness": (
            "zero final dimension eliminates the level conditional on the imported "
            "semilinear conjugacy, modularity, irreducibility, conductor and level-lowering inputs"
        ),
    }
    output = ""
    try:
        output = base.submit(source)
        dimensions = {
            int(p): int(d)
            for p, d in re.findall(r"DIM_AFTER_(\d+)=(\d+)", output)
        }
        marginal = {
            int(p): int(d)
            for p, d in re.findall(r"PAIRED_UNION_(\d+)=(\d+)", output)
        }
        body.update({
            "request_status": "completed",
            "new_dimension": parse_int(output, "NEW_DIM"),
            "paired_union_dimensions": marginal,
            "dimensions_after_primes": dimensions,
            "final_dimension": parse_int(output, "FINAL_DIM"),
            "output_tail": output[-12000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-15000:],
        })
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
