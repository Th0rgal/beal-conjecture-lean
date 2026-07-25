#!/usr/bin/env python3
"""Intersect split-prime HGM trace unions on the level-137781 parity spaces.

The exact norm-8 trace decomposes the residual newspace into three distinct
Hecke eigenspaces of dimensions 38, 46 and 46.  For each split auxiliary prime
13, 29, 41 and 43 this producer:

* constructs the full Hecke operator only once;
* restricts it to each original parity eigenspace;
* evaluates the complete generic/zero/infinity/multiplicative HGM union on the
  resulting 38x38 or 46x46 matrix;
* intersects the kernel with the kernels retained at earlier primes.

All intersections live in the fixed coordinate space of the original parity
eigenspace.  Commutativity of the Hecke algebra makes every retained subspace
stable under the later restricted operators.  A zero final dimension eliminates
the corresponding parity branch.  Positive dimensions are only necessary
marginal survivors; the stronger parameter-coupled and semilinear conditions
are deliberately omitted.
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
PRIMES = [13, 29, 41, 43]


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


def magma_list(values: list[str]) -> str:
    return "[" + ",".join(values) + "]"


def encode_rows(data: dict[str, Any]) -> str:
    encoded: list[str] = []
    for prime in PRIMES:
        if prime not in data.get("primes", []):
            raise ResearchError(f"complete local data lacks prime {prime}")
        md = data["residue_metadata"][str(prime)]
        kinds: dict[str, list[str]] = {}
        for kind in ("generic", "zero", "infinity"):
            kinds[kind] = [
                row["trace_polynomial"]
                for row in data[f"{kind}_rows"]
                if row["prime"] == prime
            ]
        encoded.append(
            f"<{prime},{magma_list(kinds['generic'])},{magma_list(kinds['zero'])},"
            f"{magma_list(kinds['infinity'])},{md['residue_degree_K7']},"
            f"{md['residue_degree_F21']}>"
        )
    return "[" + ",".join(encoded) + "]"


def magma_code(data: dict[str, Any]) -> str:
    rows = encode_rows(data)
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I7:=Factorisation(7*OK)[1][1];
I2:=Factorisation(2*OK)[1][1];
F5:=GF(5); R5<X>:=PolynomialRing(F5);
Rows:={rows};
Red:=function(P) return R5![F5!Coefficient(P,i):i in [0..Degree(P)]]; end function;
AllowedPolynomial:=function(row)
  l:=row[1]; I:=Factorisation(l*OK)[1][1]; q:=Integers()!Norm(I); U:=X;
  if row[6] div row[5] eq 2 then U:=X^2-F5!(2*l^row[5]); end if;
  P:=R5!1;
  for Q in row[2] do P*:=Red(Q); end for;
  for Q in row[3] do P*:=Evaluate(Red(Q),U); end for;
  for Q in row[4] do P*:=Evaluate(Red(Q),U); end for;
  P*:=(X-F5!(q+1))*(X+F5!(q+1));
  return P;
end function;
EvalMatrix:=function(P,T)
  n:=Nrows(T); A:=ZeroMatrix(F5,n,n); Q:=IdentityMatrix(F5,n);
  for i in [0..Degree(P)] do
    A+:=F5!Coefficient(P,i)*Q;
    if i lt Degree(P) then Q:=Q*T; end if;
  end for;
  return A;
end function;

printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,I3^3*I7); M:=NewSubspace(M0); n:=Dimension(M);
printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
printf "PHASE=T2-start\n";
T2Q:=HeckeOperator(M,I2); DeleteHeckePrecomputation(O,I2); ClearStoredModularForms(K);
T2:=Matrix(F5,T2Q); delete T2Q;
Id:=IdentityMatrix(F5,n);
S0:=Kernel(T2); Sp:=Kernel(T2-Id); Sm:=Kernel(T2+Id);
printf "TRACE0_INITIAL_DIM=%o\n",Dimension(S0);
printf "TRACE_PLUS1_INITIAL_DIM=%o\n",Dimension(Sp);
printf "TRACE_MINUS1_INITIAL_DIM=%o\n",Dimension(Sm);
delete T2;
V0:=VectorSpace(F5,Dimension(S0)); Vp:=VectorSpace(F5,Dimension(Sp)); Vm:=VectorSpace(F5,Dimension(Sm));
K0:=V0; Kp:=Vp; Km:=Vm;

for row in Rows do
  l:=row[1]; Iell:=Factorisation(l*OK)[1][1];
  printf "PHASE=T%o-start\n",l;
  TQ:=HeckeOperator(M,Iell); DeleteHeckePrecomputation(O,Iell); ClearStoredModularForms(K);
  T:=Matrix(F5,TQ); delete TQ;
  A0:=Restrict(T,S0); Ap:=Restrict(T,Sp); Am:=Restrict(T,Sm); delete T;
  P:=AllowedPolynomial(row);
  L0:=Kernel(EvalMatrix(P,A0)); Lp:=Kernel(EvalMatrix(P,Ap)); Lm:=Kernel(EvalMatrix(P,Am));
  K0:=K0 meet L0; Kp:=Kp meet Lp; Km:=Km meet Lm;
  printf "ALLOWED_DEGREE_%o=%o\n",l,Degree(P);
  printf "TRACE0_AFTER_%o=%o\n",l,Dimension(K0);
  printf "TRACE_PLUS1_AFTER_%o=%o\n",l,Dimension(Kp);
  printf "TRACE_MINUS1_AFTER_%o=%o\n",l,Dimension(Km);
  if Dimension(K0)+Dimension(Kp)+Dimension(Km) eq 0 then break; end if;
end for;
printf "B_ODD_FINAL_DIM=%o\n",Dimension(K0);
printf "B_EVEN_FINAL_DIM=%o\n",Dimension(Kp)+Dimension(Km);
printf "FINAL_DIM=%o\n",Dimension(K0)+Dimension(Kp)+Dimension(Km);
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
        "status": "level-137781 four-prime parity-chain residual HGM sieve",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [3, 1],
        "level_norm": 137781,
        "auxiliary_primes": PRIMES,
        "local_data_sha256": local.get("certificate_sha256"),
        "conditions_omitted": [
            "semilinear conjugate-prime relations",
            "exact two-Frey parameter coupling",
        ],
        "input_bytes": len(source.encode()),
        "soundness": (
            "zero final dimension eliminates every residual eigensystem at the level; "
            "positive dimension is only a necessary marginal survivor"
        ),
        "nonclaim": (
            "the local HGM identification, parity trace theorem, modularity and level "
            "lowering remain imported research inputs"
        ),
    }
    output = ""
    try:
        output = submit(source)
        dimensions: dict[str, dict[str, int]] = {}
        for prime in PRIMES:
            rows = {}
            for label, marker in (
                ("trace0", f"TRACE0_AFTER_{prime}"),
                ("trace_plus1", f"TRACE_PLUS1_AFTER_{prime}"),
                ("trace_minus1", f"TRACE_MINUS1_AFTER_{prime}"),
            ):
                match = re.search(rf"{marker}=(\d+)", output)
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
            "final_dimension": parse_int(output, "FINAL_DIM"),
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
