#!/usr/bin/env python3
"""Replay the unconditional signature-(4,5,7) power-residue certificate."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

CERTIFICATE = Path(__file__).resolve().parents[1] / "Research" / "GlobalBeal" / "signature457_power_residue.json"


class CheckError(RuntimeError):
    pass


def digest(value: dict[str, Any]) -> str:
    body = dict(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def units(modulus: int) -> list[int]:
    return [x for x in range(modulus) if math.gcd(x, modulus) == 1]


def verify_parity_mod32() -> None:
    modulus = 32
    found = 0
    for a in range(modulus):
        for b in range(modulus):
            for c in range(modulus):
                if (pow(a, 4, modulus) + pow(b, 5, modulus) - pow(c, 7, modulus)) % modulus:
                    continue
                if sum(x % 2 == 0 for x in (a, b, c)) > 1:
                    continue
                found += 1
                if sum(x % 2 == 0 for x in (a, b, c)) != 1:
                    raise CheckError(f"primitive parity was not unique at {(a,b,c)}")
                if a % 2 == 0:
                    expected_a4 = 16 if a % 4 == 2 else 0
                    if pow(a, 4, modulus) != expected_a4:
                        raise CheckError("bad even-A fourth power")
                    if (c - (pow(b, 3, modulus) + pow(a, 4, modulus))) % modulus:
                        raise CheckError("A-even congruence failed")
                elif b % 2 == 0:
                    if (c - pow(a, 4, modulus)) % modulus or c % 16 != 1:
                        raise CheckError("B-even congruence failed")
                else:
                    if (b + pow(a, 4, modulus)) % modulus or b % 16 != 15:
                        raise CheckError("C-even congruence failed")
    if found != 768:
        raise CheckError(f"unexpected primitive solution count mod 32: {found}")


def verify_group_identities(modulus_bound: int) -> None:
    for modulus in range(2, modulus_bound + 1):
        us = units(modulus)
        for a in us:
            inv_a = pow(a, -1, modulus)
            a4 = pow(a, 4, modulus)
            for c in us:
                if a4 == pow(c, 7, modulus):
                    u = pow(c, 2, modulus) * inv_a % modulus
                    if pow(u, 4, modulus) != c:
                        raise CheckError(f"B^5 identity failed mod {modulus}")
            for b in us:
                if a4 == (-pow(b, 5, modulus)) % modulus:
                    v = -a * pow(b, -1, modulus) % modulus
                    if pow(v, 4, modulus) != (-b) % modulus:
                        raise CheckError(f"C^7 identity failed mod {modulus}")
        for b in us:
            b5 = pow(b, 5, modulus)
            for c in us:
                if b5 != pow(c, 7, modulus):
                    continue
                t = pow(b, 3, modulus) * pow(pow(c, 4, modulus), -1, modulus) % modulus
                if pow(t, 7, modulus) != b or pow(t, 5, modulus) != c:
                    raise CheckError(f"A^4 common parameter failed mod {modulus}")


def verify(value: dict[str, Any], *, modulus_bound: int = 250) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("unexpected schema")
    if value.get("status") != "unconditional-signature-457-power-residue-structure":
        raise CheckError("unexpected status")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("digest mismatch")
    if value.get("scope", {}).get("equation") != "A^4+B^5=C^7":
        raise CheckError("equation mutated")
    if not value.get("parity_theorem", {}).get("exactly_one_even"):
        raise CheckError("parity theorem removed")
    if value["parity_theorem"].get("modulus") != 32:
        raise CheckError("parity modulus mutated")
    rows = value.get("full_modulus_power_congruences", [])
    if len(rows) != 3 or {row["modulus"] for row in rows} != {"A^4", "B^5", "C^7"}:
        raise CheckError("full-modulus coverage mismatch")
    if value.get("impact", {}).get("parent_signature") != "(2,5,7)":
        raise CheckError("parent signature mutated")
    if "does not eliminate" not in value.get("nonclaim", ""):
        raise CheckError("nonclaim weakened")
    verify_parity_mod32()
    verify_group_identities(modulus_bound)


def self_test(value: dict[str, Any]) -> None:
    verify(value, modulus_bound=100)
    mutations: list[dict[str, Any]] = []
    bad = copy.deepcopy(value)
    bad["parity_theorem"]["exactly_one_even"] = False
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)
    bad = copy.deepcopy(value)
    bad["full_modulus_power_congruences"].pop()
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)
    bad = copy.deepcopy(value)
    bad["impact"]["parent_signature"] = "(3,5,7)"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)
    for index, mutation in enumerate(mutations):
        try:
            verify(mutation, modulus_bound=30)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, default=CERTIFICATE)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--modulus-bound", type=int, default=250)
    args = parser.parse_args()
    value = json.loads(args.certificate.read_text())
    if args.self_test:
        self_test(value)
        bound = 100
    else:
        verify(value, modulus_bound=args.modulus_bound)
        bound = args.modulus_bound
    print(json.dumps({"status": "ok", "certificate_sha256": value["certificate_sha256"], "modulus_bound": bound, "self_test": args.self_test}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
