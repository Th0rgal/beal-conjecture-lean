#!/usr/bin/env python3
"""Replay the exact odd-branch mod-5 conductor reduction at the prime over 7."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "Research" / "Signature357" / "odd_p7_twist.json"


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("root must be object")
    return value


def canonical(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class Field:
    def __init__(self, prime: int, degree: int, modulus: list[int]):
        self.p = prime
        self.n = degree
        self.q = prime**degree
        self.mod = modulus
        self.powers = [prime**i for i in range(degree)]
        self.coefficients: list[list[int]] = []
        for value in range(self.q):
            work = value
            row = []
            for _ in range(degree):
                row.append(work % prime)
                work //= prime
            self.coefficients.append(row)

    def add(self, left: int, right: int) -> int:
        return sum(
            ((self.coefficients[left][i] + self.coefficients[right][i]) % self.p)
            * self.powers[i]
            for i in range(self.n)
        )

    def multiply(self, left: int, right: int) -> int:
        temporary = [0] * (2 * self.n - 1)
        for i, x in enumerate(self.coefficients[left]):
            if x:
                for j, y in enumerate(self.coefficients[right]):
                    if y:
                        temporary[i + j] = (temporary[i + j] + x * y) % self.p
        for exponent in range(2 * self.n - 2, self.n - 1, -1):
            coefficient = temporary[exponent] % self.p
            if coefficient:
                for i in range(self.n):
                    temporary[exponent - self.n + i] = (
                        temporary[exponent - self.n + i]
                        - coefficient * self.mod[i]
                    ) % self.p
        return sum(
            temporary[i] % self.p * self.powers[i] for i in range(self.n)
        )

    def constant(self, value: int) -> int:
        return value % self.p


def curve_coefficients(parameter: int) -> list[int]:
    # (x+2)(x^7-7*x^5+14*x^3-7*x+2-4*s), ascending.
    return [4 - 8 * parameter, -12 - 4 * parameter, -7, 28, 14, -14, -7, 2, 1]


def point_count(prime: int, degree: int, parameter: int) -> int:
    # x^2+3x+1 and x^3+4x^2+1 are irreducible over F_13.
    moduli = {1: [0, 1], 2: [1, 3, 1], 3: [1, 0, 4, 1]}
    field = Field(prime, degree, moduli[degree])
    coefficients = [field.constant(value) for value in curve_coefficients(parameter)]
    squares = {field.multiply(value, value) for value in range(field.q)}
    # Degree eight with nonzero square leading coefficient has two points at infinity.
    total = 2
    for x in range(field.q):
        value = 0
        for coefficient in reversed(coefficients):
            value = field.add(field.multiply(value, x), coefficient)
        total += 1 if value == 0 else (2 if value in squares else 0)
    return total


def trace_polynomial(prime: int, counts: list[int]) -> list[int]:
    power_sum_1 = prime + 1 - counts[0]
    power_sum_2 = prime**2 + 1 - counts[1]
    power_sum_3 = prime**3 + 1 - counts[2]
    numerator = power_sum_1**2 - (power_sum_2 + 6 * prime)
    if numerator % 2:
        raise CertificateError("nonintegral second elementary symmetric function")
    elementary_2 = numerator // 2
    numerator_3 = (
        power_sum_3
        + 3 * prime * power_sum_1
        - power_sum_1**3
        + 3 * power_sum_1 * elementary_2
    )
    if numerator_3 % 3:
        raise CertificateError("nonintegral third elementary symmetric function")
    elementary_3 = numerator_3 // 3
    return [1, -power_sum_1, elementary_2, -elementary_3]


def legendre(value: int, prime: int) -> int:
    value %= prime
    if value == 0:
        return 0
    residue = pow(value, (prime - 1) // 2, prime)
    return 1 if residue == 1 else -1


def mod_polynomial(coefficients: list[int], prime: int) -> list[int]:
    return [coefficient % prime for coefficient in coefficients]


def negative_root_polynomial(coefficients: list[int]) -> list[int]:
    # For a monic cubic, replacing every root alpha by -alpha sends
    # x^3+c1*x^2+c2*x+c3 to x^3-c1*x^2+c2*x-c3.
    return [coefficients[0], -coefficients[1], coefficients[2], -coefficients[3]]


def validate(data: dict[str, Any]) -> str:
    expected = {
        "schema_version",
        "status",
        "equation",
        "compatible_system",
        "source_dependencies",
        "producer_anchor",
        "darmon_curve_anchor",
        "quadratic_twist_group",
        "local_conclusion",
        "frontier_consequence",
        "nonclaim",
        "certificate_sha256",
    }
    if set(data) != expected:
        raise CertificateError("schema keys mismatch")
    if data["schema_version"] != 1:
        raise CertificateError("schema version mismatch")
    if canonical(data) != data["certificate_sha256"]:
        raise CertificateError("certificate digest mismatch")

    anchor = data["producer_anchor"]
    if anchor["prime"] != 13 or anchor["swapped_parameter"] != 3:
        raise CertificateError("producer anchor metadata mismatch")
    hgm_polynomial = anchor["hgm_trace_polynomial_coefficients_descending"]
    if hgm_polynomial != [1, 2, -1, -1]:
        raise CertificateError("HGM trace polynomial mismatch")

    counts = [point_count(13, degree, 3) for degree in (1, 2, 3)]
    curve = data["darmon_curve_anchor"]
    if counts != curve["point_counts"]:
        raise CertificateError(f"point-count mismatch: {counts}")
    curve_polynomial = trace_polynomial(13, counts)
    if curve_polynomial != curve["trace_polynomial_coefficients_descending"]:
        raise CertificateError(f"curve trace-polynomial mismatch: {curve_polynomial}")
    if mod_polynomial(curve_polynomial, 3) != mod_polynomial(hgm_polynomial, 3):
        raise CertificateError("positive twist comparison fails")
    negative = negative_root_polynomial(curve_polynomial)
    if mod_polynomial(negative, 3) == mod_polynomial(hgm_polynomial, 3):
        raise CertificateError("twist sign is ambiguous")
    if mod_polynomial(negative, 3) != curve[
        "negative_twist_polynomial_mod3_descending"
    ]:
        raise CertificateError("negative-twist polynomial mismatch")

    twist_group = data["quadratic_twist_group"]
    values = {
        name: legendre(radical, 13)
        for name, radical in twist_group["quadratic_radicals"].items()
    }
    if values != twist_group["values_at_prime_13"]:
        raise CertificateError(f"quadratic-character values mismatch: {values}")
    surviving = sorted(name for name, value in values.items() if value == 1)
    if surviving != sorted(twist_group["surviving_characters"]):
        raise CertificateError("quadratic-character survivor set mismatch")
    if legendre(-3, 7) != 1:
        raise CertificateError("chi_-3 is not locally trivial at 7")

    conclusion = data["local_conclusion"]
    if conclusion["congruence_twist_at_7"] != "unramified (indeed locally trivial)":
        raise CertificateError("local twist conclusion mismatch")
    if conclusion["odd_branch_residual_conductor_exponent_at_7"] != 2:
        raise CertificateError("odd conductor exponent at 7 must equal 2")
    frontier = data["frontier_consequence"]
    if frontier["remaining_odd_mod5_levels"] != [35721, 964467]:
        raise CertificateError("odd automorphic frontier mismatch")
    if frontier["removed_odd_mod5_levels"] != [729, 5103, 19683, 137781]:
        raise CertificateError("removed odd levels mismatch")
    return data["certificate_sha256"]


def self_test() -> None:
    source = load(DEFAULT)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["producer_anchor"]["hgm_trace_polynomial_coefficients_descending"] = [
        1,
        -2,
        -1,
        1,
    ]
    mutated["certificate_sha256"] = canonical(mutated)
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the negative congruence twist")

    mutated = copy.deepcopy(source)
    mutated["local_conclusion"]["odd_branch_residual_conductor_exponent_at_7"] = 1
    mutated["certificate_sha256"] = canonical(mutated)
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted conductor drop at 7")

    duplicate = '{"a":1,"a":2}'
    with tempfile.NamedTemporaryFile("w", delete=False) as fixture:
        fixture.write(duplicate)
        path = pathlib.Path(fixture.name)
    try:
        try:
            load(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)
    print("signature-357 odd-p7-twist negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load(DEFAULT))
    print("signature-357 odd-p7 twist/conductor certificate valid")
    print("  exact e7=2; remaining odd levels: 35721, 964467")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
