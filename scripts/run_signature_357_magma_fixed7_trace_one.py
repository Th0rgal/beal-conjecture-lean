#!/usr/bin/env python3
"""Read one decisive Hecke trace for fixed-7 packet 24 or 28.

The previous all-eight trace request crossed the public calculator budget after
three rows. Splitting by packet and auxiliary prime makes every request
independent and fail closed. Both the base-field trace polynomial and the
F15/K5 degree-two Frobenius transform are retained.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_357_magma_fixed7_24_28_traces as base


def make_code(packet: int, prime: int) -> str:
    return rf'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
F15 := NumberField(CyclotomicPolynomial(15)); OF15 := Integers(F15);
M := HilbertCuspForms(K,3^2*I5^3);
decomp := NewformDecomposition(NewSubspace(M));
if #decomp ne 35 then error "unexpected packet count"; end if;
form := Eigenform(decomp[{packet}]);
l := {prime}; I := Factorisation(l*OK)[1][1];
Eig := HeckeEigenvalue(form,I); Pbase := MinimalPolynomial(Eig);
fK := InertiaDegree(I); fF := InertiaDegree(Factorisation(l*OF15)[1][1]);
Efull := Eig;
if fF/fK eq 2 then Efull := Eig^2-2*l^fK; end if;
Pfull := MinimalPolynomial(Efull);
printf "TRACE|%o|%o|%o|%o|%o|%o\n",{packet},l,fK,fF,Pbase,Pfull;
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=int, choices=base.PACKETS, required=True)
    parser.add_argument("--prime", type=int, choices=base.PRIMES, required=True)
    args = parser.parse_args()

    code = make_code(args.packet, args.prime)
    record: dict[str, Any] = {
        "schema_version": 2,
        "status": "public-Magma single fixed-7 packet trace read",
        "calculator": base.CALCULATOR_URL,
        "level_exponents": [2, 3],
        "level_norm": 10125,
        "packet": args.packet,
        "prime": args.prime,
        "input_bytes": len(code.encode("utf-8")),
        "nonclaim": "a failed request leaves this packet-prime pair unresolved",
    }
    output = ""
    try:
        output = base.submit(code)
        pattern = re.compile(
            rf"TRACE\|{args.packet}\|{args.prime}\|(\d+)\|(\d+)\|([^|\n]+)\|([^|\n]+)"
        )
        match = pattern.search(output)
        if match is None:
            raise base.ResearchError("output lacked the requested trace row")
        record.update(
            {
                "request_status": "completed",
                "residue_degree_K5": int(match.group(1)),
                "residue_degree_F15": int(match.group(2)),
                "base_trace_polynomial": match.group(3).strip(),
                "full_trace_polynomial": match.group(4).strip(),
                "output_tail": output[-3000:],
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
