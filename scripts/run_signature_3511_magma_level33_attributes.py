#!/usr/bin/env python3
"""Inspect Magma's ambient/raw representation of the fixed-11 level-(3,3) newspace."""
from __future__ import annotations

import json
from typing import Any

import run_signature_3511_magma_fixed11_residual as base


def main() -> int:
    source = r'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); I5:=Factorisation(5*OK)[1][1];
M0:=HilbertCuspForms(K,3^3*I5^3); M:=NewSubspace(M0);
printf "NEW_DIM=%o\n",Dimension(M);
printf "IS_DEFINITE=%o\n",IsDefinite(M);
printf "HAS_AMBIENT=%o\n",assigned M`Ambient;
if assigned M`Ambient then
  A:=M`Ambient;
  printf "AMBIENT_DIM=%o\n",Dimension(A);
  printf "AMBIENT_DEFINITE=%o\n",IsDefinite(A);
end if;
Attrs:=GetAttributes(ModFrmHil);
printf "ATTRIBUTE_COUNT=%o\n",#Attrs;
for name in Attrs do
  if assigned M``name then
    value:=M``name;
    printf "ASSIGNED|%o|TYPE=%o",name,Type(value);
    if ISA(Type(value),Mtrx) then printf "|ROWS=%o|COLS=%o|RING=%o",Nrows(value),Ncols(value),BaseRing(value); end if;
    if ISA(Type(value),ModFrmHil) then printf "|DIM=%o|DEF=%o",Dimension(value),IsDefinite(value); end if;
    if Type(value) eq Assoc then printf "|KEYS=%o",#Keys(value); end if;
    if Type(value) eq SeqEnum then printf "|LENGTH=%o",#value; end if;
    printf "\n";
  end if;
end for;
printf "DONE=true\n";
'''
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) fixed-11 level-(3,3) raw-module attribute inventory",
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "input_bytes": len(source.encode()),
    }
    output = ""
    try:
        output = base.submit(source)
        if "DONE=true" not in output:
            raise base.ResearchError("attribute inventory did not complete")
        body.update({"request_status": "completed", "output_tail": output[-18000:]})
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-22000:],
        })
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
