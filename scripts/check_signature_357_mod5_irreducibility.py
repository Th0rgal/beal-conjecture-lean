#!/usr/bin/env python3
"""Replay the arithmetic in the independent mod-5 irreducibility-at-3 argument.

For a primitive solution A^3+B^5=C^7 with 3 not dividing A*B*C, use the
signature-(7,5,3) plus compatible system over Q(zeta_7)^+ and parameter
u=C^7/A^3. Exact enumeration modulo 9 gives u in {2,5,8}. The cited local-type
table assigns a supercuspidal type of order 12, 4, or 12 respectively at 3.

The checker verifies the finite arithmetic, field-degree calculation, source
metadata, prime-to-5/7 type orders, and certificate digest. It does not reprove
the cited compatibility or local-global representation theorems. Those remain
literature inputs outside BealUnified.Trusted.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    ROOT / "Research" / "Signature357" / "mod5_irreducibility_at3.json"
)


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: pathlib.Path) -> dict[str, Any]:
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


def require_exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def is_prime(value: int) -> bool:
    if value < 2:
        return False
    return all(value % divisor for divisor in range(2, math.isqrt(value) + 1))


def multiplicative_order(value: int, modulus: int) -> int:
    if math.gcd(value, modulus) != 1:
        raise CertificateError("multiplicative order requested for a non-unit")
    current = 1
    for exponent in range(1, modulus + 1):
        current = current * value % modulus
        if current == 1:
            return exponent
    raise CertificateError("failed to find multiplicative order")


def real_cyclotomic_residue_degree(prime: int, cyclotomic_prime: int) -> int:
    """Least f with prime^f = +/-1 modulo the cyclotomic prime."""
    if not (is_prime(prime) and is_prime(cyclotomic_prime)):
        raise CertificateError("residue-degree inputs must be prime")
    current = 1
    for degree in range(1, cyclotomic_prime):
        current = current * prime % cyclotomic_prime
        if current in {1, cyclotomic_prime - 1}:
            return degree
    raise CertificateError("failed to compute real cyclotomic residue degree")


def canonical_digest(data: dict[str, Any]) -> str:
    payload = {key: value for key, value in data.items() if key != "certificate_sha256"}
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def enumerate_unit_parameter_classes_mod_9() -> tuple[list[int], int]:
    """Enumerate primitive unit residue solutions and u=C^7/A^3 mod 9."""
    modulus = 9
    units = [value for value in range(modulus) if math.gcd(value, modulus) == 1]
    classes: set[int] = set()
    solution_count = 0
    for A in units:
        a3 = pow(A, 3, modulus)
        inverse_a3 = pow(a3, -1, modulus)
        for B in units:
            b5 = pow(B, 5, modulus)
            for C in units:
                c7 = pow(C, 7, modulus)
                if (a3 + b5 - c7) % modulus:
                    continue
                solution_count += 1
                classes.add(c7 * inverse_a3 % modulus)
    return sorted(classes), solution_count


def validate_data(data: dict[str, Any]) -> tuple[list[int], str]:
    require_exact_keys(
        data,
        {
            "schema_version",
            "signature",
            "residual_prime",
            "source_congruence_prime",
            "source",
            "orientation",
            "base_field",
            "unit_parameter_classes_mod_9",
            "local_types",
            "transfer",
            "conclusion",
            "certificate_sha256",
        },
        "manifest",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise CertificateError("schema_version must be the integer 1")
    if data["signature"] != [3, 5, 7]:
        raise CertificateError("this certificate is specific to signature (3,5,7)")

    residual_prime = data["residual_prime"]
    congruence_prime = data["source_congruence_prime"]
    if residual_prime != 5 or congruence_prime != 7:
        raise CertificateError("expected residual prime 5 and source congruence prime 7")
    if not (is_prime(residual_prime) and is_prime(congruence_prime)):
        raise CertificateError("residual characteristics must be prime")

    source = data["source"]
    if not isinstance(source, dict):
        raise CertificateError("source must be an object")
    require_exact_keys(
        source,
        {"paper_arxiv", "compatible_system_arxiv", "results"},
        "source",
    )
    expected_results = [
        "Pacetti--Villagra Torcomian, Proposition 3.2",
        "Pacetti--Villagra Torcomian, Table 3.1 and Corollary 3.6",
        "Pacetti--Villagra Torcomian, Remark 3.8",
        "Golfieri--Pacetti, Theorem 2.9 and Theorem 6.2",
    ]
    if source != {
        "paper_arxiv": "2512.17845v1",
        "compatible_system_arxiv": "2412.08804v1",
        "results": expected_results,
    }:
        raise CertificateError("source metadata does not match the audited chain")

    orientation = data["orientation"]
    if not isinstance(orientation, dict):
        raise CertificateError("orientation must be an object")
    require_exact_keys(
        orientation,
        {"beal_equation", "paper_equation", "paper_variables", "parameter", "hypothesis"},
        "orientation",
    )
    expected_orientation = {
        "beal_equation": "A^3+B^5=C^7",
        "paper_equation": "a^7+b^5+c^3=0",
        "paper_variables": ["a=-C", "b=B", "c=A", "q=7", "p=5", "r=3"],
        "parameter": "u=C^7/A^3",
        "hypothesis": "3 does not divide A*B*C",
    }
    if orientation != expected_orientation:
        raise CertificateError("orientation does not match the audited second Frey system")

    base_field = data["base_field"]
    if not isinstance(base_field, dict):
        raise CertificateError("base_field must be an object")
    require_exact_keys(
        base_field,
        {
            "label",
            "name",
            "degree",
            "defining_polynomial",
            "local_prime",
            "order_of_3_mod_7",
            "real_residue_degree",
            "local_extension",
        },
        "base_field",
    )
    if base_field["label"] != "3.3.49.1" or base_field["name"] != "Q(zeta_7)^+":
        raise CertificateError("unexpected real cyclotomic base field")
    if base_field["degree"] != 3:
        raise CertificateError("Q(zeta_7)^+ must have degree 3")
    if base_field["defining_polynomial"] != "x^3-x^2-2*x+1":
        raise CertificateError("unexpected defining polynomial")
    if base_field["local_prime"] != 3:
        raise CertificateError("this certificate is the local argument at 3")

    order = multiplicative_order(3, 7)
    if order != 6 or base_field["order_of_3_mod_7"] != order:
        raise CertificateError("the multiplicative order of 3 modulo 7 must be 6")
    residue_degree = real_cyclotomic_residue_degree(3, 7)
    if residue_degree != 3 or base_field["real_residue_degree"] != residue_degree:
        raise CertificateError("the residue degree at 3 in Q(zeta_7)^+ must be 3")
    if base_field["local_extension"] != "unramified cubic over Q_3":
        raise CertificateError("unexpected local extension description")

    actual_classes, solution_count = enumerate_unit_parameter_classes_mod_9()
    if solution_count != 18:
        raise CertificateError("unexpected number of unit solutions modulo 9")
    if actual_classes != [2, 5, 8]:
        raise CertificateError(f"unexpected parameter classes modulo 9: {actual_classes}")
    if data["unit_parameter_classes_mod_9"] != actual_classes:
        raise CertificateError("manifest parameter classes do not match exact enumeration")

    local_types = data["local_types"]
    if not isinstance(local_types, list) or len(local_types) != 3:
        raise CertificateError("local_types must contain exactly three rows")
    expected_local_types = [
        {
            "u_mod_9": 2,
            "e": 12,
            "type": "supercuspidal",
            "quadratic_extension": "ramified",
            "prime_to_5_inertia_bound": 12,
        },
        {
            "u_mod_9": 5,
            "e": 4,
            "type": "supercuspidal",
            "quadratic_extension": "unramified",
            "inducing_character_order": 4,
            "prime_to_5_inertia_bound": 4,
        },
        {
            "u_mod_9": 8,
            "e": 12,
            "type": "supercuspidal",
            "quadratic_extension": "ramified",
            "prime_to_5_inertia_bound": 12,
        },
    ]
    if local_types != expected_local_types:
        raise CertificateError("local-type table does not match the audited source rows")
    if [row["u_mod_9"] for row in local_types] != actual_classes:
        raise CertificateError("local-type rows do not cover every admissible parameter class")

    transfer = data["transfer"]
    if not isinstance(transfer, dict):
        raise CertificateError("transfer must be an object")
    require_exact_keys(
        transfer,
        {
            "quadratic_twist_allowed",
            "unramified_base_degree",
            "unramified_quadratic_contained",
            "orders_prime_to_congruence_prime",
            "orders_prime_to_residual_prime",
            "principle",
        },
        "transfer",
    )
    if transfer["quadratic_twist_allowed"] is not True:
        raise CertificateError("the source congruence is only specified up to quadratic twist")
    if transfer["unramified_base_degree"] != residue_degree:
        raise CertificateError("base-change degree does not match the residue-degree computation")
    if transfer["unramified_quadratic_contained"] is not False:
        raise CertificateError("an unramified cubic cannot contain the unramified quadratic")
    if residue_degree % 2 == 0:
        raise CertificateError("degree calculation unexpectedly permits a quadratic subfield")

    expected_orders = sorted({row["prime_to_5_inertia_bound"] for row in local_types})
    if expected_orders != [4, 12]:
        raise CertificateError("unexpected inertia-order bounds")
    if transfer["orders_prime_to_congruence_prime"] != expected_orders:
        raise CertificateError("congruence-prime order metadata mismatch")
    if transfer["orders_prime_to_residual_prime"] != expected_orders:
        raise CertificateError("residual-prime order metadata mismatch")
    for inertia_order in expected_orders:
        if math.gcd(inertia_order, congruence_prime) != 1:
            raise CertificateError("an inertia order is not prime to the source congruence prime")
        if math.gcd(inertia_order, residual_prime) != 1:
            raise CertificateError("an inertia order is not prime to the residual prime")
    if local_types[1]["inducing_character_order"] != 4:
        raise CertificateError("the unramified-quadratic type must use an order-4 character")

    expected_principle = (
        "prime-to-7 local type survives the mod-7 congruence; compatibility transfers "
        "the local type to the 5-adic member; prime-to-5 reduction preserves the "
        "distinct inducing characters"
    )
    if transfer["principle"] != expected_principle:
        raise CertificateError("unexpected local-type transfer statement")

    expected_conclusion = (
        "if 3 does not divide A*B*C, the independent residual mod-5 Frey "
        "representation over Q(zeta_7)^+ is absolutely irreducible"
    )
    if data["conclusion"] != expected_conclusion:
        raise CertificateError("unexpected conclusion text")

    digest = canonical_digest(data)
    claimed = data["certificate_sha256"]
    if (
        not isinstance(claimed, str)
        or len(claimed) != 64
        or any(character not in "0123456789abcdef" for character in claimed)
        or claimed != digest
    ):
        raise CertificateError(
            f"certificate digest mismatch: expected {claimed!r}, computed {digest}"
        )
    return actual_classes, digest


def validate(path: pathlib.Path) -> tuple[list[int], str]:
    return validate_data(load_json(path))


def expect_rejection(data: dict[str, Any], description: str) -> None:
    try:
        validate_data(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {description}")


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["unit_parameter_classes_mod_9"] = [2, 5]
    expect_rejection(mutated, "a weakened parameter-class list")

    mutated = copy.deepcopy(base)
    mutated["base_field"]["real_residue_degree"] = 1
    expect_rejection(mutated, "a false residue degree")

    mutated = copy.deepcopy(base)
    mutated["local_types"][1]["inducing_character_order"] = 5
    expect_rejection(mutated, "a residual-characteristic inertia order")

    mutated = copy.deepcopy(base)
    mutated["conclusion"] = "the Beal conjecture is proved"
    expect_rejection(mutated, "an overclaimed conclusion")

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

    print("mod-5 irreducibility-at-3 negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    classes, digest = validate(args.manifest)
    print("signature (3,5,7) mod-5 irreducibility-at-3 certificate passed")
    print(f"  admissible unit parameter classes mod 9: {classes}")
    print("  local types: e=12 ramified, e=4 unramified, e=12 ramified")
    print("  base change at 3: unramified cubic; no unramified quadratic subfield")
    print("  conclusion: independent residual mod-5 representation is absolutely irreducible")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
