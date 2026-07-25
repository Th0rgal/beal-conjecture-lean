#!/usr/bin/env python3
"""Replay the corrected cyclotomic proof audit for repeated exponents.

The checker validates only unconditional finite logic:
* the missing product-divisibility implication;
* the coefficient-pair support dichotomy in the coprime case;
* the decomposition-group calculation;
* the Teichmuller-torsion countermodel to the semilocal exponent inversion.

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


def verify_torsion_countermodel(limit: int = 50) -> None:
    gamma = 1
    rho = -1 % 3
    F = (gamma + rho) % 3
    if F != 0 or rho == 0:
        raise CheckError("bad torsion fixture")
    for n in range(1, limit + 1):
        exponent = (1 - pow(7, n)) % 3
        if exponent != 0:
            raise CheckError(f"1-7^{n} is not zero modulo 3")
        if gamma * exponent % 3 != F:
            raise CheckError(f"torsion equality failed at n={n}")


def verify(value: dict[str, Any]) -> None:
    if value.get("schema_version") != 2:
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

    verify_torsion_countermodel()
    torsion = value["semilocal_torsion_gap"]
    if "Teichmuller" not in torsion.get("torsion_obstruction", ""):
        raise CheckError("torsion obstruction was not recorded")

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
