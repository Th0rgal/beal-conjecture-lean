#!/usr/bin/env python3
"""Check the universal odd-C trace at 2 on fixed-7 packets 24 and 28.

At the unique prime above 2 in Q(sqrt(5)), every odd-C Frey specialization has
trace -1 or -8, hence trace 6 modulo 7.  This packetwise test is independent of
the mod-5 norm-8 packet argument and therefore audits the complete e3=2 closure
across both parity cases.
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
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"
PACKETS = [24, 28]


class ResearchError(RuntimeError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def metadata(page: str) -> tuple[str, dict[str, str]]:
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
        tm = re.search(r"\btype=[\"']([^\"']*)", tag, flags=re.I)
        nm = re.search(r"\bname=[\"']([^\"']*)", tag, flags=re.I)
        vm = re.search(r"\bvalue=[\"']([^\"']*)", tag, flags=re.I)
        if tm and tm.group(1).lower() == "hidden" and nm:
            hidden[html.unescape(nm.group(1))] = (
                "" if vm is None else html.unescape(vm.group(1))
            )
    return action, hidden


def submit(code: str) -> str:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(CALCULATOR_URL, headers={"User-Agent": USER_AGENT}),
        timeout=120,
    ) as response:
        landing = response.read().decode(errors="replace")
        landing_url = response.geturl()
    action, hidden = metadata(landing)
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
    with opener.open(request, timeout=240) as response:
        return html.unescape(re.sub(r"<[^>]+>", "", response.read().decode(errors="replace")))


def code() -> str:
    return r'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1]; I2 := Factorisation(2*OK)[1][1];
F7 := GF(7); R7<X> := PolynomialRing(F7);
M := HilbertCuspForms(K,3^2*I5^3);
D := NewformDecomposition(NewSubspace(M));
printf "PACKET_COUNT=%o\n",#D;
for i in [24,28] do
  f := Eigenform(D[i]); a := HeckeEigenvalue(f,I2); P := MinimalPolynomial(a);
  P7 := R7![F7!Coefficient(P,j) : j in [0..Degree(P)]];
  G := GreatestCommonDivisor(P7,X-6);
  printf "ROW|%o|%o|",i,Degree(P);
  for c in Eltseq(P) do printf "%o,",c; end for;
  printf "|%o\n",Degree(G);
end for;
'''


def main() -> int:
    source = code()
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "fixed-7 packet-24/28 universal odd-C prime-2 trace audit",
        "level_exponents": [2, 3],
        "level_norm": 10125,
        "packets": PACKETS,
        "prime_ideal_norm": 4,
        "required_trace_mod7": 6,
        "rows": [],
        "soundness": "a packet survives only when its Hecke polynomial has 6 as a root modulo 7",
    }
    output = ""
    try:
        output = submit(source)
        count = re.search(r"PACKET_COUNT=(\d+)", output)
        if count is None or int(count.group(1)) != 35:
            raise ResearchError("unexpected packet count")
        rows = []
        for match in re.finditer(r"ROW\|(24|28)\|(\d+)\|([^|\n]*)\|(\d+)", output):
            packet, degree = map(int, match.groups()[:2])
            coefficients = [int(x) for x in match.group(3).split(",") if x]
            if len(coefficients) != degree + 1:
                raise ResearchError("coefficient count mismatch")
            rows.append(
                {
                    "packet": packet,
                    "trace_polynomial_degree": degree,
                    "trace_coefficients_low_to_high": coefficients,
                    "gcd_with_x_minus_6_degree_mod7": int(match.group(4)),
                    "survives": int(match.group(4)) > 0,
                }
            )
        if [row["packet"] for row in rows] != PACKETS:
            raise ResearchError("incomplete packet rows")
        body.update(
            {
                "request_status": "completed",
                "rows": rows,
                "surviving_packets": [row["packet"] for row in rows if row["survives"]],
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
