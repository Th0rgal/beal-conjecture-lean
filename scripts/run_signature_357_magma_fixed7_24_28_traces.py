#!/usr/bin/env python3
"""Read decisive Hecke data for fixed-7 packets 24 and 28.

The odd e3=2 block has already been reduced to packets 24 and 28 at Hilbert
level (2,3). The corrected reciprocal-coordinate two-Frey analysis needs a
small set of auxiliary-prime traces. This public-Magma producer emits minimal
polynomial coefficients through explicit one-line records, avoiding Magma's
pretty-printer line wrapping.

Failed requests remain explicit and are never interpreted as elimination.
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


def make_code() -> str:
    return r'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
F15 := NumberField(CyclotomicPolynomial(15)); OF15 := Integers(F15);
M := HilbertCuspForms(K,3^2*I5^3);
decomp := NewformDecomposition(NewSubspace(M));
printf "PACKET_COUNT=%o\n",#decomp;
for index in [24,28] do
  form := Eigenform(decomp[index]);
  for l in [13,29,41,43] do
    I := Factorisation(l*OK)[1][1];
    Eig := HeckeEigenvalue(form,I);
    Pbase := MinimalPolynomial(Eig);
    fK := InertiaDegree(I);
    fF := InertiaDegree(Factorisation(l*OF15)[1][1]);
    Efull := Eig;
    if fF/fK eq 2 then Efull := Eig^2-2*l^fK; end if;
    Pfull := MinimalPolynomial(Efull);
    printf "TRACE_START|%o|%o|%o|%o|%o|%o\n",index,l,fK,fF,Degree(Pbase),Degree(Pfull);
    printf "BASE_COEFFS";
    for c in Eltseq(Pbase) do printf "|%o",c; end for;
    printf "\nFULL_COEFFS";
    for c in Eltseq(Pfull) do printf "|%o",c; end for;
    printf "\nTRACE_END\n";
  end for;
end for;
'''


def parse_coefficients(line: str, marker: str, degree: int) -> list[int]:
    prefix = marker + "|"
    if not line.startswith(prefix):
        raise ResearchError(f"expected {marker} line")
    values = [int(value.strip()) for value in line[len(prefix) :].split("|")]
    if len(values) != degree + 1:
        raise ResearchError(
            f"{marker} expected {degree + 1} coefficients, got {len(values)}"
        )
    return values


def polynomial_string(coefficients: list[int]) -> str:
    terms: list[str] = []
    for degree, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        if degree == 0:
            monomial = str(abs(coefficient))
        elif degree == 1:
            monomial = "x" if abs(coefficient) == 1 else f"{abs(coefficient)}*x"
        else:
            monomial = (
                f"x^{degree}"
                if abs(coefficient) == 1
                else f"{abs(coefficient)}*x^{degree}"
            )
        if not terms:
            terms.append(("-" if coefficient < 0 else "") + monomial)
        else:
            terms.append((" - " if coefficient < 0 else " + ") + monomial)
    return "".join(terms) if terms else "0"


def parse_rows(output: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    rows: list[dict[str, Any]] = []
    index = 0
    header = re.compile(r"TRACE_START\|(24|28)\|(13|29|41|43)\|(\d+)\|(\d+)\|(\d+)\|(\d+)$")
    while index < len(lines):
        match = header.fullmatch(lines[index])
        if match is None:
            index += 1
            continue
        if index + 3 >= len(lines):
            raise ResearchError("truncated trace record")
        packet, prime, degree_k, degree_f, base_degree, full_degree = map(
            int, match.groups()
        )
        base_coefficients = parse_coefficients(
            lines[index + 1], "BASE_COEFFS", base_degree
        )
        full_coefficients = parse_coefficients(
            lines[index + 2], "FULL_COEFFS", full_degree
        )
        if lines[index + 3] != "TRACE_END":
            raise ResearchError("trace record lacks TRACE_END")
        rows.append(
            {
                "packet": packet,
                "prime": prime,
                "residue_degree_K5": degree_k,
                "residue_degree_F15": degree_f,
                "base_trace_coefficients_low_to_high": base_coefficients,
                "full_trace_coefficients_low_to_high": full_coefficients,
                "base_trace_polynomial": polynomial_string(base_coefficients),
                "full_trace_polynomial": polynomial_string(full_coefficients),
            }
        )
        index += 4
    return rows


def main() -> int:
    code = make_code()
    body: dict[str, Any] = {
        "schema_version": 2,
        "status": "public-Magma decisive fixed-7 packet trace read",
        "calculator": CALCULATOR_URL,
        "level_exponents": [2, 3],
        "level_norm": 10125,
        "packets": PACKETS,
        "primes": PRIMES,
        "input_bytes": len(code.encode("utf-8")),
        "rows": [],
        "nonclaim": "failed output leaves both packets unresolved",
    }
    output = ""
    try:
        output = submit(code)
        count_match = re.search(r"PACKET_COUNT=(\d+)", output)
        if count_match is None or int(count_match.group(1)) != 35:
            raise ResearchError("unexpected packet count")
        rows = parse_rows(output)
        if len(rows) != len(PACKETS) * len(PRIMES):
            raise ResearchError(f"expected 8 trace rows, got {len(rows)}")
        expected_pairs = {(packet, prime) for packet in PACKETS for prime in PRIMES}
        if {(row["packet"], row["prime"]) for row in rows} != expected_pairs:
            raise ResearchError("trace packet/prime coverage mismatch")
        body.update(
            {
                "request_status": "completed",
                "packet_count": 35,
                "rows": rows,
                "output_tail": output[-3200:],
            }
        )
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-4000:],
            }
        )
    result = dict(body)
    result["certificate_sha256"] = canonical_sha256(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
