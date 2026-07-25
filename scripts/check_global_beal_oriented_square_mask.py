#!/usr/bin/env python3
"""Replay the oriented square-mask cofinality and descent certificates."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import tempfile
from typing import Any, Callable

ROOT = pathlib.Path(__file__).resolve().parents[1]
COFINALITY = ROOT / "Research" / "GlobalBeal" / "double_square_mask_cofinality.json"
CROSS = ROOT / "Research" / "GlobalBeal" / "cross_side_square_mask_descent.json"
EXPECTED_PRIMES = [
    5, 7, 11, 13, 19, 23, 37, 47, 53, 59, 61, 67, 71, 79, 83,
    101, 103, 107, 131, 139, 149, 163, 167, 173, 179, 181, 191,
    197, 199,
]


class CheckError(RuntimeError):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(value, dict):
        raise CheckError("certificate root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def is_prime(n: int) -> bool:
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def verify_digest(value: dict[str, Any], label: str) -> None:
    if value.get("schema_version") != 1:
        raise CheckError(f"{label}: schema mismatch")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError(f"{label}: digest mismatch")


def verify_cofinality(value: dict[str, Any]) -> None:
    verify_digest(value, "cofinality")
    primes = value["source"]["right_primes"]
    if primes != EXPECTED_PRIMES or len(primes) != 29:
        raise CheckError("right-prime inventory mismatch")
    if any(not is_prime(p) or p > 200 for p in primes):
        raise CheckError("invalid right prime")
    if "p<=V_r or q<=V_r" not in value["prime_mask_theorem"]["statement"]:
        raise CheckError("finite-boundary implication missing")
    if "V_r-smooth" not in value["composite_exponent_lift"]["statement"]:
        raise CheckError("smoothness deduction missing")
    if "not_covered" not in value["orientation_boundary"]:
        raise CheckError("orientation boundary missing")


def minus_cyclotomic(v: int, u: int, q: int) -> int:
    return sum(v ** (q - 1 - i) * u**i for i in range(q))


def plus_cyclotomic(v: int, u: int, q: int) -> int:
    return sum((-1) ** i * v ** (q - 1 - i) * u**i for i in range(q))


def verify_cross(value: dict[str, Any]) -> None:
    verify_digest(value, "cross")
    if "q cannot divide both" not in value["odd_Y_branch"]["synchronization"]:
        raise CheckError("synchronization conclusion missing")

    for q in (3, 5, 7, 11):
        for u in range(1, 40, 2):
            for v in range(u + 2, 60, 2):
                if math.gcd(u, v) != 1:
                    continue
                minus = minus_cyclotomic(v, u, q)
                plus = plus_cyclotomic(v, u, q)
                if v**q - u**q != (v - u) * minus:
                    raise CheckError("minus factorization failed")
                if v**q + u**q != (v + u) * plus:
                    raise CheckError("plus factorization failed")
                if math.gcd(v - u, minus) not in (1, q):
                    raise CheckError("minus gcd bound failed")
                if math.gcd(v + u, plus) not in (1, q):
                    raise CheckError("plus gcd bound failed")
                if (v - u) % q == 0 and (v + u) % q == 0:
                    raise CheckError("both branches became q-exceptional")

    for x in range(1, 50):
        for z in range(x + 1, 60):
            if math.gcd(x, z) != 1:
                continue
            for p in (3, 5):
                for r in (3, 5):
                    U = z**r - x**p
                    if U <= 0:
                        continue
                    V = z**r + x**p
                    if U * V != z ** (2 * r) - x ** (2 * p):
                        raise CheckError("U,V product identity failed")
                    if math.gcd(U, V) not in (1, 2):
                        raise CheckError("gcd(U,V) is not 1 or 2")


def expect_rejection(
    value: dict[str, Any], verifier: Callable[[dict[str, Any]], None],
    mutation: Callable[[dict[str, Any]], None], label: str,
) -> None:
    bad = copy.deepcopy(value)
    mutation(bad)
    bad["certificate_sha256"] = digest(bad)
    try:
        verifier(bad)
    except CheckError:
        return
    raise CheckError(f"negative fixture accepted: {label}")


def self_test(cofinality: dict[str, Any], cross: dict[str, Any]) -> None:
    verify_cofinality(cofinality)
    verify_cross(cross)
    expect_rejection(
        cofinality, verify_cofinality,
        lambda value: value["source"]["right_primes"].pop(),
        "deleted right prime",
    )
    expect_rejection(
        cross, verify_cross,
        lambda value: value["odd_Y_branch"].update({"synchronization": "none"}),
        "deleted synchronization",
    )
    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        handle.write('{"x":1,"x":2}')
        path = pathlib.Path(handle.name)
    try:
        try:
            load(path)
        except CheckError:
            pass
        else:
            raise CheckError("duplicate keys accepted")
    finally:
        path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    cofinality = load(COFINALITY)
    cross = load(CROSS)
    if args.self_test:
        self_test(cofinality, cross)
    else:
        verify_cofinality(cofinality)
        verify_cross(cross)
    print(json.dumps({
        "status": "ok",
        "self_test": args.self_test,
        "cofinality_certificate": cofinality["certificate_sha256"],
        "cross_certificate": cross["certificate_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
