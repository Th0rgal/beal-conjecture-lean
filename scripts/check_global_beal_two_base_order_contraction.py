#!/usr/bin/env python3
"""Replay the finite content of the two-base order contraction."""
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
    / "two_base_order_contraction.json"
)


class CheckError(RuntimeError):
    pass


def digest(value: dict[str, Any]) -> str:
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
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


def primes_up_to(n: int) -> list[int]:
    return [p for p in range(2, n + 1) if is_prime(p)]


def multiplicative_order(a: int, p: int) -> int:
    if math.gcd(a, p) != 1:
        raise ValueError("a must be a unit modulo p")
    current = a % p
    value = 1
    while current != 1:
        current = current * a % p
        value += 1
        if value > p:
            raise CheckError("order computation exceeded group size")
    return value


def H(g: int) -> int:
    return math.gcd(pow(2, g) - 1, pow(3, g) - 1)


def subgroup_size(q: int) -> int:
    return math.lcm(
        multiplicative_order(2, q),
        multiplicative_order(3, q),
    )


def verify_samples(value: dict[str, Any]) -> None:
    for raw_g, expected in value["sample_H_values"].items():
        actual = H(int(raw_g))
        if actual != expected:
            raise CheckError(f"H({raw_g})={actual}, expected {expected}")


def verify_fixed_p_equivalence(bound: int) -> None:
    primes = [p for p in primes_up_to(bound) if p > 3]
    orders = {
        p: (
            multiplicative_order(2, p),
            multiplicative_order(3, p),
        )
        for p in primes
    }
    for p in primes:
        a_p, b_p = orders[p]
        G_p = math.gcd(pow(2, a_p) - 1, pow(3, b_p) - 1)
        for q in primes:
            if p == q:
                continue
            a_q, b_q = orders[q]
            order_condition = a_p % a_q == 0 and b_p % b_q == 0
            divisor_condition = G_p % q == 0
            if order_condition != divisor_condition:
                raise CheckError(
                    f"fixed-p equivalence failed for p={p}, q={q}"
                )
            if order_condition:
                g = math.gcd(p - 1, q - 1)
                if H(g) % q:
                    raise CheckError(
                        f"gcd-exponent condition failed for p={p}, q={q}"
                    )


def verify_subgroup_bound(bound: int) -> None:
    log6 = math.log(6)
    for q in primes_up_to(bound):
        if q <= 3:
            continue
        h_q = subgroup_size(q)
        threshold = (math.log(q) / log6) ** 2
        if not h_q > threshold:
            raise CheckError(
                f"subgroup bound failed for q={q}: "
                f"h={h_q}, threshold={threshold}"
            )


def exact_pair_count(X: int) -> int:
    primes = [p for p in primes_up_to(X) if p > 3]
    orders = {
        p: (
            multiplicative_order(2, p),
            multiplicative_order(3, p),
        )
        for p in primes
    }
    count = 0
    for p in primes:
        a_p, b_p = orders[p]
        for q in primes:
            if p == q:
                continue
            a_q, b_q = orders[q]
            if a_p % a_q == 0 and b_p % b_q == 0:
                count += 1
    return count


def explicit_counting_bound(X: int) -> float:
    primes = [p for p in primes_up_to(X) if p > 3]
    small = [q for q in primes if q <= math.sqrt(X)]
    large = [q for q in primes if q > math.sqrt(X)]
    large_bound = sum(
        X * math.log(6) ** 2 / math.log(q) ** 2 + 1
        for q in large
    )
    return len(small) * len(primes) + large_bound


def verify_counts() -> None:
    for X in (100, 250, 500, 1000):
        actual = exact_pair_count(X)
        upper = explicit_counting_bound(X)
        if actual > upper + 1e-9:
            raise CheckError(
                f"finite counting bound failed at X={X}: {actual}>{upper}"
            )


def verify(value: dict[str, Any], finite_bound: int = 500) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("schema version")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("certificate digest")
    if "zero-density" not in value.get("status", ""):
        raise CheckError("status")
    if "does not prove" not in value.get("nonclaim", "").lower():
        raise CheckError("nonclaim")
    if value["conditional_arithmetic_theorem"]["orders"] != [
        "ord_q(2) divides ord_p(2)",
        "ord_q(3) divides ord_p(3)",
    ]:
        raise CheckError("order statements")
    verify_samples(value)
    verify_fixed_p_equivalence(finite_bound)
    verify_subgroup_bound(max(5000, finite_bound))
    verify_counts()


def self_test(value: dict[str, Any]) -> None:
    verify(value, 250)
    mutations: list[dict[str, Any]] = []

    bad = copy.deepcopy(value)
    bad["sample_H_values"]["12"] = 456
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["conditional_arithmetic_theorem"]["orders"].pop()
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["nonclaim"] = "This proves Beal."
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    for index, mutation in enumerate(mutations):
        try:
            verify(mutation, 100)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} was accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, default=CERTIFICATE)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--finite-bound", type=int, default=500)
    args = parser.parse_args()

    value = json.loads(args.certificate.read_text(encoding="utf-8"))
    if args.self_test:
        self_test(value)
    else:
        verify(value, args.finite_bound)

    print(
        json.dumps(
            {
                "status": "ok",
                "self_test": args.self_test,
                "certificate_sha256": value["certificate_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
