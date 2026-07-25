#!/usr/bin/env python3
"""Apply the complete prime-13 HGM trace union to level 137781.

The norm-8 calculation has already split the residual newspace into a
38-dimensional B-odd trace-zero space and a 92-dimensional B-even
multiplicative space.  At the split rational prime 13, the complete generic,
zero, infinity and multiplicative HGM trace union, after the required
full-cyclotomic degree-two transform and reduction modulo 5, has square-free
part

    G13 = gcd(P13, X^125-X),  deg(G13)=43.

This producer constructs T_13 only after T_2 and its precomputation have been
released, restricts it to the two parity spaces, and compares characteristic
polynomials with G13.  A zero gcd degree eliminates that parity branch at this
level; a positive degree is only a necessary survivor.
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
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"

# Coefficients low-to-high in F_5.  This is the square-free gcd of the full
# prime-13 local union with X^125-X.
G13_COEFFICIENTS = [
    0, 1, 4, 1, 0, 1, 2, 2, 0, 4, 3, 2, 0, 1, 4, 1, 0, 1, 0, 3, 4, 4,
    0, 3, 0, 0, 4, 2, 1, 4, 0, 0, 3, 4, 0, 4, 4, 3, 0, 3, 4, 0, 2, 1,
]
LOCAL_SOURCE_SHA256 = "c20e4d0d046df579a94e6e344e20a3bf2a87a563eb31d8ab7c58351b1d242e34"


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
        type_match = re.search(r"\btype=[\"']([^\"']*)", tag, flags=re.I)
        name_match = re.search(r"\bname=[\"']([^\"']*)", tag, flags=re.I)
        value_match = re.search(r"\bvalue=[\"']([^\"']*)", tag, flags=re.I)
        if type_match and type_match.group(1).lower() == "hidden" and name_match:
            hidden[html.unescape(name_match.group(1))] = (
                "" if value_match is None else html.unescape(value_match.group(1))
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
    with opener.open(request, timeout=300) as response:
        return html.unescape(
            re.sub(r"<[^>]+>", "", response.read().decode(errors="replace"))
        )


def magma_code() -> str:
    coefficients = ",".join(str(value) for value in G13_COEFFICIENTS)
    return rf'''
_<x> := PolynomialRing(Rationals());
K<w> := NumberField(x^3-x^2-2*x+1); OK := Integers(K);
SetStoreModularForms(K,false);
I3 := Factorisation(3*OK)[1][1];
I7 := Factorisation(7*OK)[1][1];
I2 := Factorisation(2*OK)[1][1];
I13 := Factorisation(13*OK)[1][1];
F5 := GF(5); R5<X> := PolynomialRing(F5);
G13 := R5![{coefficients}];
printf "G13_DEGREE=%o\n",Degree(G13);
printf "PHASE=space-start\n";
M0 := HilbertCuspForms(K,I3^3*I7);
ambient := Dimension(M0);
printf "AMBIENT_DIM=%o\n",ambient;
M := NewSubspace(M0);
n := Dimension(M);
printf "NEW_DIM=%o\n",n;
O := QuaternionOrder(M);
delete M0;
ClearStoredModularForms(K);
DeleteHeckePrecomputation(O);
printf "PHASE=T2-start\n";
T2Q := HeckeOperator(M,I2);
printf "PHASE=T2-rational-ready\n";
DeleteHeckePrecomputation(O,I2);
ClearStoredModularForms(K);
T2 := Matrix(F5,T2Q);
delete T2Q;
I := IdentityMatrix(F5,n);
Sodd := Kernel(T2);
Splus := Kernel(T2-I);
Sminus := Kernel(T2+I);
Seven := Splus+Sminus;
printf "B_ODD_DIM=%o\n",Dimension(Sodd);
printf "B_EVEN_DIM=%o\n",Dimension(Seven);
delete Splus; delete Sminus; delete T2;
DeleteHeckePrecomputation(O);
ClearStoredModularForms(K);
printf "PHASE=T13-start\n";
T13Q := HeckeOperator(M,I13);
printf "PHASE=T13-rational-ready\n";
DeleteHeckePrecomputation(O,I13);
ClearStoredModularForms(K);
T13m := Matrix(F5,T13Q);
delete T13Q;
printf "PHASE=T13-mod5-ready\n";
A := MatrixAlgebra(F5,n);
T13 := A!T13m;
delete T13m;
T13odd := Restrict(T13,Sodd);
T13even := Restrict(T13,Seven);
printf "PHASE=restricted-ready\n";
CPodd := R5!CharacteristicPolynomial(T13odd);
CPeven := R5!CharacteristicPolynomial(T13even);
Godd := GreatestCommonDivisor(CPodd,G13);
Geven := GreatestCommonDivisor(CPeven,G13);
printf "B_ODD_CHARPOLY_DEGREE=%o\n",Degree(CPodd);
printf "B_EVEN_CHARPOLY_DEGREE=%o\n",Degree(CPeven);
printf "B_ODD_GCD_DEGREE=%o\n",Degree(Godd);
printf "B_EVEN_GCD_DEGREE=%o\n",Degree(Geven);
printf "B_ODD_GCD=%o\n",Godd;
printf "B_EVEN_GCD=%o\n",Geven;
printf "FINAL_GCD_DEGREE=%o\n",Degree(Godd)+Degree(Geven);
'''


def parse_int(output: str, marker: str) -> int:
    match = re.search(rf"{marker}=(\d+)", output)
    if match is None:
        raise ResearchError(f"output lacked {marker}")
    return int(match.group(1))


def main() -> int:
    source = magma_code()
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "level-137781 prime-13 parity-local residual filter",
        "calculator": CALCULATOR_URL,
        "field": "K7=Q(zeta_7)^+",
        "level_exponents": [3, 1],
        "level_norm": 137781,
        "auxiliary_rational_prime": 13,
        "prime_ideal_norm": 13,
        "local_source_sha256": LOCAL_SOURCE_SHA256,
        "g13_coefficients_low_to_high_mod5": G13_COEFFICIENTS,
        "g13_degree": len(G13_COEFFICIENTS) - 1,
        "g13_derivation": "gcd(full generic/zero/infinity/multiplicative union, X^125-X)",
        "parity_dimensions_expected": {"B_odd": 38, "B_even": 92},
        "soundness": (
            "gcd degree zero eliminates the corresponding parity branch; positive degree "
            "is only a necessary residual survivor"
        ),
        "nonclaim": (
            "local HGM identification, modularity and level lowering remain imported inputs; "
            "a failed request leaves the level unresolved"
        ),
        "input_bytes": len(source.encode()),
    }
    output = ""
    try:
        output = submit(source)
        odd_dimension = parse_int(output, "B_ODD_DIM")
        even_dimension = parse_int(output, "B_EVEN_DIM")
        if (odd_dimension, even_dimension) != (38, 92):
            raise ResearchError(
                f"unexpected parity dimensions {(odd_dimension, even_dimension)}"
            )
        body.update(
            {
                "request_status": "completed",
                "ambient_dimension": parse_int(output, "AMBIENT_DIM"),
                "new_dimension": parse_int(output, "NEW_DIM"),
                "b_odd_dimension": odd_dimension,
                "b_even_dimension": even_dimension,
                "b_odd_characteristic_polynomial_degree": parse_int(
                    output, "B_ODD_CHARPOLY_DEGREE"
                ),
                "b_even_characteristic_polynomial_degree": parse_int(
                    output, "B_EVEN_CHARPOLY_DEGREE"
                ),
                "b_odd_gcd_degree": parse_int(output, "B_ODD_GCD_DEGREE"),
                "b_even_gcd_degree": parse_int(output, "B_EVEN_GCD_DEGREE"),
                "final_gcd_degree": parse_int(output, "FINAL_GCD_DEGREE"),
                "output_tail": output[-7000:],
            }
        )
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-9000:],
            }
        )
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
