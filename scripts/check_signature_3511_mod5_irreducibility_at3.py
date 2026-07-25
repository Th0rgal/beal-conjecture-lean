#!/usr/bin/env python3
"""Replay the finite arithmetic in the signature-(3,5,11) mod-5 irreducibility theorem.

The checker verifies the parameter classes, the unramified quintic local degree,
the coprime-degree Mackey contradiction, the prime-to-5 inertia orders and the
canonical certificate digest.  It deliberately treats the source local-type
identification, modularity and local--global compatibility as imported inputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "Research" / "Signature3511" / "mod5_irreducibility_at3.json"


class CheckError(RuntimeError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def order_mod(a: int, modulus: int) -> int:
    value = 1
    for exponent in range(1, modulus + 1):
        value = value * a % modulus
        if value == 1:
            return exponent
    raise CheckError("multiplicative order search failed")


def least_plus_or_minus_one_exponent(a: int, modulus: int) -> int:
    value = 1
    for exponent in range(1, modulus + 1):
        value = value * a % modulus
        if value in {1, modulus - 1}:
            return exponent
    raise CheckError("plus-or-minus-one order search failed")


def verify(value: dict[str, Any]) -> None:
    certificate = value.get("certificate_sha256")
    if not isinstance(certificate, str):
        raise CheckError("certificate_sha256 is missing")
    body = dict(value)
    body.pop("certificate_sha256")
    if digest(body) != certificate:
        raise CheckError("canonical certificate digest mismatch")

    if value.get("signature") != [3, 5, 11] or value.get("residual_prime") != 5:
        raise CheckError("unexpected signature or residual prime")
    if value.get("equation") != "A^3+B^5=C^11":
        raise CheckError("unexpected equation")

    # If A,B,C are all nonzero modulo 3, the equation A+B=C has only the two
    # simultaneous-sign solutions, and u=C^11/A^3 is always -1 modulo 3.
    triples: list[tuple[int, int, int, int]] = []
    for a in (1, 2):
        for b in (1, 2):
            for c in (1, 2):
                if (pow(a, 3, 3) + pow(b, 5, 3) - pow(c, 11, 3)) % 3 == 0:
                    u = pow(c, 11, 3) * pow(pow(a, 3, 3), -1, 3) % 3
                    triples.append((a, b, c, u))
    if triples != [(1, 1, 2, 2), (2, 2, 1, 2)]:
        raise CheckError(f"unexpected nonzero solutions modulo 3: {triples}")
    expected_classes = [integer for integer in range(9) if integer % 3 == 2]
    if value.get("unit_parameter_classes_mod_9") != expected_classes:
        raise CheckError("incorrect unit parameter classes modulo 9")

    field = value.get("base_field", {})
    if order_mod(3, 11) != 5 or field.get("order_of_3_mod_11") != 5:
        raise CheckError("incorrect order of 3 modulo 11")
    if least_plus_or_minus_one_exponent(3, 11) != 5:
        raise CheckError("incorrect real cyclotomic residue degree")
    if field.get("least_n_with_3n_equal_plus_or_minus_1_mod_11") != 5:
        raise CheckError("manifest has wrong plus-or-minus-one exponent")
    if field.get("degree") != 5 or field.get("real_residue_degree") != 5:
        raise CheckError("incorrect degree for Q(zeta_11)^+")

    base_change = value.get("odd_degree_base_change", {})
    if base_change.get("base_degree") != 5 or base_change.get("quadratic_degree") != 2:
        raise CheckError("wrong local extension degrees")
    if math.gcd(5, 2) != 1 or not base_change.get("coprime_degrees"):
        raise CheckError("quadratic and quintic extensions were not recorded as disjoint")
    # The hypothetical delta has order dividing both 2 (from delta=delta^-1)
    # and 5 (from factoring through the quintic quotient), hence is trivial.
    if math.gcd(2, base_change.get("quotient_order_in_reducibility_contradiction")) != 1:
        raise CheckError("the Mackey contradiction does not force delta to be trivial")

    local_types = value.get("local_types")
    expected_types = {
        2: ("ramified", 12),
        5: ("unramified", 4),
        8: ("ramified", 12),
    }
    if not isinstance(local_types, list) or len(local_types) != 3:
        raise CheckError("local type table is incomplete")
    seen: set[int] = set()
    orders: set[int] = set()
    for row in local_types:
        residue = row.get("u_mod_9")
        if residue not in expected_types or residue in seen:
            raise CheckError("unexpected or duplicated local residue class")
        seen.add(residue)
        expected_extension, expected_order = expected_types[residue]
        if row.get("quadratic_extension") != expected_extension:
            raise CheckError("quadratic inducing extension mismatch")
        if row.get("finite_inertia_order") != expected_order:
            raise CheckError("finite inertia order mismatch")
        if math.gcd(expected_order, 5) != 1:
            raise CheckError("inertia order is not prime to residual characteristic 5")
        orders.add(expected_order)
    if seen != set(expected_types):
        raise CheckError("local type residue classes do not cover 2,5,8")

    reduction = value.get("reduction_mod_5", {})
    if reduction.get("finite_inertia_orders") != sorted(orders):
        raise CheckError("reduction manifest has the wrong inertia-order inventory")
    if not reduction.get("orders_prime_to_5"):
        raise CheckError("prime-to-5 reduction flag is false")

    expected_conclusion = (
        "if 3 does not divide A*B*C, the independent residual mod-5 plus-HGM "
        "representation over Q(zeta_11)^+ is absolutely irreducible"
    )
    if value.get("conclusion") != expected_conclusion:
        raise CheckError("unexpected conclusion")
    if "imported" not in value.get("nonclaim", ""):
        raise CheckError("imported theorem boundary is not explicit")


def self_test(value: dict[str, Any]) -> None:
    verify(value)
    mutations: list[tuple[str, Any]] = []

    wrong_degree = copy.deepcopy(value)
    wrong_degree["base_field"]["degree"] = 3
    mutations.append(("wrong field degree", wrong_degree))

    wrong_order = copy.deepcopy(value)
    wrong_order["local_types"][0]["finite_inertia_order"] = 10
    mutations.append(("inertia order divisible by 5", wrong_order))

    wrong_class = copy.deepcopy(value)
    wrong_class["unit_parameter_classes_mod_9"] = [2, 8]
    mutations.append(("missing parameter class", wrong_class))

    wrong_quotient = copy.deepcopy(value)
    wrong_quotient["odd_degree_base_change"]["quotient_order_in_reducibility_contradiction"] = 6
    mutations.append(("non-coprime quotient order", wrong_quotient))

    for name, mutation in mutations:
        body = dict(mutation)
        body.pop("certificate_sha256", None)
        mutation["certificate_sha256"] = digest(body)
        try:
            verify(mutation)
        except CheckError:
            continue
        raise CheckError(f"negative fixture unexpectedly passed: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    value = json.loads(args.path.read_text(encoding="utf-8"))
    if args.self_test:
        self_test(value)
    else:
        verify(value)
    print("signature-(3,5,11) mod-5 irreducibility-at-3 certificate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
