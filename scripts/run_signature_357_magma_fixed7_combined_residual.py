#!/usr/bin/env python3
"""Intersect all fixed-7 level-(3,3) residual conditions in one Hecke module.

A genuine residual eigensystem lies in the superspecial subspace ``ker(T_7)``,
satisfies every local HGM trace polynomial, and obeys the semilinear Galois
relations between conjugate Hecke operators.  The characteristic-zero newform
decomposition is not required.

Parallel-weight-2 Hilbert newspaces already have a permanently fixed rational
basis in Magma.  This producer deliberately does not call ``SetRationalBasis``;
the redundant conversion was the first observed memory bottleneck.  A zero
final intersection eliminates the level conditional on the imported modularity,
level-lowering, local-trace and semilinear-descent theorems.  A nonzero space is
only a necessary survivor.
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

DATA_URL = (
    "https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/"
    "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Outputs/Data.txt"
)
EXPECTED_DATA_BLOB = "9c96357834f2298b4d91ab97812c38e84b8ef7a2"
CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
PRIMES = [13, 43, 11, 29, 41]
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def fetch_data() -> bytes:
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if git_blob_sha1(data) != EXPECTED_DATA_BLOB:
        raise ResearchError("candidate-data blob mismatch")
    return data


def rows_by_prime(data: bytes) -> dict[int, str]:
    text = data.decode().strip()
    if not text.startswith("Data:=[") or not text.endswith("];" ):
        raise ResearchError("unexpected Data.txt wrapper")
    body = text[len("Data:=[") : -2]
    rows: list[str] = []
    depth = 0
    start = 0
    for index, character in enumerate(body):
        if character in "[<":
            depth += 1
        elif character in "]>":
            depth -= 1
        elif character == "," and depth == 0:
            rows.append(body[start:index].strip())
            start = index + 1
    rows.append(body[start:].strip())
    result: dict[int, str] = {}
    for row in rows:
        match = re.match(r"<(\d+),", row)
        if match:
            result[int(match.group(1))] = row
    missing = [prime for prime in PRIMES if prime not in result]
    if missing:
        raise ResearchError(f"candidate rows missing for {missing}")
    return result


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


def magma_code(rows: dict[int, str]) -> str:
    encoded = ",".join(rows[prime] for prime in PRIMES)
    return rf'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
F15 := NumberField(CyclotomicPolynomial(15)); OF15 := Integers(F15);
F7 := GF(7); R7<X> := PolynomialRing(F7);
Rows := [{encoded}];
Red := function(P)
  return R7![F7!Coefficient(P,i) : i in [0..Degree(P)]];
end function;
EvalMatrix := function(P,T)
  n:=Nrows(T); A:=ZeroMatrix(F7,n,n); Q:=IdentityMatrix(F7,n);
  for i in [0..Degree(P)] do
    A +:= F7!Coefficient(P,i)*Q;
    Q := Q*T;
  end for;
  return A;
end function;
UnionMatrix := function(T,row)
  l:=row[1]; n:=Nrows(T); Id:=IdentityMatrix(F7,n);
  I:=Factorisation(l*OK)[1][1]; fK:=InertiaDegree(I);
  fF:=InertiaDegree(Factorisation(l*OF15)[1][1]);
  U:=T;
  if fF/fK eq 2 then U:=T*T-F7!(2*l^fK)*Id; end if;
  A:=Id;
  for P in row[2] do A:=A*EvalMatrix(Red(P),T); end for;
  for P in row[3] do A:=A*EvalMatrix(Red(P),U); end for;
  for P in row[4] do A:=A*EvalMatrix(Red(P),U); end for;
  q:=Integers()!Norm(I);
  A:=A*(T-F7!(q+1)*Id)*(T+F7!(q+1)*Id);
  return A;
end function;
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^3*I5^3);
M:=NewSubspace(M0);
n:=Dimension(M); V:=VectorSpace(F7,n);
printf "NEW_DIM=%o\n",n;
printf "PHASE=T7-start\n";
T7:=Matrix(F7,HeckeOperator(M,I7));
printf "PHASE=T7-ready\n";
S:=V meet Kernel(T7);
printf "SUPERSPECIAL_DIM=%o\n",Dimension(S);
for row in Rows do
  l:=row[1]; fac:=Factorisation(l*OK);
  printf "PHASE=prime-%o-start\n",l;
  T1:=Matrix(F7,HeckeOperator(M,fac[1][1]));
  S:=S meet Kernel(UnionMatrix(T1,row));
  if #fac eq 1 then
    S:=S meet Kernel(T1^7-T1);
  else
    T2:=Matrix(F7,HeckeOperator(M,fac[2][1]));
    S:=S meet Kernel(T2-T1^7);
    S:=S meet Kernel(T1-T2^7);
  end if;
  printf "DIM_AFTER_%o=%o\n",l,Dimension(S);
  if Dimension(S) eq 0 then break; end if;
end for;
printf "FINAL_DIM=%o\n",Dimension(S);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    rows = rows_by_prime(fetch_data())
    code = magma_code(rows)
    if "SetRationalBasis" in code:
        raise ResearchError("generated code unexpectedly contains SetRationalBasis")
    body: dict[str, Any] = {
        "schema_version": 2,
        "status": "combined fixed-7 level-(3,3) residual Hecke and semilinear sieve",
        "calculator": CALCULATOR_URL,
        "candidate_blob_sha1": EXPECTED_DATA_BLOB,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "auxiliary_primes": PRIMES,
        "input_bytes": len(code.encode()),
        "rational_basis_policy": "native parallel-weight-2 newspace basis; no redundant conversion",
        "early_zero_exit": True,
        "soundness": (
            "final dimension zero eliminates every superspecial semilinear "
            "residual eigensystem; positive dimension is only necessary"
        ),
    }
    output = ""
    try:
        output = submit(code)
        dimensions = {
            prime: int(dimension)
            for prime, dimension in re.findall(r"DIM_AFTER_(\d+)=(\d+)", output)
        }
        body.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "superspecial_dimension": parse_int(output, "SUPERSPECIAL_DIM"),
                "dimensions_after_primes": dimensions,
                "final_dimension": parse_int(output, "FINAL_DIM"),
                "output_tail": output[-5000:],
            }
        )
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-8000:],
            }
        )
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
