#!/usr/bin/env python3
"""Compute the level-(3,3) norm-4 parity cover on the raw Brandt module.

The ordinary 1024x1024 rational Hecke matrix exceeds the public calculator's
memory cap. Magma stores the newspace as a 1024-dimensional subspace of a
definite 2025-dimensional ambient Brandt module. We reduce the newspace basis
modulo 11 first, delete the rational full/new spaces and their caches, and only
then construct the ambient raw Hecke matrix.
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
I5:=Factorisation(5*OK)[1][1]; I2:=Factorisation(2*OK)[1][1]; F11:=GF(11);
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^3*I5^3); M:=NewSubspace(M0);
DefiniteFlag:=IsDefinite(M); assert DefiniteFlag; assert assigned M`Ambient;
A:=M`Ambient; O:=QuaternionOrder(M); n:=Dimension(M); d:=Dimension(A);
printf "NEW_DIM=%o\n",n; printf "AMBIENT_DIM=%o\n",d;
V:=VectorSpace(F11,d);
S:=sub<V|[V![F11!c:c in Eltseq(v)]:v in Basis(M)]>;
printf "RESIDUAL_NEWSPACE_DIM=%o\n",Dimension(S); assert Dimension(S) eq n;
delete M; delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O); delete O;
printf "PHASE=rational-spaces-and-caches-cleared\n";
printf "PHASE=raw-T2-start\n";
RawQ:=HeckeMatrixRaw(A,I2); printf "RAW_ROWS=%o\n",Nrows(RawQ);
Raw:=Matrix(F11,RawQ); delete RawQ; printf "PHASE=raw-T2-mod11-ready\n";
T:=Restrict(Raw,S); delete Raw; printf "PHASE=T2-restricted-ready\n";
I:=IdentityMatrix(F11,n);
W0:=Kernel(T); Wm1:=Kernel(T+I); Wp5:=Kernel(T-F11!5*I); Wm5:=Kernel(T+F11!5*I);
printf "TRACE0_DIM=%o\n",Dimension(W0);
printf "TRACE_MINUS1_DIM=%o\n",Dimension(Wm1);
printf "TRACE_PLUS5_DIM=%o\n",Dimension(Wp5);
printf "TRACE_MINUS5_DIM=%o\n",Dimension(Wm5);
W:=W0+Wm1+Wp5+Wm5;
printf "DIRECT_SUM_CHECK=%o\n",Dimension(W0)+Dimension(Wm1)+Dimension(Wp5)+Dimension(Wm5)-Dimension(W);
printf "FINAL_DIM=%o\n",Dimension(W);
'''
    body: dict[str, Any] = {
        "schema_version": 4,
        "status": "signature-(3,5,11) fixed-11 level-(3,3) raw-Brandt norm-4 parity cover",
        "equation": "A^3+B^5=C^11",
        "calculator": base.CALCULATOR_URL,
        "residual_characteristic": 11,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "prime2_norm": 4,
        "prime2_trace_cover_mod11": [0, 10, 5, 6],
        "strategy": "reduce the newspace basis into the ambient F_11 module; delete the rational new/full spaces and quaternion caches; then construct and reduce the 2025-dimensional raw Brandt operator",
        "soundness": (
            "zero labelled dimension eliminates that parity regime conditional on the imported "
            "prime-2 trace, modularity and level-lowering inputs"
        ),
        "input_bytes": len(source.encode()),
    }
    output = ""
    try:
        output = base.submit(source)
        fields = {
            "new_dimension": "NEW_DIM",
            "ambient_dimension": "AMBIENT_DIM",
            "raw_rows": "RAW_ROWS",
            "residual_newspace_dimension": "RESIDUAL_NEWSPACE_DIM",
            "trace0_dimension": "TRACE0_DIM",
            "trace_minus1_dimension": "TRACE_MINUS1_DIM",
            "trace_plus5_dimension": "TRACE_PLUS5_DIM",
            "trace_minus5_dimension": "TRACE_MINUS5_DIM",
            "direct_sum_check": "DIRECT_SUM_CHECK",
            "final_dimension": "FINAL_DIM",
        }
        body.update({"request_status": "completed"})
        body.update({key: parse_int(output, marker) for key, marker in fields.items()})
        if body["residual_newspace_dimension"] != body["new_dimension"]:
            raise base.ResearchError("basis reduction changed the newspace dimension")
        if body["direct_sum_check"] != 0:
            raise base.ResearchError("distinct norm-4 eigenspaces failed the direct-sum check")
        body["output_tail"] = output[-9000:]
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
