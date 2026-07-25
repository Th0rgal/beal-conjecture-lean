#!/usr/bin/env python3
"""Expose the rational packet surviving the marginal level-5103 filter.

This small public-Magma producer reconstructs the complete level p3^2*p7 space,
checks its packet inventory, selects packet 1 (the unique norm-8/marginal
survivor from the pinned enumeration), and emits its Hecke traces at the five
primes forced into C by the fixed-7 reducibility sieve.

It is an external research producer.  A separate standard-library checker is
responsible for the finite-field and Jacobi-sum comparison at 71.
"""
from __future__ import annotations

import hashlib
import html
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
PRIMES = [19, 71, 79, 89, 131]
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
    action = CALCULATOR_URL if action_match is None else urllib.parse.urljoin(
        CALCULATOR_URL, html.unescape(action_match.group(1))
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


def magma_code() -> str:
    primes = ",".join(map(str, PRIMES))
    return rf'''
_<x> := PolynomialRing(Rationals());
K<w> := NumberField(x^3-x^2-2*x+1); OK := Integers(K);
I3 := Factorisation(3*OK)[1][1]; I7 := Factorisation(7*OK)[1][1];
M := HilbertCuspForms(K,I3^2*I7); D := NewformDecomposition(NewSubspace(M));
if #D ne 10 then error "unexpected packet count"; end if;
Dims := [Dimension(D[i]) : i in [1..#D]];
if Dims ne [1,2,3,3,6,6,6,6,6,12] then error "unexpected packet dimensions"; end if;
f := Eigenform(D[1]);
printf "PACKET_COUNT=%o\n",#D;
printf "PACKET_DIMS=%o\n",Dims;
for l in [{primes}] do
  I := Factorisation(l*OK)[1][1];
  a := HeckeEigenvalue(f,I);
  printf "TRACE|%o|%o|%o|%o\n",l,InertiaDegree(I),a,MinimalPolynomial(a);
end for;
'''


def parse_list(text: str, marker: str) -> list[int]:
    match = re.search(rf"{marker}=\[\s*([^\]]*)\]", text)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    body = match.group(1).strip()
    return [] if not body else [int(value.strip()) for value in body.split(",")]


def main() -> int:
    text = submit(magma_code())
    count_match = re.search(r"PACKET_COUNT=(\d+)", text)
    if count_match is None:
        raise ResearchError("output lacked packet count")
    rows = []
    pattern = re.compile(r"^TRACE\|(\d+)\|(\d+)\|([^|]+)\|(.+)$")
    for raw in text.splitlines():
        match = pattern.match(raw.strip())
        if match:
            prime, degree, trace, polynomial = match.groups()
            rows.append(
                {
                    "prime": int(prime),
                    "residue_degree_K7": int(degree),
                    "hecke_trace": trace.replace(" ", ""),
                    "minimal_polynomial": polynomial.replace(" ", ""),
                }
            )
    if [row["prime"] for row in rows] != PRIMES:
        raise ResearchError(f"incomplete trace output: {rows}")
    body = {
        "schema_version": 1,
        "status": "public-Magma trace output for the final even-branch level-5103 packet",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [2, 1],
        "level_norm": 5103,
        "packet_index": 1,
        "packet_count": int(count_match.group(1)),
        "packet_dimensions": parse_list(text, "PACKET_DIMS"),
        "forced_c_primes": PRIMES,
        "traces": rows,
        "output_tail": text[-1800:],
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_sha256(body)
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
