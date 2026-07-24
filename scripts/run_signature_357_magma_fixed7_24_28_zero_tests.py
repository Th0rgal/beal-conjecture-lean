#!/usr/bin/env python3
"""Read the decisive mod-7 zero-trace predicates for packets 24 and 28.

Semilinear descent and the coupled mod-5 calculation force the fixed-7 base
Hecke trace to be zero modulo 7 at the inert rational primes 13 and 43.  The
public calculator previously constructed explicit algebraic eigenvalue fields;
that exceeded the memory limit at 43.  This producer instead takes the
characteristic polynomial of the Hecke operator on each already isolated
Hecke-irreducible packet.  A zero root modulo 7 is exactly the necessary packet
spectrum condition, without constructing an eigenvalue field.

The request prints coefficient lists and boolean zero-root tests only.  A failed
request is explicit and is never interpreted as an elimination.
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
PACKETS = [24, 28]
PRIMES = [13, 43]
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
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
        raise ResearchError("generated Magma input is too large")
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


def magma_code() -> str:
    return r'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
F7 := GF(7); R7<X> := PolynomialRing(F7);
M := HilbertCuspForms(K,3^2*I5^3);
decomp := NewformDecomposition(NewSubspace(M));
printf "PACKET_COUNT=%o\n",#decomp;
for index in [24,28] do
  packet := decomp[index];
  printf "PACKET_DIM|%o|%o\n",index,Dimension(packet);
  for ell in [13,43] do
    I := Factorisation(ell*OK)[1][1];
    P := CharacteristicPolynomial(HeckeOperator(packet,I));
    P7 := R7![F7!Coefficient(P,j) : j in [0..Degree(P)]];
    G := GreatestCommonDivisor(P7,X);
    printf "ZERO_TEST|%o|%o|%o|",index,ell,Degree(P);
    for c in Eltseq(P) do printf "%o,",c; end for;
    printf "|%o\n",Degree(G);
  end for;
end for;
'''


def main() -> int:
    code = magma_code()
    body: dict[str, Any] = {
        "schema_version": 2,
        "status": "public-Magma decisive fixed-7 packet-matrix zero-trace tests",
        "calculator": CALCULATOR_URL,
        "level_exponents": [2, 3],
        "level_norm": 10125,
        "packets": PACKETS,
        "primes": PRIMES,
        "required_condition": (
            "each surviving packet must have base trace 0 modulo 7 at both "
            "inert primes"
        ),
        "trace_polynomial_kind": (
            "characteristic polynomial of the Hecke operator on the "
            "Hecke-irreducible packet"
        ),
        "input_bytes": len(code.encode()),
        "rows": [],
    }
    output = ""
    try:
        output = submit(code)
        count = re.search(r"PACKET_COUNT=(\d+)", output)
        if count is None or int(count.group(1)) != 35:
            raise ResearchError("unexpected packet count")
        packet_dimensions = {
            packet: dimension
            for packet, dimension in re.findall(r"PACKET_DIM\|(24|28)\|(\d+)", output)
        }
        pattern = re.compile(r"ZERO_TEST\|(24|28)\|(13|43)\|(\d+)\|([^|\n]*)\|(\d+)")
        rows = []
        for match in pattern.finditer(output):
            packet, prime, degree = map(int, match.groups()[:3])
            coefficients = [int(value) for value in match.group(4).split(",") if value]
            gcd_degree = int(match.group(5))
            if len(coefficients) != degree + 1:
                raise ResearchError("coefficient count mismatch")
            rows.append(
                {
                    "packet": packet,
                    "packet_dimension": int(packet_dimensions[str(packet)]),
                    "prime": prime,
                    "trace_polynomial_degree": degree,
                    "trace_coefficients_low_to_high": coefficients,
                    "zero_root_mod7": gcd_degree == 1,
                }
            )
        if len(rows) != 4:
            raise ResearchError(f"expected four rows, got {len(rows)}")
        body.update(
            {
                "request_status": "completed",
                "packet_count": 35,
                "rows": rows,
                "packet_survives_both_zero_tests": {
                    str(packet): all(
                        row["zero_root_mod7"]
                        for row in rows
                        if row["packet"] == packet
                    )
                    for packet in PACKETS
                },
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
