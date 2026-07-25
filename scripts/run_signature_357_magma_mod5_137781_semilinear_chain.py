#!/usr/bin/env python3
"""Run the full split-prime semilinear chain on level 137781.

The norm-8 parity split gives residual spaces of dimensions 38,46,46.  For
13,29,41,43 the complete local HGM union is reduced modulo 5 and replaced by
its square-free gcd with X^125-X.  At each split rational prime, all three
Hecke operators are computed and the traces are required to form the
Frobenius-conjugate triple (a,a^5,a^25), up to exchanging the last two terms.

All conditions are intersected in the fixed coordinates of each original
parity eigenspace.  A zero total dimension eliminates level 137781; a positive
dimension is only a necessary residual survivor.
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
LOCAL_SOURCE_SHA256 = "c20e4d0d046df579a94e6e344e20a3bf2a87a563eb31d8ab7c58351b1d242e34"
PRIMES = [13, 29, 41, 43]
G_COEFFICIENTS: dict[int, list[int]] = {
    13: [0,1,4,1,0,1,2,2,0,4,3,2,0,1,4,1,0,1,0,3,4,4,0,3,0,0,4,2,1,4,0,0,3,4,0,4,4,3,0,3,4,0,2,1],
    29: [0,2,4,0,0,2,4,3,3,1,4,1,4,3,3,3,2,0,2,2,4,2,4,0,0,0,0,4,3,2,4,2,3,4,0,1,1,2,0,1,3,1,4,4,3,0,3,2,0,4,4,2,2,0,1,4,4,1],
    41: [0,4,1,4,2,1,2,2,3,0,3,4,3,2,1,3,3,2,0,1,1,4,1,0,1,1,4,3,0,2,4,3,2,1,0,2,1,4,2,1,1,3,3,1,2,2,1,3,3,1],
    43: [4,3,0,2,4,3,2,4,4,0,1,4,1,4,1,3,0,1,2,1,3,2,4,1,2,4,2,0,2,1,0,4,4,3,2,4,0,0,3,2,2,3,0,1,3,2,3,4,3,4,1,4,0,4,2,2,4,4,0,1,1,2,1,0,2,1,2,3,0,3,0,0,2,2,0,1,1,3,3,1,0,3,4,2,0,0,2,4,2,0,1],
}


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
    encoded = ",".join(
        f"<{prime},R5![{','.join(str(v) for v in G_COEFFICIENTS[prime])}]>"
        for prime in PRIMES
    )
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I7:=Factorisation(7*OK)[1][1];
I2:=Factorisation(2*OK)[1][1]; F5:=GF(5); R5<X>:=PolynomialRing(F5);
Rows:=[{encoded}];
EvalMatrix:=function(P,T)
  n:=Nrows(T); A:=ZeroMatrix(F5,n,n); Q:=IdentityMatrix(F5,n);
  for i in [0..Degree(P)] do
    A+:=F5!Coefficient(P,i)*Q;
    if i lt Degree(P) then Q:=Q*T; end if;
  end for;
  return A;
end function;
Conditions:=function(A,B,C,G)
  d:=Nrows(A); V:=VectorSpace(F5,d);
  K:=V meet Kernel(EvalMatrix(G,A));
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
K0:=VectorSpace(F5,Dimension(S0)); Kp:=VectorSpace(F5,Dimension(Sp)); Km:=VectorSpace(F5,Dimension(Sm));
for row in Rows do
  l:=row[1]; G:=row[2]; fac:=Factorisation(l*OK);
  R0:=[]; Rp:=[]; Rm:=[];
  for j in [1..3] do
    printf "PHASE=T%o_%o-start\n",l,j;
    TQ:=HeckeOperator(M,fac[j][1]); DeleteHeckePrecomputation(O,fac[j][1]); ClearStoredModularForms(K);
    T:=Matrix(F5,TQ); delete TQ;
    Append(~R0,Restrict(T,S0)); Append(~Rp,Restrict(T,Sp)); Append(~Rm,Restrict(T,Sm));
    delete T;
  end for;
  K0:=K0 meet Conditions(R0[1],R0[2],R0[3],G);
  Kp:=Kp meet Conditions(Rp[1],Rp[2],Rp[3],G);
  Km:=Km meet Conditions(Rm[1],Rm[2],Rm[3],G);
  printf "TRACE0_AFTER_%o=%o\n",l,Dimension(K0);
  printf "TRACE_PLUS1_AFTER_%o=%o\n",l,Dimension(Kp);
  printf "TRACE_MINUS1_AFTER_%o=%o\n",l,Dimension(Km);
  printf "TOTAL_AFTER_%o=%o\n",l,Dimension(K0)+Dimension(Kp)+Dimension(Km);
  if Dimension(K0)+Dimension(Kp)+Dimension(Km) eq 0 then break; end if;
end for;
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
        "status": "level-137781 split-prime semilinear chain",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [3, 1],
        "level_norm": 137781,
        "auxiliary_primes": PRIMES,
        "local_source_sha256": LOCAL_SOURCE_SHA256,
        "squarefree_local_polynomial_degrees": {
            str(prime): len(G_COEFFICIENTS[prime]) - 1 for prime in PRIMES
        },
        "semilinear_relations": ["a^125=a", "b+c=a^5+a^25", "b*c=a^30"],
        "soundness": (
            "zero total dimension eliminates level 137781; positive dimension is only a "
            "necessary residual survivor"
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
        dimensions: dict[str, dict[str, int]] = {}
        for prime in PRIMES:
            rows: dict[str, int] = {}
            for label, marker in (
                ("trace0", f"TRACE0_AFTER_{prime}"),
                ("trace_plus1", f"TRACE_PLUS1_AFTER_{prime}"),
                ("trace_minus1", f"TRACE_MINUS1_AFTER_{prime}"),
                ("total", f"TOTAL_AFTER_{prime}"),
            ):
                match = re.search(rf"(?:^|\n){re.escape(marker)}=(\d+)(?:\n|$)", output)
                if match is not None:
                    rows[label] = int(match.group(1))
            if rows:
                dimensions[str(prime)] = rows
        body.update({
            "request_status": "completed",
            "new_dimension": parse_int(output, "NEW_DIM"),
            "trace0_initial_dimension": parse_int(output, "TRACE0_INITIAL_DIM"),
            "trace_plus1_initial_dimension": parse_int(output, "TRACE_PLUS1_INITIAL_DIM"),
            "trace_minus1_initial_dimension": parse_int(output, "TRACE_MINUS1_INITIAL_DIM"),
            "dimensions_after_primes": dimensions,
            "b_odd_final_dimension": parse_int(output, "B_ODD_FINAL_DIM"),
            "b_even_final_dimension": parse_int(output, "B_EVEN_FINAL_DIM"),
            "total_final_dimension": parse_int(output, "TOTAL_FINAL_DIM"),
            "output_tail": output[-12000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-15000:],
        })
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
