#!/usr/bin/env python3
"""Replay the finite-field consequences of the semilinear Galois trace symmetry."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from itertools import product
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "galois_trace_symmetry.json"


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("JSON root must be an object")
    return value


def canonical_sha256(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class FiniteField:
    def __init__(self, prime: int, modulus: list[int]):
        self.prime = prime
        self.modulus = [coefficient % prime for coefficient in modulus]
        if self.modulus[-1] != 1:
            raise CertificateError("finite-field modulus must be monic")
        self.degree = len(self.modulus) - 1

    def element(self, coefficients: list[int]) -> tuple[int, ...]:
        value = [0] * self.degree
        for index, coefficient in enumerate(coefficients[: self.degree]):
            value[index] = coefficient % self.prime
        return tuple(value)

    @property
    def one(self) -> tuple[int, ...]:
        return (1,) + (0,) * (self.degree - 1)

    def multiply(self, left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
        raw = [0] * (2 * self.degree - 1)
        for i, x in enumerate(left):
            for j, y in enumerate(right):
                raw[i + j] = (raw[i + j] + x * y) % self.prime
        for exponent in range(len(raw) - 1, self.degree - 1, -1):
            coefficient = raw[exponent] % self.prime
            if coefficient:
                for index in range(self.degree):
                    raw[exponent - self.degree + index] = (
                        raw[exponent - self.degree + index]
                        - coefficient * self.modulus[index]
                    ) % self.prime
        return tuple(raw[: self.degree])

    def power(self, value: tuple[int, ...], exponent: int) -> tuple[int, ...]:
        result = self.one
        while exponent:
            if exponent & 1:
                result = self.multiply(result, value)
            value = self.multiply(value, value)
            exponent //= 2
        return result

    def elements(self) -> list[tuple[int, ...]]:
        return [tuple(value) for value in product(range(self.prime), repeat=self.degree)]


def evaluate_polynomial(coefficients: list[int], value: int, prime: int) -> int:
    return sum(
        coefficient * pow(value, exponent, prime)
        for exponent, coefficient in enumerate(coefficients)
    ) % prime


def roots(coefficients: list[int], prime: int) -> list[int]:
    return [
        value
        for value in range(prime)
        if evaluate_polynomial(coefficients, value, prime) == 0
    ]


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1:
        raise CertificateError("schema version mismatch")
    if canonical_sha256(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    mod5 = data["systems"]["mod5"]
    fixed7 = data["systems"]["fixed7"]
    if mod5["residue_field_size"] != 125 or mod5["residue_degree"] != 3:
        raise CertificateError("mod-5 residue metadata mismatch")
    if fixed7["residue_field_size"] != 49 or fixed7["residue_degree"] != 2:
        raise CertificateError("fixed-7 residue metadata mismatch")
    if mod5["trace_relation"] != "a_{sigma(l)}=a_l^5 and a_{sigma^2(l)}=a_l^25":
        raise CertificateError("mod-5 trace relation mismatch")
    if fixed7["trace_relation"] != "a_{sigma(l)}=a_l^7":
        raise CertificateError("fixed-7 trace relation mismatch")

    # theta^3+theta^2-2theta-1 and phi^2-phi-1.
    if roots([-1, -2, 1, 1], 5):
        raise CertificateError("K7 polynomial became reducible modulo 5")
    if roots([-1, -1, 1], 7):
        raise CertificateError("K5 polynomial became reducible modulo 7")

    field125 = FiniteField(5, [-1, -2, 1, 1])
    field49 = FiniteField(7, [-1, -1, 1])
    elements125 = field125.elements()
    elements49 = field49.elements()
    fixed_by_5 = [value for value in elements125 if field125.power(value, 5) == value]
    fixed_by_7 = [value for value in elements49 if field49.power(value, 7) == value]
    if len(fixed_by_5) != 5 or any(
        field125.power(value, 125) != value for value in elements125
    ):
        raise CertificateError("F125 Frobenius audit failed")
    if len(fixed_by_7) != 7 or any(
        field49.power(value, 49) != value for value in elements49
    ):
        raise CertificateError("F49 Frobenius audit failed")

    theta = field125.element([0, 1, 0])
    phi = field49.element([0, 1])
    if field125.power(theta, 5) == theta or field125.power(theta, 25) == theta:
        raise CertificateError("mod-5 Frobenius does not have degree three")
    if field125.power(theta, 125) != theta:
        raise CertificateError("mod-5 Frobenius cube failed")
    if field49.power(phi, 7) == phi or field49.power(phi, 49) != phi:
        raise CertificateError("fixed-7 Frobenius degree audit failed")

    if mod5["split_classes_mod7"] != [1, 6] or mod5["inert_classes_mod7"] != [2, 3, 4, 5]:
        raise CertificateError("K7 splitting classes mismatch")
    for residue in range(1, 7):
        expected_degree = 1 if residue in (1, 6) else 3
        degree = 1
        while pow(residue, degree, 7) not in (1, 6):
            degree += 1
        if degree != expected_degree:
            raise CertificateError(f"wrong real-cyclotomic degree for {residue}")

    if fixed7["split_classes_mod5"] != [1, 4] or fixed7["inert_classes_mod5"] != [2, 3]:
        raise CertificateError("K5 splitting classes mismatch")
    for residue in range(1, 5):
        degree = 1 if pow(residue, 2, 5) == 1 else 2
        expected_degree = 1 if residue in (1, 4) else 2
        if degree != expected_degree:
            raise CertificateError(f"wrong quadratic degree for {residue}")

    consequences = data["computational_consequences"]
    if "X^p-X" not in consequences["inert_prime_filter"]:
        raise CertificateError("inert-prime polynomial filter missing")
    if "T_sigma-T^5" not in consequences["split_prime_filter_mod5"]:
        raise CertificateError("mod-5 split-prime relation missing")
    if "T_sigma-T^7" not in consequences["split_prime_filter_fixed7"]:
        raise CertificateError("fixed-7 split-prime relation missing")
    if "imported motive-theoretic inputs" not in data["nonclaim"]:
        raise CertificateError("trust boundary missing")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = canonical_sha256(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load(MANIFEST)
    validate(base)

    mutated = copy.deepcopy(base)
    mutated["systems"]["mod5"]["inert_classes_mod7"] = [2, 3, 4]
    expect_rejection(mutated, "a missing inert residue class")

    mutated = copy.deepcopy(base)
    mutated["systems"]["fixed7"]["trace_relation"] = "a_sigma=a"
    expect_rejection(mutated, "a weakened fixed-7 trace relation")

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
    print("Galois-trace-symmetry negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    value = validate(load(MANIFEST))
    print("semilinear Galois trace symmetry finite consequences valid")
    print("  mod 5: inert K7 traces lie in F5; split triples are Frobenius conjugate")
    print("  mod 7: inert K5 traces lie in F7; split pairs are Frobenius conjugate")
    print(f"  certificate sha256: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
