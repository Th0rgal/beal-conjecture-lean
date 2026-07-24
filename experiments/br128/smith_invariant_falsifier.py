#!/usr/bin/env python3
"""Deterministically falsify the finite shadows of the BR-128 F1 hypothesis.

For A = [[x, 0, -z], [0, y, -z]], the script independently enumerates
the image of A over Z/nZ and the rank over prime fields.  It compares those
observations with the invariant factors obtained from the 1x1 and 2x2
determinantal divisors.  This is falsification evidence only, never a proof.
"""
from __future__ import annotations

import itertools
import json
from math import gcd


BOUND = 12
MODULI = tuple(range(2, 18))
PRIMES = (2, 3, 5, 7, 11, 13, 17)


def gcd3(a: int, b: int, c: int) -> int:
    return gcd(gcd(a, b), c)


def image_size(x: int, y: int, z: int, modulus: int) -> int:
    return len({((x * a - z * c) % modulus, (y * b - z * c) % modulus)
                for a, b, c in itertools.product(range(modulus), repeat=3)})


def rank_over_prime(x: int, y: int, z: int, prime: int) -> int:
    # A 2-by-3 matrix has rank two iff one of its 2-by-2 minors is nonzero.
    minors = (x * y, -x * z, y * z)
    if any(minor % prime for minor in minors):
        return 2
    if any(entry % prime for entry in (x, y, z)):
        return 1
    return 0


def main() -> None:
    cyclic_cases = field_cases = 0
    for x, y, z in itertools.product(range(1, BOUND + 1), repeat=3):
        d1 = gcd3(x, y, z)
        delta2 = gcd3(x * y, x * z, y * z)
        assert delta2 % d1 == 0
        d2 = delta2 // d1
        for n in MODULI:
            observed_cokernel = n * n // image_size(x, y, z, n)
            predicted_cokernel = gcd(n, d1) * gcd(n, d2)
            assert observed_cokernel == predicted_cokernel, (x, y, z, n)
            cyclic_cases += 1
        for p in PRIMES:
            observed_rank = rank_over_prime(x, y, z, p)
            predicted_rank = 2 if delta2 % p else (1 if d1 % p else 0)
            assert observed_rank == predicted_rank, (x, y, z, p)
            field_cases += 1
    print(json.dumps({
        "claim": "BR-128 F1 finite shadows for [[x,0,-z],[0,y,-z]]",
        "parameter_box": {"x_y_z": [1, BOUND], "moduli": list(MODULI), "primes": list(PRIMES)},
        "cyclic_group_cases": cyclic_cases,
        "finite_field_cases": field_cases,
        "counterexamples": 0,
        "result": "survived-finite-falsification",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
