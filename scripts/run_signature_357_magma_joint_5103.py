#!/usr/bin/env python3
"""Run the corrected odd-branch two-Frey test at mod-5 level 5103.

The marginal mod-5 calculation leaves packet 1 at conductor exponents (2,1).
Local-type synchronization forces the fixed-7 side to level (2,3), where the
superspecial and CM filters leave packets 24 and 28.

The mathematical parameters are

    u=C^7/A^3,   v=-B^5/A^3,   u+v=1.

The pinned PARI/GP ``hgm`` routine uses reciprocal implementation coordinates,
so the generic producer supplies ``z5=u^(-1)`` and ``z7=v^(-1)`` with
``(z5-1)*(z7-1)=1``.  This script validates those labels before comparing the
two candidate pairs at 13, 29 and 41.  Degenerate regimes remain paired in the
mathematical coordinates:

    u=0        <-> v=1,
    u=1        <-> v=0,
    u=infinity <-> v=infinity.

Failed requests are explicit and never interpreted as elimination.
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
DATA_URL = (
    "https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/"
    "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Outputs/Data.txt"
)
EXPECTED_DATA_BLOB = "9c96357834f2298b4d91ab97812c38e84b8ef7a2"
PRIMES = [13, 29, 41]
FIXED7_PACKETS = [24, 28]
MAX_INPUT = 49_000
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


class ResearchError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fetch_data() -> bytes:
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if git_blob_sha1(data) != EXPECTED_DATA_BLOB:
        raise ResearchError("fixed-7 candidate-data blob mismatch")
    return data


def split_rows(data: bytes) -> dict[int, str]:
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
    result: dict[int, str] = {}
    for row in rows:
        match = re.match(r"<(\d+),", row)
        if match:
            result[int(match.group(1))] = row
    if any(prime not in result for prime in PRIMES):
        raise ResearchError("missing selected fixed-7 candidate row")
    return result


def magma_list(values: list[str]) -> str:
    return "[" + ",".join(values) + "]"


def encoded_joint(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 2:
        raise ResearchError("joint trace data must use reciprocal-coordinate schema 2")
    if data.get("mathematical_parameter_identity") != (
        "u=C^7/A^3,v=-B^5/A^3,u+v=1"
    ):
        raise ResearchError("joint mathematical-parameter identity mismatch")
    if data.get("gp_parameter_identity") != (
        "z5=u^(-1),z7=v^(-1),(z5-1)*(z7-1)=1"
    ):
        raise ResearchError("joint GP-coordinate identity mismatch")
    rows = []
    for prime in PRIMES:
        selected = [row for row in data["rows"] if row["prime"] == prime]
        if len(selected) != prime - 2:
            raise ResearchError(f"incomplete generic joint rows at {prime}")
        pairs = []
        seen_u: set[int] = set()
        for row in selected:
            u = int(row["u_mod_prime"])
            v = int(row["v_mod_prime"])
            z5 = int(row["gp_argument_mod5"])
            z7 = int(row["gp_argument_fixed7"])
            if u in seen_u:
                raise ResearchError(f"duplicate mathematical parameter at {prime}")
            seen_u.add(u)
            if (u + v) % prime != 1:
                raise ResearchError(f"u+v relation failed at {prime}")
            if (u * z5) % prime != 1 or (v * z7) % prime != 1:
                raise ResearchError(f"reciprocal GP coordinate failed at {prime}")
            if ((z5 - 1) * (z7 - 1)) % prime != 1:
                raise ResearchError(f"coupled GP relation failed at {prime}")
            pairs.append(
                f"<{row['mod5_trace_polynomial']},{row['fixed7_trace_polynomial']}>"
            )
        rows.append(f"<{prime},{magma_list(pairs)}>")
    return "[" + ",".join(rows) + "]"


def encoded_mod5_degenerate(data: dict[str, Any]) -> str:
    rows = []
    for prime in PRIMES:
        metadata = data["residue_metadata"][str(prime)]
        zero = [
            row["trace_polynomial"]
            for row in data["zero_rows"]
            if row["prime"] == prime
        ]
        infinity = [
            row["trace_polynomial"]
            for row in data["infinity_rows"]
            if row["prime"] == prime
        ]
        if len(zero) != 7 or len(infinity) != 3:
            raise ResearchError(f"incomplete mod-5 degenerate rows at {prime}")
        rows.append(
            f"<{prime},{magma_list(zero)},{magma_list(infinity)},"
            f"{metadata['residue_degree_K7']},{metadata['residue_degree_F21']}>"
        )
    return "[" + ",".join(rows) + "]"


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
        raise ResearchError("generated Magma input exceeds calculator limit")
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    request = urllib.request.Request(
        CALCULATOR_URL, headers={"User-Agent": USER_AGENT, "Accept": "text/html"}
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


def make_code(joint: dict[str, Any], mod5: dict[str, Any], fixed_rows: dict[int, str]) -> str:
    fixed = "[" + ",".join(fixed_rows[prime] for prime in PRIMES) + "]"
    return rf'''
_<x> := PolynomialRing(Rationals());
K7<w> := NumberField(x^3-x^2-2*x+1); O7 := Integers(K7);
K5<z> := NumberField(x^2-5); O5 := Integers(K5);
F21 := NumberField(CyclotomicPolynomial(21)); OF21 := Integers(F21);
F15 := NumberField(CyclotomicPolynomial(15)); OF15 := Integers(F15);
I3 := Factorisation(3*O7)[1][1]; I7 := Factorisation(7*O7)[1][1];
J5 := Factorisation(5*O5)[1][1];
F5 := GF(5); R5<X5> := PolynomialRing(F5);
F7 := GF(7); R7<X7> := PolynomialRing(F7);
Red5 := function(P) return R5![F5!Coefficient(P,i) : i in [0..Degree(P)]]; end function;
Red7 := function(P) return R7![F7!Coefficient(P,i) : i in [0..Degree(P)]]; end function;
Common5 := function(P,Q) return Degree(GreatestCommonDivisor(Red5(P),Red5(Q))) gt 0; end function;
Common7 := function(P,Q) return Degree(GreatestCommonDivisor(Red7(P),Red7(Q))) gt 0; end function;
Any5 := function(P,L) for Q in L do if Common5(P,Q) then return true; end if; end for; return false; end function;
Any7 := function(P,L) for Q in L do if Common7(P,Q) then return true; end if; end for; return false; end function;
Joint := {encoded_joint(joint)};
Mod5Deg := {encoded_mod5_degenerate(mod5)};
FixedData := {fixed};
M5 := HilbertCuspForms(K7,I3^2*I7); D5 := NewformDecomposition(NewSubspace(M5));
M7 := HilbertCuspForms(K5,3^2*J5^3); D7 := NewformDecomposition(NewSubspace(M7));
if #D5 ne 10 then error "unexpected mod-5 packet count"; end if;
if #D7 ne 35 then error "unexpected fixed-7 packet count"; end if;
f5 := Eigenform(D5[1]); Survivors := [];
for j in {FIXED7_PACKETS} do
  f7 := Eigenform(D7[j]); alive := true;
  for k in [1..#Joint] do
    l := Joint[k][1]; pairs := Joint[k][2]; d5 := Mod5Deg[k]; d7 := FixedData[k];
    P5b := MinimalPolynomial(HeckeEigenvalue(f5,Factorisation(l*O7)[1][1]));
    E5 := HeckeEigenvalue(f5,Factorisation(l*O7)[1][1]);
    if d5[5]/d5[4] eq 2 then E5 := E5^2-2*l^d5[4]; end if;
    P5f := MinimalPolynomial(E5);
    I := Factorisation(l*O5)[1][1]; fK5 := InertiaDegree(I); fF15 := InertiaDegree(Factorisation(l*OF15)[1][1]);
    E7 := HeckeEigenvalue(f7,I); P7b := MinimalPolynomial(E7);
    if fF15/fK5 eq 2 then E7 := E7^2-2*l^fK5; end if;
    P7f := MinimalPolynomial(E7);
    generic := false;
    for pair in pairs do if Common5(P5b,pair[1]) and Common7(P7b,pair[2]) then generic := true; break; end if; end for;
    q5 := Integers()!Norm(Factorisation(l*O7)[1][1]); q7 := Integers()!Norm(I);
    zero := Any5(P5f,d5[2]) and (Common7(P7b,x-(q7+1)) or Common7(P7b,x+(q7+1)));
    one := (Common5(P5b,x-(q5+1)) or Common5(P5b,x+(q5+1))) and Any7(P7f,d7[3]);
    infinity := Any5(P5f,d5[3]) and Any7(P7f,d7[4]);
    printf "PAIR=%o PRIME=%o REGIMES=[%o,%o,%o,%o]\n",j,l,generic,zero,one,infinity;
    if not (generic or zero or one or infinity) then alive := false; break; end if;
  end for;
  if alive then Append(~Survivors,j); end if;
end for;
printf "MOD5_PACKET=1\n"; printf "FIXED7_CANDIDATES=%o\n",[24, 28]; printf "PAIR_SURVIVORS=%o\n",Survivors;
'''


def parse_list(text: str, marker: str) -> list[int]:
    match = re.search(rf"{marker}=\[\s*([^\]]*)\]", text)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    body = match.group(1).strip()
    return [] if not body else [int(value.strip()) for value in body.split(",")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--joint-data", type=pathlib.Path, required=True)
    parser.add_argument("--mod5-local", type=pathlib.Path, required=True)
    args = parser.parse_args()
    joint = json.loads(args.joint_data.read_text(encoding="utf-8"))
    mod5 = json.loads(args.mod5_local.read_text(encoding="utf-8"))
    code = make_code(joint, mod5, split_rows(fetch_data()))
    record: dict[str, Any] = {
        "schema_version": 2,
        "status": "odd-branch level-5103 exact two-Frey pair test with reciprocal GP coordinates",
        "mod5_level_exponents": [2, 1],
        "mod5_packet": 1,
        "fixed7_level_exponents": [2, 3],
        "fixed7_candidates": FIXED7_PACKETS,
        "auxiliary_primes": PRIMES,
        "joint_data_sha256": joint["certificate_sha256"],
        "joint_gp_parameter_identity": joint["gp_parameter_identity"],
        "mod5_local_data_sha256": mod5["certificate_sha256"],
        "input_bytes": len(code.encode("utf-8")),
    }
    try:
        text = submit(code)
        record["pair_survivors"] = parse_list(text, "PAIR_SURVIVORS")
        record["output_tail"] = text[-5000:]
        record["completed"] = True
    except Exception as exc:
        record["completed"] = False
        record["error"] = f"{type(exc).__name__}: {exc}"
    body = dict(record)
    result = dict(body)
    result["certificate_sha256"] = canonical_sha256(body)
    json.dump(result, __import__("sys").stdout, sort_keys=True, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
