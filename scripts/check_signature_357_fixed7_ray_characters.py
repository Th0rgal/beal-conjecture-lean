#!/usr/bin/env python3
"""Replay the full ray-character control behind the fixed-7 prime-41 target."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "fixed7_ray_character_control.json"
P = 7


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
        raise CertificateError("manifest root must be an object")
    return value


def canonical_sha256(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class F49:
    a: int = 0
    b: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "a", self.a % P)
        object.__setattr__(self, "b", self.b % P)

    @staticmethod
    def of(value: int | "F49") -> "F49":
        return value if isinstance(value, F49) else F49(value)

    def __add__(self, other: int | "F49") -> "F49":
        rhs = self.of(other)
        return F49(self.a + rhs.a, self.b + rhs.b)

    __radd__ = __add__

    def __neg__(self) -> "F49":
        return F49(-self.a, -self.b)

    def __sub__(self, other: int | "F49") -> "F49":
        return self + (-self.of(other))

    def __rsub__(self, other: int | "F49") -> "F49":
        return self.of(other) - self

    def __mul__(self, other: int | "F49") -> "F49":
        rhs = self.of(other)
        return F49(
            self.a * rhs.a - self.b * rhs.b,
            self.a * rhs.b + self.b * rhs.a,
        )

    __rmul__ = __mul__

    def inverse(self) -> "F49":
        denominator = (self.a * self.a + self.b * self.b) % P
        if denominator == 0:
            raise ZeroDivisionError
        inverse = pow(denominator, -1, P)
        return F49(self.a * inverse, -self.b * inverse)

    def pair(self) -> list[int]:
        return [self.a, self.b]


I = F49(0, 1)


def polynomial_terms(poly: str) -> dict[int, int]:
    compact = poly.replace(" ", "").replace("-", "+-")
    if compact.startswith("+-"):
        compact = compact[1:]
    terms: dict[int, int] = {}
    for term in compact.split("+"):
        if not term:
            continue
        if "x" not in term:
            degree, coefficient = 0, int(term)
        else:
            before, after = term.split("x", 1)
            if before.endswith("*"):
                before = before[:-1]
            coefficient = -1 if before == "-" else (1 if before == "" else int(before))
            degree = int(after[1:]) if after.startswith("^") else 1
        terms[degree] = terms.get(degree, 0) + coefficient
    return terms


def evaluate(poly: str, value: F49) -> F49:
    result = F49()
    for degree, coefficient in polynomial_terms(poly).items():
        power = F49(1)
        for _ in range(degree):
            power = power * value
        result = result + coefficient * power
    return result


def product_at(polynomials: list[str], value: F49) -> F49:
    result = F49(1)
    for polynomial in polynomials:
        result = result * evaluate(polynomial, value)
    return result


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1:
        raise CertificateError("schema version mismatch")
    if canonical_sha256(data) != data.get("certificate_sha256"):
        raise CertificateError("digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    shape = data["reducible_shape"]
    if shape["ray_class_group"] != "C4 x C2" or "psi" not in shape["semisimplification"]:
        raise CertificateError("reducible ray-character shape changed")

    at17 = data["order4_exclusion_at17"]
    if at17["ray_coordinate"] != [3, 0] or at17["possible_order4_values"] != ["i", "-i"]:
        raise CertificateError("prime-17 ray data mismatch")
    norm = F49(at17["norm_mod7"])
    for label, psi in (("i", I), ("-i", -I)):
        z = norm * psi + psi.inverse()
        w = z * z - 2 * norm
        products = {
            "generic": product_at(at17["generic_candidate_polynomials"], z),
            "zero": product_at(at17["zero_candidate_polynomials"], w),
            "infinity": product_at(at17["infinity_candidate_polynomials"], w),
            "multiplicative": (z - (norm + 1)) * (z + (norm + 1)),
        }
        expected = at17["products"][label]
        for regime, value in products.items():
            if value.pair() != expected[regime] or value == F49():
                raise CertificateError(
                    f"order-4 character survives at 17 in {label}/{regime}"
                )

    at41 = data["quadratic_trace_at41"]
    norm41 = F49(at41["norm_mod7"])
    for raw in at41["remaining_character_values"]:
        psi = F49(raw)
        z = norm41 * psi + psi.inverse()
        w = z * z - 2 * norm41
        if z != F49(at41["base_trace_mod7_for_both_values"]):
            raise CertificateError("quadratic ray value changed base target at 41")
        if w != F49(at41["full_trace_mod7_for_both_values"]):
            raise CertificateError("quadratic ray value changed full target at 41")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], description: str) -> None:
    data["certificate_sha256"] = canonical_sha256(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {description}")


def self_test() -> None:
    source = load(MANIFEST)
    mutated = copy.deepcopy(source)
    mutated["order4_exclusion_at17"]["generic_candidate_polynomials"][0] = "x"
    expect_rejection(mutated, "an order-4 character surviving the generic regime")

    mutated = copy.deepcopy(source)
    mutated["quadratic_trace_at41"]["norm_mod7"] = 5
    expect_rejection(mutated, "a non-character-independent prime-41 target")

    with tempfile.NamedTemporaryFile("w", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
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
    print("fixed-7 ray-character negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load(MANIFEST))
    print("fixed-7 ray-character control valid")
    print("  prime 17 excludes all order-4 ray characters in every local regime")
    print("  both remaining quadratic values give base/full targets 0/2 at prime 41")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
