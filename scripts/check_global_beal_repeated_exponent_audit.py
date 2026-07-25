#!/usr/bin/env python3
"""Replay the decomposition-group audit for the repeated-exponent family.

The unconditional part is finite group theory:
    D=< (a,b) > in C_m x C_n has D intersect ({0} x C_n)={0}
    exactly when n divides m.
This does not imply D is contained in C_m x {0}.

The arithmetic Mersenne sieve is checked as a conditional consequence of the
ideal-theoretic splitting statement imported from arXiv:2509.18275.
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
    body = dict(value)
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
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def multiplicative_order(a: int, prime: int) -> int:
    if not is_prime(prime) or a % prime == 0:
        raise ValueError("order requires a unit modulo a prime")
    value = 1
    for order in range(1, prime):
        value = value * a % prime
        if value == 1:
            return order
    raise CheckError("multiplicative order search failed")


def abstract_decomposition_group(m: int, n: int) -> set[tuple[int, int]]:
    order = math.lcm(m, n)
    return {(k % m, k % n) for k in range(order)}


def intersection_with_second_factor(
    group: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    return {(a, b) for a, b in group if a == 0}


def verify_group_equivalence(limit: int = 80) -> None:
    for m in range(1, limit + 1):
        for n in range(1, limit + 1):
            group = abstract_decomposition_group(m, n)
            trivial = intersection_with_second_factor(group) == {(0, 0)}
            if trivial != (m % n == 0):
                raise CheckError(
                    f"intersection equivalence failed for orders m={m}, n={n}"
                )


def order_sieve_holds(p: int, q: int) -> bool:
    m = multiplicative_order(2, p)
    n = multiplicative_order(2, q)
    return m % n == 0


def mersenne_gcd_holds(p: int, q: int) -> bool:
    g = math.gcd(p - 1, q - 1)
    return pow(2, g, q) == 1


def verify(value: dict[str, Any]) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("unexpected schema")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("digest mismatch")
    if value.get("source_claim_audited", {}).get("verdict") != "invalid":
        raise CheckError("the invalid inference was not marked invalid")

    verify_group_equivalence()

    example = value["explicit_counterexample_to_inference"]
    p, q, r = example["p"], example["q"], example["r"]
    m = multiplicative_order(r, p)
    n = multiplicative_order(r, q)
    if (m, n) != (example["ord_p_r"], example["ord_q_r"]):
        raise CheckError("counterexample orders mismatch")
    group = abstract_decomposition_group(m, n)
    if intersection_with_second_factor(group) != {(0, 0)}:
        raise CheckError("counterexample intersection is not trivial")
    if all(second == 0 for _, second in group):
        raise CheckError("counterexample group unexpectedly lies in first factor")
    if r % q == 1:
        raise CheckError("counterexample prime unexpectedly splits in Q(zeta_q)")

    samples = value["sample_order_sieve"]
    for p, q in samples["eliminated_pairs_p_q"]:
        if not (is_prime(p) and is_prime(q) and p > 3 and q > 3 and p != q):
            raise CheckError(f"bad eliminated sample {(p, q)}")
        if mersenne_gcd_holds(p, q):
            raise CheckError(f"eliminated sample {(p, q)} passes the sieve")

    for p, q in samples["surviving_pairs_p_q"]:
        if not order_sieve_holds(p, q):
            raise CheckError(f"surviving sample {(p, q)} fails the order condition")
        if not mersenne_gcd_holds(p, q):
            raise CheckError(f"surviving sample {(p, q)} fails the gcd-Mersenne condition")

    # Exhaustively verify the logical implication
    # ord_q(2) | ord_p(2) => q | 2^g-1 for a deterministic prime range.
    primes = [n for n in range(5, 400) if is_prime(n)]
    for p in primes:
        for q in primes:
            if p == q:
                continue
            if order_sieve_holds(p, q) and not mersenne_gcd_holds(p, q):
                raise CheckError(f"order-to-Mersenne implication failed at {(p, q)}")

    # The gcd-two subfamily has no q>3 passing the Mersenne test.
    for p in primes:
        for q in primes:
            if p == q or math.gcd(p - 1, q - 1) != 2:
                continue
            if mersenne_gcd_holds(p, q):
                raise CheckError(f"gcd-two fixture unexpectedly survives at {(p, q)}")


def self_test(value: dict[str, Any]) -> None:
    verify(value)

    mutations: list[dict[str, Any]] = []

    bad = copy.deepcopy(value)
    bad["source_claim_audited"]["verdict"] = "valid"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["explicit_counterexample_to_inference"]["ord_q_r"] = 1
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["sample_order_sieve"]["eliminated_pairs_p_q"][0] = [11, 31]
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    for index, mutation in enumerate(mutations):
        try:
            verify(mutation)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} was accepted")


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
