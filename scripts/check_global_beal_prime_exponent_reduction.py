#!/usr/bin/env python3
"""Replay the global prime-exponent reduction certificate.

The checker validates all finite and algorithmic claims in the certificate:
* the canonical {4 or odd prime} factorization rule on a large deterministic range;
* the exact six special signatures with minimum exponent at least 3;
* the all-prime boundary below exponent sum 19;
* the identification of (3,5,11) as the next boundary after conditionally closing
  (3,5,7).

The survey's completeness and the published solved-signature theorems remain imported
mathematical inputs. Finite replay does not replace those references.
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
    body = dict(value)
    body.pop("certificate_sha256", None)
    encoded = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def odd_prime_divisor(n: int) -> int:
    m = n if n % 2 == 1 else n // 2
    if m < 3 or m % 2 == 0:
        raise CheckError(f"expected an odd integer at least 3, got {m} from n={n}")
    candidate = 3
    while candidate * candidate <= m:
        if m % candidate == 0:
            return candidate
        candidate += 2
    return m


def canonical_factor(n: int) -> tuple[int, int]:
    if n < 3:
        raise ValueError("canonical reduction is defined here only for n >= 3")
    if n % 4 == 0:
        return 4, n // 4
    p = odd_prime_divisor(n)
    return p, n // p


def sorted_odd_prime_triples_below_sum(bound: int) -> list[list[int]]:
    primes = [p for p in range(3, bound) if p % 2 == 1 and is_prime(p)]
    result: list[list[int]] = []
    for i, p in enumerate(primes):
        for j in range(i, len(primes)):
            q = primes[j]
            for k in range(j, len(primes)):
                r = primes[k]
                if p + q + r >= bound:
                    break
                result.append([p, q, r])
    return result


def verify(value: dict[str, Any], *, factor_bound: int = 100_000) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("unexpected schema version")
    if value.get("status") != "literature-assisted-global-prime-exponent-reduction":
        raise CheckError("unexpected status")
    if value.get("certificate_sha256") != canonical_digest(value):
        raise CheckError("certificate digest mismatch")

    canonical = value["unconditional_canonical_reduction"]
    if canonical["canonical_exponents"] != "4 or an odd prime":
        raise CheckError("canonical exponent description was mutated")

    for n in range(3, factor_bound + 1):
        exponent, multiplier = canonical_factor(n)
        if multiplier < 1 or n != exponent * multiplier:
            raise CheckError(f"bad canonical factorization for {n}")
        if exponent == 4:
            if n % 4 != 0:
                raise CheckError(f"used exponent 4 without 4|{n}")
        elif not (exponent % 2 == 1 and is_prime(exponent) and n % exponent == 0):
            raise CheckError(f"noncanonical exponent {exponent} for {n}")

    expected_special = {
        (3, 3, 4),
        (3, 3, 6),
        (3, 3, 9),
        (3, 4, 4),
        (3, 4, 5),
        (4, 4, 4),
    }
    recorded_special = {
        tuple(row)
        for row in value["prime_or_special_reduction"][
            "special_signatures_with_minimum_at_least_3"
        ]
    }
    if recorded_special != expected_special:
        raise CheckError("special-signature inventory mismatch")

    remaining_composite = {
        tuple(row)
        for row in value["prime_or_special_reduction"][
            "remaining_non_all_prime_open_signatures"
        ]
    }
    if remaining_composite != {(2, 3, 25), (2, 5, 9)}:
        raise CheckError("remaining non-all-prime survey inventory mismatch")
    if any(min(row) >= 3 for row in remaining_composite):
        raise CheckError("a purported unresolved composite Beal signature remains")

    expected_boundary = sorted_odd_prime_triples_below_sum(19)
    recorded_boundary = sorted(
        value["conditional_signature357_impact"][
            "covered_prime_signatures_by_sum_below_19"
        ]
    )
    if recorded_boundary != expected_boundary:
        raise CheckError(
            f"prime boundary mismatch: expected {expected_boundary}, got {recorded_boundary}"
        )

    sum_19 = sorted(
        row
        for row in sorted_odd_prime_triples_below_sum(20)
        if sum(row) == 19
    )
    solved_sum_19 = sorted(
        value["conditional_signature357_impact"]["solved_prime_signatures_of_sum_19"]
    )
    next_signature = value["conditional_signature357_impact"][
        "next_smallest_open_signature_by_exponent_sum"
    ]
    if sorted(solved_sum_19 + [next_signature]) != sum_19:
        raise CheckError(
            f"sum-19 partition mismatch: expected {sum_19}, got "
            f"{sorted(solved_sum_19 + [next_signature])}"
        )

    if next_signature != [3, 5, 11]:
        raise CheckError("next signature was mutated")
    if sum(next_signature) != 19 or not all(is_prime(p) and p % 2 for p in next_signature):
        raise CheckError("next signature is not an odd-prime triple of sum 19")

    covered = {tuple(row) for row in recorded_boundary}
    for row in sorted_odd_prime_triples_below_sum(sum(next_signature)):
        if tuple(row) not in covered:
            raise CheckError(f"uncovered smaller prime signature {row}")


def run_self_test(value: dict[str, Any]) -> None:
    verify(value, factor_bound=20_000)

    mutations: list[dict[str, Any]] = []

    bad = copy.deepcopy(value)
    bad["unconditional_canonical_reduction"]["canonical_exponents"] = "odd primes only"
    bad["certificate_sha256"] = canonical_digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["prime_or_special_reduction"][
        "special_signatures_with_minimum_at_least_3"
    ].pop()
    bad["certificate_sha256"] = canonical_digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["conditional_signature357_impact"][
        "next_smallest_open_signature_by_exponent_sum"
    ] = [3, 7, 7]
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
        run_self_test(value)
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
