#!/usr/bin/env python3
"""Apply the complete prime-2 parity cover after the fixed-11 paired chain.

For a primitive solution A^3+B^5=C^11 there are exactly three parity regimes:

* A odd, B even, C odd: the good reduction trace at the norm-4 prime is 0;
* A even, B odd, C odd: the good reduction trace is -1;
* A and B odd, C even: the Frey parameter reduces to 1 and level lowering
  gives the multiplicative target +/-(4+1)=+/-5.

The four residual eigenvalues 0,-1,+5,-5 are distinct modulo 11.  This script
intersects their direct sum with the paired split-prime survivor space.  Zero in
one labelled eigenspace closes the corresponding parity regime, conditional on
the imported Frey-model, local trace, modularity and level-lowering inputs.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_3511_magma_fixed11_residual as base

LEVEL_CHAINS: dict[tuple[int, int], list[int]] = {
    (2, 2): [19, 29, 41],
    (2, 3): [19, 29, 31, 41, 79],
    (3, 2): [19, 29, 31, 41, 79, 89],
}


def parse_level(raw: str) -> tuple[int, int]:
    try:
        value = tuple(int(x) for x in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("level must be e3,e5") from exc
    if len(value) != 2 or value not in LEVEL_CHAINS:
        raise argparse.ArgumentTypeError(f"unsupported level {raw}")
    return value


def magma_code(e3: int, e5: int, rows: list[str]) -> str:
    encoded = ",".join(rows)
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); SetStoreModularForms(K,false);
I5:=Factorisation(5*OK)[1][1]; I2:=Factorisation(2*OK)[1][1];
F15:=NumberField(CyclotomicPolynomial(15)); OF15:=Integers(F15);
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
  T1Q:=HeckeOperator(M,fac[1][1]); DeleteHeckePrecomputation(O,fac[1][1]); ClearStoredModularForms(K);
  T1:=Matrix(F11,T1Q); delete T1Q;
  T2Q:=HeckeOperator(M,fac[2][1]); DeleteHeckePrecomputation(O,fac[2][1]); ClearStoredModularForms(K);
  T2:=Matrix(F11,T2Q); delete T2Q;
  S:=S meet PairedUnion(row,T1,T2);
  printf "DIM_AFTER_%o=%o\n",l,Dimension(S);
  delete T1; delete T2;
end for;
printf "PAIR_SURVIVOR_DIM=%o\n",Dimension(S);
printf "PHASE=T2-start\n";
TQ:=HeckeOperator(M,I2); DeleteHeckePrecomputation(O,I2); ClearStoredModularForms(K);
T:=Matrix(F11,TQ); delete TQ; I:=IdentityMatrix(F11,n);
W0:=Kernel(T); Wm1:=Kernel(T+I); Wp5:=Kernel(T-F11!5*I); Wm5:=Kernel(T+F11!5*I);
printf "TRACE0_GLOBAL_DIM=%o\n",Dimension(W0);
printf "TRACE_MINUS1_GLOBAL_DIM=%o\n",Dimension(Wm1);
printf "TRACE_PLUS5_GLOBAL_DIM=%o\n",Dimension(Wp5);
printf "TRACE_MINUS5_GLOBAL_DIM=%o\n",Dimension(Wm5);
S0:=S meet W0; Sm1:=S meet Wm1; Sp5:=S meet Wp5; Sm5:=S meet Wm5;
printf "A_ODD_B_EVEN_C_ODD_DIM=%o\n",Dimension(S0);
printf "A_EVEN_B_ODD_C_ODD_DIM=%o\n",Dimension(Sm1);
printf "C_EVEN_TRACE_PLUS5_DIM=%o\n",Dimension(Sp5);
printf "C_EVEN_TRACE_MINUS5_DIM=%o\n",Dimension(Sm5);
Sfinal:=S0+Sm1+Sp5+Sm5;
printf "DIRECT_SUM_CHECK=%o\n",Dimension(S0)+Dimension(Sm1)+Dimension(Sp5)+Dimension(Sm5)-Dimension(Sfinal);
printf "FINAL_DIM=%o\n",Dimension(Sfinal);
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
    chain = LEVEL_CHAINS[(e3, e5)]
    data = base.fetch_data()
    rows = [base.selected_row(data, prime) for prime in chain]
    source = magma_code(e3, e5, rows)
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) complete prime-2 parity cover after paired chain",
        "equation": "A^3+B^5=C^11",
        "calculator": base.CALCULATOR_URL,
        "candidate_blob_sha1": base.EXPECTED_DATA_BLOB,
        "residual_characteristic": 11,
        "level_exponents": [e3, e5],
        "level_norm": 3 ** (2 * e3) * 5**e5,
        "paired_chain_primes": chain,
        "prime2_norm": 4,
        "prime2_trace_cover_mod11": [0, 10, 5, 6],
        "parity_trace_map": {
            "A_odd_B_even_C_odd": 0,
            "A_even_B_odd_C_odd": 10,
            "C_even": [5, 6],
        },
        "soundness": (
            "zero labelled dimension eliminates that parity regime conditional on the imported "
            "prime-2 Frey trace, modularity and level-lowering theorems"
        ),
        "input_bytes": len(source.encode()),
    }
    output = ""
    try:
        output = base.submit(source)
        fields = {
            "new_dimension": "NEW_DIM",
            "pair_survivor_dimension": "PAIR_SURVIVOR_DIM",
            "a_odd_b_even_c_odd_dimension": "A_ODD_B_EVEN_C_ODD_DIM",
            "a_even_b_odd_c_odd_dimension": "A_EVEN_B_ODD_C_ODD_DIM",
            "c_even_trace_plus5_dimension": "C_EVEN_TRACE_PLUS5_DIM",
            "c_even_trace_minus5_dimension": "C_EVEN_TRACE_MINUS5_DIM",
            "direct_sum_check": "DIRECT_SUM_CHECK",
            "final_dimension": "FINAL_DIM",
        }
        body.update({"request_status": "completed"})
        body.update({key: parse_int(output, marker) for key, marker in fields.items()})
        if body["direct_sum_check"] != 0:
            raise base.ResearchError("distinct prime-2 eigenspaces failed the direct-sum check")
        body["output_tail"] = output[-10000:]
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-14000:],
            }
        )
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
