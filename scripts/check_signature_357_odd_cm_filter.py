#!/usr/bin/env python3
"""Replay the odd-branch CM/ghost filtering for signature (3,5,7).

The finite arithmetic is elementary: Pacetti--Villagra Torcomian Proposition 5.8
says that a CM specialization has paper variable b supported only at q and r.
In Beal orientation b=-C and (q,r)=(5,3), while the Dahmen--Siksek odd branch
has gcd(C,15)=1. Hence C=1, incompatible with positive A^3+B^5=C^7.

The checker also intersects the paper's persistent CM packets with the exact
fixed-7 survivor sets already certified in fixed7_frontier.json. Proposition
5.8, the packet classifications, and the ghost local-type theorem remain
explicit literature inputs outside BealUnified.Trusted.
"""

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
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "odd_branch_cm_filter.json"
FIXED7_MANIFEST = ROOT / "Research" / "Signature357" / "fixed7_frontier.json"


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("manifest root must be an object")
    return value


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def canonical_digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sorted_unique_ints(value: Any, context: str) -> list[int]:
    if not isinstance(value, list) or any(type(item) is not int for item in value):
        raise CertificateError(f"{context} must be an integer array")
    if value != sorted(set(value)):
        raise CertificateError(f"{context} must be sorted and duplicate-free")
    return value


def fixed7_levels() -> dict[tuple[int, int], dict[str, Any]]:
    data = load_json(FIXED7_MANIFEST)
    levels = data.get("levels")
    if not isinstance(levels, list):
        raise CertificateError("fixed7 frontier has no levels array")
    result: dict[tuple[int, int], dict[str, Any]] = {}
    for entry in levels:
        if not isinstance(entry, dict):
            raise CertificateError("fixed7 level entry must be an object")
        raw_level = entry.get("level_exponents")
        if (
            not isinstance(raw_level, list)
            or len(raw_level) != 2
            or any(type(item) is not int for item in raw_level)
        ):
            raise CertificateError("malformed fixed7 level exponents")
        level = (raw_level[0], raw_level[1])
        if level in result:
            raise CertificateError("duplicate fixed7 level")
        result[level] = entry
    return result


def validate_data(data: dict[str, Any]) -> tuple[list[int], str]:
    exact_keys(
        data,
        {
            "schema_version",
            "status",
            "scope",
            "source_chain",
            "cm_support_arithmetic",
            "levels",
            "conclusions",
            "certificate_sha256",
        },
        "manifest",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "research-certificate-with-imported-CM-support-and-fixed7-results":
        raise CertificateError("unexpected research-certificate status")

    scope = data["scope"]
    if not isinstance(scope, dict):
        raise CertificateError("scope must be an object")
    exact_keys(
        scope,
        {"equation", "branch", "conditions", "paper_orientation"},
        "scope",
    )
    expected_conditions = [
        "A>0",
        "B>0",
        "C>0",
        "C odd",
        "3 does not divide A*B*C",
        "5 does not divide A*C",
        "7 divides A",
    ]
    if scope != {
        "equation": "A^3+B^5=C^7",
        "branch": "Dahmen--Siksek odd branch",
        "conditions": expected_conditions,
        "paper_orientation": "a=B,b=-C,c=A,p=7,q=5,r=3",
    }:
        raise CertificateError("scope or variable orientation mismatch")

    source = data["source_chain"]
    if not isinstance(source, dict):
        raise CertificateError("source_chain must be an object")
    exact_keys(
        source,
        {"cm_support", "fixed7_level22", "fixed7_level32", "ghost_exclusion"},
        "source_chain",
    )
    if "Proposition 5.8" not in source["cm_support"] or "{q,r}" not in source["cm_support"]:
        raise CertificateError("CM support theorem metadata is missing")
    if "Theorem 7.18" not in source["ghost_exclusion"]:
        raise CertificateError("ghost exclusion theorem metadata is missing")

    arithmetic = data["cm_support_arithmetic"]
    if not isinstance(arithmetic, dict):
        raise CertificateError("cm_support_arithmetic must be an object")
    exact_keys(
        arithmetic,
        {
            "paper_b",
            "allowed_prime_support",
            "odd_branch_coprime_to",
            "only_positive_C",
            "minimum_positive_left_side",
            "right_side_if_C_is_1",
            "conclusion",
        },
        "cm_support_arithmetic",
    )
    support = sorted_unique_ints(arithmetic["allowed_prime_support"], "allowed_prime_support")
    if arithmetic["paper_b"] != "-C" or support != [3, 5]:
        raise CertificateError("CM support was not transferred to the Beal right base")
    if arithmetic["odd_branch_coprime_to"] != math.prod(support):
        raise CertificateError("odd branch must be coprime to 3*5")

    # If every prime divisor of a positive C lies in {3,5}, then C=3^a*5^b.
    # Coprimality with 15 forces a=b=0, hence C=1.
    possible_exponents = [
        (a, b)
        for a in range(2)
        for b in range(2)
        if math.gcd(3**a * 5**b, 15) == 1
    ]
    if possible_exponents != [(0, 0)] or arithmetic["only_positive_C"] != 1:
        raise CertificateError("CM support plus gcd(C,15)=1 did not force C=1")
    minimum_left = 1**3 + 1**5
    if (
        arithmetic["minimum_positive_left_side"] != minimum_left
        or minimum_left != 2
        or arithmetic["right_side_if_C_is_1"] != 1
        or minimum_left <= arithmetic["right_side_if_C_is_1"]
    ):
        raise CertificateError("positivity contradiction at C=1 is missing")
    if arithmetic["conclusion"] != "the odd branch cannot give a CM specialization":
        raise CertificateError("unexpected CM conclusion")

    levels = data["levels"]
    if not isinstance(levels, list) or len(levels) != 4:
        raise CertificateError("levels must contain exactly four conductor levels")
    by_level: dict[tuple[int, int], dict[str, Any]] = {}
    for entry in levels:
        if not isinstance(entry, dict):
            raise CertificateError("level entry must be an object")
        raw_level = entry.get("level_exponents")
        if (
            not isinstance(raw_level, list)
            or len(raw_level) != 2
            or any(type(item) is not int for item in raw_level)
        ):
            raise CertificateError("malformed level_exponents")
        level = (raw_level[0], raw_level[1])
        if level in by_level:
            raise CertificateError("duplicate level entry")
        by_level[level] = entry
    if set(by_level) != {(2, 2), (3, 2), (2, 3), (3, 3)}:
        raise CertificateError("unexpected conductor-level set")

    fixed = fixed7_levels()

    level22 = by_level[(2, 2)]
    exact_keys(
        level22,
        {
            "level_exponents",
            "newform_count",
            "fixed7_complete",
            "fixed7_survivors",
            "persistent_cm_forms",
            "odd_branch_survivors_after_cm_filter",
            "conclusion",
        },
        "level (2,2)",
    )
    survivors22 = sorted_unique_ints(level22["fixed7_survivors"], "level22 survivors")
    cm22 = sorted_unique_ints(level22["persistent_cm_forms"], "level22 CM forms")
    fixed22 = fixed[(2, 2)]
    if (
        level22["newform_count"] != fixed22["newform_count"]
        or level22["fixed7_complete"] is not True
        or fixed22["fixed7_complete"] is not True
        or survivors22 != fixed22["fixed7_survivors"]
        or survivors22 != [3, 9, 12]
        or cm22 != survivors22
        or level22["odd_branch_survivors_after_cm_filter"] != []
    ):
        raise CertificateError("the complete level-(2,2) CM closure is incorrect")
    if level22["conclusion"] != "the odd branch has no solution lowering to level (2,2)":
        raise CertificateError("unexpected level-(2,2) conclusion")

    level32 = by_level[(3, 2)]
    exact_keys(
        level32,
        {
            "level_exponents",
            "newform_count",
            "fixed7_complete",
            "fixed7_survivors",
            "persistent_cm_forms",
            "cm_intersection",
            "odd_branch_survivors_after_cm_filter",
        },
        "level (3,2)",
    )
    survivors32 = sorted_unique_ints(level32["fixed7_survivors"], "level32 survivors")
    cm32 = sorted_unique_ints(level32["persistent_cm_forms"], "level32 CM forms")
    intersection = sorted(set(survivors32) & set(cm32))
    remaining = sorted(set(survivors32) - set(cm32))
    fixed32 = fixed[(3, 2)]
    if (
        level32["newform_count"] != fixed32["newform_count"]
        or level32["fixed7_complete"] is not True
        or fixed32["fixed7_complete"] is not True
        or survivors32 != fixed32["fixed7_survivors"]
        or survivors32 != [21, 22, 26, 33, 61, 65, 78, 92, 98]
        or cm32 != [64, 65, 69, 73, 77, 78, 79]
        or intersection != level32["cm_intersection"]
        or intersection != [65, 78]
        or remaining != level32["odd_branch_survivors_after_cm_filter"]
        or remaining != [21, 22, 26, 33, 61, 92, 98]
    ):
        raise CertificateError("level-(3,2) CM intersection is incorrect")

    level23 = by_level[(2, 3)]
    exact_keys(
        level23,
        {
            "level_exponents",
            "newform_count",
            "fixed7_complete",
            "persistent_cm_forms",
            "persistent_forms_excluded_in_odd_branch",
            "required_rerun",
        },
        "level (2,3)",
    )
    if (
        level23["newform_count"] != 35
        or level23["fixed7_complete"] is not False
        or sorted_unique_ints(level23["persistent_cm_forms"], "level23 CM forms")
        != [1, 7, 11, 12, 13, 16, 21]
        or level23["persistent_forms_excluded_in_odd_branch"] is not True
        or level23["required_rerun"] != "TheoremA(2,3,Data : flag := true)"
    ):
        raise CertificateError("level-(2,3) persistent CM metadata mismatch")

    level33 = by_level[(3, 3)]
    exact_keys(
        level33,
        {
            "level_exponents",
            "newform_count",
            "fixed7_complete",
            "persistent_ghost_forms",
            "ghost_hypothesis_in_beal_orientation",
            "persistent_forms_excluded_in_odd_branch",
            "required_rerun",
        },
        "level (3,3)",
    )
    if (
        level33["newform_count"] != 112
        or level33["fixed7_complete"] is not False
        or sorted_unique_ints(level33["persistent_ghost_forms"], "level33 ghosts") != [22, 39]
        or level33["ghost_hypothesis_in_beal_orientation"] != "3 does not divide A"
        or level33["persistent_forms_excluded_in_odd_branch"] is not True
        or level33["required_rerun"] != "TheoremA(3,3,Data : flag := true)"
    ):
        raise CertificateError("level-(3,3) ghost metadata mismatch")

    conclusions = data["conclusions"]
    expected_conclusions = [
        "all persistent CM packets are impossible in the Dahmen--Siksek odd branch",
        "the complete fixed-7 level (2,2) is closed in the odd branch",
        "the complete fixed-7 level (3,2) has exactly seven non-CM survivors after the CM filter",
        "at the two incomplete levels only additional p=7-specific packets can remain after the persistent CM/ghost filters",
    ]
    if conclusions != expected_conclusions:
        raise CertificateError("conclusion list mismatch")

    digest = canonical_digest(data)
    if data["certificate_sha256"] != digest:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {digest}"
        )
    return remaining, digest


def validate(path: pathlib.Path) -> tuple[list[int], str]:
    return validate_data(load_json(path))


def expect_rejection(data: dict[str, Any], description: str) -> None:
    try:
        validate_data(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {description}")


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["cm_support_arithmetic"]["allowed_prime_support"] = [3, 5, 7]
    expect_rejection(mutated, "a weakened CM support set")

    mutated = copy.deepcopy(base)
    mutated["levels"][0]["odd_branch_survivors_after_cm_filter"] = [3]
    expect_rejection(mutated, "a surviving CM packet at level (2,2)")

    mutated = copy.deepcopy(base)
    mutated["levels"][1]["cm_intersection"] = [65]
    expect_rejection(mutated, "an incomplete level-(3,2) CM intersection")

    mutated = copy.deepcopy(base)
    mutated["levels"][3]["persistent_forms_excluded_in_odd_branch"] = False
    expect_rejection(mutated, "a retained odd-branch ghost packet")

    duplicate = '{"schema_version":1,"schema_version":1}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write(duplicate)
        path = pathlib.Path(handle.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)

    print("odd-branch CM/ghost filter negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    remaining, digest = validate(args.manifest)
    print("signature (3,5,7) odd-branch CM/ghost filter certificate passed")
    print("  level (2,2): closed after eliminating CM packets 3,9,12")
    print(f"  level (3,2): seven non-CM survivors remain: {remaining}")
    print("  incomplete levels: persistent CM/ghost packets excluded; flagged reruns still required")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
