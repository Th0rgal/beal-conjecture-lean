#!/usr/bin/env python3
"""Replay the finite arithmetic in the fixed-7 ray/Hasse dichotomy.

This checker verifies the pinned candidate-polynomial products modulo 7, the
ray-class coordinates in Q(sqrt(5)), the nodal splitting character at t=1,
and the three Hasse--Witt matrices at the residual prime 7.

It deliberately does not prove the imported reducible-character shape,
local-trace exhaustiveness, finite-flat full-faithfulness statement, or
compatible-system local-type transfer.  Those are explicit expert-audit
inputs outside BealUnified.Trusted.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "ray_hasse_dichotomy.json"
P = 7


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("manifest root must be an object")
    return value


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class F49:
    """a+b*i in F_7[i], i^2=-1."""

    a: int = 0
    b: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "a", self.a % P)
        object.__setattr__(self, "b", self.b % P)

    @staticmethod
    def coerce(value: object) -> "F49":
        if isinstance(value, F49):
            return value
        if type(value) is not int:
            raise TypeError(f"cannot coerce {value!r} to F49")
        return F49(value, 0)

    def __add__(self, other: object) -> "F49":
        other = self.coerce(other)
        return F49(self.a + other.a, self.b + other.b)

    __radd__ = __add__

    def __neg__(self) -> "F49":
        return F49(-self.a, -self.b)

    def __sub__(self, other: object) -> "F49":
        return self + (-self.coerce(other))

    def __rsub__(self, other: object) -> "F49":
        return self.coerce(other) - self

    def __mul__(self, other: object) -> "F49":
        other = self.coerce(other)
        return F49(
            self.a * other.a - self.b * other.b,
            self.a * other.b + self.b * other.a,
        )

    __rmul__ = __mul__

    def __pow__(self, exponent: int) -> "F49":
        if type(exponent) is not int:
            raise TypeError("exponent must be an integer")
        if exponent < 0:
            return self.inverse() ** (-exponent)
        result = F49(1)
        base = self
        while exponent:
            if exponent & 1:
                result = result * base
            base = base * base
            exponent >>= 1
        return result

    def inverse(self) -> "F49":
        denominator = (self.a * self.a + self.b * self.b) % P
        if denominator == 0:
            raise ZeroDivisionError("division by zero in F49")
        inv = pow(denominator, -1, P)
        return F49(self.a * inv, -self.b * inv)

    def as_json(self) -> list[int]:
        return [self.a, self.b]


I = F49(0, 1)


# A univariate polynomial is stored as degree -> integer coefficient.
def parse_polynomial(text: str) -> dict[int, int]:
    compact = text.replace(" ", "").replace("-", "+-")
    if compact.startswith("+"):
        compact = compact[1:]
    terms: dict[int, int] = {}
    for token in compact.split("+"):
        if not token:
            continue
        if "x^2" in token:
            degree = 2
            coefficient = token.replace("*x^2", "").replace("x^2", "")
        elif "x" in token:
            degree = 1
            coefficient = token.replace("*x", "").replace("x", "")
        else:
            degree = 0
            coefficient = token
        if coefficient in {"", "+"}:
            value = 1
        elif coefficient == "-":
            value = -1
        else:
            value = int(coefficient)
        terms[degree] = terms.get(degree, 0) + value
    if not terms:
        raise CertificateError(f"empty polynomial: {text!r}")
    return terms


def parse_polynomial_list(text: str) -> list[dict[int, int]]:
    return [parse_polynomial(piece) for piece in text.split(",") if piece.strip()]


def evaluate(poly: dict[int, int], value: F49) -> F49:
    result = F49(0)
    for degree in range(max(poly), -1, -1):
        result = result * value + poly.get(degree, 0)
    return result


def product_at(polys: list[dict[int, int]], value: F49) -> F49:
    result = F49(1)
    for poly in polys:
        result = result * evaluate(poly, value)
    return result


CANDIDATES: dict[int, tuple[int, list[dict[int, int]], list[dict[int, int]], list[dict[int, int]]]] = {
    11: (
        1,
        parse_polynomial_list(
            "x+5,x-2,x^2-5,x^2+4*x-1,x^2+3*x+1,x^2-x-1,"
            "x^2+x-11,x^2+2*x-19,x^2+5*x-5"
        ),
        parse_polynomial_list(
            "x^2-4*x-316,x^2+x-101,x^2-19*x-61,"
            "x^2-19*x+59,x^2+41*x+419"
        ),
        parse_polynomial_list("x+22"),
    ),
    13: (
        2,
        parse_polynomial_list(
            "x-7,x+14,x-10,x+15,x-20,x+10,x,x+3,x+8,x+10,x-11"
        ),
        parse_polynomial_list("x+338"),
        parse_polynomial_list("x-338,x+169"),
    ),
    17: (
        2,
        parse_polynomial_list(
            "x+31,x+10,x+17,x+7,x+15,x+2,x-20,x+6,x+11,"
            "x-23,x-18,x+20,x-28,x+20,x-20"
        ),
        parse_polynomial_list("x+578"),
        parse_polynomial_list("x+382"),
    ),
    19: (
        1,
        parse_polynomial_list(
            "x^2+7*x+1,x^2+4*x-16,x^2+11*x+29,x^2+6*x+4,"
            "x^2-6*x-11,x^2+7*x+11,x^2+9*x+9,x^2-4*x-1,"
            "x^2-2*x-4,x^2-x-1,x^2+2*x-19,x^2+9*x+19,"
            "x^2-5*x-25,x^2+4*x-1,x^2+3*x+1,x-5,x^2+2*x-19"
        ),
        parse_polynomial_list("x+38"),
        parse_polynomial_list("x+22,x^2-22*x-599"),
    ),
    71: (
        1,
        parse_polynomial_list(
            "x^2-9*x-131,x^2+25*x+155,x^2-11*x+19,x^2+13*x+31,"
            "x^2+6*x+4,x^2+3*x-99,x^2-8*x+11,x^2+10*x-100,"
            "x^2-8*x-29,x^2-14*x+29,x^2+20*x+95,x^2-15*x+55,"
            "x-6,x-2,x^2-245,x^2+5*x-5,x^2-26*x+164,x^2+7*x-49,"
            "x^2+9*x-81,x^2-45,x^2+15*x+25,x^2+6*x-71,x+1,"
            "x^2+16*x+59,x^2-x-61,x^2-6*x-11,x-4,x^2-12*x+31,"
            "x^2+15*x+25,x^2-5*x-5,x^2-4*x-41,x^2+10*x-55,"
            "x^2-4*x-1,x^2-20*x+95,x+7,x^2-18*x+76,x^2+11*x-1,"
            "x^2+3*x-29,x+11,x+7,x^2-x-31,x^2-8*x-4,x^2-7*x+1,"
            "x-1,x^2+3*x+1,x^2+4*x-76,x+4,x^2+6*x-36,"
            "x^2-14*x+44,x^2-2*x-4,x^2-9*x-81,x^2+18*x+76,"
            "x^2+15*x+45,x^2-x-11,x^2+19*x+59,x^2+6*x+4,"
            "x^2+13*x-19,x^2+25*x+145,x^2-5*x-95,x^2+15*x+45,"
            "x^2-18*x+76,x^2-80,x^2-10*x+5,x^2+2*x-179,"
            "x^2+24*x+139,x^2+4*x-121,x^2+7*x+1,x^2-3*x-29,"
            "x^2+10*x-55"
        ),
        parse_polynomial_list(
            "x^2-59*x-11381,x^2+41*x-10861,x^2-19*x-61,"
            "x^2-199*x+8699,x^2+236*x+13604"
        ),
        parse_polynomial_list("x+142"),
    ),
}


def candidate_products(prime: int, psi: F49) -> tuple[F49, F49, F49, F49]:
    residue_degree, generic, at_zero, at_infinity = CANDIDATES[prime]
    norm = F49(prime**residue_degree)
    z = norm * psi + psi.inverse()
    w = z * z - 2 * norm
    return (
        product_at(generic, z),
        product_at(at_zero, w),
        product_at(at_infinity, w),
        (z - (norm + 1)) * (z + (norm + 1)),
    )

