#!/usr/bin/env python3
"""Read and filter one decisive Hecke trace for fixed-7 packet 24 or 28.

The public calculator previously constructed an algebraic eigenform and its
Hecke eigenvalue. At prime 43 that field construction exceeded the memory
limit, although the packet had already been isolated by ``NewformDecomposition``.
This producer instead computes the Hecke matrix on the packet itself and records
its characteristic polynomial. For a Hecke-irreducible packet this has exactly
the residual spectrum needed by every subsequent compatibility test, without
constructing an explicit eigenvalue field.

At rational primes inert in ``Q(sqrt(5))`` (13 and 43 in the selected set),
semilinear Galois trace symmetry additionally requires the residual trace to lie
in ``F_7``. The producer therefore records ``gcd(P mod 7, X^7-X)`` directly.
Every packet-prime request is independent and fail closed.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_357_magma_fixed7_24_28_traces as base

INERT_PRIMES = {13, 43}


def make_code(packet: int, prime: int) -> str:
    return rf'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
F15 := NumberField(CyclotomicPolynomial(15)); OF15 := Integers(F15);
F7 := GF(7); R7<X> := PolynomialRing(F7);
M := HilbertCuspForms(K,3^2*I5^3);
decomp := NewformDecomposition(NewSubspace(M));
if #decomp ne 35 then error "unexpected packet count"; end if;
packet_space := decomp[{packet}];
l := {prime}; I := Factorisation(l*OK)[1][1];
printf "PACKET_DIM=%o\n",Dimension(packet_space);
Tbase := HeckeOperator(packet_space,I);
printf "PHASE=packet-hecke-ready\n";
Pbase := CharacteristicPolynomial(Tbase);
fK := InertiaDegree(I); fF := InertiaDegree(Factorisation(l*OF15)[1][1]);
Tfull := Tbase;
if fF/fK eq 2 then
  Tfull := Tbase*Tbase-2*l^fK*IdentityMatrix(Rationals(),Nrows(Tbase));
end if;
Pfull := CharacteristicPolynomial(Tfull);
printf "TRACE_START|%o|%o|%o|%o|%o|%o\n",{packet},l,fK,fF,Degree(Pbase),Degree(Pfull);
printf "BASE_COEFFS";
for c in Eltseq(Pbase) do printf "|%o",c; end for;
printf "\nFULL_COEFFS";
for c in Eltseq(Pfull) do printf "|%o",c; end for;
printf "\nTRACE_END\n";
P7 := R7![F7!Coefficient(Pbase,i) : i in [0..Degree(Pbase)]];
Gscalar := GreatestCommonDivisor(P7,X^7-X);
printf "SCALAR_GCD_DEGREE=%o\n",Degree(Gscalar);
printf "SCALAR_GCD_COEFFS";
for c in Eltseq(Gscalar) do printf "|%o",Integers()!c; end for;
printf "\n";
'''


def parse_scalar(output: str) -> tuple[int, list[int]]:
    degree_match = re.search(r"SCALAR_GCD_DEGREE=(\d+)", output)
    coeff_match = re.search(r"SCALAR_GCD_COEFFS\|([^\n]+)", output)
    if degree_match is None or coeff_match is None:
        raise base.ResearchError("output lacked scalar gcd record")
    degree = int(degree_match.group(1))
    coefficients = [int(value.strip()) for value in coeff_match.group(1).split("|")]
    if len(coefficients) != degree + 1:
        raise base.ResearchError("scalar gcd coefficient count mismatch")
    return degree, coefficients


def parse_packet_dimension(output: str) -> int:
    match = re.search(r"PACKET_DIM=(\d+)", output)
    if match is None:
        raise base.ResearchError("output lacked packet dimension")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=int, choices=base.PACKETS, required=True)
    parser.add_argument("--prime", type=int, choices=base.PRIMES, required=True)
    args = parser.parse_args()

    code = make_code(args.packet, args.prime)
    record: dict[str, Any] = {
        "schema_version": 5,
        "status": "public-Magma packet Hecke characteristic-polynomial trace test",
        "calculator": base.CALCULATOR_URL,
        "level_exponents": [2, 3],
        "level_norm": 10125,
        "packet": args.packet,
        "prime": args.prime,
        "rational_prime_inert_in_K5": args.prime in INERT_PRIMES,
        "input_bytes": len(code.encode("utf-8")),
        "trace_polynomial_kind": "characteristic polynomial on the Hecke-irreducible packet",
        "full_trace_transform": "T_full=T_base^2-2*l^fK when fF/fK=2",
        "soundness": (
            "the packet characteristic polynomial contains the complete Hecke "
            "spectrum; at an inert rational prime scalar_gcd_degree zero "
            "eliminates the packet under imported semilinear Galois symmetry"
        ),
        "nonclaim": "a failed request leaves this packet-prime pair unresolved",
    }
    output = ""
    try:
        output = base.submit(code)
        rows = base.parse_rows(output)
        if len(rows) != 1:
            raise base.ResearchError(f"expected one trace row, got {len(rows)}")
        row = rows[0]
        if (row["packet"], row["prime"]) != (args.packet, args.prime):
            raise base.ResearchError("trace packet/prime mismatch")
        scalar_degree, scalar_coefficients = parse_scalar(output)
        record.update(
            {
                "request_status": "completed",
                "packet_dimension": parse_packet_dimension(output),
                **row,
                "scalar_gcd_degree": scalar_degree,
                "scalar_gcd_coefficients_low_to_high": scalar_coefficients,
                "inert_scalar_compatible": (
                    True if args.prime not in INERT_PRIMES else scalar_degree > 0
                ),
                "output_tail": output[-6000:],
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
