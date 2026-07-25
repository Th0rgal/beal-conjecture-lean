#!/usr/bin/env python3
"""Probe the level-19683 mod-5 branch in the indefinite ambient Hilbert space.

The definite newspace construction reaches dimension 225 but exhausts the public
Magma memory limit while building T_2.  Over the odd-degree field K7, the full
ambient space is computed independently by the indefinite algorithm and has
only dimension 244.  This probe computes T_2 there, splits the exact parity
traces 0,+1,-1, and then imposes the removed-prime trace a_7=+/-8 mod 5.

A zero survivor in the full ambient space eliminates the newspace a fortiori.
A positive survivor is not claimed to be new and leaves the level unresolved.
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
        return html.unescape(re.sub(r"<[^>]+>", "", response.read().decode(errors="replace")))


def magma_code() -> str:
    return r'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I7:=Factorisation(7*OK)[1][1];
I2:=Factorisation(2*OK)[1][1]; F5:=GF(5);
printf "PHASE=ambient-start\n";
M:=HilbertCuspForms(K,I3^3); n:=Dimension(M);
printf "AMBIENT_DIM=%o\n",n;
printf "IS_DEFINITE=%o\n",IsDefinite(M);
printf "PHASE=T2-start\n";
T2Q:=HeckeOperator(M,I2); T2:=Matrix(F5,T2Q); delete T2Q;
printf "PHASE=T2-ready\n";
Id:=IdentityMatrix(F5,n);
S0:=Kernel(T2); Sp:=Kernel(T2-Id); Sm:=Kernel(T2+Id);
printf "TRACE0_DIM=%o\n",Dimension(S0);
printf "TRACE_PLUS1_DIM=%o\n",Dimension(Sp);
printf "TRACE_MINUS1_DIM=%o\n",Dimension(Sm);
delete T2;
printf "PHASE=T7-start\n";
T7Q:=HeckeOperator(M,I7); T7:=Matrix(F5,T7Q); delete T7Q;
printf "PHASE=T7-ready\n";
R0:=Restrict(T7,S0); Rp:=Restrict(T7,Sp); Rm:=Restrict(T7,Sm);
I0:=IdentityMatrix(F5,Dimension(S0));
Ip:=IdentityMatrix(F5,Dimension(Sp));
Im:=IdentityMatrix(F5,Dimension(Sm));
K0:=Kernel((R0-F5!2*I0)*(R0-F5!3*I0));
Kp:=Kernel((Rp-F5!2*Ip)*(Rp-F5!3*Ip));
Km:=Kernel((Rm-F5!2*Im)*(Rm-F5!3*Im));
printf "TRACE0_AFTER_REMOVED7_DIM=%o\n",Dimension(K0);
printf "TRACE_PLUS1_AFTER_REMOVED7_DIM=%o\n",Dimension(Kp);
printf "TRACE_MINUS1_AFTER_REMOVED7_DIM=%o\n",Dimension(Km);
printf "FINAL_AMBIENT_DIM=%o\n",Dimension(K0)+Dimension(Kp)+Dimension(Km);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    source = magma_code()
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "level-19683 indefinite-ambient parity and removed-prime probe",
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [3, 0],
        "level_norm": 19683,
        "calculator": CALCULATOR_URL,
        "parity_traces_mod5": [0, 1, 4],
        "removed_prime7_targets_mod5": [2, 3],
        "input_bytes": len(source.encode()),
        "soundness": (
            "zero final ambient dimension eliminates the 225-dimensional newspace; "
            "positive ambient dimension includes possible oldforms and is only necessary"
        ),
        "nonclaim": (
            "the parity traces, removed-prime local theorem, modularity and level lowering "
            "remain imported research inputs"
        ),
    }
    output = ""
    try:
        output = submit(source)
        body.update({
            "request_status": "completed",
            "ambient_dimension": parse_int(output, "AMBIENT_DIM"),
            "trace0_dimension": parse_int(output, "TRACE0_DIM"),
            "trace_plus1_dimension": parse_int(output, "TRACE_PLUS1_DIM"),
            "trace_minus1_dimension": parse_int(output, "TRACE_MINUS1_DIM"),
            "trace0_after_removed7_dimension": parse_int(output, "TRACE0_AFTER_REMOVED7_DIM"),
            "trace_plus1_after_removed7_dimension": parse_int(output, "TRACE_PLUS1_AFTER_REMOVED7_DIM"),
            "trace_minus1_after_removed7_dimension": parse_int(output, "TRACE_MINUS1_AFTER_REMOVED7_DIM"),
            "final_ambient_dimension": parse_int(output, "FINAL_AMBIENT_DIM"),
            "output_tail": output[-7000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-10000:],
        })
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
