#!/usr/bin/env python3
"""Replay the prime-2 mod-5 obstruction for every B-odd (3,5,7) solution.

This extends the existing A-even certificate to the complementary C-even
parameter degeneration. The finite arithmetic is independently replayed; the
finite-flat and local-global compatibility statements remain explicit imported
lemmas.
"""
from __future__ import annotations

import argparse
import copy
import itertools
import pathlib
import tempfile
from fractions import Fraction
from typing import Any

import check_signature_357_mod5_prime2 as base

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "mod5_prime2_b_odd.json"
CertificateError = base.CertificateError


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return base.load_json(path)


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version", "status", "scope", "imported_lemmas",
            "finite_fields", "trace_branches", "character_certificate",
            "parity_certificate", "literature_corollary", "source_audit",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "research-certificate-with-imported-local-lemmas":
        raise CertificateError("unexpected status")

    scope = data["scope"]
    exact_keys(
        scope,
        {"equation", "hypotheses", "orientation", "field", "residual_prime", "claim"},
        "scope",
    )
    if scope["equation"] != "A^3+B^5=C^7" or scope["residual_prime"] != 5:
        raise CertificateError("scope metadata mismatch")
    if scope["hypotheses"] != ["pairwise coprime positive A,B,C", "B odd"]:
        raise CertificateError("the certificate must cover exactly the B-odd branch")
    if not isinstance(data["imported_lemmas"], list) or len(data["imported_lemmas"]) != 4:
        raise CertificateError("expected four explicit imported lemmas")

    fields = data["finite_fields"]
    exact_keys(fields, {"F64", "F125"}, "finite_fields")
    f64 = fields["F64"]
    exact_keys(
        f64,
        {
            "characteristic", "degree", "modulus_binary", "primitive_element",
            "primitive_order", "cyclotomic_order", "phi21_ascending",
        },
        "F64",
    )
    if (
        f64["characteristic"] != 2
        or f64["degree"] != 6
        or f64["modulus_binary"] != base.GF64_MODULUS
        or f64["primitive_element"] != 2
        or f64["primitive_order"] != 63
        or f64["cyclotomic_order"] != 21
        or f64["phi21_ascending"]
        != [1, -1, 0, 1, -1, 0, 1, 0, -1, 1, 0, -1, 1]
    ):
        raise CertificateError("F64 metadata mismatch")
    if base.multiplicative_order_64(2) != 63:
        raise CertificateError("selected F64 generator is not primitive")
    logs = base.discrete_log_table(2)

    f125 = fields["F125"]
    exact_keys(
        f125,
        {"characteristic", "degree", "minimal_polynomial_ascending", "theta_order"},
        "F125",
    )
    if (
        f125["characteristic"] != 5
        or f125["degree"] != 3
        or f125["minimal_polynomial_ascending"] != [4, 3, 1, 1]
        or f125["theta_order"] != 31
    ):
        raise CertificateError("F125 metadata mismatch")
    if base.f125_pow(base.F125_THETA, 31) != base.F125_ONE:
        raise CertificateError("theta does not have order dividing 31")
    if base.F125_THETA == base.F125_ONE:
        raise CertificateError("theta is trivial")

    branches = data["trace_branches"]
    exact_keys(branches, {"C_even", "A_even"}, "trace_branches")
    expected_integer_traces = {"C_even": 9, "A_even": -16}
    integer_traces: dict[str, int] = {}
    for name, branch in branches.items():
        exact_keys(
            branch,
            {
                "parameter", "valuation_at_2", "unit_reduction", "parameters",
                "jacobi_character_exponents", "jacobi_reduced_phi21",
                "jacobi_sum_reduced_phi21", "jacobi_motive_factor",
                "normalized_trace", "weight2_tate_multiplier", "weight2_trace",
                "weight2_trace_mod5",
            },
            f"trace_branches.{name}",
        )
        if branch["unit_reduction"] != 1:
            raise CertificateError(f"{name}: the odd unit must reduce to 1")
        vectors = []
        for pair in branch["jacobi_character_exponents"]:
            if not isinstance(pair, list) or len(pair) != 2:
                raise CertificateError(f"{name}: malformed Jacobi exponent pair")
            coefficients = base.jacobi_coefficients(pair[0], pair[1], logs)
            vectors.append(
                base.reduce_monic_polynomial(coefficients, f64["phi21_ascending"])
            )
        if vectors != branch["jacobi_reduced_phi21"]:
            raise CertificateError(f"{name}: Jacobi reduction mismatch: {vectors}")
        summed = [sum(vector[i] for vector in vectors) for i in range(12)]
        if summed != branch["jacobi_sum_reduced_phi21"]:
            raise CertificateError(f"{name}: Jacobi sum mismatch: {summed}")
        if any(summed[1:]):
            raise CertificateError(f"{name}: total Jacobi trace is not rational")
        if branch["jacobi_motive_factor"] != 64:
            raise CertificateError(f"{name}: Jacobi-motive factor must be 64")
        normalized = -Fraction(summed[0], branch["jacobi_motive_factor"])
        if normalized != Fraction(branch["normalized_trace"]):
            raise CertificateError(f"{name}: normalized trace mismatch")
        if branch["weight2_tate_multiplier"] != 64:
            raise CertificateError(f"{name}: Tate multiplier must equal 64")
        weight2 = normalized * branch["weight2_tate_multiplier"]
        if weight2.denominator != 1 or weight2.numerator != branch["weight2_trace"]:
            raise CertificateError(f"{name}: integral weight-2 trace mismatch")
        if weight2.numerator % 5 != branch["weight2_trace_mod5"]:
            raise CertificateError(f"{name}: residual trace mismatch")
        integer_traces[name] = weight2.numerator
    if integer_traces != expected_integer_traces:
        raise CertificateError(f"unexpected branch traces: {integer_traces}")

    character = data["character_certificate"]
    exact_keys(
        character,
        {
            "inertia_killing_exponent", "unit_signature_weights", "allowed_signatures",
            "minkowski_numerator", "minkowski_denominator", "class_number_conclusion",
            "K7_prime_2_norm", "F_over_K_residue_degree", "residual_trace_mod5",
            "residual_determinant_mod5", "forced_full_field_character_value",
            "required_character_power", "actual_power_mod5",
        },
        "character_certificate",
    )
    if character["inertia_killing_exponent"] != 84:
        raise CertificateError("inertia exponent must be lcm(12,28)=84")
    weights = character["unit_signature_weights"]
    allowed = [
        list(signature)
        for signature in itertools.product((0, 1), repeat=3)
        if 84 * sum(s * w for s, w in zip(signature, weights)) % 31 == 0
    ]
    if allowed != character["allowed_signatures"] or allowed != [[0, 0, 0], [1, 1, 1]]:
        raise CertificateError(f"finite-flat signature mismatch: {allowed}")
    if not (
        character["minkowski_numerator"] == 42
        and character["minkowski_denominator"] == 27
        and Fraction(42, 27) < 2
        and character["class_number_conclusion"] == 1
    ):
        raise CertificateError("class-number certificate mismatch")
    if character["K7_prime_2_norm"] != 8 or character["F_over_K_residue_degree"] != 2:
        raise CertificateError("prime-2 degree metadata mismatch")

    residual_traces = {value % 5 for value in integer_traces.values()}
    if residual_traces != {character["residual_trace_mod5"]} or residual_traces != {4}:
        raise CertificateError(
            f"the two parity branches do not have the same residual trace: {residual_traces}"
        )
    determinant = (character["K7_prime_2_norm"] ** 2) % 5
    if determinant != character["residual_determinant_mod5"] or determinant != 4:
        raise CertificateError("residual determinant mismatch")
    roots = [
        value
        for value in range(1, 5)
        if (value * value - 4 * value + determinant) % 5 == 0
    ]
    if roots != [2] or roots[0] != character["forced_full_field_character_value"]:
        raise CertificateError(f"unexpected reducible character value: {roots}")
    required_power = 84 // character["F_over_K_residue_degree"]
    if required_power != character["required_character_power"] or required_power != 42:
        raise CertificateError("required character power mismatch")
    actual_power = pow(roots[0], required_power, 5)
    if actual_power != character["actual_power_mod5"] or actual_power != 4:
        raise CertificateError("final character contradiction missing")

    parity = data["parity_certificate"]
    exact_keys(
        parity,
        {"primitive_mod2_classes", "B_odd_classes", "interpretation"},
        "parity_certificate",
    )
    primitive_classes = []
    for A, B, C in itertools.product((0, 1), repeat=3):
        if (A + B - C) % 2:
            continue
        if sum(value == 0 for value in (A, B, C)) > 1:
            continue
        primitive_classes.append([A, B, C])
    if primitive_classes != parity["primitive_mod2_classes"] or primitive_classes != [
        [0, 1, 1], [1, 0, 1], [1, 1, 0]
    ]:
        raise CertificateError(f"primitive parity classes mismatch: {primitive_classes}")
    b_odd = [row for row in primitive_classes if row[1] == 1]
    if b_odd != parity["B_odd_classes"] or b_odd != [[0, 1, 1], [1, 1, 0]]:
        raise CertificateError(f"B-odd parity classes mismatch: {b_odd}")

    literature = data["literature_corollary"]
    exact_keys(
        literature,
        {"Dahmen_Siksek_even_branch", "Dahmen_Siksek_odd_branch", "conclusion"},
        "literature_corollary",
    )
    if "every hypothetical primitive" not in literature["conclusion"]:
        raise CertificateError("global literature corollary is missing")

    source = data["source_audit"]
    exact_keys(
        source,
        {
            "hypergeometric_paper", "parameter", "inversion",
            "finite_monodromy_trace", "weight2_normalization",
            "finite_flat_character_input",
        },
        "source_audit",
    )
    if (
        source["hypergeometric_paper"] != "arXiv:2412.08804v2"
        or "equation (30)" not in source["finite_monodromy_trace"]
        or "Q(zeta_21)" not in source["finite_monodromy_trace"]
    ):
        raise CertificateError("source metadata mismatch")

    actual_sha = base.canonical_sha256(data)
    if actual_sha != data["certificate_sha256"]:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {actual_sha}"
        )
    return actual_sha


def self_test() -> None:
    source = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(source)
    mutated["trace_branches"]["C_even"]["jacobi_reduced_phi21"][0][0] -= 1
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated C-even Jacobi trace")

    mutated = copy.deepcopy(source)
    mutated["trace_branches"]["A_even"]["weight2_trace"] = -11
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated A-even trace")

    mutated = copy.deepcopy(source)
    mutated["parity_certificate"]["B_odd_classes"] = [[0, 1, 1]]
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted an incomplete parity branch")

    mutated = copy.deepcopy(source)
    mutated["character_certificate"]["required_character_power"] = 12
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

    print("B-odd mod-5 prime-2 negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.manifest))
    print("B-odd mod-5 prime-2 certificate valid")
    print(f"certificate sha256: {digest}")
    print("branch traces: C even -> 9; A even -> -16; both are 4 mod 5")
    print("conclusion (conditional on imported local lemmas): B odd => absolute irreducibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
