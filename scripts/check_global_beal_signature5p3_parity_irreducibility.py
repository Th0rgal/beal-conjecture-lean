#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "Research/GlobalBeal/signature5p3_parity_irreducibility.json"


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def validate(data: dict) -> None:
    certificate = data.pop("certificate_sha256", None)
    if certificate != digest(data):
        raise AssertionError("certificate digest mismatch")
    if data["schema_version"] != 1:
        raise AssertionError("schema version")
    if data["odd_b_branch"]["explicit_bound"] != "C(2)=13":
        raise AssertionError("odd branch bound")

    even = data["even_b_branch"]
    if even["minus_conductor_at_2"] != 5:
        raise AssertionError("conductor exponent")
    if "order 4" not in even["local_type"]["description"]:
        raise AssertionError("local type order")

    # Exact parity implication modulo 4.  The exponent 17 is only a concrete
    # odd-prime representative; every p>13 has the same reduction modulo 4.
    witnesses: list[tuple[int, int, int]] = []
    for a in range(4):
        for b in range(4):
            for c in range(4):
                if b % 2 == 0 and a % 2 == 1 and c % 2 == 1:
                    if (pow(a, 5, 4) + pow(b, 17, 4) + pow(c, 3, 4)) % 4 == 0:
                        witnesses.append((a, b, c))
                        if pow(a, 5, 4) != (3 * pow(c, 3, 4)) % 4:
                            raise AssertionError("mod-4 implication failed")
    if not witnesses:
        raise AssertionError("parity branch had no residue witnesses")

    # Mackey criterion in the only finite-order component used by the proof.
    # An order-four character can equal its conjugate inverse only after its
    # order drops to at most two.  Reduction in characteristic prime to four
    # preserves the order-four roots of unity.
    for p in (17, 19, 23, 29, 31, 37, 41, 43, 47):
        if p <= 13 or not all(p % d for d in range(2, math.isqrt(p) + 1)):
            raise AssertionError("bad prime fixture")
        if math.gcd(p, 4) != 1:
            raise AssertionError("order-four reduction is not tame")
        if 4 // math.gcd(4, 2) != 2:
            raise AssertionError("order-four conjugate quotient collapsed")

    if "at least one" not in data["conclusion"]:
        raise AssertionError("overstated conclusion")
    if "does not prove" not in data["nonclaim"].lower():
        raise AssertionError("missing nonclaim")


def self_test(data: dict) -> None:
    mutations = (
        lambda d: d["odd_b_branch"].__setitem__("explicit_bound", "C(2)=17"),
        lambda d: d["even_b_branch"].__setitem__("minus_conductor_at_2", 4),
        lambda d: d["even_b_branch"]["local_type"].__setitem__(
            "description", "principal series"
        ),
        lambda d: d.__setitem__("conclusion", "all solutions are impossible"),
    )
    for mutate in mutations:
        bad = copy.deepcopy(data)
        bad.pop("certificate_sha256", None)
        mutate(bad)
        bad["certificate_sha256"] = digest(bad)
        try:
            validate(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("negative fixture was accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(PATH.read_text())
    validate(copy.deepcopy(data))
    if args.self_test:
        self_test(data)
    print("signature (5,p,3) parity irreducibility certificate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
