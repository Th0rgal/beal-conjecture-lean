#!/usr/bin/env python3
"""Test fixed-7 level (3,3) directly in the residual Hecke module.

The characteristic-zero decomposition of the 2025-dimensional Hilbert space
exceeds the public calculator limit.  This producer instead computes the
superspecial subspace `ker(T_7)` modulo 7, restricts one auxiliary Hecke
operator to it, and compares its characteristic polynomial with the union of
all allowed local trace polynomials.

A degree-zero gcd eliminates every residual Hecke eigensystem at this level for
the selected auxiliary prime.  A nonzero gcd is only a necessary survivor and
is never promoted to a packet count.
"""
from __future__ import annotations

import argparse
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
CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
EXPECTED_DATA_BLOB = "9c96357834f2298b4d91ab97812c38e84b8ef7a2"
PRIMES = [11, 13, 17, 19, 29, 31, 41, 59, 61, 71]
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fetch_data() -> bytes:
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if git_blob_sha1(data) != EXPECTED_DATA_BLOB:
        raise ResearchError("candidate-data blob mismatch")
    return data


def selected_row(data: bytes, prime: int) -> str:
    text = data.decode("utf-8").strip()
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
    for row in rows:
        match = re.match(r"<(\d+),", row)
        if match and int(match.group(1)) == prime:
            return row
    raise ResearchError(f"candidate row for {prime} is missing")


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
        raise ResearchError("generated input exceeds calculator limit")
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(CALCULATOR_URL, headers={"User-Agent": USER_AGENT}),
        timeout=120,
    ) as response:
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


def make_code(row: str) -> str:
    return rf'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
F15 := NumberField(CyclotomicPolynomial(15)); OF15 := Integers(F15);
F7 := GF(7); R7<X> := PolynomialRing(F7);
Row := {row};
Red := function(P)
  return R7![F7!Coefficient(P,i) : i in [0..Degree(P)]];
end function;
UnionPolynomial := function(row)
  l := row[1]; I := Factorisation(l*OK)[1][1];
  fK := InertiaDegree(I); fF := InertiaDegree(Factorisation(l*OF15)[1][1]);
  q := Integers()!Norm(I); U := X;
  if fF/fK eq 2 then U := X^2-F7!(2*l^fK); end if;
  P := R7!1;
  for Q in row[2] do P *:= Red(Q); end for;
  for Q in row[3] do P *:= Evaluate(Red(Q),U); end for;
  for Q in row[4] do P *:= Evaluate(Red(Q),U); end for;
  P *:= (X-F7!(q+1))*(X+F7!(q+1));
  return P;
end function;
M0 := HilbertCuspForms(K,3^3*I5^3);
M := NewSubspace(M0); SetRationalBasis(M);
printf "NEW_DIM=%o\n",Dimension(M);
T7 := Matrix(F7,HeckeOperator(M,I7));
S := Kernel(T7); d := Dimension(S);
printf "SUPERSPECIAL_DIM=%o\n",d;
if d eq 0 then
  printf "AUXILIARY_PRIME=%o\n",Row[1];
  printf "UNION_POLYNOMIAL_DEGREE=0\n";
  printf "RESTRICTED_CHARPOLY_DEGREE=0\n";
  printf "GCD_DEGREE=0\n";
else
  I := Factorisation(Row[1]*OK)[1][1];
  T := Matrix(F7,HeckeOperator(M,I));
  TS := Matrix(F7,d,d,&cat[Coordinates(S,S.i*T) : i in [1..d]]);
  P := UnionPolynomial(Row);
  CP := R7!CharacteristicPolynomial(TS);
  G := GreatestCommonDivisor(CP,P);
  printf "AUXILIARY_PRIME=%o\n",Row[1];
  printf "UNION_POLYNOMIAL_DEGREE=%o\n",Degree(P);
  printf "RESTRICTED_CHARPOLY_DEGREE=%o\n",Degree(CP);
  printf "GCD_DEGREE=%o\n",Degree(G);
  printf "GCD=%o\n",G;
end if;
'''


def parse_int(text: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", text)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prime", type=int, choices=PRIMES, required=True)
    args = parser.parse_args()
    row = selected_row(fetch_data(), args.prime)
    code = make_code(row)
    record: dict[str, Any] = {
        "schema_version": 1,
        "status": "fixed-7 level-(3,3) residual Hecke-module test",
        "calculator": CALCULATOR_URL,
        "candidate_blob_sha1": EXPECTED_DATA_BLOB,
        "level_exponents": [3, 3],
        "level_norm": 91125,
        "auxiliary_prime": args.prime,
        "input_bytes": len(code.encode("utf-8")),
        "soundness": (
            "gcd degree zero eliminates every superspecial residual eigensystem; "
            "positive degree is only a necessary survivor"
        ),
    }
    try:
        output = submit(code)
        record.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "superspecial_dimension": parse_int(output, "SUPERSPECIAL_DIM"),
                "union_polynomial_degree": parse_int(
                    output, "UNION_POLYNOMIAL_DEGREE"
                ),
                "restricted_charpoly_degree": parse_int(
                    output, "RESTRICTED_CHARPOLY_DEGREE"
                ),
                "gcd_degree": parse_int(output, "GCD_DEGREE"),
                "output_tail": output[-1600:],
            }
        )
    except Exception as exc:
        record.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
    body = dict(record)
    result = dict(body)
    result["certificate_sha256"] = canonical_sha256(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
