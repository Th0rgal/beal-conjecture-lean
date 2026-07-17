#!/usr/bin/env python3
"""Exact bounded falsifier for the odd-prime plus-sign LTE formula."""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path


def valuation(n: int, p: int) -> int:
    if n <= 0 or p <= 1:
        raise ValueError("valuation expects n > 0 and p > 1")
    v = 0
    while n % p == 0:
        n //= p
        v += 1
    return v


def primes_up_to(limit: int) -> list[int]:
    sieve = bytearray(b"\x01") * (limit + 1)
    if limit >= 0:
        sieve[0:2] = b"\x00\x00"
    for p in range(2, int(limit**0.5) + 1):
        if sieve[p]:
            sieve[p * p : limit + 1 : p] = b"\x00" * (((limit - p * p) // p) + 1)
    return [p for p in range(2, limit + 1) if sieve[p]]


def lte_holds(q: int, a: int, b: int, n: int) -> bool:
    return valuation(a**n + b**n, q) == valuation(a + b, q) + valuation(n, q)


def _first_counterexample(predicate, qs, a_bound: int, n_values: list[int]):
    for q in qs:
        for a in range(1, a_bound + 1):
            for b in range(1, a_bound + 1):
                for n in n_values:
                    if predicate(q, a, b, n) and not lte_holds(q, a, b, n):
                        return {
                            "q": q, "a": a, "b": b, "n": n,
                            "lhs_valuation": valuation(a**n + b**n, q),
                            "rhs_valuation": valuation(a + b, q) + valuation(n, q),
                        }
    return None


def run(a_bound: int, prime_bound: int, n_bound: int) -> dict:
    started = time.perf_counter()
    odd_primes = [q for q in primes_up_to(prime_bound) if q != 2]
    odd_ns = list(range(3, n_bound + 1, 2))
    even_ns = list(range(2, n_bound + 1, 2))
    valid_cases = 0
    violations: list[dict] = []

    for q in odd_primes:
        for a in range(1, a_bound + 1):
            for b in range(1, a_bound + 1):
                if math.gcd(a, b) != 1 or (a + b) % q or (a * b) % q == 0:
                    continue
                for n in odd_ns:
                    valid_cases += 1
                    if not lte_holds(q, a, b, n):
                        violations.append({"q": q, "a": a, "b": b, "n": n})

    counters = {
        "remove_odd_n": _first_counterexample(
            lambda q, a, b, n: math.gcd(a, b) == 1 and (a + b) % q == 0 and (a * b) % q != 0,
            odd_primes, a_bound, even_ns,
        ),
        "remove_q_divides_sum": _first_counterexample(
            lambda q, a, b, n: math.gcd(a, b) == 1 and (a + b) % q != 0 and (a * b) % q != 0,
            odd_primes, a_bound, odd_ns,
        ),
        "remove_q_coprime_ab": _first_counterexample(
            lambda q, a, b, n: (a + b) % q == 0 and (a * b) % q == 0,
            odd_primes, a_bound, odd_ns,
        ),
        "allow_q_two_with_odd_n": _first_counterexample(
            lambda q, a, b, n: math.gcd(a, b) == 1 and (a + b) % 2 == 0 and (a * b) % 2 != 0,
            [2], a_bound, odd_ns,
        ),
    }

    return {
        "schema_version": 1,
        "experiment": "plus_lte_assumption_miner",
        "parameters": {"a_bound": a_bound, "prime_bound": prime_bound, "n_bound": n_bound},
        "valid_hypothesis_cases_tested": valid_cases,
        "valid_hypothesis_violations": violations,
        "minimal_counterexamples_when_assumption_removed": counters,
        "elapsed_seconds": time.perf_counter() - started,
        "interpretation": {
            "certified_scope": "finite exhaustive check under stated bounds",
            "not_proved": "the general LTE theorem; zero bounded violations are only falsification evidence",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a-bound", type=int, default=200)
    parser.add_argument("--prime-bound", type=int, default=97)
    parser.add_argument("--n-bound", type=int, default=31)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.a_bound, args.prime_bound, args.n_bound)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "cases": result["valid_hypothesis_cases_tested"],
        "violations": len(result["valid_hypothesis_violations"]),
        "elapsed_seconds": result["elapsed_seconds"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
