#!/usr/bin/env python3
"""Replay the exact prime-2 traces of the odd-C fixed-7 Frey curve.

The arithmetic layer is dependency-free. It enumerates the two characteristic-2
special fibres over F_4 and F_16, adds the two points at infinity, reconstructs
the genus-two Weil polynomial, and verifies that it is the square of the stated
real-multiplication quadratic factor.
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
DEFAULT = ROOT / "Research" / "Signature357" / "fixed7_prime2_trace_union.json"


class CertificateError(ValueError):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("manifest root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def degree(value: int) -> int:
    return value.bit_length() - 1


def polynomial_mod(value: int, modulus: int) -> int:
    modulus_degree = degree(modulus)
    while value and degree(value) >= modulus_degree:
        value ^= modulus << (degree(value) - modulus_degree)
    return value


def polynomial_gcd(a: int, b: int) -> int:
    while b:
        a, b = b, polynomial_mod(a, b)
    return a


def irreducible_binary(modulus: int, extension_degree: int) -> bool:
    if degree(modulus) != extension_degree or not (modulus & 1):
        return False
    x = 0b10
    power = x
    for divisor in range(1, extension_degree // 2 + 1):
        power = field_square(power, extension_degree, modulus)
        if (
            extension_degree % divisor == 0
            and polynomial_gcd(power ^ x, modulus) != 1
        ):
            return False
    power = x
    for _ in range(extension_degree):
        power = field_square(power, extension_degree, modulus)
    return power == x


def field_mul(a: int, b: int, extension_degree: int, modulus: int) -> int:
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << extension_degree):
            a ^= modulus
    return result & ((1 << extension_degree) - 1)


def field_square(a: int, extension_degree: int, modulus: int) -> int:
    return field_mul(a, a, extension_degree, modulus)


def field_pow(a: int, exponent: int, extension_degree: int, modulus: int) -> int:
    result = 1
    while exponent:
        if exponent & 1:
            result = field_mul(result, a, extension_degree, modulus)
        a = field_square(a, extension_degree, modulus)
        exponent >>= 1
    return result


def affine_count(case: str, extension_degree: int, modulus: int) -> int:
    q = 1 << extension_degree
    count = 0
    for x in range(q):
        x3 = field_pow(x, 3, extension_degree, modulus)
        if case == "A_odd_B_even":
            h, rhs = x3, x
        elif case == "A_even_B_odd":
            h, rhs = x3 ^ 1, 1
        else:
            raise CertificateError(f"unknown parity case {case}")
        for y in range(q):
            lhs = field_square(y, extension_degree, modulus) ^ field_mul(
                h, y, extension_degree, modulus
            )
            if lhs == rhs:
                count += 1
    return count


def polynomial_mul(a: list[int], b: list[int]) -> list[int]:
    result = [0] * (len(a) + len(b) - 1)
    for i, left in enumerate(a):
        for j, right in enumerate(b):
            result[i + j] += left * right
    return result


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1 or digest(data) != data.get(
        "certificate_sha256"
    ):
        raise CertificateError("schema or certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation changed")
    scope = data.get("scope", {})
    if scope.get("branch") != "C odd" or scope.get("prime_ideal_norm") != 4:
        raise CertificateError("scope or norm changed")
    parity = data.get("parity", {})
    if parity.get("equation_mod2") != "A+B=C" or parity.get("C_mod2") != 1:
        raise CertificateError("parity equation changed")
    expected_parity = [
        {"A_mod2": 1, "B_mod2": 0, "case": "A_odd_B_even"},
        {"A_mod2": 0, "B_mod2": 1, "case": "A_even_B_odd"},
    ]
    if parity.get("primitive_cases") != expected_parity:
        raise CertificateError("primitive parity cases changed")

    fields = data.get("finite_fields", {})
    field_specs = {"F4": (2, 0b111), "F16": (4, 0b10011)}
    for label, (extension_degree, modulus) in field_specs.items():
        record = fields.get(label, {})
        if (
            record.get("degree") != extension_degree
            or record.get("modulus_binary") != modulus
        ):
            raise CertificateError(f"{label} metadata changed")
        if not irreducible_binary(modulus, extension_degree):
            raise CertificateError(f"{label} modulus is reducible")

    infinity = data.get("points_at_infinity", {})
    if infinity.get("count") != 2 or infinity.get("values") != [0, 1]:
        raise CertificateError("points at infinity changed")

    expected_cases = {
        "A_odd_B_even": {
            "reduction": "y^2+x^3*y=x",
            "affine": {"F4": 3, "F16": 31},
            "projective": {"F4": 5, "F16": 33},
            "S1": 0,
            "S2": -16,
            "weil": [1, 0, 8, 0, 16],
            "factor": [1, 0, 4],
            "trace": 0,
        },
        "A_even_B_odd": {
            "reduction": "y^2+(x^3+1)*y=1",
            "affine": {"F4": 5, "F16": 29},
            "projective": {"F4": 7, "F16": 31},
            "S1": -2,
            "S2": -14,
            "weil": [1, 2, 9, 8, 16],
            "factor": [1, 1, 4],
            "trace": -1,
        },
    }
    records = data.get("cases")
    if not isinstance(records, list) or [
        record.get("name") for record in records
    ] != list(expected_cases):
        raise CertificateError("parity case order changed")
    for record in records:
        name = record["name"]
        expected = expected_cases[name]
        if record.get("reduction") != expected["reduction"]:
            raise CertificateError(f"{name} reduction changed")
        computed_affine = {
            label: affine_count(name, degree_value, modulus)
            for label, (degree_value, modulus) in field_specs.items()
        }
        if (
            computed_affine != expected["affine"]
            or record.get("affine_counts") != computed_affine
        ):
            raise CertificateError(f"{name} affine point count changed")
        projective = {label: count + 2 for label, count in computed_affine.items()}
        if (
            projective != expected["projective"]
            or record.get("projective_counts") != projective
        ):
            raise CertificateError(f"{name} projective point count changed")
        q = 4
        s1 = q + 1 - projective["F4"]
        s2 = q * q + 1 - projective["F16"]
        a2_numerator = s1 * s1 - s2
        if a2_numerator % 2:
            raise CertificateError(f"{name} non-integral Weil coefficient")
        a2 = a2_numerator // 2
        weil = [1, -s1, a2, -q * s1, q * q]
        if (s1, s2) != (expected["S1"], expected["S2"]):
            raise CertificateError(f"{name} power sums changed")
        if record.get("power_sums") != {"S1": s1, "S2": s2}:
            raise CertificateError(f"{name} recorded power sums changed")
        if (
            weil != expected["weil"]
            or record.get("weil_polynomial_descending") != weil
        ):
            raise CertificateError(f"{name} Weil polynomial changed")
        factor = expected["factor"]
        if (
            polynomial_mul(factor, factor) != weil
            or record.get("rm_factor_descending") != factor
        ):
            raise CertificateError(f"{name} RM factorization changed")
        trace = -factor[1]
        if trace != expected["trace"] or record.get("rm_trace") != trace:
            raise CertificateError(f"{name} RM trace changed")

    conclusion = data.get("conclusion", {})
    if conclusion.get("integer_trace_set") != [0, -1]:
        raise CertificateError("integer trace set changed")
    if conclusion.get("trace_set_mod7") != [0, 6]:
        raise CertificateError("residual trace set changed")
    if conclusion.get("annihilating_polynomial_mod7") != "T*(T+1)":
        raise CertificateError("annihilating polynomial changed")
    if "imported literature inputs" not in data.get("nonclaim", ""):
        raise CertificateError("trust boundary missing")
    return data["certificate_sha256"]


def expect_rejection(value: dict[str, Any], label: str) -> None:
    value["certificate_sha256"] = digest(value)
    try:
        validate(value)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load(DEFAULT)
    validate(base)
    mutated = copy.deepcopy(base)
    mutated["cases"][0]["affine_counts"]["F16"] += 1
    expect_rejection(mutated, "a mutated point count")
    mutated = copy.deepcopy(base)
    mutated["cases"][1]["rm_trace"] = 0
    expect_rejection(mutated, "a mutated RM trace")
    mutated = copy.deepcopy(base)
    mutated["conclusion"]["trace_set_mod7"] = [0]
    expect_rejection(mutated, "an incomplete trace set")
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
    print("fixed-7 prime-2 trace-union negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(args.manifest))
    print("fixed-7 prime-2 trace-union certificate valid")
    print("  exact RM traces at the norm-4 prime: 0 and -1")
    print("  residual annihilator: T*(T+1) modulo 7")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
