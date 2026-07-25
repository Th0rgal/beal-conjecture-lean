#!/usr/bin/env python3
"""Split fixed-7 level (3,3) by the exact prime-2 parity traces.

Exact point counts give trace 0 when A is odd and B is even, and trace -1
when A is even and B is odd. The same Hecke matrix therefore measures both
parity branches separately and their complete trace union.

Magma's Hilbert modular-form Hecke interface accepts no optional low-memory
parameters. Peak memory is reduced instead by releasing the ambient space,
clearing stored modular forms and all old quaternion Hecke precomputation before
constructing the ordinary T_2 operator. Prime-specific precomputation is deleted
before the rational matrix is converted modulo 7. The trace union is formed as
the sum of two distinct eigenspaces rather than by materializing T(T+1).
"""
from __future__ import annotations

import hashlib
import html
import http.cookiejar
import json
import re
import urllib.parse
import urllib.request
from typing import Any

CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def metadata(page: str) -> tuple[str, dict[str, str]]:
    form = re.search(r"<form\b([^>]*)>(.*?)</form>", page, flags=re.I | re.S)
    if form is None:
        raise ResearchError("calculator page contains no form")
    attributes, body = form.groups()
    action_match = re.search(r"\baction=[\"']([^\"']*)", attributes, flags=re.I)
    action = CALCULATOR_URL if action_match is None else urllib.parse.urljoin(
        CALCULATOR_URL, html.unescape(action_match.group(1))
    )
    hidden: dict[str, str] = {}
    for tag in re.findall(r"<input\b[^>]*>", body, flags=re.I):
        type_match = re.search(r"\btype=[\"']([^\"']*)", tag, flags=re.I)
        name_match = re.search(r"\bname=[\"']([^\"']*)", tag, flags=re.I)
        value_match = re.search(r"\bvalue=[\"']([^\"']*)", tag, flags=re.I)
        if type_match and type_match.group(1).lower() == "hidden" and name_match:
            hidden[html.unescape(name_match.group(1))] = (
                "" if value_match is None else html.unescape(value_match.group(1))
            )
    return action, hidden


def submit(code: str) -> str:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(CALCULATOR_URL, headers={"User-Agent": USER_AGENT}),
        timeout=120,
    ) as response:
        landing = response.read().decode(errors="replace")
        landing_url = response.geturl()
    action, hidden = metadata(landing)
    hidden["input"] = code
    parsed = urllib.parse.urlparse(action)
    request = urllib.request.Request(
        action,
        data=urllib.parse.urlencode(hidden).encode(),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": landing_url,
            "Origin": f"{parsed.scheme}://{parsed.netloc}",
        },
    )
    with opener.open(request, timeout=300) as response:
        return html.unescape(
            re.sub(r"<[^>]+>", "", response.read().decode(errors="replace"))
        )


def magma_code() -> str:
    return r'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K);
SetStoreModularForms(K,false);
I5:=Factorisation(5*OK)[1][1]; I2:=Factorisation(2*OK)[1][1]; F7:=GF(7);
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^3*I5^3);
M:=NewSubspace(M0);
n:=Dimension(M); printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M);
delete M0;
ClearStoredModularForms(K);
DeleteHeckePrecomputation(O);
printf "PHASE=ambient-and-cache-cleared\n";
printf "PHASE=T2-rational-start\n";
TQ:=HeckeOperator(M,I2);
printf "PHASE=T2-rational-ready\n";
DeleteHeckePrecomputation(O,I2);
ClearStoredModularForms(K);
printf "PHASE=T2-precomputation-cleared\n";
T:=Matrix(F7,TQ);
delete TQ;
printf "PHASE=T2-mod7-ready\n";
I:=IdentityMatrix(F7,n);
S_even_B:=Kernel(T);
S_odd_B:=Kernel(T+I);
S_union:=S_even_B+S_odd_B;
printf "B_EVEN_TRACE0_DIM=%o\n",Dimension(S_even_B);
printf "B_ODD_TRACE_MINUS1_DIM=%o\n",Dimension(S_odd_B);
printf "TRACE_UNION_DIM=%o\n",Dimension(S_union);
printf "DIRECT_SUM_CHECK=%o\n",Dimension(S_even_B)+Dimension(S_odd_B)-Dimension(S_union);
printf "FINAL_DIM=%o\n",Dimension(S_union);
'''


def parse(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    source = magma_code()
    body: dict[str, Any] = {
        "schema_version": 7,
        "status": "fixed-7 level-(3,3) exact prime-2 parity decomposition",
        "calculator": CALCULATOR_URL,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "prime_ideal_norm": 4,
        "parity_trace_map": {
            "B_even_A_odd": 0,
            "B_odd_A_even": -1,
        },
        "allowed_traces_mod7": [0, 6],
        "annihilating_polynomial": "T*(T+1)",
        "union_implementation": "ker(T) direct-sum ker(T+1), avoiding T*(T+1)",
        "hecke_strategy": {
            "interface": "ordinary ModFrmHil HeckeOperator; optional parameters unsupported",
            "pre_operator_cleanup": True,
        },
        "memory_policy": (
            "delete ambient space, stored modular forms and old quaternion precomputation "
            "before constructing T2; delete prime-specific precomputation before reducing "
            "the rational matrix modulo 7"
        ),
        "input_bytes": len(source.encode()),
        "soundness": (
            "zero B-even trace-0 dimension closes that parity branch; zero union "
            "closes the complete fixed-7 level-(3,3) odd branch; positive dimensions "
            "are only necessary survivor spaces"
        ),
        "nonclaim": (
            "the point-count trace theorem, modularity and level lowering are imported "
            "inputs; a failed request leaves every corresponding branch unresolved"
        ),
    }
    output = ""
    try:
        output = submit(source)
        even_dimension = parse(output, "B_EVEN_TRACE0_DIM")
        odd_dimension = parse(output, "B_ODD_TRACE_MINUS1_DIM")
        union_dimension = parse(output, "TRACE_UNION_DIM")
        direct_sum_error = parse(output, "DIRECT_SUM_CHECK")
        if direct_sum_error != 0 or even_dimension + odd_dimension != union_dimension:
            raise ResearchError(
                "distinct trace eigenspaces did not form the recorded direct sum"
            )
        body.update(
            {
                "request_status": "completed",
                "new_dimension": parse(output, "NEW_DIM"),
                "b_even_trace0_dimension": even_dimension,
                "b_odd_trace_minus1_dimension": odd_dimension,
                "trace_union_dimension": union_dimension,
                "direct_sum_check": direct_sum_error,
                "final_dimension": parse(output, "FINAL_DIM"),
                "output_tail": output[-6000:],
            }
        )
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-9000:],
            }
        )
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
