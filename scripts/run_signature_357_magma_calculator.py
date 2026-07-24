#!/usr/bin/env python3
"""Run an optimized fixed-7 Hilbert-newform replay on the public Magma calculator.

The published integer-resultant computation at conductor exponents (2,3) takes
about 105 seconds.  For the fixed residual characteristic 7 we can work directly
in F_7: a resultant is divisible by 7 exactly when the reduced coefficient-field
polynomial and candidate trace polynomial have a common factor.  This avoids the
large integer resultants and is designed to fit the public calculator's 60-second
per-request limit.

The pinned candidate data are split into independent batches to respect the
calculator's 50,000-byte input limit.  Every batch recomputes the 35 newform
packets and returns those surviving all auxiliary primes in that batch; the exact
full survivor set is their intersection.

This is an internet-facing research producer, not a trusted checker.
"""

from __future__ import annotations

import hashlib
import html
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
    "beal-conjecture-lean-research/1.0 "
    "(+https://github.com/Th0rgal/beal-conjecture-lean)"
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
printf "FIXED7_SURVIVORS=%o\n",S;
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


def submit(code: str) -> tuple[str, list[int], int]:
    if len(code.encode("utf-8")) > MAX_INPUT:
        raise ResearchError("generated Magma input exceeds calculator limit")
    encoded = urllib.parse.urlencode({"input": code}).encode("ascii")
    request = urllib.request.Request(
        CALCULATOR_URL,
        data=encoded,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        page = response.read().decode("utf-8", errors="replace")
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    match = re.search(r"FIXED7_SURVIVORS=\[\s*([^\]]*)\]", text)
    count = re.search(r"PACKET_COUNT=(\d+)", text)
    if match is None or count is None:
        snippet = text[-4000:]
        raise ResearchError(f"calculator output lacked result markers:\n{snippet}")
    content = match.group(1).strip()
    survivors = [] if not content else [int(value.strip()) for value in content.split(",")]
    return text, survivors, int(count.group(1))


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
    for number, batch in enumerate(batch_rows, start=1):
        code = make_code(batch)
        text, survivors, packet_count = submit(code)
        if packet_count != 35:
            raise ResearchError(f"batch {number}: expected 35 packets, got {packet_count}")
        current = set(survivors)
        intersection = current if intersection is None else intersection & current
        outputs.append(
            {
                "batch": number,
                "auxiliary_primes": [prime for prime, _row in batch],
                "input_bytes": len(code.encode("utf-8")),
                "survivors": survivors,
                "output_tail": text[-1000:],
            }
        )
    body = {
        "schema_version": 1,
        "status": "public-Magma fixed-7 replay for conductor exponents (2,3)",
        "source": {
            "calculator": CALCULATOR_URL,
            "source_candidate_git_blob": EXPECTED_DATA_BLOB,
            "source_commit": "e88f914c577ab6cf9a45e5cdd82c1993477fb423",
        },
        "level_exponents": [2, 3],
        "packet_count": 35,
        "batch_count": len(outputs),
        "batches": outputs,
        "fixed7_survivors": sorted(intersection or set()),
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_digest(body)
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
