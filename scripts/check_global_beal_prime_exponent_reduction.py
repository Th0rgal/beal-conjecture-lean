#!/usr/bin/env python3
"""Replay the corrected global canonical-exponent reduction for Beal.

The checker certifies the elementary reduction to exponents in
``{4} union {odd primes}``, the corrected partition of that canonical core, and
the finite boundary around the candidate signature ``(3,5,7)``.  It does not
reprove the survey's solved-signature inventory or the candidate (3,5,7)
argument; those remain explicit imported inputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

CERTIFICATE = (
    Path(__file__).resolve().parents[1]
    / "Research"
    / "GlobalBeal"
    / "global_prime_exponent_reduction.json"
)


class CheckError(RuntimeError):
    pass


def canonical_digest(value: dict[str, Any]) -> str:
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def odd_prime_divisor(n: int) -> int:
    if n < 3 or n % 2 == 0:
        raise CheckError(f"expected odd n >= 3, got {n}")
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return divisor
        divisor += 2
    return n


def canonical_factor(n: int) -> tuple[int, int]:
    if n < 3:
        raise ValueError("canonical reduction requires n >= 3")
    if n % 4 == 0:
        return 4, n // 4
    odd_part = n if n % 2 else n // 2
    prime = odd_prime_divisor(odd_part)
    return prime, n // prime


def canonical_values_below(bound: int) -> list[int]:
    values = [4]
    values.extend(n for n in range(3, bound) if n % 2 and is_prime(n))
    return sorted(set(values))


def sorted_canonical_triples_below_sum(bound: int) -> list[list[int]]:
    values = canonical_values_below(bound)
    result: list[list[int]] = []
    for i, p in enumerate(values):
        for j in range(i, len(values)):
            q = values[j]
            for k in range(j, len(values)):
                r = values[k]
                if p + q + r >= bound:
                    break
                result.append([p, q, r])
    return result


def sorted_canonical_triples_of_sum(total: int) -> list[list[int]]:
    return [
        row
        for row in sorted_canonical_triples_below_sum(total + 1)
        if sum(row) == total
    ]


EXPECTED_COVERAGE: dict[tuple[int, int, int], str] = {
    (3, 3, 3): "Fermat's Last Theorem",
    (3, 3, 4): "solved special signature",
    (3, 3, 5): "solved (3,3,p) family",
    (3, 3, 7): "solved (3,3,p) family",
    (3, 4, 4): "solved special signature",
    (3, 4, 5): "solved special signature",
    (3, 4, 7): "reduce exponent 4 to 2; solved parent (2,3,7)",
    (3, 5, 5): "solved (p,p,3) family",
    (3, 5, 7): "candidate conditional proof in Signature357",
    (4, 4, 4): "Fermat's Last Theorem / solved special signature",
    (4, 4, 5): "reduce one exponent 4 to 2; solved special parent (2,4,5)",
    (4, 4, 7): "reduce one exponent 4 to 2; solved special parent (2,4,7)",
    (4, 5, 5): "reduce exponent 4 to 2; solved (p,p,2) family",
    (5, 5, 5): "Fermat's Last Theorem",
}


def verify(value: dict[str, Any], *, factor_bound: int = 100_000) -> None:
    if value.get("schema_version") != 2:
        raise CheckError("unexpected schema version")
    if value.get("status") != "literature-assisted-canonical-beal-core-reduction":
        raise CheckError("unexpected status")
    if value.get("certificate_sha256") != canonical_digest(value):
        raise CheckError("certificate digest mismatch")

    canonical = value["unconditional_canonical_reduction"]
    if canonical.get("canonical_exponents") != "4 or an odd prime":
        raise CheckError("canonical exponent description was mutated")

    for n in range(3, factor_bound + 1):
        exponent, multiplier = canonical_factor(n)
        if multiplier < 1 or exponent * multiplier != n:
            raise CheckError(f"bad canonical factorization for {n}")
        if exponent == 4:
            if n % 4:
                raise CheckError(f"used exponent 4 without 4 | {n}")
        elif not (is_prime(exponent) and exponent % 2 == 1 and n % exponent == 0):
            raise CheckError(f"bad odd-prime canonical exponent {exponent} for {n}")

    core = value["corrected_canonical_core"]
    if "three odd-prime exponents" not in core.get("withdrawn_claim", ""):
        raise CheckError("the old prime-only claim was not explicitly withdrawn")
    statement = core.get("statement", "")
    if "all-odd-prime" not in statement or "exactly one exponent 4" not in statement:
        raise CheckError("corrected canonical-core statement is incomplete")

    one_four = core["one_four_core"]
    if one_four.get("form") != "(4,p,q) up to term placement, with p and q odd primes":
        raise CheckError("one-four core was mutated")
    if one_four.get("remaining_case") != "p and q distinct":
        raise CheckError("repeated one-four case was not removed")

    expected_cores = {
        "square-constrained even core (4,p,q) with distinct odd primes p,q",
        "repeated odd-prime core (p,p,q) with distinct odd primes p,q",
        "three-distinct-odd-prime core (p,q,r)",
    }
    if set(value.get("unresolved_infinite_cores", [])) != expected_cores:
        raise CheckError("unresolved infinite-core partition mismatch")

    impact = value["conditional_signature357_impact"]
    recorded = {
        tuple(row["signature"]): row["coverage"]
        for row in impact["canonical_signatures_of_sum_below_16"]
    }
    if recorded != EXPECTED_COVERAGE:
        raise CheckError(
            f"boundary coverage mismatch: expected {EXPECTED_COVERAGE}, got {recorded}"
        )

    expected_below = {tuple(row) for row in sorted_canonical_triples_below_sum(16)}
    if set(recorded) != expected_below:
        raise CheckError(
            f"canonical boundary enumeration mismatch: {sorted(expected_below)}"
        )

    sum_16 = sorted_canonical_triples_of_sum(16)
    if sum_16 != [[4, 5, 7]]:
        raise CheckError(f"unexpected canonical signatures of sum 16: {sum_16}")
    if impact.get("unique_canonical_signature_of_sum_16") != [4, 5, 7]:
        raise CheckError("unique sum-16 signature was mutated")
    if impact.get("next_target") != [4, 5, 7]:
        raise CheckError("correct next target was mutated")
    if impact.get("former_next_target_withdrawn") != [3, 5, 11]:
        raise CheckError("former incorrect target was not withdrawn")
    if impact.get("parent_prime_signature") != [2, 5, 7]:
        raise CheckError("parent prime signature was mutated")
    if "square" not in impact.get("square_restriction", ""):
        raise CheckError("square restriction was not recorded")

    nonclaim = value.get("nonclaim", "").lower()
    if "does not prove beal" not in nonclaim:
        raise CheckError("missing fail-closed nonclaim")


def self_test(value: dict[str, Any]) -> None:
    verify(value, factor_bound=20_000)
    mutations: list[dict[str, Any]] = []

    bad = copy.deepcopy(value)
    bad["corrected_canonical_core"]["withdrawn_claim"] = "every counterexample has odd primes"
    bad["certificate_sha256"] = canonical_digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["conditional_signature357_impact"]["next_target"] = [3, 5, 11]
    bad["certificate_sha256"] = canonical_digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["unresolved_infinite_cores"].pop()
    bad["certificate_sha256"] = canonical_digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["conditional_signature357_impact"]["canonical_signatures_of_sum_below_16"].pop()
    bad["certificate_sha256"] = canonical_digest(bad)
    mutations.append(bad)

    for index, mutation in enumerate(mutations):
        try:
            verify(mutation, factor_bound=2_000)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} was incorrectly accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, default=CERTIFICATE)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--factor-bound", type=int, default=100_000)
    args = parser.parse_args()

    value = json.loads(args.certificate.read_text(encoding="utf-8"))
    if args.self_test:
        self_test(value)
    else:
        verify(value, factor_bound=args.factor_bound)
    print(
        json.dumps(
            {
                "status": "ok",
                "certificate": str(args.certificate),
                "certificate_sha256": value["certificate_sha256"],
                "factor_bound": 20_000 if args.self_test else args.factor_bound,
                "self_test": args.self_test,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
