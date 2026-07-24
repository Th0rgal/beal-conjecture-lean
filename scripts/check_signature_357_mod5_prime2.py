#!/usr/bin/env python3
"""Replay the mod-5 prime-2 character obstruction for signature (3,5,7).

The checker reconstructs the finite-field Jacobi arithmetic over F_64, the
Jacobi-motive Tate factor, the finite-flat unit-signature calculation over
F_125, the class-number-one bound for Q(zeta_7)^+, and the final Frobenius
character contradiction.  Four representation-theoretic inputs remain
explicitly imported and are not disguised as Python computations.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import pathlib
import tempfile
from fractions import Fraction
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "mod5_prime2_obstruction.json"


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


# F_64 = F_2[x]/(x^6+x+1).
GF64_DEGREE = 6
GF64_MODULUS = (1 << 6) | (1 << 1) | 1


def gf64_mul(left: int, right: int) -> int:
    result = 0
    a = left
    b = right
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << GF64_DEGREE):
            a ^= GF64_MODULUS
    return result & ((1 << GF64_DEGREE) - 1)


def gf64_pow(base: int, exponent: int) -> int:
    if exponent < 0:
        if base == 0:
            raise CertificateError("zero has no inverse")
        base = gf64_pow(base, 62)
        exponent = -exponent
    result = 1
    while exponent:
        if exponent & 1:
            result = gf64_mul(result, base)
        base = gf64_mul(base, base)
        exponent >>= 1
    return result


def multiplicative_order_64(value: int) -> int:
    if value == 0:
        raise CertificateError("zero has no multiplicative order")
    for candidate in range(1, 64):
        if gf64_pow(value, candidate) == 1:
            return candidate
    raise CertificateError("failed to compute F64 order")


def discrete_log_table(generator: int) -> dict[int, int]:
    table: dict[int, int] = {}
    current = 1
    for exponent in range(63):
        if current in table:
            raise CertificateError("generator repeated before order 63")
        table[current] = exponent
        current = gf64_mul(current, generator)
    if current != 1 or len(table) != 63:
        raise CertificateError("invalid F64 logarithm table")
    return table


def jacobi_coefficients(
    exponent_a: int, exponent_b: int, logs: dict[int, int]
) -> list[int]:
    """Return coefficients in Z[zeta_21], indexed by powers 0..20."""
    coefficients = [0] * 21
    for value in range(64):
        if value == 0 or value == 1:
            continue
        one_minus = value ^ 1  # characteristic two
        first = logs[value] % 21
        second = logs[one_minus] % 21
        index = (exponent_a * first + exponent_b * second) % 21
        coefficients[index] += 1
    return coefficients


def reduce_monic_polynomial(
    coefficients: list[int], modulus_ascending: list[int]
) -> list[int]:
    if not modulus_ascending or modulus_ascending[-1] != 1:
        raise CertificateError("cyclotomic modulus must be monic")
    out = coefficients[:]
    degree = len(modulus_ascending) - 1
    while len(out) > degree:
        lead_index = len(out) - 1
        lead = out[lead_index]
        if lead:
            shift = lead_index - degree
            for index, coefficient in enumerate(modulus_ascending):
                out[index + shift] -= lead * coefficient
        out.pop()
    out += [0] * (degree - len(out))
    return out


# F_125 = F_5[theta]/(theta^3+theta^2-2theta-1).
F125 = tuple[int, int, int]
F125_ONE: F125 = (1, 0, 0)
F125_THETA: F125 = (0, 1, 0)


def f125_mul(left: F125, right: F125) -> F125:
    raw = [0] * 5
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            raw[i + j] = (raw[i + j] + a * b) % 5
    # theta^3 = 1 + 2 theta - theta^2 = 1+2 theta+4 theta^2.
    for degree in range(4, 2, -1):
        coefficient = raw[degree] % 5
        if coefficient:
            raw[degree] = 0
            shift = degree - 3
            raw[shift] = (raw[shift] + coefficient) % 5
            raw[shift + 1] = (raw[shift + 1] + 2 * coefficient) % 5
            raw[shift + 2] = (raw[shift + 2] + 4 * coefficient) % 5
    return tuple(raw[:3])  # type: ignore[return-value]


def f125_pow(value: F125, exponent: int) -> F125:
    if exponent < 0:
        if value == (0, 0, 0):
            raise CertificateError("zero has no inverse")
        value = f125_pow(value, 123)
        exponent = -exponent
    result = F125_ONE
    base = value
    while exponent:
        if exponent & 1:
            result = f125_mul(result, base)
        base = f125_mul(base, base)
        exponent >>= 1
    return result


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version",
            "status",
            "scope",
            "source_audit",
            "imported_lemmas",
            "finite_fields",
            "trace_certificate",
            "character_certificate",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "research-certificate-with-imported-local-lemmas":
        raise CertificateError("unexpected certificate status")
    if not isinstance(data["imported_lemmas"], list) or len(data["imported_lemmas"]) != 4:
        raise CertificateError("expected exactly four imported lemmas")

    source = data["source_audit"]
    exact_keys(
        source,
        {
            "hypergeometric_paper",
            "inversion",
            "jacobi_motive",
            "finite_monodromy_trace",
            "weight2_normalization",
            "finite_flat_character_input",
        },
        "source_audit",
    )
    if (
        source["hypergeometric_paper"] != "arXiv:2412.08804v2"
        or source["inversion"] != "equation (15)"
        or "equation (30)" not in source["finite_monodromy_trace"]
        or "Q(zeta_21)" not in source["finite_monodromy_trace"]
    ):
        raise CertificateError("source audit metadata mismatch")

    fields = data["finite_fields"]
    exact_keys(fields, {"F64", "F125"}, "finite_fields")
    f64 = fields["F64"]
    exact_keys(
        f64,
        {
            "characteristic",
            "degree",
            "modulus_binary",
            "primitive_element",
            "primitive_order",
            "cyclotomic_order",
            "phi21_ascending",
        },
        "F64",
    )
    if (
        f64["characteristic"] != 2
        or f64["degree"] != 6
        or f64["modulus_binary"] != GF64_MODULUS
        or f64["primitive_element"] != 2
        or f64["primitive_order"] != 63
        or f64["cyclotomic_order"] != 21
    ):
        raise CertificateError("unexpected F64 metadata")
    if multiplicative_order_64(2) != 63:
        raise CertificateError("x is not primitive in the selected F64 model")
    logs = discrete_log_table(2)

    phi21 = f64["phi21_ascending"]
    if phi21 != [1, -1, 0, 1, -1, 0, 1, 0, -1, 1, 0, -1, 1]:
        raise CertificateError("incorrect Phi_21 polynomial")

    trace = data["trace_certificate"]
    exact_keys(
        trace,
        {
            "inverse_parameter",
            "valuation_at_2",
            "unit_reduction",
            "parameters",
            "jacobi_character_exponents",
            "jacobi_values",
            "residue_field_norm",
            "jacobi_motive_factor",
            "normalized_trace",
            "weight2_tate_multiplier",
            "weight2_trace",
            "weight2_trace_mod5",
        },
        "trace_certificate",
    )
    if trace["unit_reduction"] != 1:
        raise CertificateError("the odd unit must reduce to one modulo 2")
    if trace["jacobi_character_exponents"] != [[-4, -10], [-14, 10]]:
        raise CertificateError("unexpected Jacobi character exponents")

    values: list[int] = []
    for exponents in trace["jacobi_character_exponents"]:
        coefficients = jacobi_coefficients(exponents[0], exponents[1], logs)
        reduced = reduce_monic_polynomial(coefficients, phi21)
        if reduced[1:] != [0] * 11:
            raise CertificateError(
                f"Jacobi sum does not reduce to an integer: {reduced}"
            )
        values.append(reduced[0])
    if values != trace["jacobi_values"] or values != [8, 8]:
        raise CertificateError(f"Jacobi values mismatch: {values}")

    q = trace["residue_field_norm"]
    if q != 64:
        raise CertificateError("the full cyclotomic residue field must have norm 64")

    # Definition 2.3 gives
    # J0 = -g(-3)g(3)g(7)g(-7)g(0)/(g(10)g(-10)).
    # In characteristic 2, chi(-1)=1, so g(k)g(-k)=q for k != 0
    # and g(0)=-1. Hence J0=q.
    jacobi_motive_factor = ((-1) * q * q * (-1)) // q
    if jacobi_motive_factor != trace["jacobi_motive_factor"] or jacobi_motive_factor != q:
        raise CertificateError("Jacobi-motive Tate factor mismatch")

    normalized_trace = -Fraction(sum(values), jacobi_motive_factor)
    if normalized_trace != Fraction(trace["normalized_trace"]):
        raise CertificateError(f"normalized trace mismatch: {normalized_trace}")
    multiplier = trace["weight2_tate_multiplier"]
    if multiplier != q:
        raise CertificateError("unexpected weight-2 Tate multiplier")
    weight2_trace = multiplier * normalized_trace
    if weight2_trace.denominator != 1 or weight2_trace.numerator != trace["weight2_trace"]:
        raise CertificateError("weight-2 trace mismatch")
    if weight2_trace.numerator % 5 != trace["weight2_trace_mod5"]:
        raise CertificateError("weight-2 residual trace mismatch")

    f125 = fields["F125"]
    exact_keys(
        f125,
        {
            "characteristic",
            "degree",
            "minimal_polynomial_ascending",
            "theta_order",
        },
        "F125",
    )
    if (
        f125["characteristic"] != 5
        or f125["degree"] != 3
        or f125["minimal_polynomial_ascending"] != [4, 3, 1, 1]
    ):
        raise CertificateError("unexpected F125 metadata")
    if any((a**3 + a**2 + 3 * a + 4) % 5 == 0 for a in range(5)):
        raise CertificateError("selected cubic is reducible over F5")
    if f125_pow(F125_THETA, 31) != F125_ONE or F125_THETA == F125_ONE:
        raise CertificateError("theta does not have order 31")
    if f125["theta_order"] != 31:
        raise CertificateError("unexpected theta order metadata")

    character = data["character_certificate"]
    exact_keys(
        character,
        {
            "inertia_killing_exponent",
            "unit_signature_weights",
            "allowed_signatures",
            "minkowski_numerator",
            "minkowski_denominator",
            "class_number_conclusion",
            "K7_prime_2_norm",
            "F_over_K_residue_degree",
            "reducible_full_field_equation",
            "forced_v_mod5",
            "required_v_power",
            "actual_v_power_mod5",
        },
        "character_certificate",
    )
    if character["inertia_killing_exponent"] != 84:
        raise CertificateError("inertia exponent must equal lcm(12,28)=84")
    weights = character["unit_signature_weights"]
    allowed = [
        list(signature)
        for signature in itertools.product((0, 1), repeat=3)
        if (84 * sum(s * w for s, w in zip(signature, weights))) % 31 == 0
    ]
    if allowed != character["allowed_signatures"] or allowed != [[0, 0, 0], [1, 1, 1]]:
        raise CertificateError(f"finite-flat signatures mismatch: {allowed}")

    if not (
        character["minkowski_numerator"] == 42
        and character["minkowski_denominator"] == 27
        and Fraction(42, 27) < 2
        and character["class_number_conclusion"] == 1
    ):
        raise CertificateError("Minkowski class-number certificate mismatch")
    if character["K7_prime_2_norm"] != 8 or character["F_over_K_residue_degree"] != 2:
        raise CertificateError("prime-2 residue-degree metadata mismatch")

    trace_mod5 = trace["weight2_trace_mod5"]
    determinant_mod5 = (character["K7_prime_2_norm"] ** 2) % 5
    roots = [
        value
        for value in range(1, 5)
        if (value * value - trace_mod5 * value + determinant_mod5) % 5 == 0
    ]
    if roots != [2]:
        raise CertificateError(f"unexpected reducible Frobenius roots: {roots}")
    forced_v = roots[0]
    if forced_v != character["forced_v_mod5"]:
        raise CertificateError("forced v metadata mismatch")
    required_power = 84 // character["F_over_K_residue_degree"]
    if required_power != character["required_v_power"]:
        raise CertificateError("required v power mismatch")
    actual_power = pow(forced_v, required_power, 5)
    if actual_power != character["actual_v_power_mod5"] or actual_power == 1:
        raise CertificateError("the final character contradiction was not obtained")

    expected_sha = data["certificate_sha256"]
    actual_sha = canonical_sha256(data)
    if expected_sha != actual_sha:
        raise CertificateError(
            f"certificate digest mismatch: expected {expected_sha}, got {actual_sha}"
        )
    return actual_sha


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["trace_certificate"]["jacobi_values"][0] = 7
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated Jacobi sum")

    mutated = copy.deepcopy(base)
    mutated["character_certificate"]["allowed_signatures"] = [[0, 0, 0]]
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted an incomplete signature list")

    mutated = copy.deepcopy(base)
    mutated["character_certificate"]["required_v_power"] = 6
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a weakened character contradiction")

    duplicate = '{"schema_version":1,"schema_version":1}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write(duplicate)
        path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted a duplicate JSON key")
    finally:
        path.unlink(missing_ok=True)

    print("mod-5 prime-2 negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.manifest))
    print("mod-5 prime-2 obstruction certificate valid")
    print(f"certificate sha256: {digest}")
    print("conclusion (conditional on imported local lemmas): absolute irreducibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
