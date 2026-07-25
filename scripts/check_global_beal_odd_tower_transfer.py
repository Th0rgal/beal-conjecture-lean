#!/usr/bin/env python3
"""Replay the n=9 and n=15 odd-exponent tower-transfer certificate."""
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
DEFAULT = ROOT / "Research" / "GlobalBeal" / "odd_tower_transfer_9_15.json"


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
        raise CheckError("root must be an object")
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


def valuation(n: int, prime: int) -> int:
    count = 0
    while n % prime == 0:
        n //= prime
        count += 1
    return count


def orientations(rows: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        "right_odd_exponent": [
            row for row in rows if row[0] > 0 and row[1] > 0 and row[2] > 0
        ],
        "right_even_exponent": [
            row for row in rows if row[0] > 0 and row[1] < 0 and row[2] > 0
        ],
        "right_cubic_exponent": [
            row for row in rows if row[0] > 0 and row[1] < 0 and row[2] < 0
        ],
    }


EXPECTED = {
    "n9": {
        "n": 9,
        "rows": [
            [0, -1, -1],
            [1, 0, 1],
            [-1, 0, 1],
            [1, -1, 0],
            [-1, -1, 0],
            [3, -2, 1],
            [-3, -2, 1],
            [13, 7, 2],
            [-13, 7, 2],
        ],
        "witnesses": {3: 3, 13: 13},
    },
    "n15": {
        "n": 15,
        "rows": [
            [-1, -1, 0],
            [1, -1, 0],
            [-1, 0, 1],
            [1, 0, 1],
            [0, 1, 1],
            [0, -1, -1],
            [-3, -2, 1],
            [3, -2, 1],
        ],
        "witnesses": {3: 3},
    },
}


def verify(value: dict[str, Any]) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("schema mismatch")
    if digest(value) != value.get("certificate_sha256"):
        raise CheckError("digest mismatch")
    if set(value["instances"]) != set(EXPECTED):
        raise CheckError("instance inventory mismatch")

    for key, expected in EXPECTED.items():
        record = value["instances"][key]
        if record["odd_exponent"] != expected["n"]:
            raise CheckError(f"wrong exponent in {key}")
        rows = record["primitive_integer_solutions_x2_y3_zn"]
        if rows != expected["rows"]:
            raise CheckError(f"solution list mismatch in {key}")
        for x, y, z in rows:
            if x * x + y * y * y != z ** expected["n"]:
                raise CheckError(f"equation failed at {(x, y, z)} in {key}")
            if not primitive([x, y, z]):
                raise CheckError(f"nonprimitive row {(x, y, z)} in {key}")

        actual_orientations = orientations(rows)
        stored = record["orientation_reductions"]
        for name, actual in actual_orientations.items():
            if stored[name]["compatible_rows"] != actual:
                raise CheckError(f"orientation mismatch {key}/{name}")

        candidate_x = sorted(
            {row[0] for values in actual_orientations.values() for row in values}
        )
        if record["positive_x_coordinates_requiring_proper_power"] != candidate_x:
            raise CheckError(f"candidate x mismatch in {key}")
        witnesses = {
            item["x_coordinate"]: item["prime"]
            for item in record["valuation_one_witnesses"]
        }
        if witnesses != expected["witnesses"]:
            raise CheckError(f"witness inventory mismatch in {key}")
        if set(witnesses) != set(candidate_x):
            raise CheckError(f"witness coverage mismatch in {key}")
        for x, prime in witnesses.items():
            if valuation(x, prime) != 1:
                raise CheckError(f"valuation witness failed for {x} at {prime}")
        if "a>=2" not in record["conclusion"]:
            raise CheckError(f"tower range missing in {key}")

    if "n in {9,15}" not in value["combined_conclusion"]:
        raise CheckError("combined theorem missing")
    if "all six permutations" not in value["transfer_principle"][
        "permutation_coverage"
    ]:
        raise CheckError("permutation bridge missing")


def self_test(value: dict[str, Any]) -> None:
    verify(value)
    mutations: list[dict[str, Any]] = []

    bad = copy.deepcopy(value)
    bad["instances"]["n9"]["primitive_integer_solutions_x2_y3_zn"][0][0] = 1
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["instances"]["n15"]["valuation_one_witnesses"][0]["prime"] = 2
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["instances"]["n9"]["orientation_reductions"]["right_odd_exponent"][
        "compatible_rows"
    ] = []
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
            raise CheckError("duplicate keys accepted")
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
