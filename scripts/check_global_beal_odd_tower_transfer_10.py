#!/usr/bin/env python3
"""Replay the unconditional {2a,3b,10c} infinite-family theorem."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "Research" / "GlobalBeal" / "odd_tower_transfer_10.json"


class CheckError(RuntimeError):
    pass


def load(path: pathlib.Path) -> dict[str, Any]:
    def reject(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise CheckError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject)
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


def primitive(row: list[int]) -> bool:
    x, y, z = row
    return math.gcd(math.gcd(abs(x), abs(y)), abs(z)) == 1


EXPECTED_BROWN = [
    [-1, -1, 0],
    [1, -1, 0],
    [-1, 0, -1],
    [-1, 0, 1],
    [1, 0, -1],
    [1, 0, 1],
    [0, 1, -1],
    [0, 1, 1],
    [-3, -2, -1],
    [-3, -2, 1],
    [3, -2, -1],
    [3, -2, 1],
]


def sign_filter(rows: list[list[int]], pattern: str) -> list[list[int]]:
    if pattern == "positive-positive-positive":
        return [r for r in rows if r[0] > 0 and r[1] > 0 and r[2] > 0]
    if pattern == "positive-negative-positive":
        return [r for r in rows if r[0] > 0 and r[1] < 0 and r[2] > 0]
    raise CheckError(f"unknown sign pattern: {pattern}")


def verify(value: dict[str, Any]) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("schema mismatch")
    if value.get("status") != (
        "unconditional-infinite-tower-closure-for-exponent-multiset-2a-3b-10c"
    ):
        raise CheckError("unexpected status")
    if digest(value) != value.get("certificate_sha256"):
        raise CheckError("certificate digest mismatch")

    theorem = value["theorem"]
    if "{2a,3b,10c}" not in theorem["statement"]:
        raise CheckError("wrong exponent family")
    if theorem["exponent_range"] != {"a": "a>=2", "b": "b>=1", "c": "c>=1"}:
        raise CheckError("exponent range mismatch")
    if "all six permutations" not in theorem["permutation_coverage"]:
        raise CheckError("permutation coverage missing")

    brown = value["brown_input"]
    rows = brown["solutions"]
    if rows != EXPECTED_BROWN or brown["solution_count"] != 12:
        raise CheckError("Brown solution list mismatch")
    if len({tuple(row) for row in rows}) != 12:
        raise CheckError("duplicate Brown row")
    for row in rows:
        x, y, z = row
        if x * x + y * y * y != z ** 10:
            raise CheckError(f"Brown equation failed at {row}")
        if not primitive(row):
            raise CheckError(f"nonprimitive Brown row {row}")

    orientations = value["orientation_reductions"]
    expected_names = {
        "right_exponent_10c",
        "right_exponent_2a",
        "right_exponent_3b",
    }
    if set(orientations) != expected_names:
        raise CheckError("orientation inventory mismatch")

    all_positive = sign_filter(rows, "positive-positive-positive")
    if all_positive != []:
        raise CheckError(f"unexpected all-positive Brown row: {all_positive}")
    if orientations["right_exponent_10c"]["compatible_brown_rows"] != all_positive:
        raise CheckError("right-10c sign filter mismatch")

    positive_negative_positive = sign_filter(rows, "positive-negative-positive")
    if positive_negative_positive != [[3, -2, 1]]:
        raise CheckError(
            f"unexpected positive-negative-positive rows: {positive_negative_positive}"
        )
    if orientations["right_exponent_2a"]["compatible_brown_rows"] != positive_negative_positive:
        raise CheckError("right-2a sign filter mismatch")

    if any(
        base ** exponent == 3
        for exponent in range(2, 32)
        for base in range(1, 4)
    ):
        raise CheckError("3 incorrectly accepted as a proper power")
    obstruction = value["finite_obstructions"]["proper_power_obstruction"]
    if obstruction != {
        "classified_x_coordinate": 3,
        "prime": 3,
        "valuation": 1,
        "consequence": "3 is not an a-th power in positive integers for any a>=2",
    }:
        raise CheckError("proper-power obstruction changed")

    dahmen = value["dahmen_input"]
    if "n=5" not in dahmen["theorem_used"]:
        raise CheckError("Dahmen n=5 input missing")
    right3 = orientations["right_exponent_3b"]
    if right3["source_equation"] != "x^2+y^10=z^3":
        raise CheckError("right-3b source equation mismatch")
    if "Dahmen" not in right3["elimination"]:
        raise CheckError("right-3b elimination input missing")

    if "does not prove the full Beal conjecture" not in value["nonclaim"]:
        raise CheckError("trust-boundary nonclaim missing")


def self_test(value: dict[str, Any]) -> None:
    verify(value)
    mutations: list[dict[str, Any]] = []

    bad = copy.deepcopy(value)
    bad["brown_input"]["solutions"][0][0] = 0
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["orientation_reductions"]["right_exponent_2a"][
        "compatible_brown_rows"
    ] = []
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["finite_obstructions"]["proper_power_obstruction"]["valuation"] = 2
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["dahmen_input"]["theorem_used"] = "no theorem"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    for index, mutation in enumerate(mutations):
        try:
            verify(mutation)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} accepted")

    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        handle.write('{"x":1,"x":2}')
        path = pathlib.Path(handle.name)
    try:
        try:
            load(path)
        except CheckError:
            pass
        else:
            raise CheckError("duplicate JSON keys accepted")
    finally:
        path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    value = load(args.certificate)
    self_test(value) if args.self_test else verify(value)
    print(
        json.dumps(
            {
                "status": "ok",
                "certificate_sha256": value["certificate_sha256"],
                "self_test": args.self_test,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
