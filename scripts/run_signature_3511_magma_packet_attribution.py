#!/usr/bin/env python3
"""Attribute the final fixed-11 residual spaces for signature (3,5,11).

The paired split-prime chain reduces levels (2,2) and (2,3) to small residual
Hecke modules.  This producer identifies which characteristic-zero packets can
support those modules in two independent ways:

* direct reduction of each packet basis modulo 11, when the Magma basis matrix
  is available and integral at 11;
* packet Hecke-polynomial fingerprints at the inert primes 13 and 17.

Positive matches are only packet-attribution evidence.  They do not eliminate a
packet, and failed basis reduction is recorded rather than interpreted.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_3511_magma_fixed11_residual as base
import run_signature_3511_magma_fixed11_split_pair_chain as paired

LEVEL_CHAINS: dict[tuple[int, int], list[int]] = {
    (2, 2): [19, 29, 41],
    (2, 3): [19, 29, 31, 41, 79],
}
FINGERPRINT_PRIMES = [13, 17]


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
    fingerprints = ",".join(str(p) for p in FINGERPRINT_PRIMES)
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); SetStoreModularForms(K,false);
I5:=Factorisation(5*OK)[1][1]; F15:=NumberField(CyclotomicPolynomial(15)); OF15:=Integers(F15);
F11:=GF(11); R11<X>:=PolynomialRing(F11); Rows:=[{encoded}]; Fingerprints:=[{fingerprints}];
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
printf "SURVIVOR_DIM=%o\n",Dimension(S);
printf "PHASE=decomposition-start\n";
D:=NewformDecomposition(M); printf "PACKET_COUNT=%o\n",#D;
for i in [1..#D] do
  f:=Eigenform(D[i]); CF:=CoefficientField(f);
  printf "PACKET_META|%o|%o|%o\n",i,Dimension(D[i]),Degree(CF);
  try
    B:=BasisMatrix(D[i]);
    printf "PACKET_BASIS_SHAPE|%o|%o|%o\n",i,Nrows(B),Ncols(B);
    BR:=Matrix(F11,B); W:=RowSpace(BR);
    if Degree(W) eq n then
      printf "PACKET_DIRECT_INTERSECTION|%o|%o|%o\n",i,Dimension(W),Dimension(S meet W);
    else
      printf "PACKET_DIRECT_WRONG_DEGREE|%o|%o\n",i,Degree(W);
    end if;
  catch err
    printf "PACKET_BASIS_FAILED|%o\n",i;
  end try;
end for;
for ell in Fingerprints do
  Iell:=Factorisation(ell*OK)[1][1];
  printf "PHASE=fingerprint-%o-start\n",ell;
  TQ:=HeckeOperator(M,Iell); DeleteHeckePrecomputation(O,Iell); ClearStoredModularForms(K);
  T:=Matrix(F11,TQ); delete TQ;
  RS:=Restrict(T,S); CP:=R11!CharacteristicPolynomial(RS); delete T;
  printf "SURVIVOR_CHARPOLY|%o|%o|%o\n",ell,Degree(CP),CP;
  for i in [1..#D] do
    f:=Eigenform(D[i]); eig:=HeckeEigenvalue(f,Iell); P:=Red(MinimalPolynomial(eig));
    G:=GreatestCommonDivisor(CP,P);
    printf "PACKET_FINGERPRINT|%o|%o|%o|%o\n",ell,i,Degree(P),Degree(G);
  end for;
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
    chain = LEVEL_CHAINS[(e3, e5)]
    data = base.fetch_data()
    rows = [base.selected_row(data, prime) for prime in chain]
    source = magma_code(e3, e5, rows)
    record: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) residual packet attribution",
        "equation": "A^3+B^5=C^11",
        "calculator": base.CALCULATOR_URL,
        "candidate_blob_sha1": base.EXPECTED_DATA_BLOB,
        "residual_characteristic": 11,
        "level_exponents": [e3, e5],
        "level_norm": 3 ** (2 * e3) * 5**e5,
        "paired_chain_primes": chain,
        "fingerprint_primes": FINGERPRINT_PRIMES,
        "soundness": (
            "packet matches only attribute necessary residual survivors; they do not by "
            "themselves eliminate packets or establish compatibility of residual primes"
        ),
        "input_bytes": len(source.encode()),
    }
    output = ""
    try:
        output = base.submit(source)
        direct_rows = [
            {
                "packet": int(packet),
                "packet_residual_dimension": int(packet_dimension),
                "intersection_dimension": int(intersection),
            }
            for packet, packet_dimension, intersection in re.findall(
                r"PACKET_DIRECT_INTERSECTION\|(\d+)\|(\d+)\|(\d+)", output
            )
        ]
        fingerprints: dict[str, list[dict[str, int]]] = {}
        for prime, packet, polynomial_degree, gcd_degree in re.findall(
            r"PACKET_FINGERPRINT\|(\d+)\|(\d+)\|(\d+)\|(\d+)", output
        ):
            fingerprints.setdefault(prime, []).append(
                {
                    "packet": int(packet),
                    "packet_polynomial_degree": int(polynomial_degree),
                    "gcd_degree": int(gcd_degree),
                }
            )
        positive_sets = [
            {row["packet"] for row in rows if row["gcd_degree"] > 0}
            for rows in fingerprints.values()
        ]
        common = sorted(set.intersection(*positive_sets)) if positive_sets else []
        record.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "survivor_dimension": parse_int(output, "SURVIVOR_DIM"),
                "final_dimension": parse_int(output, "FINAL_DIM"),
                "packet_count": parse_int(output, "PACKET_COUNT"),
                "direct_packet_intersections": direct_rows,
                "fingerprints": fingerprints,
                "packets_matching_every_fingerprint": common,
                "basis_failures": [
                    int(value)
                    for value in re.findall(r"PACKET_BASIS_FAILED\|(\d+)", output)
                ],
                "output_tail": output[-16000:],
            }
        )
    except Exception as exc:
        record.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-20000:],
            }
        )
    result = dict(record)
    result["certificate_sha256"] = base.digest(record)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
