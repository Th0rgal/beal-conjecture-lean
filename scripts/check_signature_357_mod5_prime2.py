#!/usr/bin/env python3
"""Replay the parity-complete mod-5 prime-2 obstruction for signature (3,5,7).

For a primitive solution A^3+B^5=C^7 with B odd, exactly one of A,C is even.
The plus HGM H((1/7,-1/7),(1/3,-1/3)|C^7/A^3) is therefore in the
zero or infinity degeneration at 2. The checker reconstructs both exact Jacobi
traces over F_64, the finite-flat unit-signature calculation over F_125, the
class-number-one argument for Q(zeta_7)^+, and the resulting absolute
irreducibility contradiction.

Five representation-theoretic inputs are kept explicit in the manifest; this
program checks their arithmetic consequences but does not reprove them.
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
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
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
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


# F_64 = F_2[x]/(x^6+x+1).
GF64_DEGREE = 6
GF64_MODULUS = (1 << 6) | (1 << 1) | 1


def gf64_mul(left: int, right: int) -> int:
    result = 0
    a, b = left, right
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << GF64_DEGREE):
            a ^= GF64_MODULUS
    return result & 63


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
    """Ordinary Jacobi sum in Z[zeta_21], indexed by powers 0..20."""
    coefficients = [0] * 21
    for value in range(64):
        if value in (0, 1):
            continue
        one_minus = value ^ 1
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


def add_polynomials(values: list[list[int]]) -> list[int]:
    if not values:
        raise CertificateError("empty polynomial sum")
    length = len(values[0])
    if any(len(value) != length for value in values):
        raise CertificateError("incompatible polynomial lengths")
    return [sum(value[index] for value in values) for index in range(length)]


def scalar_polynomial(value: list[int]) -> int:
    if value[1:] != [0] * (len(value) - 1):
        raise CertificateError(f"expected rational integer in Q(zeta_21), got {value}")
    return value[0]


# F_125 = F_5[theta]/(theta^3+theta^2-2theta-1).
F125 = tuple[int, int, int]
F125_ONE: F125 = (1, 0, 0)
F125_THETA: F125 = (0, 1, 0)


def f125_mul(left: F125, right: F125) -> F125:
    raw = [0] * 5
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            raw[i + j] = (raw[i + j] + a * b) % 5
    # theta^3 = 1+2*theta-theta^2.
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


def verify_trace_branch(
    branch: dict[str, Any], logs: dict[int, int], phi21: list[int], q: int
) -> tuple[int, int]:
    exact_keys(
        branch,
        {
            "name",
            "parity_condition",
            "parameter_behavior",
            "formula",
            "jacobi_character_exponents",
            "expected_jacobi_sum",
            "weight2_trace",
            "weight2_trace_mod5",
        },
        "trace branch",
    )
    exponents = branch["jacobi_character_exponents"]
    if not isinstance(exponents, list) or len(exponents) != 2:
        raise CertificateError("each degeneration must contain two Jacobi sums")
    reduced = [
        reduce_monic_polynomial(
            jacobi_coefficients(pair[0], pair[1], logs), phi21
        )
        for pair in exponents
    ]
    total = add_polynomials(reduced)
    if total != branch["expected_jacobi_sum"]:
        raise CertificateError(f"{branch['name']} Jacobi sum mismatch: {total}")
    integer_sum = scalar_polynomial(total)
    # Formula (30) or (31): outer Jacobi factor q, followed by the weight-two
    # Tate multiplier q, so the integral weight-two trace is -integer_sum.
    normalized = -Fraction(integer_sum, q)
    weight2_trace = q * normalized
    if (
        weight2_trace.denominator != 1
        or weight2_trace.numerator != branch["weight2_trace"]
    ):
        raise CertificateError(f"{branch['name']} weight-two trace mismatch")
    if weight2_trace.numerator % 5 != branch["weight2_trace_mod5"]:
        raise CertificateError(f"{branch['name']} residual trace mismatch")
    return weight2_trace.numerator, weight2_trace.numerator % 5


def validate(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
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
            "conclusion",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 2:
        raise CertificateError("schema_version must equal 2")
    if data["status"] != "research-certificate-with-imported-local-lemmas":
        raise CertificateError("unexpected certificate status")
    if not isinstance(data["imported_lemmas"], list) or len(data["imported_lemmas"]) != 5:
        raise CertificateError("expected exactly five imported lemmas")

    scope = data["scope"]
    exact_keys(
        scope,
        {
            "equation",
            "hypotheses",
            "orientation",
            "parameter",
            "field",
            "residual_prime",
            "claim",
        },
        "scope",
    )
    if scope != {
        "equation": "A^3+B^5=C^7",
        "hypotheses": ["pairwise coprime positive A,B,C", "B odd"],
        "orientation": "(-C)^7+B^5+A^3=0",
        "parameter": "t=C^7/A^3",
        "field": "K7=Q(zeta_7)^+",
        "residual_prime": 5,
        "claim": "the plus mod-5 HGM representation is absolutely irreducible",
    }:
        raise CertificateError("scope metadata mismatch")
    parity_cases = sorted((A, (A + 1) % 2) for A in (0, 1))
    if parity_cases != [(0, 1), (1, 0)]:
        raise CertificateError("B-odd parity cover failed")

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
        or source["inversion"]
        != "equation (15), which swaps the two parameter pairs"
        or "formulas (30) and (31)" not in source["finite_monodromy_trace"]
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

    f125 = fields["F125"]
    exact_keys(
        f125,
        {"characteristic", "degree", "minimal_polynomial_ascending", "theta_order"},
        "F125",
    )
    if f125 != {
        "characteristic": 5,
        "degree": 3,
        "minimal_polynomial_ascending": [4, 3, 1, 1],
        "theta_order": 31,
    }:
        raise CertificateError("unexpected F125 metadata")
    if any((a**3 + a**2 + 3 * a + 4) % 5 == 0 for a in range(5)):
        raise CertificateError("selected cubic is reducible over F5")
    if f125_pow(F125_THETA, 31) != F125_ONE or F125_THETA == F125_ONE:
        raise CertificateError("theta does not have exact order 31")

    trace = data["trace_certificate"]
    exact_keys(
        trace,
        {
            "residue_field_norm",
            "jacobi_motive_factor",
            "weight2_tate_multiplier",
            "branches",
        },
        "trace_certificate",
    )
    q = trace["residue_field_norm"]
    if (
        q != 64
        or trace["jacobi_motive_factor"] != q
        or trace["weight2_tate_multiplier"] != q
    ):
        raise CertificateError("prime-2 normalization metadata mismatch")
    branches = trace["branches"]
    if not isinstance(branches, list) or len(branches) != 2:
        raise CertificateError("expected zero and infinity branches")
    expected_branch_headers = [
        (
            "zero",
            "A odd and C even",
            "v_2(t)>0",
            "formula (30)",
            [[-4, -10], [-14, 10]],
        ),
        (
            "infinity",
            "A even and C odd",
            "v_2(t)<0",
            "formula (31)",
            [[-4, 10], [6, -10]],
        ),
    ]
    results: dict[str, int] = {}
    residual_results: dict[str, int] = {}
    for branch, header in zip(branches, expected_branch_headers):
        name, parity, behavior, formula, exponents = header
        if (
            branch["name"] != name
            or branch["parity_condition"] != parity
            or branch["parameter_behavior"] != behavior
            or branch["formula"] != formula
            or branch["jacobi_character_exponents"] != exponents
        ):
            raise CertificateError(f"{name} branch metadata mismatch")
        integral, residual = verify_trace_branch(branch, logs, phi21, q)
        results[name] = integral
        residual_results[name] = residual
    if results != {"zero": -16, "infinity": 9} or set(residual_results.values()) != {4}:
        raise CertificateError(f"unexpected parity-complete traces: {results}")

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
            "full_field_determinant_mod5",
            "forced_full_field_eigenvalue_mod5",
            "required_eigenvalue_power",
            "actual_eigenvalue_power_mod5",
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
    if allowed != [[0, 0, 0], [1, 1, 1]] or character["allowed_signatures"] != allowed:
        raise CertificateError(f"finite-flat signatures mismatch: {allowed}")
    if not (
        character["minkowski_numerator"] == 42
        and character["minkowski_denominator"] == 27
        and Fraction(42, 27) < 2
        and character["class_number_conclusion"] == 1
    ):
        raise CertificateError("Minkowski class-number certificate mismatch")
    if (
        character["K7_prime_2_norm"] != 8
        or character["F_over_K_residue_degree"] != 2
    ):
        raise CertificateError("prime-2 residue-degree metadata mismatch")
    determinant = (
        character["K7_prime_2_norm"] ** character["F_over_K_residue_degree"]
    ) % 5
    if determinant != 4 or character["full_field_determinant_mod5"] != determinant:
        raise CertificateError("full-field determinant must be 64=4 mod5")
    # Both branches have full-field trace 4 mod5, so a reducible characteristic
    # polynomial is X^2-4X+4=(X-2)^2 over the algebraic closure.
    roots = [
        value
        for value in range(5)
        if (value * value - 4 * value + determinant) % 5 == 0
    ]
    if roots != [2] or character["forced_full_field_eigenvalue_mod5"] != 2:
        raise CertificateError(f"unexpected forced full-field eigenvalue: {roots}")
    required_power = 84 // character["F_over_K_residue_degree"]
    actual_power = pow(2, required_power, 5)
    if (
        character["required_eigenvalue_power"] != required_power
        or required_power != 42
    ):
        raise CertificateError("required eigenvalue power must be 42")
    if (
        character["actual_eigenvalue_power_mod5"] != actual_power
        or actual_power != 4
    ):
        raise CertificateError("the character contradiction 2^42=-1 was not obtained")

    expected_conclusion = {
        "mod5": "B odd implies the residual mod-5 plus HGM is absolutely irreducible",
        "parity_cover": "B even implies A and C odd, hence C odd and the independent fixed-7 irreducibility theorem applies; every primitive solution has at least one absolutely irreducible Frey representation",
    }
    if data["conclusion"] != expected_conclusion:
        raise CertificateError("conclusion metadata mismatch")

    actual_sha = canonical_sha256(data)
    if data["certificate_sha256"] != actual_sha:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {actual_sha}"
        )
    return actual_sha, {
        "weight2_traces": results,
        "residual_trace": 4,
        "allowed_signatures": allowed,
        "forced_eigenvalue": 2,
        "forced_power": actual_power,
    }


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)
    mutations = [
        lambda data: data["trace_certificate"]["branches"][1].__setitem__(
            "weight2_trace", 8
        ),
        lambda data: data["trace_certificate"]["branches"][1][
            "jacobi_character_exponents"
        ].__setitem__(0, [-4, -10]),
        lambda data: data["character_certificate"].__setitem__(
            "allowed_signatures", [[0, 0, 0]]
        ),
        lambda data: data["conclusion"].__setitem__("mod5", "Beal is proved"),
    ]
    for mutate in mutations:
        data = copy.deepcopy(base)
        mutate(data)
        try:
            validate(data)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted a mutated certificate")
    duplicate = '{"schema_version":2,"schema_version":2}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write(duplicate)
        path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)
    print("mod-5 prime-2 parity-cover negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest, details = validate(load_json(args.manifest))
    print("mod-5 prime-2 parity-complete certificate valid")
    print(f"certificate sha256: {digest}")
    print(json.dumps(details, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
