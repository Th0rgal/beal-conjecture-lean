#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CERT = ROOT / "Research" / "GlobalBeal" / "graph_or_ray_certificate.json"


class CheckError(RuntimeError):
    pass


def digest(value):
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()).hexdigest()


def primes_upto(limit):
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, math.isqrt(limit) + 1):
        if sieve[p]:
            count = (limit - p * p) // p + 1
            sieve[p * p:limit + 1:p] = b"\x00" * count
    return [n for n in range(2, limit + 1) if sieve[n]]


def fueter(p, n):
    return tuple(((n + 1) * c) // p - (n * c) // p for c in range(1, p))


def sigma(p, vector, a):
    inverse = pow(a, -1, p)
    result = [0] * (p - 1)
    for c, coefficient in enumerate(vector, 1):
        result[(c * inverse % p) - 1] += coefficient
    return tuple(result)


def conjugates(p):
    result, seen = [], set()
    for n in range(1, (p - 1) // 2 + 1):
        base = fueter(p, n)
        for a in range(1, p):
            value = sigma(p, base, a)
            if value not in seen:
                seen.add(value)
                result.append(value)
    return result


def phi(p, vector):
    return sum(
        coefficient * pow(c, -1, p)
        for c, coefficient in enumerate(vector, 1)
    ) % p


def multiply(a, b, p):
    product = 0
    while b:
        if b & 1:
            product ^= a
        b >>= 1
        a <<= 1
    modulus = (1 << p) - 1
    while product.bit_length() - 1 >= p - 1:
        degree = product.bit_length() - 1
        product ^= modulus << (degree - (p - 1))
    return product


def power(base, exponent, p):
    result = 1
    while exponent:
        if exponent & 1:
            result = multiply(result, base, p)
        base = multiply(base, base, p)
        exponent >>= 1
    return result


def zeta(p, exponent):
    return power(2, exponent % p, p)


def action(p, vector):
    result = 1
    for c, coefficient in enumerate(vector, 1):
        if coefficient:
            factor = 1 ^ zeta(p, pow(c, -1, p))
            result = multiply(result, power(factor, coefficient, p), p)
    return result


def verify(value):
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("digest")
    if value.get("schema_version") != 1:
        raise CheckError("schema")
    if value.get("status") != (
        "unconditional-mod2-collapse-and-graph-or-ray-class-dichotomy"
    ):
        raise CheckError("status")
    if value["mod2_collapse_theorem"]["key_norm"] != (
        "Norm_K/Q(zeta+zeta^(-1))=Phi_p(-1)=1"
    ):
        raise CheckError("norm")
    if "does not prove" not in value.get("nonclaim", ""):
        raise CheckError("nonclaim")

    expected = {row["p"]: row for row in value["finite_audit"]["rows"]}
    bound = value["finite_audit"]["prime_bound"]
    for p in [q for q in primes_upto(bound) if q >= 5]:
        rows = conjugates(p)
        inverse_two = pow(2, -1, p)
        values = []
        for vector in rows:
            current = phi(p, vector)
            values.append(current)
            assert action(p, vector) == zeta(p, current * inverse_two)
        frequencies = Counter(values)
        zero_pairs = sum(
            frequencies[a] * frequencies[(-a) % p]
            for a in frequencies
        )
        record = expected[p]
        assert record["conjugate_fueter_count"] == len(rows)
        assert record["phi_zero_ordered_pairs"] == zero_pairs
        assert record["all_generator_identities_verified"] is True


def self_test(value):
    verify(value)
    mutations = []

    bad = copy.deepcopy(value)
    bad["mod2_collapse_theorem"]["key_norm"] = "Norm=-1"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["finite_audit"]["rows"][0]["phi_zero_ordered_pairs"] += 1
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["nonclaim"] = "This proves Beal."
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    for index, mutation in enumerate(mutations):
        try:
            verify(mutation)
        except (AssertionError, CheckError):
            continue
        raise CheckError(f"negative fixture {index} accepted")


def main():
    value = json.loads(CERT.read_text(encoding="utf-8"))
    verify(value)
    self_test(value)
    print(json.dumps({
        "status": "ok",
        "certificate_sha256": value["certificate_sha256"],
        "audited_primes": [row["p"] for row in value["finite_audit"]["rows"]],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
