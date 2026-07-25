#!/usr/bin/env python3
"""Apply the prime-13 local and semilinear conditions to level 137781.

After the norm-8 parity split, the residual newspace has dimensions 38, 46 and
46 for traces 0,+1,-1.  At the three primes above 13, rational specialization
requires the Hecke traces to be a Frobenius-conjugate triple in F_125.  If a is
the trace at the first prime, the other two traces have unordered values
a^5,a^25.  This is imposed by

    a^125=a,
    b+c=a^5+a^25,
    b*c=a^30.

The complete local HGM union at the first prime is represented by the
square-free degree-43 polynomial G13.  Zero output dimension eliminates the
corresponding parity branch; positive dimension is only a necessary survivor.
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
G13_COEFFICIENTS = [
    0, 1, 4, 1, 0, 1, 2, 2, 0, 4, 3, 2, 0, 1, 4, 1, 0, 1, 0, 3, 4, 4,
    0, 3, 0, 0, 4, 2, 1, 4, 0, 0, 3, 4, 0, 4, 4, 3, 0, 3, 4, 0, 2, 1,
]
LOCAL_SOURCE_SHA256 = "c20e4d0d046df579a94e6e344e20a3bf2a87a563eb31d8ab7c58351b1d242e34"


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
    coefficients = ",".join(str(value) for value in G13_COEFFICIENTS)
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I7:=Factorisation(7*OK)[1][1];
I2:=Factorisation(2*OK)[1][1]; P13:=Factorisation(13*OK);
F5:=GF(5); R5<X>:=PolynomialRing(F5); G13:=R5![{coefficients}];
EvalMatrix:=function(P,T)
  n:=Nrows(T); A:=ZeroMatrix(F5,n,n); Q:=IdentityMatrix(F5,n);
  for i in [0..Degree(P)] do
    A+:=F5!Coefficient(P,i)*Q;
    if i lt Degree(P) then Q:=Q*T; end if;
  end for;
  return A;
end function;
IntersectConditions:=function(A,B,C)
  d:=Nrows(A); V:=VectorSpace(F5,d); Id:=IdentityMatrix(F5,d);
  K:=V meet Kernel(EvalMatrix(G13,A));
  K:=K meet Kernel(A^125-A);
  K:=K meet Kernel(B+C-A^5-A^25);
  K:=K meet Kernel(B*C-A^30);
  return K;
end function;
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,I3^3*I7); M:=NewSubspace(M0); n:=Dimension(M);
printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
printf "PHASE=T2-start\n";
T2Q:=HeckeOperator(M,I2); DeleteHeckePrecomputation(O,I2); ClearStoredModularForms(K);
T2:=Matrix(F5,T2Q); delete T2Q; Id:=IdentityMatrix(F5,n);
S0:=Kernel(T2); Sp:=Kernel(T2-Id); Sm:=Kernel(T2+Id); delete T2;
printf "TRACE0_INITIAL_DIM=%o\n",Dimension(S0);
printf "TRACE_PLUS1_INITIAL_DIM=%o\n",Dimension(Sp);
printf "TRACE_MINUS1_INITIAL_DIM=%o\n",Dimension(Sm);
R0:=[]; Rp:=[]; Rm:=[];
for j in [1..3] do
  printf "PHASE=T13_%o-start\n",j;
  TQ:=HeckeOperator(M,P13[j][1]); DeleteHeckePrecomputation(O,P13[j][1]); ClearStoredModularForms(K);
  T:=Matrix(F5,TQ); delete TQ;
  Append(~R0,Restrict(T,S0)); Append(~Rp,Restrict(T,Sp)); Append(~Rm,Restrict(T,Sm));
  delete T;
end for;
printf "PHASE=three-restrictions-ready\n";
K0:=IntersectConditions(R0[1],R0[2],R0[3]);
Kp:=IntersectConditions(Rp[1],Rp[2],Rp[3]);
Km:=IntersectConditions(Rm[1],Rm[2],Rm[3]);
printf "TRACE0_AFTER_LOCAL=%o\n",Dimension(Kernel(EvalMatrix(G13,R0[1])));
printf "TRACE_PLUS1_AFTER_LOCAL=%o\n",Dimension(Kernel(EvalMatrix(G13,Rp[1])));
printf "TRACE_MINUS1_AFTER_LOCAL=%o\n",Dimension(Kernel(EvalMatrix(G13,Rm[1])));
printf "TRACE0_AFTER_SEMILINEAR=%o\n",Dimension(K0);
printf "TRACE_PLUS1_AFTER_SEMILINEAR=%o\n",Dimension(Kp);
printf "TRACE_MINUS1_AFTER_SEMILINEAR=%o\n",Dimension(Km);
printf "B_ODD_FINAL_DIM=%o\n",Dimension(K0);
printf "B_EVEN_FINAL_DIM=%o\n",Dimension(Kp)+Dimension(Km);
printf "TOTAL_FINAL_DIM=%o\n",Dimension(K0)+Dimension(Kp)+Dimension(Km);
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
        "status": "level-137781 prime-13 local-plus-semilinear parity sieve",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [3, 1],
        "level_norm": 137781,
        "auxiliary_rational_prime": 13,
        "local_source_sha256": LOCAL_SOURCE_SHA256,
        "g13_coefficients_low_to_high_mod5": G13_COEFFICIENTS,
        "semilinear_relations": [
            "a^125=a",
            "b+c=a^5+a^25",
            "b*c=a^30",
        ],
        "soundness": (
            "zero final dimension eliminates the corresponding parity branch; positive "
            "dimension is only a necessary survivor"
        ),
        "nonclaim": (
            "the local HGM identification, semilinear descent, modularity and level lowering "
            "remain imported research inputs"
        ),
        "input_bytes": len(source.encode()),
    }
    output = ""
    try:
        output = submit(source)
        body.update({
            "request_status": "completed",
            "new_dimension": parse_int(output, "NEW_DIM"),
            "trace0_initial_dimension": parse_int(output, "TRACE0_INITIAL_DIM"),
            "trace_plus1_initial_dimension": parse_int(output, "TRACE_PLUS1_INITIAL_DIM"),
            "trace_minus1_initial_dimension": parse_int(output, "TRACE_MINUS1_INITIAL_DIM"),
            "trace0_after_local_dimension": parse_int(output, "TRACE0_AFTER_LOCAL"),
            "trace_plus1_after_local_dimension": parse_int(output, "TRACE_PLUS1_AFTER_LOCAL"),
            "trace_minus1_after_local_dimension": parse_int(output, "TRACE_MINUS1_AFTER_LOCAL"),
            "trace0_after_semilinear_dimension": parse_int(output, "TRACE0_AFTER_SEMILINEAR"),
            "trace_plus1_after_semilinear_dimension": parse_int(output, "TRACE_PLUS1_AFTER_SEMILINEAR"),
            "trace_minus1_after_semilinear_dimension": parse_int(output, "TRACE_MINUS1_AFTER_SEMILINEAR"),
            "b_odd_final_dimension": parse_int(output, "B_ODD_FINAL_DIM"),
            "b_even_final_dimension": parse_int(output, "B_EVEN_FINAL_DIM"),
            "total_final_dimension": parse_int(output, "TOTAL_FINAL_DIM"),
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
