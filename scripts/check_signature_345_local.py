#!/usr/bin/env python3
"""Replay the sequential local eliminations in Section 5 of Siksek--Stoll.

The checker reconstructs all 49 Edwards triples and follows Lemma 5.1 in its
printed order:

1. eliminate the 16 listed curves with no Q_2-point;
2. among the remaining curves, eliminate the two listed curves with no Q_3-point;
3. among those still remaining, eliminate the eight listed indices whose U_i is
   empty modulo 256;
4. verify that the complement is exactly the printed 23-index set I.

No CAS is used. Absence modulo p^k is a rigorous local obstruction because any
Q_p-point on the weighted-projective curve can be scaled so u,v are p-integral
and not both divisible by p.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import tempfile
from typing import Any

import check_signature_345_edwards as ed

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature345" / "local_obstructions.json"
EDWARDS_MANIFEST = ROOT / "Research" / "Signature345" / "edwards_forms.json"


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
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(data, dict):
        raise CertificateError("manifest root must be an object")
    return data


def require_exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


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
        raise CertificateError("failed to reconstruct exactly 49 Edwards triples")
    return triples


def integral_coefficients(poly: ed.HomogeneousPolynomial) -> tuple[int, ...]:
    if not poly.is_integral():
        raise CertificateError("local checker received a non-integral form")
    return tuple(coefficient.numerator for coefficient in poly.coefficients)


def eval_ascending(coefficients: tuple[int, ...], x: int, modulus: int) -> int:
    value = 0
    for coefficient in reversed(coefficients):
        value = (value * x + coefficient) % modulus
    return value


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

    # Chart v a unit: scale to (u:v)=(x:1). Since deg(f)=30 is even,
    # unit scaling changes f by a square.
    for x in range(modulus):
        if is_square_mod_prime_power(
            evaluate_chart_v_unit(f, x, modulus), prime, exponent
        ):
            return True

    # Chart u a unit and v divisible by p: scale to (1:p*x).
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
        raise CertificateError("the audited primitive modulus must be 256")

    def admissible(values: tuple[int, int, int]) -> bool:
        f_value, _g_value, _h_value = values
        return is_square_mod_prime_power(f_value, 2, 8) and not all(
            value % 2 == 0 for value in values
        )

    # The two projective charts cover all pairs not both even. Pairs both even
    # are automatically outside U_i because f,g,h are then all even.
    for x in range(modulus):
        if admissible(triple_values_chart_v_unit(triple, x, modulus)):
            return True
    for x in range(modulus // 2):
        if admissible(triple_values_chart_u_unit(triple, 2 * x, modulus)):
            return True
    return False


def validate_data(data: dict[str, Any]) -> tuple[dict[int, int], dict[int, int]]:
    require_exact_keys(
        data, {"schema_version", "source", "search_bounds", "expected"}, "manifest"
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise CertificateError("schema_version must be the integer 1")

    source = data["source"]
    require_exact_keys(source, {"arxiv", "section", "lemma"}, "source")
    if source != {"arxiv": "1103.1979v1", "section": "5", "lemma": "5.1"}:
        raise CertificateError("unexpected source metadata")

    bounds = data["search_bounds"]
    require_exact_keys(
        bounds,
        {"max_2_adic_power", "max_3_adic_power", "primitive_modulus"},
        "search_bounds",
    )
    if (
        type(bounds["max_2_adic_power"]) is not int
        or bounds["max_2_adic_power"] < 1
        or type(bounds["max_3_adic_power"]) is not int
        or bounds["max_3_adic_power"] < 1
        or bounds["primitive_modulus"] != 256
    ):
        raise CertificateError("invalid search bounds")

    expected = data["expected"]
    require_exact_keys(
        expected,
        {"no_Q2", "no_Q3", "primitive_mod_256_empty", "surviving_indices"},
        "expected",
    )
    for name in expected:
        if not isinstance(expected[name], list) or any(
            type(value) is not int for value in expected[name]
        ):
            raise CertificateError(f"expected.{name} must be an integer array")
        if expected[name] != sorted(set(expected[name])):
            raise CertificateError(f"expected.{name} must be sorted and duplicate-free")

    expected_q2 = set(expected["no_Q2"])
    expected_q3 = set(expected["no_Q3"])
    expected_u = set(expected["primitive_mod_256_empty"])
    expected_survivors = set(expected["surviving_indices"])
    if expected_q2 & expected_q3 or expected_q2 & expected_u or expected_q3 & expected_u:
        raise CertificateError("the printed sequential elimination sets must be disjoint")
    if expected_survivors != set(range(1, 50)) - expected_q2 - expected_q3 - expected_u:
        raise CertificateError("surviving_indices is not the exact complement")

    triples = reconstruct_triples()
    q2_powers: dict[int, int] = {}
    q3_powers: dict[int, int] = {}

    actual_q2: set[int] = set()
    for form_id, (f, _g, _h) in triples.items():
        q2 = first_obstructing_power(f, 2, bounds["max_2_adic_power"])
        if q2 is not None:
            actual_q2.add(form_id)
            q2_powers[form_id] = q2
    if actual_q2 != expected_q2:
        raise CertificateError(
            f"2-adic obstruction set mismatch: expected {sorted(expected_q2)}, "
            f"got {sorted(actual_q2)}"
        )

    after_q2 = set(range(1, 50)) - actual_q2
    actual_q3: set[int] = set()
    for form_id in sorted(after_q2):
        f = triples[form_id][0]
        q3 = first_obstructing_power(f, 3, bounds["max_3_adic_power"])
        if q3 is not None:
            actual_q3.add(form_id)
            q3_powers[form_id] = q3
    if actual_q3 != expected_q3:
        raise CertificateError(
            f"sequential 3-adic obstruction mismatch: expected {sorted(expected_q3)}, "
            f"got {sorted(actual_q3)}"
        )

    after_local = after_q2 - actual_q3
    actual_u = {
        form_id
        for form_id in after_local
        if not primitive_modulus_set_nonempty(
            triples[form_id], bounds["primitive_modulus"]
        )
    }
    if actual_u != expected_u:
        raise CertificateError(
            f"sequential mod-256 obstruction mismatch: expected {sorted(expected_u)}, "
            f"got {sorted(actual_u)}"
        )

    actual_survivors = after_local - actual_u
    if actual_survivors != expected_survivors:
        raise CertificateError("replayed survivor set does not match Lemma 5.1")

    return q2_powers, q3_powers


def validate(path: pathlib.Path) -> tuple[dict[int, int], dict[int, int]]:
    return validate_data(load_json(path))


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = json.loads(json.dumps(base))
    mutated["expected"]["no_Q2"].remove(1)
    try:
        validate_data(mutated)
    except (CertificateError, ed.CertificateError):
        pass
    else:
        raise RuntimeError("checker accepted a weakened 2-adic obstruction set")

    mutated = json.loads(json.dumps(base))
    mutated["expected"]["primitive_mod_256_empty"][0] = 6
    try:
        validate_data(mutated)
    except (CertificateError, ed.CertificateError):
        pass
    else:
        raise RuntimeError("checker accepted a mutated mod-256 obstruction set")

    duplicate = '{"schema_version":1,"schema_version":1}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write(duplicate)
        duplicate_path = pathlib.Path(handle.name)
    try:
        try:
            load_json(duplicate_path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        duplicate_path.unlink(missing_ok=True)

    print("signature (3,4,5) local negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    q2_powers, q3_powers = validate(args.manifest)
    print("signature (3,4,5) local obstruction certificate passed")
    print(f"  no Q_2: {sorted(q2_powers)}")
    print(f"  first obstructing powers of 2: {q2_powers}")
    print(f"  no Q_3 after the Q_2 stage: {sorted(q3_powers)}")
    print(f"  first obstructing powers of 3: {q3_powers}")
    print("  primitive mod-256 exclusions: [7, 8, 12, 19, 21, 22, 30, 34]")
    print("  surviving curve count: 23")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
