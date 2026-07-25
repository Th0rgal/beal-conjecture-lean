#!/usr/bin/env python3
"""Replay the uniform full-modulus theorem for A^4+B^p=C^q."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

CERTIFICATE = Path(__file__).resolve().parents[1] / "Research" / "GlobalBeal" / "one_four_core_power_residue.json"


class CheckError(RuntimeError):
    pass


def digest(value: dict[str, Any]) -> str:
    body = dict(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def egcd(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x, y = egcd(b, a % b)
    return g, y, x - (a // b) * y


def units(n: int) -> list[int]:
    return [x for x in range(n) if math.gcd(x, n) == 1]


def root_of_c(a: int, c: int, q: int, n: int) -> int:
    if q % 4 == 1:
        k = (q - 1) // 4
        return a * pow(pow(c, k, n), -1, n) % n
    if q % 4 == 3:
        k = (q - 3) // 4
        return pow(c, k + 1, n) * pow(a, -1, n) % n
    raise ValueError("q must be odd")


def root_of_minus_b(a: int, b: int, p: int, n: int) -> int:
    d = (-b) % n
    if p % 4 == 1:
        k = (p - 1) // 4
        return a * pow(pow(d, k, n), -1, n) % n
    if p % 4 == 3:
        k = (p - 3) // 4
        return pow(d, k + 1, n) * pow(a, -1, n) % n
    raise ValueError("p must be odd")


def verify_parity() -> None:
    for p in range(3, 18, 2):
        for q in range(3, 18, 2):
            if math.gcd(p, q) != 1:
                continue
            count = 0
            for a in range(8):
                for b in range(8):
                    for c in range(8):
                        if (pow(a, 4, 8) + pow(b, p, 8) - pow(c, q, 8)) % 8:
                            continue
                        if sum(x % 2 == 0 for x in (a, b, c)) > 1:
                            continue
                        count += 1
                        if sum(x % 2 == 0 for x in (a, b, c)) != 1:
                            raise CheckError("parity uniqueness failed")
                        if a % 2 == 0 and (b - c) % 8:
                            raise CheckError("A-even branch failed")
                        if b % 2 == 0 and c % 8 != 1:
                            raise CheckError("B-even branch failed")
                        if c % 2 == 0 and b % 8 != 7:
                            raise CheckError("C-even branch failed")
            if count == 0:
                raise CheckError(f"unexpected empty parity replay for {(p,q)}")


def verify_groups(modulus_bound: int, exponent_bound: int) -> None:
    odds = [e for e in range(3, exponent_bound + 1, 2)]
    for n in range(2, modulus_bound + 1):
        us = units(n)
        for p in odds:
            for q in odds:
                if math.gcd(p, q) != 1:
                    continue
                g, a_coeff, b_coeff = egcd(q, p)
                if g != 1 or a_coeff * q + b_coeff * p != 1:
                    raise CheckError("Bezout failure")
                for a in us:
                    a4 = pow(a, 4, n)
                    for c in us:
                        if a4 == pow(c, q, n):
                            if pow(root_of_c(a, c, q, n), 4, n) != c:
                                raise CheckError(f"C root failed mod {n}")
                    for b in us:
                        if a4 == pow((-b) % n, p, n):
                            if pow(root_of_minus_b(a, b, p, n), 4, n) != (-b) % n:
                                raise CheckError(f"-B root failed mod {n}")
                for b in us:
                    bp = pow(b, p, n)
                    for c in us:
                        if bp != pow(c, q, n):
                            continue
                        t = pow(b, a_coeff, n) * pow(c, b_coeff, n) % n
                        if pow(t, q, n) != b or pow(t, p, n) != c:
                            raise CheckError(f"common parameter failed mod {n}")


def verify(value: dict[str, Any], *, modulus_bound: int = 80, exponent_bound: int = 15) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("schema")
    if value.get("status") != "unconditional-one-four-core-power-residue-structure":
        raise CheckError("status")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("digest")
    if value.get("scope", {}).get("equation") != "A^4+B^p=C^q":
        raise CheckError("equation")
    if not value.get("parity_theorem", {}).get("exactly_one_even"):
        raise CheckError("parity")
    if value.get("source_dependencies") != "none; the theorem is elementary group arithmetic plus parity":
        raise CheckError("dependencies")
    if value.get("common_parameter_mod_A4", {}).get("conclusions") != ["t^q=B modulo A^4", "t^p=C modulo A^4"]:
        raise CheckError("common parameter conclusions")
    if "does not eliminate" not in value.get("nonclaim", ""):
        raise CheckError("nonclaim")
    verify_parity()
    verify_groups(modulus_bound, exponent_bound)


def self_test(value: dict[str, Any]) -> None:
    verify(value, modulus_bound=35, exponent_bound=11)
    mutations: list[dict[str, Any]] = []
    bad = copy.deepcopy(value)
    bad["parity_theorem"]["exactly_one_even"] = False
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)
    bad = copy.deepcopy(value)
    bad["common_parameter_mod_A4"]["conclusions"].pop()
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)
    bad = copy.deepcopy(value)
    bad["source_dependencies"] = "abc conjecture"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)
    for index, mutation in enumerate(mutations):
        try:
            verify(mutation, modulus_bound=10, exponent_bound=7)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, default=CERTIFICATE)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--modulus-bound", type=int, default=80)
    parser.add_argument("--exponent-bound", type=int, default=15)
    args = parser.parse_args()
    value = json.loads(args.certificate.read_text())
    if args.self_test:
        self_test(value)
    else:
        verify(value, modulus_bound=args.modulus_bound, exponent_bound=args.exponent_bound)
    print(json.dumps({"status": "ok", "certificate_sha256": value["certificate_sha256"], "self_test": args.self_test}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
