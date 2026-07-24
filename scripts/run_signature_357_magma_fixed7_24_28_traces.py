#!/usr/bin/env python3
"""Read the decisive Hecke data of fixed-7 packets 24 and 28.

The odd e3=2 block has already been reduced to packets 24 and 28 at Hilbert
level (2,3).  The corrected reciprocal-coordinate two-Frey analysis only needs
four auxiliary primes.  This public-Magma producer records both the base-field
Hecke polynomial and the polynomial after the degree-two F15/K5 Frobenius
transformation used at the zero/infinity specializations.

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
    printf "TRACE|%o|%o|%o|%o|%o|%o\n",index,l,fK,fF,Pbase,Pfull;
  end for;
end for;
'''


def main() -> int:
    code = make_code()
    body: dict[str, Any] = {
        "schema_version": 1,
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
    try:
        output = submit(code)
        count_match = re.search(r"PACKET_COUNT=(\d+)", output)
        if count_match is None or int(count_match.group(1)) != 35:
            raise ResearchError("unexpected packet count")
        pattern = re.compile(
            r"TRACE\|(24|28)\|(13|29|41|43)\|(\d+)\|(\d+)\|([^|\n]+)\|([^|\n]+)"
        )
        rows = []
        for match in pattern.finditer(output):
            packet, prime, degree_k, degree_f = map(int, match.groups()[:4])
            rows.append(
                {
                    "packet": packet,
                    "prime": prime,
                    "residue_degree_K5": degree_k,
                    "residue_degree_F15": degree_f,
                    "base_trace_polynomial": match.group(5).strip(),
                    "full_trace_polynomial": match.group(6).strip(),
                }
            )
        if len(rows) != len(PACKETS) * len(PRIMES):
            raise ResearchError(f"expected 8 trace rows, got {len(rows)}")
        body.update(
            {
                "request_status": "completed",
                "packet_count": 35,
                "rows": rows,
                "output_tail": output[-2400:],
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
    result["certificate_sha256"] = canonical_sha256(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
