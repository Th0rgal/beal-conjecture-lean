#!/usr/bin/env python3
"""Probe direct finite-field Brandt construction for definite Hilbert spaces."""
from __future__ import annotations

import json
from typing import Any

import run_signature_3511_magma_fixed11_residual as base


def main() -> int:
    source = r'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); I5:=Factorisation(5*OK)[1][1]; I2:=Factorisation(2*OK)[1][1]; F11:=GF(11);
M:=NewSubspace(HilbertCuspForms(K,3^2*I5^2)); flag:=IsDefinite(M); assert flag;
O:=QuaternionOrder(M);
printf "HMF_DIM=%o\n",Dimension(M); printf "ORDER_TYPE=%o\n",Type(O);
try
  B:=BrandtModule(O,F11 : ComputeGrams:=false);
  printf "BRANDT_CREATED=true\n";
  printf "BRANDT_TYPE=%o\n",Type(B);
  printf "BRANDT_DIM=%o\n",Dimension(B);
  printf "BRANDT_DEGREE=%o\n",Degree(B);
  try
    T:=HeckeOperator(B,I2);
    printf "IDEAL_HECKE=true\n";
    printf "IDEAL_HECKE_ROWS=%o\n",Nrows(T);
  catch ideal_error
    printf "IDEAL_HECKE=false\n";
    printf "IDEAL_HECKE_ERROR=%o\n",ideal_error;
  end try;
  try
    Tn:=HeckeOperator(B,Integers()!Norm(I2));
    printf "NORM_HECKE=true\n";
    printf "NORM_HECKE_ROWS=%o\n",Nrows(Tn);
  catch norm_error
    printf "NORM_HECKE=false\n";
    printf "NORM_HECKE_ERROR=%o\n",norm_error;
  end try;
catch brandt_error
  printf "BRANDT_CREATED=false\n";
  printf "BRANDT_ERROR=%o\n",brandt_error;
end try;
printf "DONE=true\n";
'''
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) direct finite-field Hilbert Brandt API probe",
        "test_level_exponents": [2, 2],
        "residual_characteristic": 11,
        "input_bytes": len(source.encode()),
        "nonclaim": "API discovery only; no arithmetic elimination follows from this probe",
    }
    output = ""
    try:
        output = base.submit(source)
        if "DONE=true" not in output:
            raise base.ResearchError("finite Brandt API probe did not complete")
        body.update({"request_status": "completed", "output_tail": output[-10000:]})
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-14000:],
        })
    result = dict(body)
    result["certificate_sha256"] = base.digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
