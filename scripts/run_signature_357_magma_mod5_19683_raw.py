#!/usr/bin/env python3
"""Filter level 19683 on the raw definite Brandt module.

The ordinary 225-dimensional Hecke operator exhausts the public calculator's
memory.  `HeckeMatrixRaw` acts on the full internal definite module before the
cuspidal/rational-basis projection.  Over K7, whose class number is one, the
expected difference is the single Eisenstein line, with Hecke eigenvalue
Norm(P)+1 at every unramified prime.

This probe computes the raw norm-8 parity eigenspaces, applies the removed-prime
7 trace target ±8 modulo 5, and separately identifies the common Eisenstein
line by its norm-8 and norm-7 eigenvalues.  The reported cusp upper bound is
raw survivors minus the verified Eisenstein survivor.  A zero cusp upper bound
eliminates the level; positive output is only a necessary survivor.
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
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def metadata(page: str) -> tuple[str, dict[str, str]]:
    form = re.search(r"<form\b([^>]*)>(.*?)</form>", page, flags=re.I | re.S)
    if form is None:
        raise ResearchError("calculator page contains no form")
    attributes, body = form.groups()
    match = re.search(r"\baction=[\"']([^\"']*)", attributes, flags=re.I)
    action = CALCULATOR_URL if match is None else urllib.parse.urljoin(
        CALCULATOR_URL, html.unescape(match.group(1))
    )
    hidden: dict[str, str] = {}
    for tag in re.findall(r"<input\b[^>]*>", body, flags=re.I):
        tm = re.search(r"\btype=[\"']([^\"']*)", tag, flags=re.I)
        nm = re.search(r"\bname=[\"']([^\"']*)", tag, flags=re.I)
        vm = re.search(r"\bvalue=[\"']([^\"']*)", tag, flags=re.I)
        if tm and tm.group(1).lower() == "hidden" and nm:
            hidden[html.unescape(nm.group(1))] = "" if vm is None else html.unescape(vm.group(1))
    return action, hidden


def submit(code: str) -> str:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(CALCULATOR_URL, headers={"User-Agent": USER_AGENT}), timeout=120
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
        return html.unescape(re.sub(r"<[^>]+>", "", response.read().decode(errors="replace")))


def magma_code() -> str:
    return r'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I7:=Factorisation(7*OK)[1][1];
I2:=Factorisation(2*OK)[1][1]; F5:=GF(5);
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,I3^3); M:=NewSubspace(M0);
printf "CUSP_NEW_DIM=%o\n",Dimension(M);
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
printf "PHASE=raw-T2-start\n";
T2Q:=HeckeMatrixRaw(M,I2); DeleteHeckePrecomputation(O,I2); ClearStoredModularForms(K);
printf "RAW_DIM=%o\n",Nrows(T2Q);
T2:=Matrix(F5,T2Q); delete T2Q;
printf "PHASE=raw-T2-ready\n";
n:=Nrows(T2); V:=VectorSpace(F5,n); Id:=IdentityMatrix(F5,n);
S0:=Kernel(T2); Sp:=Kernel(T2-Id); Sm:=Kernel(T2+Id);
printf "RAW_TRACE0_DIM=%o\n",Dimension(S0);
printf "RAW_TRACE_PLUS1_DIM=%o\n",Dimension(Sp);
printf "RAW_TRACE_MINUS1_DIM=%o\n",Dimension(Sm);
printf "PHASE=raw-T7-start\n";
T7Q:=HeckeMatrixRaw(M,I7); DeleteHeckePrecomputation(O,I7); ClearStoredModularForms(K);
T7:=Matrix(F5,T7Q); delete T7Q;
printf "PHASE=raw-T7-ready\n";
R0:=Restrict(T7,S0); Rp:=Restrict(T7,Sp); Rm:=Restrict(T7,Sm);
I0:=IdentityMatrix(F5,Dimension(S0)); Ip:=IdentityMatrix(F5,Dimension(Sp)); Im:=IdentityMatrix(F5,Dimension(Sm));
K0:=Kernel((R0-F5!2*I0)*(R0-F5!3*I0));
Kp:=Kernel((Rp-F5!2*Ip)*(Rp-F5!3*Ip));
Km:=Kernel((Rm-F5!2*Im)*(Rm-F5!3*Im));
printf "RAW_TRACE0_AFTER7=%o\n",Dimension(K0);
printf "RAW_TRACE_PLUS1_AFTER7=%o\n",Dimension(Kp);
printf "RAW_TRACE_MINUS1_AFTER7=%o\n",Dimension(Km);
RawTotal:=Dimension(K0)+Dimension(Kp)+Dimension(Km);
printf "RAW_TOTAL_AFTER7=%o\n",RawTotal;
E8:=Kernel(T2-F5!4*Id);
E7:=Kernel(T7-F5!3*Id);
E:=E8 meet E7;
printf "EISENSTEIN_CANDIDATE_DIM=%o\n",Dimension(E);
VerifiedE:=Dimension(E);
CuspUpper:=RawTotal-VerifiedE;
printf "CUSP_SURVIVOR_UPPER_BOUND=%o\n",CuspUpper;
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"(?:^|\n){re.escape(marker)}=(\d+)(?:\n|$)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    source = magma_code()
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "level-19683 raw Brandt parity and removed-prime filter",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [3, 0],
        "level_norm": 19683,
        "parity_traces_mod5": [0, 1, 4],
        "removed_prime7_targets_mod5": [2, 3],
        "eisenstein_signatures_mod5": {"norm8": 4, "norm7": 3},
        "soundness": (
            "zero cusp survivor upper bound eliminates the level, provided the raw module "
            "differs from the independently computed cuspidal newspace only by the verified "
            "class-number-one Eisenstein line"
        ),
        "nonclaim": (
            "the exact raw-to-cuspidal quotient statement, parity traces, removed-prime local "
            "theorem, modularity and level lowering remain explicit imported inputs"
        ),
        "input_bytes": len(source.encode()),
    }
    output = ""
    try:
        output = submit(source)
        raw_dim = parse_int(output, "RAW_DIM")
        cusp_dim = parse_int(output, "CUSP_NEW_DIM")
        eisenstein_dimension = parse_int(output, "EISENSTEIN_CANDIDATE_DIM")
        if raw_dim - cusp_dim != eisenstein_dimension:
            raise ResearchError(
                "raw/cusp dimension difference does not equal the verified Eisenstein dimension"
            )
        body.update({
            "request_status": "completed",
            "cuspidal_new_dimension": cusp_dim,
            "raw_dimension": raw_dim,
            "raw_trace0_dimension": parse_int(output, "RAW_TRACE0_DIM"),
            "raw_trace_plus1_dimension": parse_int(output, "RAW_TRACE_PLUS1_DIM"),
            "raw_trace_minus1_dimension": parse_int(output, "RAW_TRACE_MINUS1_DIM"),
            "raw_trace0_after7_dimension": parse_int(output, "RAW_TRACE0_AFTER7"),
            "raw_trace_plus1_after7_dimension": parse_int(output, "RAW_TRACE_PLUS1_AFTER7"),
            "raw_trace_minus1_after7_dimension": parse_int(output, "RAW_TRACE_MINUS1_AFTER7"),
            "raw_total_after7_dimension": parse_int(output, "RAW_TOTAL_AFTER7"),
            "eisenstein_candidate_dimension": eisenstein_dimension,
            "cusp_survivor_upper_bound": parse_int(output, "CUSP_SURVIVOR_UPPER_BOUND"),
            "output_tail": output[-9000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-12000:],
        })
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
