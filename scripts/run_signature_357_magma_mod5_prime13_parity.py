#!/usr/bin/env python3
"""Apply the complete prime-13 HGM trace union after the norm-8 parity split.

At the remaining mod-5 level 137781, the exact prime-2 computation decomposes
its residual frontier into the distinct eigenspaces

    ker(T2), ker(T2-1), ker(T2+1)

of dimensions 38, 46 and 46.  This producer constructs the prime-13 Hecke
operator once, restricts it to those small stable spaces, and compares each
restricted characteristic polynomial with the complete generic/zero/infinity/
multiplicative HGM trace union modulo 5.

A gcd of degree zero eliminates the corresponding parity branch.  Positive
degree is only a necessary residual survivor, and every failed request is
recorded explicitly.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import http.cookiejar
import json
import pathlib
import re
import urllib.parse
import urllib.request
from typing import Any

CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"
PRIME = 13


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
        return html.unescape(re.sub(r"<[^>]+>", "", response.read().decode(errors="replace")))


def magma_list(values: list[str]) -> str:
    return "[" + ",".join(values) + "]"


def local_row(data: dict[str, Any]) -> tuple[list[str], list[str], list[str], int, int]:
    if PRIME not in data.get("primes", []):
        raise ResearchError("complete local data does not contain prime 13")
    metadata = data["residue_metadata"][str(PRIME)]
    rows: dict[str, list[str]] = {}
    for kind in ("generic", "zero", "infinity"):
        rows[kind] = [
            row["trace_polynomial"]
            for row in data[f"{kind}_rows"]
            if row["prime"] == PRIME
        ]
    return (
        rows["generic"], rows["zero"], rows["infinity"],
        metadata["residue_degree_K7"], metadata["residue_degree_F21"],
    )


def magma_code(data: dict[str, Any]) -> str:
    generic, zero, infinity, degree_k, degree_f = local_row(data)
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I7:=Factorisation(7*OK)[1][1];
I2:=Factorisation(2*OK)[1][1]; I13:=Factorisation(13*OK)[1][1];
F5:=GF(5); R5<X>:=PolynomialRing(F5);
Generic:={magma_list(generic)};
Zero:={magma_list(zero)};
Infinity:={magma_list(infinity)};
Red:=function(P) return R5![F5!Coefficient(P,i):i in [0..Degree(P)]]; end function;
U:=X;
if {degree_f} div {degree_k} eq 2 then U:=X^2-F5!(2*13^{degree_k}); end if;
Allowed:=R5!1;
for P in Generic do Allowed*:=Red(P); end for;
for P in Zero do Allowed*:=Evaluate(Red(P),U); end for;
for P in Infinity do Allowed*:=Evaluate(Red(P),U); end for;
q:=Integers()!Norm(I13);
Allowed*:=(X-F5!(q+1))*(X+F5!(q+1));
printf "ALLOWED_DEGREE=%o\n",Degree(Allowed);
printf "ALLOWED_GCD_F5=%o\n",GreatestCommonDivisor(Allowed,X^5-X);

printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,I3^3*I7);
printf "AMBIENT_DIM=%o\n",Dimension(M0);
M:=NewSubspace(M0); n:=Dimension(M);
printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
printf "PHASE=T2-start\n";
T2Q:=HeckeOperator(M,I2);
DeleteHeckePrecomputation(O,I2); ClearStoredModularForms(K);
T2:=Matrix(F5,T2Q); delete T2Q;
Id:=IdentityMatrix(F5,n);
S0:=Kernel(T2); Sp:=Kernel(T2-Id); Sm:=Kernel(T2+Id);
printf "TRACE0_DIM=%o\n",Dimension(S0);
printf "TRACE_PLUS1_DIM=%o\n",Dimension(Sp);
printf "TRACE_MINUS1_DIM=%o\n",Dimension(Sm);
delete T2;

printf "PHASE=T13-start\n";
T13Q:=HeckeOperator(M,I13);
DeleteHeckePrecomputation(O,I13); ClearStoredModularForms(K);
T13:=Matrix(F5,T13Q); delete T13Q;
printf "PHASE=T13-mod5-ready\n";

T0:=Restrict(T13,S0); Tp:=Restrict(T13,Sp); Tm:=Restrict(T13,Sm);
CP0:=R5!CharacteristicPolynomial(T0);
CPp:=R5!CharacteristicPolynomial(Tp);
CPm:=R5!CharacteristicPolynomial(Tm);
G0:=GreatestCommonDivisor(CP0,Allowed);
Gp:=GreatestCommonDivisor(CPp,Allowed);
Gm:=GreatestCommonDivisor(CPm,Allowed);
printf "TRACE0_GCD_DEGREE=%o\n",Degree(G0);
printf "TRACE_PLUS1_GCD_DEGREE=%o\n",Degree(Gp);
printf "TRACE_MINUS1_GCD_DEGREE=%o\n",Degree(Gm);
printf "TRACE0_GCD=%o\n",G0;
printf "TRACE_PLUS1_GCD=%o\n",Gp;
printf "TRACE_MINUS1_GCD=%o\n",Gm;
printf "B_ODD_SURVIVES=%o\n",Degree(G0) gt 0;
printf "B_EVEN_SURVIVES=%o\n",Degree(Gp) gt 0 or Degree(Gm) gt 0;
printf "FINAL_SURVIVING_PARITY_COUNT=%o\n",(Degree(G0) gt 0 select 1 else 0)+(Degree(Gp) gt 0 or Degree(Gm) gt 0 select 1 else 0);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-data", type=pathlib.Path, required=True)
    args = parser.parse_args()
    local = json.loads(args.local_data.read_text(encoding="utf-8"))
    source = magma_code(local)
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "level-137781 prime-13 parity-split residual HGM filter",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [3, 1],
        "level_norm": 137781,
        "auxiliary_prime": PRIME,
        "local_data_sha256": local.get("certificate_sha256"),
        "input_bytes": len(source.encode()),
        "soundness": (
            "gcd degree zero eliminates the corresponding norm-8 parity eigenspace; "
            "positive degree is only a necessary residual survivor"
        ),
        "nonclaim": (
            "the local HGM identification, parity trace theorem, modularity and level "
            "lowering remain imported research inputs"
        ),
    }
    output = ""
    try:
        output = submit(source)
        body.update({
            "request_status": "completed",
            "ambient_dimension": parse_int(output, "AMBIENT_DIM"),
            "new_dimension": parse_int(output, "NEW_DIM"),
            "trace0_dimension": parse_int(output, "TRACE0_DIM"),
            "trace_plus1_dimension": parse_int(output, "TRACE_PLUS1_DIM"),
            "trace_minus1_dimension": parse_int(output, "TRACE_MINUS1_DIM"),
            "allowed_polynomial_degree": parse_int(output, "ALLOWED_DEGREE"),
            "trace0_gcd_degree": parse_int(output, "TRACE0_GCD_DEGREE"),
            "trace_plus1_gcd_degree": parse_int(output, "TRACE_PLUS1_GCD_DEGREE"),
            "trace_minus1_gcd_degree": parse_int(output, "TRACE_MINUS1_GCD_DEGREE"),
            "surviving_parity_count": parse_int(output, "FINAL_SURVIVING_PARITY_COUNT"),
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
