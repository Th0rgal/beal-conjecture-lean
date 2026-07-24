#!/usr/bin/env python3
"""Test the universal odd-branch fixed-7 base trace at the norm-4 prime.

For C odd, the pinned degenerate HGM computation over Q(zeta_15) gives the
degree-two Frobenius trace w in {-1,-8}.  The prime above 2 has norm q=4 in
Q(sqrt(5)), and the relative residue degree is two, so

    w = a_P^2 - 2*q = a_P^2 - 8.

Thus a_P^2 is 7 or 0, and consequently a_P=0 modulo 7.  A zero kernel of T_P on
the full level-(3,3) newspace eliminates the last fixed-7 level before imposing
superspecial or odd auxiliary-prime conditions.  A failed request is explicit.
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
S := Kernel(T);
printf "TRACE0_DIM=%o\n",Dimension(S);
printf "FINAL_DIM=%o\n",Dimension(S);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    code = magma_code()
    full_traces = [-1, -8]
    base_trace_squares = [value + 8 for value in full_traces]
    body: dict[str, Any] = {
        "schema_version": 2,
        "status": "fixed-7 level-(3,3) universal odd-C base-trace-at-2 probe",
        "calculator": CALCULATOR_URL,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "auxiliary_rational_prime": 2,
        "base_prime_norm": 4,
        "full_cyclotomic_residue_degree_over_base": 2,
        "full_cyclotomic_trace_integers": full_traces,
        "base_trace_square_integers": base_trace_squares,
        "base_trace_mod7": 0,
        "trace_transform": "w=a_P^2-2*Norm(P)=a_P^2-8",
        "input_bytes": len(code.encode()),
        "conditions_applied": ["a_P=0 mod 7 at the unique prime P above 2"],
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
            "the full-cyclotomic trace set, modularity and level lowering are imported inputs; "
            "a failed request leaves the level unresolved"
        ),
    }
    if [value % 7 for value in base_trace_squares] != [0, 0]:
        raise ResearchError("base/full trace reduction does not force trace zero")
    output = ""
    try:
        output = submit(code)
        body.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "trace0_dimension": parse_int(output, "TRACE0_DIM"),
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
