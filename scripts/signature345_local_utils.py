#!/usr/bin/env python3
"""Shared exact arithmetic for `(3,4,5)` local-profile diagnostics.

This module reconstructs the 49 Edwards triples and exposes finite-modulus
operations used by the inventory scripts. It deliberately makes no claim that a
reconstructed Table-1 ID equals a later `C_i` label in Siksek--Stoll.
"""

from __future__ import annotations

import pathlib

import check_signature_345_edwards as ed

ROOT = pathlib.Path(__file__).resolve().parents[1]
EDWARDS_MANIFEST = ROOT / "Research" / "Signature345" / "edwards_forms.json"


class LocalArithmeticError(ValueError):
    pass


def reconstruct_triples() -> dict[
    int,
    tuple[
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
    ],
]:
    data = ed.load_json(EDWARDS_MANIFEST)
    ed.validate_data(data)
    triples: dict[
        int,
        tuple[
            ed.HomogeneousPolynomial,
            ed.HomogeneousPolynomial,
            ed.HomogeneousPolynomial,
        ],
    ] = {}
    for entry in data["base_forms"]:
        alpha = [ed.parse_fraction(value) for value in entry["alpha"]]
        triples[entry["id"]] = ed.edwards_covariants(ed.dodecic(alpha))
    for entry in data["derived_variants"]:
        f, g, h = triples[entry["source_id"]]
        if entry["negate_f"]:
            f = f.scale(-1)
        triples[entry["id"]] = (f, g, h)
    if set(triples) != set(range(1, 50)):
        raise LocalArithmeticError("failed to reconstruct exactly 49 Edwards triples")
    return triples


def integral_coefficients(poly: ed.HomogeneousPolynomial) -> tuple[int, ...]:
    if not poly.is_integral():
        raise LocalArithmeticError("local arithmetic received a non-integral form")
    return tuple(coefficient.numerator for coefficient in poly.coefficients)


def eval_ascending(coefficients: tuple[int, ...], x: int, modulus: int) -> int:
    value = 0
    for coefficient in reversed(coefficients):
        value = (value * x + coefficient) % modulus
    return value


def eval_integer(coefficients: tuple[int, ...], x: int) -> int:
    value = 0
    for coefficient in reversed(coefficients):
        value = value * x + coefficient
    return value


def derivative(coefficients: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(i * coefficients[i] for i in range(1, len(coefficients)))


def evaluate_chart_v_unit(
    poly: ed.HomogeneousPolynomial, x: int, modulus: int
) -> int:
    return eval_ascending(integral_coefficients(poly), x, modulus)


def evaluate_chart_u_unit(
    poly: ed.HomogeneousPolynomial, v: int, modulus: int
) -> int:
    return eval_ascending(tuple(reversed(integral_coefficients(poly))), v, modulus)


def valuation(value: int, prime: int, cap: int) -> int:
    value %= prime**cap
    if value == 0:
        return cap
    result = 0
    while result < cap and value % prime == 0:
        result += 1
        value //= prime
    return result


def is_square_mod_prime_power(value: int, prime: int, exponent: int) -> bool:
    modulus = prime**exponent
    value %= modulus
    if value == 0:
        return True
    order = valuation(value, prime, exponent)
    if order % 2:
        return False
    unit = value // (prime**order)
    remaining = exponent - order
    if prime == 2:
        if remaining <= 1:
            return True
        if remaining == 2:
            return unit % 4 == 1
        return unit % 8 == 1
    return pow(unit % prime, (prime - 1) // 2, prime) == 1


def has_primitive_square_point_mod(
    f: ed.HomogeneousPolynomial, prime: int, exponent: int
) -> bool:
    modulus = prime**exponent
    for x in range(modulus):
        if is_square_mod_prime_power(
            evaluate_chart_v_unit(f, x, modulus), prime, exponent
        ):
            return True
    for x in range(prime ** (exponent - 1)):
        v = prime * x
        if is_square_mod_prime_power(
            evaluate_chart_u_unit(f, v, modulus), prime, exponent
        ):
            return True
    return False


def first_obstructing_power(
    f: ed.HomogeneousPolynomial, prime: int, maximum: int
) -> int | None:
    for exponent in range(1, maximum + 1):
        if not has_primitive_square_point_mod(f, prime, exponent):
            return exponent
    return None


def triple_values_chart_v_unit(
    triple: tuple[
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
    ],
    x: int,
    modulus: int,
) -> tuple[int, int, int]:
    return tuple(
        evaluate_chart_v_unit(poly, x, modulus) for poly in triple
    )  # type: ignore[return-value]


def triple_values_chart_u_unit(
    triple: tuple[
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
    ],
    v: int,
    modulus: int,
) -> tuple[int, int, int]:
    return tuple(
        evaluate_chart_u_unit(poly, v, modulus) for poly in triple
    )  # type: ignore[return-value]


def primitive_modulus_set_nonempty(
    triple: tuple[
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
        ed.HomogeneousPolynomial,
    ],
    modulus: int,
) -> bool:
    if modulus != 256:
        raise LocalArithmeticError("the audited primitive modulus must be 256")

    def admissible(values: tuple[int, int, int]) -> bool:
        f_value, _g_value, _h_value = values
        return is_square_mod_prime_power(f_value, 2, 8) and not all(
            value % 2 == 0 for value in values
        )

    for x in range(modulus):
        if admissible(triple_values_chart_v_unit(triple, x, modulus)):
            return True
    for x in range(modulus // 2):
        if admissible(triple_values_chart_u_unit(triple, 2 * x, modulus)):
            return True
    return False
