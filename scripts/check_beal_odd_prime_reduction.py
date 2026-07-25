#!/usr/bin/env python3
"""Replay the exact Beal-range special-signature classification.

This checker verifies finite arithmetic and the canonical certificate digest. It
does not replay the three imported literature theorems at signatures (3,3,4),
(3,4,4), and (3,4,5).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CERT = ROOT / "Research" / "beal_odd_prime_reduction.json"

EXPECTED_SPECIAL = {
    (3, 3, 4),
    (3, 3, 6),
    (3, 3, 9),
    (3, 4, 4),
    (3, 4, 5),
    (4, 4, 4),
}


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def prime(n: int) -> bool:
    if n < 2:
        return False
    return all(n % d for d in range(2, math.isqrt(n) + 1))


def divisors(n: int) -> list[int]:
    return [d for d in range(1, n + 1) if n % d == 0]


def hyperbolic(signature: tuple[int, int, int]) -> bool:
    p, q, r = signature
    return p * q + p * r + q * r < p * q * r


def special(signature: tuple[int, int, int]) -> bool:
    p, q, r = signature
    if all(prime(n) for n in signature) or not hyperbolic(signature):
        return False
    for P in divisors(p):
        for Q in divisors(q):
            for R in divisors(r):
                if (P, Q, R) != signature and hyperbolic((P, Q, R)):
                    return False
    return True


def classify_by_proof_cases(
    p: int, q: int, r: int
) -> tuple[int, int, int] | None:
    """Executable form of the unbounded case split in the research note.

    The input is ordered and assumed to satisfy the special-signature predicate.
    Each branch uses only exact inequalities and elementary divisor bounds.
    """
    assert 3 <= p <= q <= r
    assert special((p, q, r))

    def large_proper_divisor(n: int) -> int:
        """A composite integer at least six has a proper divisor at least three."""
        assert n >= 6 and not prime(n)
        d = max(x for x in divisors(n) if x < n)
        assert d >= 3
        return d

    if p >= 5:
        # Some coordinate is composite. Replacing it by a divisor >= 3 leaves
        # all other coordinates >= 5, so the reciprocal sum is at most 11/15.
        for index, n in enumerate((p, q, r)):
            if not prime(n):
                d = large_proper_divisor(n)
                shadow = [p, q, r]
                shadow[index] = d
                assert 15 * (
                    shadow[0] * shadow[1]
                    + shadow[0] * shadow[2]
                    + shadow[1] * shadow[2]
                ) <= 11 * shadow[0] * shadow[1] * shadow[2]
                assert hyperbolic(tuple(shadow))
                raise AssertionError("a p>=5 triple cannot be special")
        raise AssertionError("special requires a composite coordinate")

    if p == 4:
        # The proper shadow (2,q,r) must be non-hyperbolic.
        assert 2 * q + 2 * r + q * r >= 2 * q * r
        assert q == 4 and r == 4
        return (4, 4, 4)

    assert p == 3
    if q >= 5:
        # Any composite coordinate yields a (3,>=3,>=5) hyperbolic shadow.
        for index, n in enumerate((q, r), start=1):
            if not prime(n):
                d = large_proper_divisor(n)
                shadow = [p, q, r]
                shadow[index] = d
                assert 15 * (
                    shadow[0] * shadow[1]
                    + shadow[0] * shadow[2]
                    + shadow[1] * shadow[2]
                ) <= 13 * shadow[0] * shadow[1] * shadow[2]
                assert hyperbolic(tuple(shadow))
                raise AssertionError(
                    "a q>=5 non-all-prime triple cannot be special"
                )
        raise AssertionError("special requires a composite coordinate")

    if q == 4:
        # The shadow (3,2,r) is non-hyperbolic, forcing r <= 6.
        assert 3 * 2 + 3 * r + 2 * r >= 3 * 2 * r
        assert r <= 6
        if r == 6:
            assert hyperbolic((3, 4, 3))
            raise AssertionError("(3,4,6) has a hyperbolic proper shadow")
        assert r in (4, 5)
        return (3, 4, r)

    assert q == 3
    assert not prime(r)
    largest = max(d for d in divisors(r) if d < r)
    # The shadow (3,3,largest) must be non-hyperbolic.
    assert 9 + 6 * largest >= 9 * largest
    assert largest <= 3
    if r % 2 == 0:
        assert r // 2 <= largest <= 3
        assert r in (4, 6)
    else:
        smallest_prime = min(d for d in divisors(r) if prime(d))
        assert smallest_prime >= 3
        assert r // smallest_prime <= largest <= 3
        assert r <= 9
        assert r == 9
    return (3, 3, r)


def verify(value: dict[str, Any]) -> None:
    digest = value.pop("certificate_sha256")
    assert canonical_digest(value) == digest

    recorded = {
        tuple(row)
        for row in value["classification"][
            "ordered_beal_range_special_signatures"
        ]
    }
    assert recorded == EXPECTED_SPECIAL

    for signature in EXPECTED_SPECIAL:
        assert special(signature)
        assert classify_by_proof_cases(*signature) == signature

    # Independent finite audit beyond the algebraic boundary in the proof.
    observed = set()
    for p in range(3, 65):
        for q in range(p, 65):
            for r in range(q, 65):
                if special((p, q, r)):
                    observed.add((p, q, r))
    assert observed == EXPECTED_SPECIAL

    trusted = value["boundary_status"]["trusted_divisor_reductions"]
    flattened = {
        tuple(signature)
        for row in trusted
        for signature in row["signatures"]
    }
    assert flattened == {(3, 3, 6), (3, 3, 9), (4, 4, 4)}
    assert 3 == math.gcd(3, 6) == math.gcd(3, 9)

    literature = {
        tuple(row["signature"])
        for row in value["boundary_status"][
            "literature_solved_formalization_pending"
        ]
    }
    assert literature == {(3, 3, 4), (3, 4, 4), (3, 4, 5)}
    assert flattened | literature == EXPECTED_SPECIAL

    # Every prime at least three is odd.
    for n in range(3, 257):
        if prime(n):
            assert n % 2 == 1


def self_test() -> None:
    original = json.loads(CERT.read_text())
    verify(json.loads(json.dumps(original)))

    mutations = []
    bad = json.loads(json.dumps(original))
    bad["classification"]["ordered_beal_range_special_signatures"].pop()
    mutations.append(bad)

    bad = json.loads(json.dumps(original))
    bad["classification"]["ordered_beal_range_special_signatures"].append(
        [3, 4, 6]
    )
    mutations.append(bad)

    bad = json.loads(json.dumps(original))
    bad["boundary_status"]["literature_solved_formalization_pending"][0][
        "signature"
    ] = [3, 3, 5]
    mutations.append(bad)

    bad = json.loads(json.dumps(original))
    bad["certificate_sha256"] = "0" * 64
    mutations.append(bad)

    for bad in mutations:
        try:
            verify(bad)
        except (AssertionError, KeyError, ValueError):
            pass
        else:
            raise AssertionError("negative fixture unexpectedly passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        verify(json.loads(CERT.read_text()))
    print("beal odd-prime reduction certificate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
