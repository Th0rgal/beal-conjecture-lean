#!/usr/bin/env python3
"""Replay the corrected cyclotomic proof audit for repeated exponents.

The checker validates only unconditional finite logic:
* the missing product-divisibility implication;
* the coefficient-pair support dichotomy in the coprime case;
* the decomposition-group calculation;
* a compatible Q_7 Hensel countermodel to the semilocal exponent inversion.

It deliberately verifies that the previously retained Mersenne/order sieve has
been withdrawn.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

CERTIFICATE = (
    Path(__file__).resolve().parents[1]
    / "Research"
    / "GlobalBeal"
    / "repeated_exponent_cyclotomic_audit.json"
)


class CheckError(RuntimeError):
    pass


def digest(value: dict[str, Any]) -> str:
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def abstract_decomposition_group(m: int, n: int) -> set[tuple[int, int]]:
    return {(k % m, k % n) for k in range(math.lcm(m, n))}


def second_factor_intersection(
    group: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    return {(a, b) for a, b in group if a == 0}


def verify_decomposition_groups(limit: int = 100) -> None:
    for m in range(1, limit + 1):
        for n in range(1, limit + 1):
            group = abstract_decomposition_group(m, n)
            trivial = second_factor_intersection(group) == {(0, 0)}
            if trivial != (m % n == 0):
                raise CheckError(
                    f"D intersect H equivalence failed at m={m}, n={n}"
                )
            contained_in_first = all(second == 0 for _, second in group)
            if contained_in_first != (n == 1):
                raise CheckError(
                    f"D subset G equivalence failed at m={m}, n={n}"
                )


def verify_pair_support_lemma(limit: int = 50) -> None:
    for k in range(1, limit + 1):
        for a0 in range(k + 1):
            a1 = k - a0
            for b0 in range(k + 1):
                b1 = k - b0
                if a0 * b0 != 0 or a1 * b1 != 0:
                    continue
                if a0 + b0 != k or a1 + b1 != k:
                    raise CheckError(
                        f"support lemma failed for k={k}, a={(a0,a1)}, b={(b0,b1)}"
                    )


def teichmueller_cubic_root(precision: int) -> int:
    """Lift 2 mod 7 to the unique cubic root of unity mod 7^precision."""
    if precision < 1:
        raise ValueError("precision must be positive")
    omega = 2
    modulus = 7
    for _ in range(1, precision):
        next_modulus = modulus * 7
        lifts = [
            (omega + digit * modulus) % next_modulus
            for digit in range(7)
            if pow(omega + digit * modulus, 3, next_modulus) == 1
        ]
        if len(lifts) != 1:
            raise CheckError(f"Hensel lift was not unique: {lifts}")
        omega = lifts[0]
        modulus = next_modulus
    return omega


def signed_pow(unit: int, exponent: int, modulus: int) -> int:
    if exponent >= 0:
        return pow(unit, exponent, modulus)
    return pow(pow(unit, -1, modulus), -exponent, modulus)


def verify_exact_q7_countermodel(precisions: list[int]) -> None:
    if precisions != list(range(1, 11)):
        raise CheckError("unexpected Q_7 precision list")
    for n in precisions:
        modulus = 7**n
        omega = teichmueller_cubic_root(n)
        if omega % 7 != 2:
            raise CheckError(f"wrong Teichmuller residue at n={n}")
        if omega == 1 or pow(omega, 3, modulus) != 1:
            raise CheckError(f"nontrivial cubic root failed at n={n}")
        if pow(omega, 7, modulus) != omega:
            raise CheckError(f"Teichmuller fixed-point identity failed at n={n}")

        rho = omega
        gamma = (pow(omega, -1, modulus) * 8) % modulus
        F = (rho * gamma) % modulus
        if F != 8 % modulus:
            raise CheckError(f"rho*gamma identity failed at n={n}")

        # This is exactly the displayed semilocal congruence with r=7,f=1:
        # F ≡ gamma^(1-7^n) (mod 7^n), while rho remains nontrivial.
        if signed_pow(gamma, 1 - 7**n, modulus) != F:
            raise CheckError(f"semilocal congruence failed at n={n}")
        if rho % 7 == 1:
            raise CheckError(f"rho became trivial at n={n}")


def verify(value: dict[str, Any]) -> None:
    if value.get("schema_version") != 3:
        raise CheckError("unexpected schema version")
    if value.get("status") != "unconditional-cyclotomic-proof-gap-audit":
        raise CheckError("unexpected audit status")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("certificate digest mismatch")

    gap = value["lemma5_product_divisibility_gap"]
    if "coprimality" not in gap.get("missing_hypothesis", ""):
        raise CheckError("missing product-divisibility diagnosis")
    if not (2 % 2 == 0 and 2 % 2 == 0 and 2 % 4 != 0):
        raise CheckError("product-divisibility counterexample failed")

    verify_pair_support_lemma()
    collapse = value["lemma5_coprime_case_collapse"]
    if "t1+t2=k*N" not in collapse.get("group_ring_consequence", ""):
        raise CheckError("norm-element collapse was not recorded")
    if "dichotomy" not in collapse:
        raise CheckError("Lemma 5 dichotomy is missing")

    verify_decomposition_groups()
    example = value["lemma6_decomposition_group_gap"]["counterexample"]
    if (example["p"], example["q"], example["r"]) != (5, 3, 2):
        raise CheckError("decomposition-group counterexample was mutated")
    if (example["ord_p_r"], example["ord_q_r"]) != (4, 2):
        raise CheckError("counterexample orders were mutated")
    group = abstract_decomposition_group(4, 2)
    if second_factor_intersection(group) != {(0, 0)}:
        raise CheckError("counterexample intersection is not trivial")
    if all(second == 0 for _, second in group):
        raise CheckError("counterexample group lies in the first factor")
    if 2 % 3 == 1:
        raise CheckError("counterexample prime unexpectedly splits completely")

    torsion = value["semilocal_torsion_gap"]
    if "Teichmuller" not in torsion.get("torsion_obstruction", ""):
        raise CheckError("torsion obstruction was not recorded")
    exact = torsion.get("exact_q7_hensel_countermodel", {})
    if exact.get("rho_nontrivial") != "rho is congruent to 2 modulo 7":
        raise CheckError("exact Q_7 model was mutated")
    verify_exact_q7_countermodel(exact.get("verified_precisions", []))

    withdrawn = set(value.get("withdrawn_consequences", []))
    required_withdrawals = {
        "the claimed universal proof of x^p+y^p=z^q for distinct odd primes",
        "the conditional order relation ord_q(r) divides ord_p(r) for every r dividing x*y*(x+y)",
        "the derived Mersenne-divisor sieve q divides 2^g-1",
        "the claimed closure of the repeated-prime Beal core",
    }
    if withdrawn != required_withdrawals:
        raise CheckError("withdrawn-consequence set mismatch")

    serialized = json.dumps(value, sort_keys=True)
    forbidden_active_keys = (
        '"conditional_corrected_consequence"',
        '"sample_order_sieve"',
        '"gcd_mersenne_sieve"',
    )
    if any(key in serialized for key in forbidden_active_keys):
        raise CheckError("a withdrawn Mersenne/order sieve remains active")

    if "not a no-solution theorem" not in value.get("nonclaim", ""):
        raise CheckError("fail-closed nonclaim is missing")


def self_test(value: dict[str, Any]) -> None:
    verify(value)
    mutations: list[dict[str, Any]] = []

    bad = copy.deepcopy(value)
    bad["lemma5_product_divisibility_gap"]["missing_hypothesis"] = "none"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["lemma6_decomposition_group_gap"]["counterexample"]["ord_q_r"] = 1
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["withdrawn_consequences"].remove(
        "the derived Mersenne-divisor sieve q divides 2^g-1"
    )
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["semilocal_torsion_gap"]["torsion_obstruction"] = "no obstruction"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["semilocal_torsion_gap"]["exact_q7_hensel_countermodel"][
        "rho_nontrivial"
    ] = "rho is congruent to 1 modulo 7"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    for index, mutation in enumerate(mutations):
        try:
            verify(mutation)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} was incorrectly accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, default=CERTIFICATE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    value = json.loads(args.certificate.read_text(encoding="utf-8"))
    if args.self_test:
        self_test(value)
    else:
        verify(value)
    print(
        json.dumps(
            {
                "status": "ok",
                "certificate_sha256": value["certificate_sha256"],
                "self_test": args.self_test,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
