#!/usr/bin/env python3
"""Filter the exact fixed-7 level-(3,2) survivor list by superspeciality."""
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
SURVIVORS = [21, 22, 26, 33, 61, 65, 78, 92, 98]
NON_CM_SURVIVORS = [21, 22, 26, 33, 61, 92, 98]
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


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
    if len(code.encode()) > MAX_INPUT:
        raise ResearchError("generated input exceeds calculator limit")
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
    return rf'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5); OK := Integers(K);
I5 := Factorisation(5*OK)[1][1]; I7 := Factorisation(7*OK)[1][1];
F7 := GF(7); R7<X> := PolynomialRing(F7);
Red := function(P) return R7![F7!Coefficient(P,i) : i in [0..Degree(P)]]; end function;
M := HilbertCuspForms(K,3^3*I5^2);
D := NewformDecomposition(NewSubspace(M));
if #D ne 111 then error "unexpected packet count"; end if;
S := []; SnonCM := [];
for i in {SURVIVORS} do
  P := MinimalPolynomial(HeckeEigenvalue(Eigenform(D[i]),I7));
  if Degree(GreatestCommonDivisor(Red(P),X)) gt 0 then Append(~S,i); end if;
end for;
for i in {NON_CM_SURVIVORS} do
  P := MinimalPolynomial(HeckeEigenvalue(Eigenform(D[i]),I7));
  if Degree(GreatestCommonDivisor(Red(P),X)) gt 0 then Append(~SnonCM,i); end if;
end for;
printf "SPACE_DIMENSION=%o\n",Dimension(M);
printf "PACKET_COUNT=%o\n",#D;
printf "FIXED7_INPUT=%o\n",{SURVIVORS};
printf "SUPERSPECIAL_SURVIVORS=%o\n",S;
printf "NONCM_SUPERSPECIAL_SURVIVORS=%o\n",SnonCM;
'''


def parse_list(text: str, marker: str) -> list[int]:
    match = re.search(rf"{marker}=\[\s*([^\]]*)\]", text)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    body = match.group(1).strip()
    return [] if not body else [int(value.strip()) for value in body.split(",")]


def parse_int(text: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", text)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    code = magma_code()
    record: dict[str, Any] = {
        "schema_version": 1,
        "status": "public-Magma fixed-7 level-(3,2) superspecial filter",
        "calculator": CALCULATOR_URL,
        "level_exponents": [3, 2],
        "level_norm": 18225,
        "fixed7_survivors_input": SURVIVORS,
        "non_cm_survivors_input": NON_CM_SURVIVORS,
        "input_bytes": len(code.encode()),
        "soundness": "a packet can represent the odd branch only if its Hecke polynomial at the prime above 7 has zero as a residual root",
    }
    try:
        output = submit(code)
        record.update(
            {
                "request_status": "completed",
                "space_dimension": parse_int(output, "SPACE_DIMENSION"),
                "packet_count": parse_int(output, "PACKET_COUNT"),
                "superspecial_survivors": parse_list(output, "SUPERSPECIAL_SURVIVORS"),
                "non_cm_superspecial_survivors": parse_list(
                    output, "NONCM_SUPERSPECIAL_SURVIVORS"
                ),
                "output_tail": output[-1600:],
            }
        )
    except Exception as exc:
        record.update(
            {"request_status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        )
    result = dict(record)
    result["certificate_sha256"] = canonical_sha256(record)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
