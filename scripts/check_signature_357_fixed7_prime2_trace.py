#!/usr/bin/env python3
"""Replay the corrected prime-2 traces of the fixed-7 Frey family.

For C odd, primitivity forces the two parity cases (A,B)=(1,0) or (0,1)
modulo 2.  The integral Artin--Schreier model reduces to

    y^2+x^3*y=x,
    y^2+(x^3+1)*y=1.

The checker counts their points over F_4 and F_16, reconstructs the genus-2
Weil polynomials, extracts the two-dimensional RM trace, and recomputes the
irreducibility resultant.  It uses no CAS and rejects mutated certificates.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "fixed7_prime2_trace_correction.json"


class CertificateError(ValueError):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("manifest root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


# Binary polynomial representations of x^2+x+1 and x^4+x+1.
MODULI = {2: 0b111, 4: 0b10011}


def multiply(left: int, right: int, degree: int) -> int:
    modulus = MODULI[degree]
    result = 0
    a = left
    b = right
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << degree):
            a ^= modulus
    return result & ((1 << degree) - 1)


def point_count(degree: int, a_coefficient: int, b_coefficient: int) -> int:
    """Count y^2+(x^3+b)y=a*x+b^2, including two points at infinity."""
    q = 1 << degree
    affine = 0
    for x in range(q):
        x2 = multiply(x, x, degree)
        x3 = multiply(x2, x, degree)
        h = x3 ^ b_coefficient
        right = multiply(a_coefficient, x, degree) ^ multiply(
            b_coefficient, b_coefficient, degree
        )
        for y in range(q):
            left = multiply(y, y, degree) ^ multiply(h, y, degree)
            if left == right:
                affine += 1
    return affine + 2


def weil_coefficients(q: int, count_q: int, count_q2: int) -> tuple[int, ...]:
    s1 = q + 1 - count_q
    s2 = q * q + 1 - count_q2
    numerator = s1 * s1 - s2
    if numerator % 2:
        raise CertificateError("second Weil coefficient is not integral")
    e2 = numerator // 2
    return (1, -s1, e2, -q * s1, q * q)


def square_quadratic(trace: int, q: int) -> tuple[int, ...]:
    # (T^2-trace*T+q)^2, coefficients descending.
    return (1, -2 * trace, trace * trace + 2 * q, -2 * trace * q, q * q)


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or digest mismatch")
    if data.get("status") != "elementary-finite-field-correction-of-the-prime2-frey-trace":
        raise CertificateError("unexpected status")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    scope = data["scope"]
    if scope["branch"] != "C odd" or scope["base_field"] != "F_4":
        raise CertificateError("scope changed")
    if scope["base_prime_norm"] != 4:
        raise CertificateError("base norm changed")
    expected_parity = [
        {"A_mod2": 1, "B_mod2": 0, "reduced_curve": "y^2+x^3*y=x"},
        {"A_mod2": 0, "B_mod2": 1, "reduced_curve": "y^2+(x^3+1)*y=1"},
    ]
    if scope["parity_cases"] != expected_parity:
        raise CertificateError("parity reductions changed")

    expected_rows = []
    traces = []
    for case, a_coefficient, b_coefficient in (
        ("A odd, B even", 1, 0),
        ("A even, B odd", 0, 1),
    ):
        count4 = point_count(2, a_coefficient, b_coefficient)
        count16 = point_count(4, a_coefficient, b_coefficient)
        q = 4
        s1 = q + 1 - count4
        s2 = q * q + 1 - count16
        if s1 % 2:
            raise CertificateError("RM trace is not integral")
        trace = s1 // 2
        polynomial = weil_coefficients(q, count4, count16)
        if polynomial != square_quadratic(trace, q):
            raise CertificateError("Weil polynomial is not the expected RM square")
        traces.append(trace)
        polynomial_text = (
            "T^4+8*T^2+16=(T^2+4)^2"
            if trace == 0
            else "T^4+2*T^3+9*T^2+8*T+16=(T^2+T+4)^2"
        )
        expected_rows.append(
            {
                "F16": count16,
                "F4": count4,
                "case": case,
                "power_sums": {"S1": s1, "S2": s2},
                "rm_trace": trace,
                "weil_polynomial": polynomial_text,
            }
        )
    if data["point_counts"] != expected_rows:
        raise CertificateError(f"point-count rows changed: {expected_rows}")
    if traces != [0, -1] or data["corrected_trace_set"] != traces:
        raise CertificateError("corrected trace set mismatch")

    diagnosis = data["diagnosis"]
    if data["published_pair"] != [-1, -8] or not diagnosis["published_pair_mixes_levels"]:
        raise CertificateError("published-pair diagnosis changed")
    if diagnosis["degree_two_transform"] != "a_(P^2)=a_P^2-2*Norm(P)=a_P^2-8":
        raise CertificateError("degree-two trace formula changed")
    if [trace * trace - 8 for trace in traces] != [-8, -7]:
        raise CertificateError("degree-two traces do not replay")
    if "-8 is the degree-two trace" not in diagnosis["explanation"]:
        raise CertificateError("normalization explanation missing")

    obstruction = data["irreducibility_obstruction"]
    resultants = [4 + 1 - trace for trace in traces]
    product = resultants[0] * resultants[1]
    norm = product * product
    if resultants != [5, 6] or obstruction["resultants_at_X_equals_1"] != resultants:
        raise CertificateError("resultant list mismatch")
    if obstruction["product"] != product or obstruction["absolute_norm"] != norm:
        raise CertificateError("resultant product or norm mismatch")
    if obstruction["prime_support"] != [2, 3, 5] or obstruction["corrected_bound_C2"] != 5:
        raise CertificateError("corrected irreducibility bound mismatch")
    if norm % 7 == 0 or not obstruction["residual_prime_7_excluded"]:
        raise CertificateError("residual prime 7 was not excluded")

    hecke = data["fixed7_hecke_condition"]
    if hecke != {
        "allowed_base_traces": [0, 6],
        "annihilating_polynomial": "X*(X+1)",
        "modulus": 7,
    }:
        raise CertificateError("fixed-7 Hecke condition changed")
    if "imported literature input" not in data.get("nonclaim", ""):
        raise CertificateError("trust-boundary nonclaim missing")
    return data["certificate_sha256"]


def expect_rejection(value: dict[str, Any], label: str) -> None:
    value["certificate_sha256"] = digest(value)
    try:
        validate(value)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load(MANIFEST)
    validate(base)

    mutated = copy.deepcopy(base)
    mutated["point_counts"][0]["F4"] += 1
    expect_rejection(mutated, "a mutated F4 point count")

    mutated = copy.deepcopy(base)
    mutated["diagnosis"]["published_pair_mixes_levels"] = False
    expect_rejection(mutated, "a removed normalization warning")

    mutated = copy.deepcopy(base)
    mutated["irreducibility_obstruction"]["corrected_bound_C2"] = 13
    expect_rejection(mutated, "the obsolete irreducibility bound")

    mutated = copy.deepcopy(base)
    mutated["fixed7_hecke_condition"]["allowed_base_traces"] = [6]
    expect_rejection(mutated, "an incomplete Hecke trace set")

    with tempfile.NamedTemporaryFile("w", delete=False) as fixture:
        fixture.write('{"x":1,"x":2}')
        path = pathlib.Path(fixture.name)
    try:
        try:
            load(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("duplicate keys accepted")
    finally:
        path.unlink(missing_ok=True)

    print("corrected prime-2 trace negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(MANIFEST))
    print("fixed-7 prime-2 trace correction valid")
    print("  base RM traces over F4: 0 and -1")
    print("  corrected irreducibility support: {2,3,5}; C(2)=5")
    print("  residual Hecke condition: T_P*(T_P+1)=0 modulo 7")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
