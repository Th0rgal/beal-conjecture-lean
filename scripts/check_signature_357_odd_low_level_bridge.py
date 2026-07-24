#!/usr/bin/env python3
"""Replay the odd-branch low-level multi-Frey bridge for signature (3,5,7).

The complete LMFDB range leaves one mod-5 packet in the Dahmen--Siksek odd
branch: 3.3.49.1-729.1-b.  Its base-change elliptic curve has Kodaira type III
at 3, hence semistability defect 4.  The source HGM local table has defect
12,4,12 for u=C^7/A^3 congruent to 2,5,8 modulo 9.  Prime-to-5 local-type
compatibility therefore forces u=5 modulo 9.

Exact unit enumeration then gives B^5=4*A^3 modulo 9, which is precisely the
condition forcing epsilon_3=2 for the first, fixed-7 Frey representation.  The
fixed-7 level-(2,2) packets are all CM and already excluded in the odd branch,
so only fixed-7 level (2,3) remains.

The local-type compatibility, LMFDB local data, and conductor theorem are explicit
literature/database inputs.  The checker independently replays the finite
arithmetic and cross-checks all repository manifests.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "Research" / "Signature357" / "odd_low_level_bridge.json"
LOCAL_TYPES = ROOT / "Research" / "Signature357" / "mod5_irreducibility_at3.json"
LOW_FILTER = ROOT / "Research" / "Signature357" / "lmfdb_low_level_filter.json"
CM_FILTER = ROOT / "Research" / "Signature357" / "odd_branch_cm_filter.json"


class CertificateError(ValueError):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError(f"{path} root must be an object")
    return value


def digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def unit_rows_mod9() -> list[tuple[int, int, int, int, int]]:
    units = [value for value in range(9) if math.gcd(value, 9) == 1]
    rows: list[tuple[int, int, int, int, int]] = []
    for A in units:
        a3 = pow(A, 3, 9)
        inverse = pow(a3, -1, 9)
        for B in units:
            b5 = pow(B, 5, 9)
            for C in units:
                c7 = pow(C, 7, 9)
                if (a3 + b5 - c7) % 9:
                    continue
                u = c7 * inverse % 9
                ratio = b5 * inverse % 9
                rows.append((A, B, C, u, ratio))
    return rows


def validate_data(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("schema_version") != 1:
        raise CertificateError("schema_version must equal 1")
    if digest(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate digest mismatch")

    local = load(LOCAL_TYPES)
    local_rows = local.get("local_types")
    if not isinstance(local_rows, list):
        raise CertificateError("local-type manifest has no rows")
    type_map = {str(row["u_mod_9"]): row["e"] for row in local_rows}
    expected_map = data["local_type_match"]["hgm_types_by_u_mod9"]
    if type_map != expected_map or type_map != {"2": 12, "5": 4, "8": 12}:
        raise CertificateError("HGM local-type map mismatch")

    low = load(LOW_FILTER)
    branch = low.get("branch_filters", {}).get("odd_branch")
    if not isinstance(branch, dict):
        raise CertificateError("low-level filter lacks the odd branch")
    survivors = branch.get("survivors")
    if survivors != [data["mod5_packet"]["label"]]:
        raise CertificateError("the complete low-level odd frontier is not one packet")
    if data["mod5_packet"]["label"] != "3.3.49.1-729.1-b":
        raise CertificateError("unexpected surviving mod-5 packet")
    if data["mod5_packet"]["semistability_defect"] != 4:
        raise CertificateError("packet local defect must be 4")

    matching = sorted(
        int(residue)
        for residue, defect in type_map.items()
        if defect == data["mod5_packet"]["semistability_defect"]
    )
    if matching != [5] or data["local_type_match"]["forced_u_mod9"] != 5:
        raise CertificateError("local-type matching did not force u=5 modulo 9")

    rows = unit_rows_mod9()
    u5 = [row for row in rows if row[3] == 5]
    bridge = data["congruence_bridge"]
    if len(rows) != bridge["unit_solution_count_mod9"] or len(rows) != 18:
        raise CertificateError("unexpected number of primitive unit solutions modulo 9")
    if len(u5) != bridge["solutions_with_u_mod9_5"] or len(u5) != 6:
        raise CertificateError("unexpected number of u=5 solutions modulo 9")
    if any(row[4] != 4 for row in u5):
        raise CertificateError("u=5 did not force B^5/A^3=4 modulo 9")
    if bridge["forced_fixed7_epsilon3"] != 2:
        raise CertificateError("the imported first-Frey conductor consequence is missing")

    cm = load(CM_FILTER)
    cm_levels = cm.get("levels")
    if not isinstance(cm_levels, list):
        raise CertificateError("odd CM filter has no levels")
    level22 = next(
        (row for row in cm_levels if row.get("level_exponents") == [2, 2]), None
    )
    if level22 is None:
        raise CertificateError("odd CM filter lacks level (2,2)")
    reduction = data["fixed7_reduction"]
    if level22.get("fixed7_survivors") != reduction["level_22_survivors_before_cm_filter"]:
        raise CertificateError("level-(2,2) fixed-7 survivors mismatch")
    if level22.get("odd_branch_survivors_after_cm_filter") != reduction["level_22_survivors_after_odd_cm_filter"]:
        raise CertificateError("level-(2,2) CM filtering mismatch")
    if reduction["possible_levels_before_cm_filter"] != [[2, 2], [2, 3]]:
        raise CertificateError("epsilon_3=2 must leave exactly levels (2,2),(2,3)")
    if reduction["only_remaining_level"] != [2, 3]:
        raise CertificateError("the one remaining fixed-7 level must be (2,3)")

    return {
        "unit_rows": len(rows),
        "u5_rows": len(u5),
        "mod5_packet": data["mod5_packet"]["label"],
        "forced_u_mod9": 5,
        "remaining_fixed7_level": [2, 3],
    }


def self_test() -> None:
    base = load(DEFAULT)
    validate_data(base)

    mutated = copy.deepcopy(base)
    mutated["local_type_match"]["forced_u_mod9"] = 2
    mutated["certificate_sha256"] = digest(mutated)
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the wrong local parameter class")

    mutated = copy.deepcopy(base)
    mutated["fixed7_reduction"]["only_remaining_level"] = [3, 3]
    mutated["certificate_sha256"] = digest(mutated)
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the wrong fixed-7 level")

    print("odd low-level bridge negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    result = validate_data(load(args.manifest))
    print(
        f"validated odd low-level bridge: mod5={result['mod5_packet']}, "
        f"u={result['forced_u_mod9']} mod 9, "
        f"fixed7={tuple(result['remaining_fixed7_level'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
