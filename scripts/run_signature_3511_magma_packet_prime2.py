#!/usr/bin/env python3
"""Read the norm-4 Hecke traces of source exceptional packets modulo 11."""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

import run_signature_3511_magma_fixed11_residual as base

PACKETS: dict[tuple[int, int], list[int]] = {
    (2, 2): [3, 4, 9, 12],
    (2, 3): [1, 7, 11, 12, 13, 16, 21],
    (3, 2): [64, 65, 69, 73, 77, 78, 79],
}


def parse_level(raw: str) -> tuple[int, int]:
    try:
        value = tuple(int(x) for x in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("level must be e3,e5") from exc
    if len(value) != 2 or value not in PACKETS:
        raise argparse.ArgumentTypeError(f"unsupported level {raw}")
    return value


def magma_code(e3: int, e5: int, packets: list[int]) -> str:
    encoded = ",".join(str(i) for i in packets)
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); I5:=Factorisation(5*OK)[1][1]; I2:=Factorisation(2*OK)[1][1];
F11:=GF(11); R11<X>:=PolynomialRing(F11); Wanted:=[{encoded}];
Red:=function(P) return R11![F11!Coefficient(P,i):i in [0..Degree(P)]]; end function;
printf "PHASE=space-start\n";
M:=NewSubspace(HilbertCuspForms(K,3^{e3}*I5^{e5})); D:=NewformDecomposition(M);
printf "PACKET_COUNT=%o\n",#D;
for i in Wanted do
  f:=Eigenform(D[i]); eig:=HeckeEigenvalue(f,I2); P:=Red(MinimalPolynomial(eig));
  printf "PACKET_PRIME2|%o|%o|%o|%o|%o|%o\n",i,Degree(P),
    Degree(GreatestCommonDivisor(P,X)),
    Degree(GreatestCommonDivisor(P,X+1)),
    Degree(GreatestCommonDivisor(P,X-5)),
    Degree(GreatestCommonDivisor(P,X+5));
  printf "PACKET_PRIME2_POLY|%o|%o\n",i,P;
end for;
printf "DONE=true\n";
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=parse_level, required=True)
    args = parser.parse_args()
    e3, e5 = args.level
    source = magma_code(e3, e5, PACKETS[(e3, e5)])
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) exceptional-packet prime-2 trace audit",
        "level_exponents": [e3, e5],
        "level_norm": 3 ** (2 * e3) * 5**e5,
        "packets": PACKETS[(e3, e5)],
        "residual_characteristic": 11,
        "trace_targets_mod11": {"trace0": 0, "trace_minus1": 10, "trace_plus5": 5, "trace_minus5": 6},
        "input_bytes": len(source.encode()),
        "nonclaim": "positive gcd only records a possible residual embedding at the norm-4 prime",
    }
    output = ""
    try:
        output = base.submit(source)
        rows = []
        for values in re.findall(r"PACKET_PRIME2\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)", output):
            packet, degree, d0, dm1, dp5, dm5 = map(int, values)
            rows.append({
                "packet": packet,
                "polynomial_degree": degree,
                "trace0_gcd_degree": d0,
                "trace_minus1_gcd_degree": dm1,
                "trace_plus5_gcd_degree": dp5,
                "trace_minus5_gcd_degree": dm5,
            })
        if len(rows) != len(PACKETS[(e3, e5)]) or "DONE=true" not in output:
            raise base.ResearchError("packet trace coverage is incomplete")
        body.update({
            "request_status": "completed",
            "rows": rows,
            "output_tail": output[-7000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-10000:],
        })
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
