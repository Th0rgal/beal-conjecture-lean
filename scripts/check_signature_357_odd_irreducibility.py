#!/usr/bin/env python3
"""Replay the arithmetic in the direct fixed-7 irreducibility argument.

This checker deliberately does not apply Pacetti--Villagra Torcomian's
large-prime corollary at p=7. Instead it checks the finite-field, unit,
class-number, and Frobenius arithmetic of a direct fixed-prime argument.

The finite-flat rank-one signature statement, the away-7 inertia bounds, and
the prime-2 Frey trace set remain explicitly imported local/global lemmas.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "odd_irreducibility.json"


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


def digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# F_49 = F_7[e]/(e^2-e-1). A pair (a,b) represents a+b*e.
F49 = tuple[int, int]
ONE: F49 = (1, 0)


def add(x: F49, y: F49) -> F49:
    return ((x[0] + y[0]) % 7, (x[1] + y[1]) % 7)


def mul(x: F49, y: F49) -> F49:
    a, b = x
    c, d = y
    return ((a * c + b * d) % 7, (a * d + b * c + b * d) % 7)


def power(x: F49, exponent: int) -> F49:
    if exponent < 0:
        raise CertificateError("negative exponent")
    result = ONE
    base = x
    while exponent:
        if exponent & 1:
            result = mul(result, base)
        base = mul(base, base)
        exponent >>= 1
    return result


def order(x: F49) -> int:
    if x == (0, 0):
        raise CertificateError("zero has no multiplicative order")
    for candidate in range(1, 49):
        if power(x, candidate) == ONE:
            return candidate
    raise CertificateError("element is not in F49^*")


# Quotient by u^2+u+4 over F_7. A pair a+b*u uses u^2=3+6u.
def umul(x: F49, y: F49) -> F49:
    a, b = x
    c, d = y
    return ((a * c + 3 * b * d) % 7, (a * d + b * c + 6 * b * d) % 7)


def upower(x: F49, exponent: int) -> F49:
    result = ONE
    base = x
    while exponent:
        if exponent & 1:
            result = umul(result, base)
        base = umul(base, base)
        exponent >>= 1
    return result


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version",
            "status",
            "scope",
            "imported_lemmas",
            "unit_certificate",
            "class_number_certificate",
            "frobenius_certificate",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 2:
        raise CertificateError("schema_version must equal 2")
    if data["status"] != "research-certificate-with-imported-finite-flat-lemma":
        raise CertificateError("unexpected status")
    if not isinstance(data["imported_lemmas"], list) or len(data["imported_lemmas"]) != 4:
        raise CertificateError("expected exactly four imported lemmas")

    scope = data["scope"]
    exact_keys(
        scope,
        {
            "equation",
            "hypotheses",
            "orientation",
            "field",
            "residual_prime",
            "claim",
        },
        "scope",
    )
    if (
        scope["equation"] != "A^3+B^5=C^7"
        or scope["orientation"] != "B^5+(-C)^7+A^3=0"
        or scope["field"] != "K=Q(sqrt(5))"
        or scope["residual_prime"] != 7
    ):
        raise CertificateError("scope/orientation mismatch")

    unit = data["unit_certificate"]
    exact_keys(
        unit,
        {
            "minimal_polynomial_mod7_ascending",
            "epsilon",
            "epsilon_conjugate",
            "epsilon_order",
            "inertia_killing_exponent",
            "signature_weights",
            "allowed_signatures",
        },
        "unit_certificate",
    )
    if unit["minimal_polynomial_mod7_ascending"] != [6, 6, 1]:
        raise CertificateError("unexpected minimal polynomial")
    if any((x * x - x - 1) % 7 == 0 for x in range(7)):
        raise CertificateError("the selected quadratic is reducible over F7")

    epsilon = tuple(unit["epsilon"])
    epsilon_conjugate = tuple(unit["epsilon_conjugate"])
    if epsilon != (0, 1) or epsilon_conjugate != (1, 6):
        raise CertificateError("unit coordinates mismatch")
    if power(epsilon, 2) != add(epsilon, ONE):
        raise CertificateError("epsilon^2 != epsilon+1")
    if mul(epsilon, epsilon_conjugate) != (6, 0):
        raise CertificateError("unit conjugate/norm mismatch")
    if order(epsilon) != unit["epsilon_order"] or order(epsilon) != 16:
        raise CertificateError("epsilon does not have order 16")

    exponent = unit["inertia_killing_exponent"]
    if exponent != 60:
        raise CertificateError("inertia-killing exponent must be 60")
    allowed: list[list[int]] = []
    for signature in itertools.product((0, 1), repeat=2):
        value = mul(
            power(epsilon, signature[0]),
            power(epsilon_conjugate, signature[1]),
        )
        if power(value, exponent) == ONE:
            allowed.append(list(signature))
    if allowed != unit["allowed_signatures"] or allowed != [[0, 0], [1, 1]]:
        raise CertificateError(f"finite-flat signature list mismatch: {allowed}")

    class_number = data["class_number_certificate"]
    exact_keys(
        class_number,
        {
            "field_discriminant",
            "degree",
            "minkowski_bound_squared_numerator",
            "minkowski_bound_squared_denominator",
            "bound_lt_2_squared",
            "class_number",
        },
        "class_number_certificate",
    )
    if (
        class_number["field_discriminant"] != 5
        or class_number["degree"] != 2
        or class_number["minkowski_bound_squared_numerator"] != 5
        or class_number["minkowski_bound_squared_denominator"] != 4
        or not class_number["bound_lt_2_squared"]
        or not 5 < 16
        or class_number["class_number"] != 1
    ):
        raise CertificateError("Minkowski class-number certificate mismatch")

    frob = data["frobenius_certificate"]
    exact_keys(
        frob,
        {
            "auxiliary_rational_prime",
            "prime_norm",
            "trace_candidates",
            "trace_mod7",
            "reducible_polynomial_ascending_mod7",
            "u4_mod7",
            "u12_mod7",
            "u60_mod7",
            "unramified_character_required_u60",
        },
        "frobenius_certificate",
    )
    if frob["auxiliary_rational_prime"] != 2 or frob["prime_norm"] != 4:
        raise CertificateError("prime-2 metadata mismatch")
    residues = sorted({value % 7 for value in frob["trace_candidates"]})
    if frob["trace_candidates"] != [-1, -8] or residues != [6] or frob["trace_mod7"] != 6:
        raise CertificateError("prime-2 trace reduction mismatch")

    if frob["reducible_polynomial_ascending_mod7"] != [4, 1, 1]:
        raise CertificateError("wrong reducible Frobenius polynomial")
    u: F49 = (0, 1)
    powers = {4: upower(u, 4), 12: upower(u, 12), 60: upower(u, 60)}
    if powers[4] != (frob["u4_mod7"], 0) or powers[4] != (5, 0):
        raise CertificateError("u^4 arithmetic mismatch")
    if powers[12] != (frob["u12_mod7"], 0) or powers[12] != (6, 0):
        raise CertificateError("u^12 arithmetic mismatch")
    if powers[60] != (frob["u60_mod7"], 0) or powers[60] != (6, 0):
        raise CertificateError("u^60 arithmetic mismatch")
    if frob["unramified_character_required_u60"] != 1 or powers[60] == ONE:
        raise CertificateError("final character contradiction missing")

    actual = digest(data)
    if data["certificate_sha256"] != actual:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {actual}"
        )
    return actual


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["unit_certificate"]["epsilon_order"] = 8
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated unit order")

    mutated = copy.deepcopy(base)
    mutated["unit_certificate"]["allowed_signatures"] = [[0, 0]]
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted an incomplete signature list")

    mutated = copy.deepcopy(base)
    mutated["frobenius_certificate"]["u60_mod7"] = 1
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a removed Frobenius contradiction")

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
            raise RuntimeError("checker accepted duplicate keys")
    finally:
        path.unlink(missing_ok=True)

    print("direct fixed-7 irreducibility negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load_json(args.manifest))
    print("direct fixed-7 irreducibility arithmetic certificate valid")
    print(f"certificate sha256: {certificate}")
    print("conclusion conditional on four explicitly imported representation lemmas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
