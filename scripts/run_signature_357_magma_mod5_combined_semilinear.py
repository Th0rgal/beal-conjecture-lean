#!/usr/bin/env python3
"""Intersect the odd-branch mod-5 residual Hecke conditions level by level.

The cyclotomic untwist reduces the odd branch to Hilbert levels 5103, 19683 and
137781 over K7=Q(zeta_7)^+.  A rational specialization imposes more than a
marginal trace condition: at inert rational primes its trace is scalar in F5,
and at split primes the three conjugate traces form a Frobenius orbit.  This
producer intersects those semilinear relations with the complete local HGM
trace-polynomial unions directly in the residual Hecke module.

A zero final dimension is a fail-closed elimination of all residual eigensystems
at that level, conditional on the imported compatible-system, local-trace,
semilinear-descent and level-lowering theorems.  A nonzero dimension is only a
necessary survivor space.
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
LEVEL_PAIRS = [(2, 1), (3, 0), (3, 1)]
# Put inert primes first, then completely split primes.
INERT_PRIMES = [11, 23]
SPLIT_PRIMES = [13, 29, 41, 43]
PRIMES = INERT_PRIMES + SPLIT_PRIMES
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
    action = (
        CALCULATOR_URL
        if action_match is None
        else urllib.parse.urljoin(CALCULATOR_URL, html.unescape(action_match.group(1)))
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
        raise ResearchError(f"generated input has {len(code.encode())} bytes")
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
    with opener.open(request, timeout=210) as response:
        page = response.read().decode(errors="replace")
    return html.unescape(re.sub(r"<[^>]+>", "", page))


def rows_from(data: dict[str, Any], wanted: list[int]) -> dict[int, tuple[Any, ...]]:
    result: dict[int, tuple[Any, ...]] = {}
    for prime in wanted:
        if prime not in data.get("primes", []):
            raise ResearchError(f"local data lacks prime {prime}")
        metadata = data["residue_metadata"][str(prime)]
        kinds = {
            kind: [
                row["trace_polynomial"]
                for row in data[f"{kind}_rows"]
                if row["prime"] == prime
            ]
            for kind in ("generic", "zero", "infinity")
        }
        result[prime] = (
            prime,
            kinds["generic"],
            kinds["zero"],
            kinds["infinity"],
            metadata["residue_degree_K7"],
            metadata["residue_degree_F21"],
        )
    return result


def magma_list(values: list[str]) -> str:
    return "[" + ",".join(values) + "]"


def encode_row(row: tuple[Any, ...]) -> str:
    prime, generic, zero, infinity, degree_k, degree_f = row
    return (
        f"<{prime},{magma_list(generic)},{magma_list(zero)},"
        f"{magma_list(infinity)},{degree_k},{degree_f}>"
    )


def magma_code(e3: int, e7: int, rows: dict[int, tuple[Any, ...]]) -> str:
    encoded = ",".join(encode_row(rows[prime]) for prime in PRIMES)
    return rf'''
_<x> := PolynomialRing(Rationals());
K<w> := NumberField(x^3-x^2-2*x+1); OK := Integers(K);
I3 := Factorisation(3*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
I2 := Factorisation(2*OK)[1][1];
F5 := GF(5); R5<X> := PolynomialRing(F5);
Rows := [{encoded}];
Red := function(P)
  return R5![F5!Coefficient(P,i) : i in [0..Degree(P)]];
end function;
EvalMatrix := function(P,T)
  n:=Nrows(T); A:=ZeroMatrix(F5,n,n); Q:=IdentityMatrix(F5,n);
  for i in [0..Degree(P)] do
    A +:= F5!Coefficient(P,i)*Q;
    Q:=Q*T;
  end for;
  return A;
end function;
UnionMatrix := function(T,row)
  l:=row[1]; n:=Nrows(T); Id:=IdentityMatrix(F5,n); U:=T;
  if row[6]/row[5] eq 2 then U:=T*T-F5!(2*l^row[5])*Id; end if;
  A:=Id;
  for P in row[2] do A:=A*EvalMatrix(Red(P),U); end for;
  for P in row[3] do A:=A*EvalMatrix(Red(P),U); end for;
  for P in row[4] do A:=A*EvalMatrix(Red(P),U); end for;
  q:=Integers()!Norm(Factorisation(l*OK)[1][1]);
  A:=A*(T-F5!(q+1)*Id)*(T+F5!(q+1)*Id);
  return A;
end function;
M0:=HilbertCuspForms(K,I3^{e3}*I7^{e7});
M:=NewSubspace(M0); SetRationalBasis(M);
n:=Dimension(M); V:=VectorSpace(F5,n);
printf "LEVEL_PAIR=[{e3},{e7}]\n";
printf "LEVEL_NORM=%o\n",27^{e3}*7^{e7};
printf "NEW_DIM=%o\n",n;
T2:=Matrix(F5,HeckeOperator(M,I2));
S:=V meet Kernel(T2);
printf "NORM8_DIM=%o\n",Dimension(S);
for row in Rows do
  l:=row[1]; fac:=Factorisation(l*OK);
  T1:=Matrix(F5,HeckeOperator(M,fac[1][1]));
  S:=S meet Kernel(UnionMatrix(T1,row));
  if #fac eq 1 then
    S:=S meet Kernel(T1^5-T1);
  elif #fac eq 3 then
    T2c:=Matrix(F5,HeckeOperator(M,fac[2][1]));
    T3c:=Matrix(F5,HeckeOperator(M,fac[3][1]));
    S:=S meet Kernel(T2c+T3c-T1^5-T1^25);
    S:=S meet Kernel(T2c*T3c-T1^30);
    S:=S meet Kernel(T1^125-T1);
  end if;
  printf "DIM_AFTER_%o=%o\n",l,Dimension(S);
end for;
printf "FINAL_DIM=%o\n",Dimension(S);
'''


def parse_pair(raw: str) -> tuple[int, int]:
    try:
        pair = tuple(int(value) for value in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("pair must be e3,e7") from exc
    if len(pair) != 2 or pair not in LEVEL_PAIRS:
        raise argparse.ArgumentTypeError(f"unsupported pair {raw}")
    return pair


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split-data", type=pathlib.Path, required=True)
    parser.add_argument("--inert-data", type=pathlib.Path, required=True)
    parser.add_argument("--pair", type=parse_pair, required=True)
    args = parser.parse_args()
    split = json.loads(args.split_data.read_text())
    inert = json.loads(args.inert_data.read_text())
    rows = rows_from(inert, INERT_PRIMES)
    rows.update(rows_from(split, SPLIT_PRIMES))
    e3, e7 = args.pair
    code = magma_code(e3, e7, rows)
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "combined odd mod-5 residual HGM and semilinear Hecke sieve",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "inert_primes": INERT_PRIMES,
        "split_primes": SPLIT_PRIMES,
        "split_local_sha256": split.get("certificate_sha256"),
        "inert_local_sha256": inert.get("certificate_sha256"),
        "input_bytes": len(code.encode()),
        "soundness": "final dimension zero eliminates every norm-8 semilinear residual eigensystem; positive dimension is only necessary",
    }
    try:
        output = submit(code)
        body.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "norm8_dimension": parse_int(output, "NORM8_DIM"),
                "dimensions_after_primes": {
                    str(prime): parse_int(output, f"DIM_AFTER_{prime}")
                    for prime in PRIMES
                },
                "final_dimension": parse_int(output, "FINAL_DIM"),
                "output_tail": output[-2200:],
            }
        )
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
