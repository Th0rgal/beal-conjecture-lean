#!/usr/bin/env python3
"""Exact census for odd plus-cyclotomic cofactors.

The GPU/CPU search is untrusted.  This script emits explicit failure lists and
all higher-valuation witnesses so decisive claims can be replayed.
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import time
from pathlib import Path

from provenance import artifact_provenance


def valuation(n: int, p: int) -> int:
    if n <= 0 or p <= 1:
        raise ValueError("valuation expects n > 0 and p > 1")
    v = 0
    while n % p == 0:
        n //= p
        v += 1
    return v


def _is_prime(n: int) -> bool:
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


def validate_ells(ells: list[int]) -> list[int]:
    if len(ells) != len(set(ells)):
        raise ValueError("ells must be unique")
    if not ells or any(ell < 3 or ell % 2 == 0 or not _is_prime(ell) for ell in ells):
        raise ValueError("ells must be distinct odd primes")
    return ells


def cyclotomic_plus_cofactor(u: int, v: int, ell: int) -> int:
    if u <= 0 or v <= 0 or ell < 3 or ell % 2 == 0:
        raise ValueError("u,v must be positive and ell must be odd >= 3")
    numerator = u**ell + v**ell
    denominator = u + v
    q, r = divmod(numerator, denominator)
    if r:
        raise ArithmeticError("odd plus-power factorization failed")
    return q


def _small_factor(n: int) -> dict[int, int]:
    factors: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d = 3 if d == 2 else d + 2
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def multiplicative_order(a: int, p: int) -> int:
    a %= p
    if math.gcd(a, p) != 1:
        raise ValueError("a must be a unit modulo p")
    order = p - 1
    for r in _small_factor(order):
        while order % r == 0 and pow(a, order // r, p) == 1:
            order //= r
    return order


def factor_integer(n: int) -> list[tuple[int, int]]:
    from cypari2 import Pari

    pari = Pari()
    matrix = pari.factor(n)
    return [(int(matrix[i, 0]), int(matrix[i, 1])) for i in range(matrix.nrows())]


def _chunk(args: tuple[int, int, int, int]) -> dict:
    ell, u_lo, u_hi, bound = args
    pairs = prime_factors = exceptional_ell = higher = 0
    gcd_failures: list[dict] = []
    order_failures: list[dict] = []
    congruence_failures: list[dict] = []
    higher_cases: list[dict] = []
    factor_identity_failures: list[dict] = []

    for u in range(u_lo, u_hi):
        for v in range(1, bound + 1):
            if math.gcd(u, v) != 1:
                continue
            pairs += 1
            cofactor = cyclotomic_plus_cofactor(u, v, ell)
            if (u + v) * cofactor != u**ell + v**ell:
                factor_identity_failures.append({"ell": ell, "u": u, "v": v})
                continue
            g = math.gcd(u + v, cofactor)
            if ell % g != 0:
                gcd_failures.append({"ell": ell, "u": u, "v": v, "gcd": g})

            for q, exponent in factor_integer(cofactor):
                prime_factors += 1
                if q == ell:
                    exceptional_ell += 1
                    continue
                inv_v = pow(v, -1, q)
                uv = (u * inv_v) % q
                minus_uv = (-u * inv_v) % q
                order_uv = multiplicative_order(uv, q)
                order_minus = multiplicative_order(minus_uv, q)
                if order_uv != 2 * ell or order_minus != ell:
                    order_failures.append({
                        "ell": ell, "u": u, "v": v, "q": q,
                        "order_uv": order_uv, "order_minus_uv": order_minus,
                    })
                if (q - 1) % (2 * ell) != 0:
                    congruence_failures.append({"ell": ell, "u": u, "v": v, "q": q})
                if exponent > 1:
                    higher += 1
                    higher_cases.append({
                        "ell": ell, "u": u, "v": v, "q": q,
                        "valuation": exponent, "cofactor": str(cofactor),
                    })

    return {
        "pairs": pairs,
        "prime_factors": prime_factors,
        "exceptional_ell_factors": exceptional_ell,
        "higher_valuation_occurrences": higher,
        "higher_valuation_cases": higher_cases,
        "gcd_failures": gcd_failures,
        "order_failures": order_failures,
        "congruence_failures": congruence_failures,
        "factor_identity_failures": factor_identity_failures,
    }


def run(ells: list[int], bound: int, workers: int) -> dict:
    ells = validate_ells(ells)
    if bound < 1 or workers < 1:
        raise ValueError("bound and workers must be positive")
    chunks: list[tuple[int, int, int, int]] = []
    width = max(1, math.ceil(bound / workers))
    for ell in ells:
        for lo in range(1, bound + 1, width):
            chunks.append((ell, lo, min(bound + 1, lo + width), bound))

    started = time.perf_counter()
    if workers == 1:
        partials = [_chunk(c) for c in chunks]
    else:
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=workers) as pool:
            partials = pool.map(_chunk, chunks)

    merged = {
        "schema_version": 1,
        "experiment": "odd_plus_cyclotomic_census",
        "parameters": {"ells": ells, "base_bound": bound, "workers": workers},
        "pairs_tested": sum(p["pairs"] for p in partials),
        "distinct_prime_factor_occurrences_tested": sum(p["prime_factors"] for p in partials),
        "ell_exception_factor_occurrences": sum(p["exceptional_ell_factors"] for p in partials),
        "higher_valuation_occurrences": sum(p["higher_valuation_occurrences"] for p in partials),
        "elapsed_seconds": time.perf_counter() - started,
    }
    for key in ("gcd_failures", "order_failures", "congruence_failures", "factor_identity_failures"):
        merged[key] = sorted((x for p in partials for x in p[key]), key=lambda x: tuple(x.values()))
    merged["higher_valuation_cases"] = sorted(
        (x for p in partials for x in p["higher_valuation_cases"]),
        key=lambda x: (x["ell"], x["u"], x["v"], x["q"]),
    )
    merged["interpretation"] = {
        "bounded_scope": "producer census over the stated ordered coprime base range, with PARI factorization; independently reproduced by independent_reproduce.py",
        "not_proved": "primitive-divisor existence or the unrestricted Beal conjecture",
    }
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ells", default="3,5,7,11")
    parser.add_argument("--bound", type=int, default=100)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ells = validate_ells([int(x) for x in args.ells.split(",") if x])
    result = run(ells, args.bound, args.workers)
    result["provenance"] = artifact_provenance(__file__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in (
        "pairs_tested", "distinct_prime_factor_occurrences_tested",
        "higher_valuation_occurrences", "elapsed_seconds")}, sort_keys=True))


if __name__ == "__main__":
    main()
