#!/usr/bin/env python3
"""Test the universal odd-branch fixed-7 trace condition at the norm-4 prime.

For every primitive specialization with C odd, the imported Frey trace computation
at the unique prime above 2 gives a_P in {-1,-8}, hence a_P=6 modulo 7.  The
condition is independent of the 3-adic conductor block and of which variable is
even.  A zero kernel of T_P-6 on the full level-(3,3) newspace therefore eliminates
the last fixed-7 level before imposing superspecial or auxiliary-prime conditions.

The request uses Magma's low-memory Hecke path and is fail closed.
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
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def form_metadata(page: str) -> tuple[str, dict[str, str]]:
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
    if len(code.encode()) > MAX_INPUT:
        raise ResearchError("generated Magma input is too large")
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(CALCULATOR_URL, headers={"User-Agent": USER_AGENT}),
        timeout=120,
    ) as response:
        landing = response.read().decode(errors="replace")
        landing_url = response.geturl()
    action, hidden = form_metadata(landing)
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
        page = response.read().decode(errors="replace")
    return html.unescape(re.sub(r"<[^>]+>", "", page))


def magma_code() -> str:
    return r'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
I2 := Factorisation(2*OK)[1][1];
F7 := GF(7);
printf "PHASE=space-start\n";
M0 := HilbertCuspForms(K,3^3*I5^3);
M := NewSubspace(M0);
n := Dimension(M);
printf "NEW_DIM=%o\n",n;
O := QuaternionOrder(M);
DeleteHeckePrecomputation(O);
printf "PHASE=T2-low-memory-start\n";
TQ := HeckeOperator(M,I2 : LowMemory:=true, UseLLL:=false, ThetaPrec:=0);
printf "PHASE=T2-low-memory-ready\n";
T := Matrix(F7,TQ);
delete TQ;
DeleteHeckePrecomputation(O,I2);
printf "PHASE=T2-mod7-ready\n";
S := Kernel(T-6*IdentityMatrix(F7,n));
printf "TRACE6_DIM=%o\n",Dimension(S);
printf "FINAL_DIM=%o\n",Dimension(S);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    code = magma_code()
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "fixed-7 level-(3,3) universal odd-C trace-at-2 residual probe",
        "calculator": CALCULATOR_URL,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "auxiliary_rational_prime": 2,
        "prime_ideal_norm": 4,
        "required_trace_integers": [-1, -8],
        "required_trace_mod7": 6,
        "input_bytes": len(code.encode()),
        "conditions_applied": ["a_P=6 mod 7 at the unique prime P above 2"],
        "conditions_omitted": [
            "superspecial T_7 kernel",
            "local HGM unions at odd auxiliary primes",
            "semilinear conjugate-prime constraints",
        ],
        "soundness": (
            "final dimension zero eliminates the complete fixed-7 level-(3,3) odd branch; "
            "positive dimension is only a necessary survivor space"
        ),
        "nonclaim": (
            "the trace set {-1,-8}, modularity and level lowering are imported inputs; "
            "a failed request leaves the level unresolved"
        ),
    }
    output = ""
    try:
        output = submit(code)
        body.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "trace6_dimension": parse_int(output, "TRACE6_DIM"),
                "final_dimension": parse_int(output, "FINAL_DIM"),
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
