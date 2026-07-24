#!/usr/bin/env python3
"""Run an optimized fixed-7 Hilbert-newform replay on the public Magma calculator.

The published integer-resultant computation at conductor exponents (2,3) takes
about 105 seconds.  For the fixed residual characteristic 7 we work directly in
F_7: a resultant is divisible by 7 exactly when the reduced coefficient-field
polynomial and candidate trace polynomial have a common factor.  This avoids the
large integer resultants and is designed to fit the public calculator's
60-second per-request limit.

The pinned candidate data are split into independent batches to respect the
calculator's 50,000-byte input limit.  Every batch recomputes the 35 newform
packets and returns those surviving all auxiliary primes in that batch; the exact
full survivor set is their intersection.  The calculation also applies the odd-
branch superspecial condition at the unique prime above 7: the Hecke eigenvalue
must vanish modulo at least one prime above 7 in its coefficient field.

This is an internet-facing research producer, not a trusted checker.
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

DATA_URL = (
    "https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/"
    "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Outputs/Data.txt"
)
CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
EXPECTED_DATA_BLOB = "9c96357834f2298b4d91ab97812c38e84b8ef7a2"
MAX_INPUT = 49_000
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/136.0 Safari/537.36 "
    "beal-conjecture-lean-research/1.0"
)


class ResearchError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def split_rows(data: bytes) -> list[tuple[int, str]]:
    if git_blob_sha1(data) != EXPECTED_DATA_BLOB:
        raise ResearchError("candidate-data Git blob mismatch")
    text = data.decode("utf-8").strip()
    if not text.startswith("Data:=[") or not text.endswith("];"):
        raise ResearchError("unexpected Data.txt wrapper")
    inside = text[len("Data:=[") : -2]
    rows: list[str] = []
    depth = 0
    start = 0
    for index, character in enumerate(inside):
        if character in "[<":
            depth += 1
        elif character in "]>":
            depth -= 1
        elif character == "," and depth == 0:
            rows.append(inside[start:index].strip())
            start = index + 1
    rows.append(inside[start:].strip())
    result: list[tuple[int, str]] = []
    for row in rows:
        match = re.match(r"<(\d+),", row)
        if match is None:
            raise ResearchError(f"could not identify auxiliary prime in {row[:80]!r}")
        result.append((int(match.group(1)), row))
    if len(result) != 37:
        raise ResearchError(f"expected 37 candidate rows, got {len(result)}")
    return result


MAGMA_PREFIX = r'''
_<x> := PolynomialRing(Rationals());
K<z> := NumberField(x^2-5);
OK := Integers(K);
I5 := Factorisation(5*OK)[1][1];
F7 := GF(7);
R7<X> := PolynomialRing(F7);

Red := function(P)
  return R7![F7!Coefficient(P,i) : i in [0..Degree(P)]];
end function;

Common := function(P,Q)
  return Degree(GreatestCommonDivisor(Red(P),Red(Q))) gt 0;
end function;

AnyCommon := function(P,L)
  for Q in L do
    if Common(P,Q) then return true; end if;
  end for;
  return false;
end function;

Possible := function(form,row)
  l := row[1];
  if l eq 7 then return true; end if;
  I := Factorisation(l*OK)[1][1];
  Eig := HeckeEigenvalue(form,I);
  P := MinimalPolynomial(Eig);
  if AnyCommon(P,row[2]) then return true; end if;

  F := NumberField(CyclotomicPolynomial(15));
  OF := Integers(F);
  f1 := InertiaDegree(Factorisation(l*OF)[1][1]);
  f2 := InertiaDegree(Factorisation(l*OK)[1][1]);
  E2 := Eig;
  if f1/f2 eq 2 then E2 := Eig^2-2*l^f2; end if;
  P2 := MinimalPolynomial(E2);
  if AnyCommon(P2,row[3]) or AnyCommon(P2,row[4]) then return true; end if;

  q := Integers()!Norm(I);
  if Common(P,x-(q+1)) or Common(P,x+(q+1)) then return true; end if;
  return false;
end function;
'''

MAGMA_SUFFIX = r'''
M := HilbertCuspForms(K,3^2*I5^3);
decomp := NewformDecomposition(NewSubspace(M));
S := [];
for i in [1..#decomp] do
  form := Eigenform(decomp[i]);
  alive := true;
  for row in Data do
    if not Possible(form,row) then
      alive := false;
      break;
    end if;
  end for;
  if alive then Append(~S,i); end if;
end for;

I7 := Factorisation(7*OK)[1][1];
Ssup := [];
for i in S do
  form := Eigenform(decomp[i]);
  P7 := MinimalPolynomial(HeckeEigenvalue(form,I7));
  if Common(P7,x) then Append(~Ssup,i); end if;
end for;

printf "FIXED7_SURVIVORS=%o\n",S;
printf "SUPERSPECIAL_SURVIVORS=%o\n",Ssup;
printf "PACKET_COUNT=%o\n",#decomp;
'''


def batches(rows: list[tuple[int, str]]) -> list[list[tuple[int, str]]]:
    result: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for item in rows:
        proposed = current + [item]
        code = make_code(proposed)
        if len(code.encode("utf-8")) > MAX_INPUT:
            if not current:
                raise ResearchError(f"single row at {item[0]} exceeds calculator limit")
            result.append(current)
            current = [item]
        else:
            current = proposed
    if current:
        result.append(current)
    return result


def make_code(rows: list[tuple[int, str]]) -> str:
    data = "Data:=[" + ",".join(row for _prime, row in rows) + "];\n"
    return MAGMA_PREFIX + data + MAGMA_SUFFIX


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
        if (
            type_match is not None
            and type_match.group(1).lower() == "hidden"
            and name_match is not None
        ):
            hidden[html.unescape(name_match.group(1))] = (
                "" if value_match is None else html.unescape(value_match.group(1))
            )
    return action, hidden


def parse_integer_list(text: str, marker: str) -> list[int]:
    match = re.search(rf"{re.escape(marker)}=\[\s*([^\]]*)\]", text)
    if match is None:
        raise ResearchError(f"calculator output lacked {marker}")
    content = match.group(1).strip()
    return [] if not content else [int(value.strip()) for value in content.split(",")]


def submit(code: str) -> tuple[str, list[int], list[int], int]:
    if len(code.encode("utf-8")) > MAX_INPUT:
        raise ResearchError("generated Magma input exceeds calculator limit")

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    get_request = urllib.request.Request(
        CALCULATOR_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
    )
    with opener.open(get_request, timeout=120) as response:
        landing = response.read().decode("utf-8", errors="replace")
        landing_url = response.geturl()
    action, hidden = form_metadata(landing)
    payload = dict(hidden)
    payload["input"] = code
    encoded = urllib.parse.urlencode(payload).encode("utf-8")
    parsed = urllib.parse.urlparse(action)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    request = urllib.request.Request(
        action,
        data=encoded,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": landing_url,
            "Origin": origin,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with opener.open(request, timeout=180) as response:
        page = response.read().decode("utf-8", errors="replace")
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    survivors = parse_integer_list(text, "FIXED7_SURVIVORS")
    superspecial = parse_integer_list(text, "SUPERSPECIAL_SURVIVORS")
    count = re.search(r"PACKET_COUNT=(\d+)", text)
    if count is None:
        snippet = text[-4000:]
        raise ResearchError(f"calculator output lacked packet count:\n{snippet}")
    if not set(superspecial) <= set(survivors):
        raise ResearchError("superspecial set is not a subset of fixed-7 survivors")
    return text, survivors, superspecial, int(count.group(1))


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    rows = split_rows(fetch(DATA_URL))
    batch_rows = batches(rows)
    outputs: list[dict[str, Any]] = []
    intersection: set[int] | None = None
    superspecial_intersection: set[int] | None = None
    for number, batch in enumerate(batch_rows, start=1):
        code = make_code(batch)
        text, survivors, superspecial, packet_count = submit(code)
        if packet_count != 35:
            raise ResearchError(f"batch {number}: expected 35 packets, got {packet_count}")
        current = set(survivors)
        current_superspecial = set(superspecial)
        intersection = current if intersection is None else intersection & current
        superspecial_intersection = (
            current_superspecial
            if superspecial_intersection is None
            else superspecial_intersection & current_superspecial
        )
        outputs.append(
            {
                "batch": number,
                "auxiliary_primes": [prime for prime, _row in batch],
                "input_bytes": len(code.encode("utf-8")),
                "survivors": survivors,
                "superspecial_survivors": superspecial,
                "output_tail": text[-1000:],
            }
        )
    fixed7 = sorted(intersection or set())
    superspecial = sorted(superspecial_intersection or set())
    if not set(superspecial) <= set(fixed7):
        raise ResearchError("final superspecial set is not contained in fixed-7 set")
    body = {
        "schema_version": 2,
        "status": (
            "public-Magma fixed-7 and superspecial replay for conductor "
            "exponents (2,3)"
        ),
        "source": {
            "calculator": CALCULATOR_URL,
            "source_candidate_git_blob": EXPECTED_DATA_BLOB,
            "source_commit": "e88f914c577ab6cf9a45e5cdd82c1993477fb423",
        },
        "level_exponents": [2, 3],
        "packet_count": 35,
        "batch_count": len(outputs),
        "batches": outputs,
        "fixed7_survivors": fixed7,
        "superspecial_survivors": superspecial,
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_digest(body)
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
