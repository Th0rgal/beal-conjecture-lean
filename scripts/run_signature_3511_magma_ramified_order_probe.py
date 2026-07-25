#!/usr/bin/env python3
"""Probe Jacquet--Langlands orders with the exact total conductor.

For level 3^e3*p5^e5, use the definite quaternion algebra ramified at both
real places and at 3,p5, together with an Eichler order of level
3^(e3-1)*p5^(e5-1).  The algebra discriminant and Eichler level then multiply
to the target conductor.
"""
from __future__ import annotations

import json
import re
from typing import Any

import run_signature_3511_magma_fixed11_residual as base


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"(?:^|\n){re.escape(marker)}=(\d+)(?:\n|$)", output)
    if match is None:
        raise base.ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    source = r'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I5:=Factorisation(5*OK)[1][1]; I2:=Factorisation(2*OK)[1][1];
printf "PHASE=ramified-algebra-start\n";
Q:=QuaternionAlgebra(I3*I5,RealPlaces(K));
finite,infinite:=RamifiedPlaces(Q);
printf "FINITE_RAMIFIED_COUNT=%o\n",#finite;
printf "INFINITE_RAMIFIED_COUNT=%o\n",#infinite;
Omax:=MaximalOrder(Q);
Osmall:=Order(Omax,I3*I5);
Olarge:=Order(Omax,I3^2*I5^2);
printf "SMALL_ORDER_DISC_NORM=%o\n",Integers()!Norm(Discriminant(Osmall));
printf "LARGE_ORDER_DISC_NORM=%o\n",Integers()!Norm(Discriminant(Olarge));
printf "PHASE=small-level-start\n";
Msmall0:=HilbertCuspForms(K,3^2*I5^2);
MsmallAuto:=NewSubspace(Msmall0);
MsmallRam:=NewSubspace(Msmall0 : QuaternionOrder:=Osmall);
printf "SMALL_AUTO_DIM=%o\n",Dimension(MsmallAuto);
printf "SMALL_RAM_DIM=%o\n",Dimension(MsmallRam);
Ta:=HeckeOperator(MsmallAuto,I2); Tr:=HeckeOperator(MsmallRam,I2);
printf "SMALL_AUTO_CHARPOLY=%o\n",CharacteristicPolynomial(Ta);
printf "SMALL_RAM_CHARPOLY=%o\n",CharacteristicPolynomial(Tr);
printf "SMALL_CHARPOLY_EQUAL=%o\n",CharacteristicPolynomial(Ta) eq CharacteristicPolynomial(Tr);
delete Ta; delete Tr; delete MsmallAuto; delete MsmallRam; delete Msmall0;
ClearStoredModularForms(K); DeleteHeckePrecomputation(Osmall); DeleteHeckePrecomputation(Olarge);
printf "PHASE=large-level-start\n";
Mlarge0:=HilbertCuspForms(K,3^3*I5^3);
Mlarge:=NewSubspace(Mlarge0 : QuaternionOrder:=Olarge);
printf "LARGE_DIM=%o\n",Dimension(Mlarge);
printf "LARGE_DEFINITE=%o\n",IsDefinite(Mlarge);
printf "PHASE=large-T2-start\n";
TQ:=HeckeOperator(Mlarge,I2); printf "LARGE_T2_ROWS=%o\n",Nrows(TQ);
printf "DONE=true\n";
'''
    body: dict[str, Any] = {
        "schema_version": 2,
        "status": "signature-(3,5,11) exact-conductor ramified Eichler-order probe",
        "equation": "A^3+B^5=C^11",
        "finite_ramification": ["prime above 3", "prime above 5"],
        "infinite_ramification": "all two real places of Q(sqrt(5))",
        "comparison_level_exponents": [2, 2],
        "target_level_exponents": [3, 3],
        "target_level_norm": 91125,
        "order_construction": "algebra discriminant 3*p5 times Eichler level 3^(e3-1)*p5^(e5-1)",
        "input_bytes": len(source.encode()),
        "soundness": (
            "matching small-level dimensions and Hecke characteristic polynomials validate the "
            "alternative Jacquet--Langlands realization computationally; this probe alone makes no elimination claim"
        ),
    }
    output = ""
    try:
        output = base.submit(source)
        if "DONE=true" not in output:
            raise base.ResearchError("ramified-order probe did not complete")
        equality = re.search(r"(?:^|\n)SMALL_CHARPOLY_EQUAL=(true|false)(?:\n|$)", output)
        if equality is None:
            raise base.ResearchError("small-level comparison lacked equality marker")
        body.update({
            "request_status": "completed",
            "finite_ramified_count": parse_int(output, "FINITE_RAMIFIED_COUNT"),
            "infinite_ramified_count": parse_int(output, "INFINITE_RAMIFIED_COUNT"),
            "small_order_discriminant_norm": parse_int(output, "SMALL_ORDER_DISC_NORM"),
            "large_order_discriminant_norm": parse_int(output, "LARGE_ORDER_DISC_NORM"),
            "small_auto_dimension": parse_int(output, "SMALL_AUTO_DIM"),
            "small_ramified_dimension": parse_int(output, "SMALL_RAM_DIM"),
            "small_hecke_charpoly_equal": equality.group(1) == "true",
            "large_dimension": parse_int(output, "LARGE_DIM"),
            "large_t2_rows": parse_int(output, "LARGE_T2_ROWS"),
            "output_tail": output[-12000:],
        })
        if body["finite_ramified_count"] != 2 or body["infinite_ramified_count"] != 2:
            raise base.ResearchError("quaternion algebra has the wrong ramification set")
        if body["small_order_discriminant_norm"] != 3**4 * 5**2:
            raise base.ResearchError("small Eichler order has the wrong discriminant norm")
        if body["large_order_discriminant_norm"] != 3**6 * 5**3:
            raise base.ResearchError("large Eichler order has the wrong discriminant norm")
        if body["small_auto_dimension"] != body["small_ramified_dimension"]:
            raise base.ResearchError("alternative small-level realization has the wrong dimension")
        if not body["small_hecke_charpoly_equal"]:
            raise base.ResearchError("alternative small-level Hecke polynomial does not match")
        if body["large_dimension"] != 1024 or body["large_t2_rows"] != 1024:
            raise base.ResearchError("large ramified-order newspace has unexpected dimensions")
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-16000:],
        })
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
