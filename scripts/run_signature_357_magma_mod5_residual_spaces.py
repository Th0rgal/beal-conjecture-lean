#!/usr/bin/env python3
"""Test a mod-5 Hilbert level in the residual Hecke module.

The characteristic-zero packet decomposition is unnecessary for a fail-closed
elimination. The script computes the norm-8 subspace ``ker(T_2)`` modulo 5,
restricts one auxiliary Hecke operator to it, and takes a gcd between its
characteristic polynomial and the polynomial encoding the union of generic,
zero, infinity and multiplicative local HGM traces.

A degree-zero gcd eliminates every residual Hecke eigensystem at that level for
the selected auxiliary prime. A positive degree is only a necessary survivor.
Failed Magma requests retain the raw output tail so implementation errors cannot
masquerade as unresolved arithmetic.
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
LEVEL_PAIRS = [(3, 0), (2, 2), (3, 1), (3, 2)]
PRIMES = [13, 29, 41, 43]
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


def candidate_row(local: dict[str, Any], prime: int) -> tuple[Any, ...]:
    if prime not in local["primes"]:
        raise ResearchError(f"local producer does not contain prime {prime}")
    metadata = local["residue_metadata"][str(prime)]
    kinds: dict[str, list[str]] = {}
    for kind in ("generic", "zero", "infinity"):
        kinds[kind] = [
            row["trace_polynomial"]
            for row in local[f"{kind}_rows"]
            if row["prime"] == prime
        ]
    return (
        prime,
        kinds["generic"],
        kinds["zero"],
        kinds["infinity"],
        metadata["residue_degree_K7"],
        metadata["residue_degree_F21"],
    )


def make_code(e3: int, e7: int, row: tuple[Any, ...]) -> str:
    prime, generic, zero, infinity, degree_k, degree_f = row
    encoded = (
        f"<{prime},{magma_list(generic)},{magma_list(zero)},"
        f"{magma_list(infinity)},{degree_k},{degree_f}>"
    )
    return rf'''
_<x> := PolynomialRing(Rationals());
K<w> := NumberField(x^3-x^2-2*x+1); OK := Integers(K);
I3 := Factorisation(3*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
I2 := Factorisation(2*OK)[1][1];
F5 := GF(5); R5<X> := PolynomialRing(F5);
Row := {encoded};
Red := function(P)
  return R5![F5!Coefficient(P,i) : i in [0..Degree(P)]];
end function;
UnionPolynomial := function(row)
  l := row[1]; I := Factorisation(l*OK)[1][1];
  q := Integers()!Norm(I); U := X;
  if row[6]/row[5] eq 2 then U := X^2-F5!(2*l^row[5]); end if;
  P := R5!1;
  for Q in row[2] do P *:= Red(Q); end for;
  for Q in row[3] do P *:= Evaluate(Red(Q),U); end for;
  for Q in row[4] do P *:= Evaluate(Red(Q),U); end for;
  P *:= (X-F5!(q+1))*(X+F5!(q+1));
  return P;
end function;
printf "PHASE=space-start\n";
M0 := HilbertCuspForms(K,I3^{e3}*I7^{e7});
printf "AMBIENT_DIM=%o\n",Dimension(M0);
M := NewSubspace(M0);
printf "NEW_DIM_PREBASIS=%o\n",Dimension(M);
SetRationalBasis(M);
printf "PHASE=rational-basis-ready\n";
printf "LEVEL_PAIR=[{e3},{e7}]\n";
printf "LEVEL_NORM=%o\n",27^{e3}*7^{e7};
printf "NEW_DIM=%o\n",Dimension(M);
T2Q := HeckeOperator(M,I2);
printf "PHASE=T2-rational-ready\n";
T2 := Matrix(F5,T2Q);
printf "PHASE=T2-mod5-ready\n";
S := Kernel(T2); d := Dimension(S);
printf "NORM8_DIM=%o\n",d;
if d eq 0 then
  printf "AUXILIARY_PRIME=%o\n",Row[1];
  printf "UNION_POLYNOMIAL_DEGREE=0\n";
  printf "RESTRICTED_CHARPOLY_DEGREE=0\n";
  printf "GCD_DEGREE=0\n";
else
  I := Factorisation(Row[1]*OK)[1][1];
  TQ := HeckeOperator(M,I);
  printf "PHASE=Taux-rational-ready\n";
  T := Matrix(F5,TQ);
  printf "PHASE=Taux-mod5-ready\n";
  TS := Matrix(F5,d,d,&cat[Coordinates(S,S.i*T) : i in [1..d]]);
  P := UnionPolynomial(Row);
  CP := R5!CharacteristicPolynomial(TS);
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
    parser.add_argument("--pair", type=parse_pair, required=True)
    parser.add_argument("--prime", type=int, choices=PRIMES, required=True)
    args = parser.parse_args()
    local = json.loads(args.local_data.read_text(encoding="utf-8"))
    e3, e7 = args.pair
    code = make_code(e3, e7, candidate_row(local, args.prime))
    record: dict[str, Any] = {
        "schema_version": 3,
        "status": "public-Magma residual Hecke-module characteristic-polynomial test",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "source_local_data_sha256": local["certificate_sha256"],
        "level_exponents": [e3, e7],
        "level_norm": 27**e3 * 7**e7,
        "auxiliary_prime": args.prime,
        "input_bytes": len(code.encode("utf-8")),
        "soundness": (
            "gcd degree zero eliminates every norm-8 residual eigensystem; "
            "positive degree is only a necessary survivor"
        ),
    }
    output = ""
    try:
        output = submit(code)
        record.update(
            {
                "request_status": "completed",
                "new_dimension": parse_int(output, "NEW_DIM"),
                "norm8_dimension": parse_int(output, "NORM8_DIM"),
                "union_polynomial_degree": parse_int(
                    output, "UNION_POLYNOMIAL_DEGREE"
                ),
                "restricted_charpoly_degree": parse_int(
                    output, "RESTRICTED_CHARPOLY_DEGREE"
                ),
                "gcd_degree": parse_int(output, "GCD_DEGREE"),
                "output_tail": output[-4000:],
            }
        )
    except Exception as exc:
        record.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-8000:],
            }
        )
    body = dict(record)
    result = dict(body)
    result["certificate_sha256"] = canonical_sha256(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
