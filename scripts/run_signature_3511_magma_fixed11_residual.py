#!/usr/bin/env python3
"""Residual Hecke-module test for the next prime signature (3,5,11).

Rewrite a putative primitive solution as

    B^5 + (-C)^11 + A^3 = 0.

The Pacetti--Villagra genus-two Frey representation over Q(sqrt(5)) lowers,
when its residual representation is absolutely irreducible, to one of the four
levels 3^e3 * p5^e5 with e3,e5 in {2,3}.  This producer avoids a
characteristic-zero newform decomposition: it computes one Hecke operator on
the complete newspace modulo 11 and compares its characteristic polynomial
with the complete generic/zero/infinity/multiplicative local trace union.

A degree-zero gcd eliminates the whole level under the imported modularity,
irreducibility, conductor and level-lowering theorems.  Positive degree is only
a necessary residual survivor.  Request failures remain explicit.
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
EXPECTED_DATA_BLOB = "9c96357834f2298b4d91ab97812c38e84b8ef7a2"
CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"
LEVELS = [(2, 2), (2, 3), (3, 2), (3, 3)]
AUXILIARY_PRIMES = [13, 17, 19, 29, 31, 41, 59, 61, 71]


class ResearchError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


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
        referer = response.geturl()
    action, hidden = metadata(landing)
    hidden["input"] = code
    parsed = urllib.parse.urlparse(action)
    request = urllib.request.Request(
        action,
        data=urllib.parse.urlencode(hidden).encode(),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": referer,
            "Origin": f"{parsed.scheme}://{parsed.netloc}",
        },
    )
    with opener.open(request, timeout=600) as response:
        return html.unescape(re.sub(r"<[^>]+>", "", response.read().decode(errors="replace")))


def magma_code(e3: int, e5: int, row: str) -> str:
    return rf'''
_<x>:=PolynomialRing(Rationals());
K<z>:=NumberField(x^2-5); OK:=Integers(K); SetStoreModularForms(K,false);
I5:=Factorisation(5*OK)[1][1]; F15:=NumberField(CyclotomicPolynomial(15)); OF15:=Integers(F15);
F11:=GF(11); R11<X>:=PolynomialRing(F11); Row:={row};
Red:=function(P) return R11![F11!Coefficient(P,i):i in [0..Degree(P)]]; end function;
UnionPolynomial:=function(row)
  l:=row[1]; I:=Factorisation(l*OK)[1][1];
  fK:=InertiaDegree(I); fF:=InertiaDegree(Factorisation(l*OF15)[1][1]);
  q:=Integers()!Norm(I); U:=X;
  if fF div fK eq 2 then U:=X^2-F11!(2*l^fK); end if;
  P:=R11!1;
  for Q in row[2] do P*:=Red(Q); end for;
  for Q in row[3] do P*:=Evaluate(Red(Q),U); end for;
  for Q in row[4] do P*:=Evaluate(Red(Q),U); end for;
  P*:=(X-F11!(q+1))*(X+F11!(q+1));
  return SquarefreePart(P);
end function;
printf "PHASE=space-start\n";
M0:=HilbertCuspForms(K,3^{e3}*I5^{e5}); M:=NewSubspace(M0); n:=Dimension(M);
printf "LEVEL_EXPONENTS=[{e3},{e5}]\n"; printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); delete M0; ClearStoredModularForms(K); DeleteHeckePrecomputation(O);
Iell:=Factorisation(Row[1]*OK)[1][1]; printf "PHASE=Taux-start\n";
TQ:=HeckeOperator(M,Iell); DeleteHeckePrecomputation(O,Iell); ClearStoredModularForms(K);
T:=Matrix(F11,TQ); delete TQ; printf "PHASE=Taux-mod11-ready\n";
CP:=R11!CharacteristicPolynomial(T); P:=UnionPolynomial(Row); G:=GreatestCommonDivisor(CP,P);
printf "AUXILIARY_PRIME=%o\n",Row[1];
printf "CHARPOLY_DEGREE=%o\n",Degree(CP);
printf "UNION_POLYNOMIAL_DEGREE=%o\n",Degree(P);
printf "GCD_DEGREE=%o\n",Degree(G);
printf "GCD=%o\n",G;
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{re.escape(marker)}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def parse_level(raw: str) -> tuple[int, int]:
    try:
        pair = tuple(int(value) for value in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("level must be e3,e5") from exc
    if len(pair) != 2 or pair not in LEVELS:
        raise argparse.ArgumentTypeError(f"unsupported level {raw}")
    return pair


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=parse_level, required=True)
    parser.add_argument("--prime", type=int, choices=AUXILIARY_PRIMES, required=True)
    args = parser.parse_args()
    e3, e5 = args.level
    row = selected_row(fetch_data(), args.prime)
    source = magma_code(e3, e5, row)
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "signature-(3,5,11) fixed-11 residual whole-newspace test",
        "equation": "A^3+B^5=C^11",
        "orientation": "B^5+(-C)^11+A^3=0",
        "calculator": CALCULATOR_URL,
        "candidate_blob_sha1": EXPECTED_DATA_BLOB,
        "residual_characteristic": 11,
        "level_exponents": [e3, e5],
        "level_norm": 3**(2*e3) * 5**e5,
        "auxiliary_prime": args.prime,
        "input_bytes": len(source.encode()),
        "soundness": (
            "gcd degree zero eliminates the complete residual newspace at this level, "
            "conditional on the imported modularity, absolute irreducibility, conductor and "
            "level-lowering theorems; positive degree is only a necessary survivor"
        ),
        "nonclaim": (
            "reducible residual representations and any failure of the imported level theorem "
            "remain outside this computation"
        ),
    }
    output = ""
    try:
        output = submit(source)
        body.update({
            "request_status": "completed",
            "new_dimension": parse_int(output, "NEW_DIM"),
            "charpoly_degree": parse_int(output, "CHARPOLY_DEGREE"),
            "union_polynomial_degree": parse_int(output, "UNION_POLYNOMIAL_DEGREE"),
            "gcd_degree": parse_int(output, "GCD_DEGREE"),
            "output_tail": output[-7000:],
        })
        if body["charpoly_degree"] != body["new_dimension"]:
            raise ResearchError("characteristic-polynomial degree does not match newspace dimension")
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
