#!/usr/bin/env python3
"""Filter signature-(3,5,7) Hilbert spaces directly in the residual Hecke module.

This fail-closed producer avoids characteristic-zero newform decomposition. It
reduces commuting Hecke operators modulo 5 and intersects kernels of the local
candidate-polynomial products. A zero final kernel eliminates every residual
Hecke eigensystem at the requested level, conditional on the imported local
trace-polynomial and level-lowering theorems. A nonzero kernel is only a
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
LEVEL_PAIRS = [(2, 1), (1, 3), (3, 0), (2, 2), (3, 1), (2, 3), (3, 2)]
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def form_metadata(page: str) -> tuple[str, dict[str, str]]:
    form = re.search(r"<form\b([^>]*)>(.*?)</form>", page, flags=re.I | re.S)
    if form is None:
        raise ResearchError("calculator page contains no form")
    attributes, body = form.groups()
    action_match = re.search(r"\baction=[\"']([^\"']*)", attributes, flags=re.I)
    action = (
        CALCULATOR_URL
        if action_match is None
        else urllib.parse.urljoin(
            CALCULATOR_URL, html.unescape(action_match.group(1))
        )
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
    if len(code.encode("utf-8")) > MAX_INPUT:
        raise ResearchError(f"generated input has {len(code.encode())} bytes")
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    request = urllib.request.Request(
        CALCULATOR_URL, headers={"User-Agent": USER_AGENT}
    )
    with opener.open(request, timeout=120) as response:
        landing = response.read().decode("utf-8", errors="replace")
        landing_url = response.geturl()
    action, hidden = form_metadata(landing)
    hidden["input"] = code
    parsed = urllib.parse.urlparse(action)
    request = urllib.request.Request(
        action,
        data=urllib.parse.urlencode(hidden).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": landing_url,
            "Origin": f"{parsed.scheme}://{parsed.netloc}",
        },
    )
    with opener.open(request, timeout=210) as response:
        page = response.read().decode("utf-8", errors="replace")
    return html.unescape(re.sub(r"<[^>]+>", "", page))


def magma_list(polynomials: list[str]) -> str:
    return "[" + ",".join(polynomials) + "]"


def candidate_rows(
    local: dict[str, Any],
) -> list[tuple[int, list[str], list[str], list[str], int, int]]:
    result = []
    for prime in local["primes"]:
        metadata = local["residue_metadata"][str(prime)]
        kinds: dict[str, list[str]] = {}
        for kind in ("generic", "zero", "infinity"):
            kinds[kind] = [
                row["trace_polynomial"]
                for row in local[f"{kind}_rows"]
                if row["prime"] == prime
            ]
        result.append(
            (
                prime,
                kinds["generic"],
                kinds["zero"],
                kinds["infinity"],
                metadata["residue_degree_K7"],
                metadata["residue_degree_F21"],
            )
        )
    return result


PREFIX = r'''
_<x> := PolynomialRing(Rationals());
K<w> := NumberField(x^3-x^2-2*x+1); OK := Integers(K);
I3 := Factorisation(3*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
I2 := Factorisation(2*OK)[1][1];
F5 := GF(5);
EvalMatrix := function(Q,T)
  n:=Nrows(T); A:=ZeroMatrix(F5,n,n); P:=IdentityMatrix(F5,n);
  for j in [0..Degree(Q)] do
    A +:= F5!Coefficient(Q,j)*P;
    P:=P*T;
  end for;
  return A;
end function;
RegimeMatrix := function(T,row,index)
  l:=row[1]; fK:=row[5]; fF:=row[6]; n:=Nrows(T);
  Id:=IdentityMatrix(F5,n); U:=T;
  if fF/fK eq 2 then U:=T*T-F5!(2*l^fK)*Id; end if;
  L:=index eq 1 select row[2] else (index eq 2 select row[3] else row[4]);
  A:=Id;
  for Q in L do A:=A*EvalMatrix(Q,U); end for;
  return A;
end function;
MultiplicityMatrix := function(T,q)
  n:=Nrows(T); Id:=IdentityMatrix(F5,n);
  return (T-F5!(q+1)*Id)*(T+F5!(q+1)*Id);
end function;
LocalUnionMatrix := function(T,row,mask)
  n:=Nrows(T); A:=IdentityMatrix(F5,n);
  if mask[1] then A:=A*RegimeMatrix(T,row,1); end if;
  if mask[2] then A:=A*RegimeMatrix(T,row,2); end if;
  if mask[3] then A:=A*RegimeMatrix(T,row,3); end if;
  if mask[4] then
    q:=Integers()!Norm(Factorisation(row[1]*OK)[1][1]);
    A:=A*MultiplicityMatrix(T,q);
  end if;
  return A;
end function;
'''


def make_code(e3: int, e7: int, rows: list[tuple[Any, ...]]) -> str:
    encoded = [
        f"<{prime},{magma_list(generic)},{magma_list(zero)},"
        f"{magma_list(infinity)},{degree_k},{degree_f}>"
        for prime, generic, zero, infinity, degree_k, degree_f in rows
    ]
    data = "Rows:=[" + ",".join(encoded) + "];\n"
    suffix = rf'''
M0:=HilbertCuspForms(K,I3^{e3}*I7^{e7});
M:=NewSubspace(M0); SetRationalBasis(M);
printf "LEVEL_PAIR=[{e3},{e7}]\n";
printf "LEVEL_NORM=%o\n",27^{e3}*7^{e7};
printf "NEW_DIM=%o\n",Dimension(M);
T2:=Matrix(F5,HeckeOperator(M,I2));
V:=VectorSpace(F5,Dimension(M));
S8:=V meet Kernel(T2);
printf "NORM8_DIM=%o\n",Dimension(S8);
S:=S8; MarginalDims:=[];
for row in Rows do
  I:=Factorisation(row[1]*OK)[1][1];
  T:=Matrix(F5,HeckeOperator(M,I));
  A:=LocalUnionMatrix(T,row,[true,true,true,true]);
  S:=S meet Kernel(A);
  Append(~MarginalDims,<row[1],Dimension(S)>);
end for;
printf "MARGINAL_DIMS=%o\n",MarginalDims;
printf "MARGINAL_FINAL_DIM=%o\n",Dimension(S);
E:=S8; EvenDims:=[];
for row in Rows do
  l:=row[1];
  mask:=l eq 13 select [false,true,true,false]
    else (l eq 29 select [true,true,false,false]
    else (l eq 41 select [true,true,true,false]
    else [true,true,true,true]));
  I:=Factorisation(l*OK)[1][1];
  T:=Matrix(F5,HeckeOperator(M,I));
  A:=LocalUnionMatrix(T,row,mask);
  E:=E meet Kernel(A);
  Append(~EvenDims,<l,Dimension(E)>);
end for;
printf "EVEN_DIMS=%o\n",EvenDims;
printf "EVEN_FINAL_DIM=%o\n",Dimension(E);
'''
    return PREFIX + data + suffix


def parse_int(text: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", text)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def parse_pairs(text: str, marker: str) -> list[list[int]]:
    match = re.search(rf"{marker}=\[\s*([^\]]*)\]", text)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return [
        [int(left), int(right)]
        for left, right in re.findall(r"<\s*(\d+)\s*,\s*(\d+)\s*>", match.group(1))
    ]


def parse_pair(raw: str) -> tuple[int, int]:
    try:
        pair = tuple(int(value) for value in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("pair must be e3,e7") from exc
    if len(pair) != 2 or pair not in LEVEL_PAIRS:
        raise argparse.ArgumentTypeError(f"unsupported pair {raw}")
    return pair


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-data", type=pathlib.Path, required=True)
    parser.add_argument("--pair", type=parse_pair)
    args = parser.parse_args()
    local = json.loads(args.local_data.read_text(encoding="utf-8"))
    rows = candidate_rows(local)
    pairs = [args.pair] if args.pair else LEVEL_PAIRS
    outputs: list[dict[str, Any]] = []
    for e3, e7 in pairs:
        code = make_code(e3, e7, rows)
        record: dict[str, Any] = {
            "level_exponents": [e3, e7],
            "level_norm": 27**e3 * 7**e7,
            "input_bytes": len(code.encode("utf-8")),
            "branch_scope": (
                "even-only"
                if e3 == 1 or e7 == 3
                else ("odd-only" if e3 == 3 else "both")
            ),
        }
        try:
            text = submit(code)
            record.update(
                {
                    "status": "completed",
                    "new_dimension": parse_int(text, "NEW_DIM"),
                    "norm8_dimension": parse_int(text, "NORM8_DIM"),
                    "marginal_dimensions": parse_pairs(text, "MARGINAL_DIMS"),
                    "marginal_final_dimension": parse_int(
                        text, "MARGINAL_FINAL_DIM"
                    ),
                    "even_dimensions": parse_pairs(text, "EVEN_DIMS"),
                    "even_final_dimension": parse_int(text, "EVEN_FINAL_DIM"),
                    "output_tail": text[-1600:],
                }
            )
        except Exception as exc:
            record.update(
                {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
            )
            if "text" in locals():
                record["output_tail"] = text[-2000:]
        outputs.append(record)
    body = {
        "schema_version": 1,
        "status": "public-Magma residual Hecke-module kernel filter",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "source_local_data_sha256": local["certificate_sha256"],
        "levels": outputs,
        "soundness": (
            "zero kernel is a finite elimination conditional on the imported "
            "local trace-polynomial theorem; nonzero kernel is only necessary"
        ),
        "nonclaim": (
            "this producer does not identify characteristic-zero packets and "
            "does not interpret failed levels as empty"
        ),
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_sha256(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
