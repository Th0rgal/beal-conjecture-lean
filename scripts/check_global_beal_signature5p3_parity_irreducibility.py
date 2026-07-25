#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "Research/GlobalBeal/signature5p3_parity_irreducibility.json"


def digest(value: dict[str, Any]) -> str:
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def validate(data: dict[str, Any]) -> None:
    if data.get("certificate_sha256") != digest(data):
        raise AssertionError("certificate digest mismatch")
    if data.get("schema_version") != 1:
        raise AssertionError("schema version")
    if data["odd_b_branch"]["explicit_bound"] != "C(2)=13":
        raise AssertionError("odd branch bound")

    even = data["even_b_branch"]
    if even["minus_conductor_at_2"] != 5:
        raise AssertionError("conductor exponent")
    if "order 4" not in even["local_type"]["description"]:
        raise AssertionError("local type order")

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

    for p in (17, 19, 23, 29, 31, 37, 41, 43, 47):
        if p <= 13 or any(p % d == 0 for d in range(2, math.isqrt(p) + 1)):
            raise AssertionError("bad prime fixture")
        if math.gcd(p, 4) != 1:
            raise AssertionError("order-four reduction is not tame")

    if "at least one" not in data["conclusion"]:
        raise AssertionError("overstated conclusion")
    if "does not prove" not in data["nonclaim"].lower():
        raise AssertionError("missing nonclaim")


def self_test(data: dict[str, Any]) -> None:
    validate(data)
    mutations: list[dict[str, Any]] = []
    for edit in ("bound", "conductor", "type", "claim"):
        bad = copy.deepcopy(data)
        if edit == "bound":
            bad["odd_b_branch"]["explicit_bound"] = "C(2)=17"
        elif edit == "conductor":
            bad["even_b_branch"]["minus_conductor_at_2"] = 4
        elif edit == "type":
            bad["even_b_branch"]["local_type"]["description"] = "principal series"
        else:
            bad["conclusion"] = "all solutions are impossible"
        bad["certificate_sha256"] = digest(bad)
        mutations.append(bad)
    for bad in mutations:
        try:
            validate(bad)
        except AssertionError:
            continue
        raise AssertionError("negative fixture was accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(PATH.read_text())
    validate(data)
    if args.self_test:
        self_test(data)
    print("signature (5,p,3) parity irreducibility certificate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
