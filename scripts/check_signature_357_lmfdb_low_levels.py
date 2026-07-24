#!/usr/bin/env python3
"""Replay the complete LMFDB low-level mod-5 filter for signature (3,5,7).

The pinned inventory is the canonical response from LMFDB's documented complete
degree-three range (level norm <=2059). This offline checker verifies the
14-packet enumeration, applies the norm-8 residual congruence, composes the
global non-CM certificate and the even-7-unit local-type certificate, and derives
the branch-local survivor sets.

It does not assert that levels above 2059 are empty and does not prove the
(3,5,7) equation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import tempfile
from typing import Any

import check_signature_357_mod5_even_7unit as even7
import check_signature_357_mod5_noncm as noncm

ROOT = pathlib.Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "Research" / "Signature357" / "lmfdb_low_levels.json"
FILTER = ROOT / "Research" / "Signature357" / "lmfdb_low_level_filter.json"
EXPECTED_LEVELS = [1, 7, 27, 49, 189, 343, 729, 1323]


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError(f"{path} root must be an object")
    return value


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def polynomial_constant(polynomial: str) -> int:
    if polynomial == "x":
        return 0
    compact = polynomial.replace(" ", "")
    match = re.search(r"([+-]?\d+)$", compact)
    if match is None:
        raise CertificateError(f"cannot parse polynomial constant: {polynomial!r}")
    return int(match.group(1))


def has_prime_above_five_with_zero_trace(record: dict[str, Any]) -> bool:
    value = record["hecke_eigenvalue_norm8"]
    if type(value) is int:
        return value % 5 == 0
    if value == "e":
        # In Q[e]/(f), a prime above 5 with e=0 exists exactly when f(0)=0 mod 5.
        return polynomial_constant(record["hecke_polynomial"]) % 5 == 0
    raise CertificateError(
        f"unsupported norm-8 eigenvalue encoding for {record.get('label')}: {value!r}"
    )


def validate_inventory(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    exact_keys(
        data,
        {
            "candidate_levels_within_bound", "certificate_sha256", "level_count",
            "levels", "prime_ordering", "schema_version", "source", "status",
            "total_coefficient_field_dimension", "total_record_count",
        },
        "inventory",
    )
    if data["schema_version"] != 2:
        raise CertificateError("inventory schema_version must equal 2")
    if canonical_sha256(data) != data["certificate_sha256"]:
        raise CertificateError("inventory certificate hash mismatch")
    if data["candidate_levels_within_bound"] != EXPECTED_LEVELS:
        raise CertificateError("candidate level list mismatch")
    if data["level_count"] != 8 or len(data["levels"]) != 8:
        raise CertificateError("expected exactly eight complete-range levels")
    if data["total_record_count"] != 14:
        raise CertificateError("expected exactly fourteen HMF packets")
    if data["total_coefficient_field_dimension"] != 26:
        raise CertificateError("unexpected total coefficient-field dimension")
    if data["prime_ordering"] != {
        "norm8_index_zero_based": 1,
        "norm8_prime": "[8, 2, 2]",
    }:
        raise CertificateError("norm-8 prime metadata mismatch")

    records: dict[str, dict[str, Any]] = {}
    total_records = 0
    total_dimension = 0
    for expected_norm, level in zip(EXPECTED_LEVELS, data["levels"]):
        exact_keys(
            level,
            {
                "exponent_pair", "level_norm", "record_count", "records",
                "total_coefficient_field_dimension",
            },
            f"level {expected_norm}",
        )
        if level["level_norm"] != expected_norm:
            raise CertificateError("level records are not in canonical norm order")
        pair = level["exponent_pair"]
        if (
            not isinstance(pair, list) or len(pair) != 2
            or any(type(value) is not int for value in pair)
            or 27 ** pair[0] * 7 ** pair[1] != expected_norm
        ):
            raise CertificateError(f"invalid exponent pair at level {expected_norm}")
        level_records = level["records"]
        if level["record_count"] != len(level_records):
            raise CertificateError(f"record count mismatch at level {expected_norm}")
        local_dimension = 0
        for record in level_records:
            exact_keys(
                record,
                {
                    "dimension", "hecke_eigenvalue_norm8", "hecke_polynomial",
                    "is_CM", "is_base_change", "label", "level_ideal",
                    "level_norm", "parallel_weight",
                },
                "packet record",
            )
            label = record["label"]
            if not isinstance(label, str) or label in records:
                raise CertificateError(f"duplicate or malformed packet label {label!r}")
            if record["level_norm"] != expected_norm or record["parallel_weight"] != 2:
                raise CertificateError(f"level/weight mismatch for {label}")
            if type(record["dimension"]) is not int or record["dimension"] < 1:
                raise CertificateError(f"invalid dimension for {label}")
            if record["is_CM"] not in {"yes", "no"}:
                raise CertificateError(f"invalid CM flag for {label}")
            if record["is_base_change"] not in {"yes", "no"}:
                raise CertificateError(f"invalid base-change flag for {label}")
            records[label] = dict(record, exponent_pair=list(pair))
            local_dimension += record["dimension"]
        if local_dimension != level["total_coefficient_field_dimension"]:
            raise CertificateError(f"dimension sum mismatch at level {expected_norm}")
        total_records += len(level_records)
        total_dimension += local_dimension
    if total_records != 14 or total_dimension != 26:
        raise CertificateError("aggregate HMF totals do not replay")
    return records


def validate_filter(
    manifest: dict[str, Any], inventory: dict[str, Any], records: dict[str, dict[str, Any]]
) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str]]:
    exact_keys(
        manifest,
        {
            "schema_version", "status", "scope", "residual_filter",
            "global_noncm_filter", "even_7unit_local_type_filter",
            "branch_filters", "source_dependencies", "certificate_sha256",
        },
        "filter manifest",
    )
    if manifest["schema_version"] != 3:
        raise CertificateError("filter schema_version must equal 3")
    if canonical_sha256(manifest) != manifest["certificate_sha256"]:
        raise CertificateError("filter certificate hash mismatch")

    scope = manifest["scope"]
    exact_keys(
        scope,
        {
            "equation", "field", "residual_characteristic",
            "complete_level_norm_bound", "candidate_level_norms",
            "inventory_path", "inventory_sha256", "global_noncm_path",
            "global_noncm_sha256", "even_7unit_local_type_path",
            "even_7unit_local_type_sha256",
        },
        "scope",
    )
    if scope["inventory_sha256"] != inventory["certificate_sha256"]:
        raise CertificateError("filter is not bound to the pinned inventory")
    if scope["candidate_level_norms"] != inventory["candidate_levels_within_bound"]:
        raise CertificateError("filter level list differs from inventory")

    try:
        noncm_digest = noncm.validate(noncm.load_json(ROOT / scope["global_noncm_path"]))
    except noncm.CertificateError as exc:
        raise CertificateError(f"global non-CM certificate failed: {exc}") from exc
    if noncm_digest != scope["global_noncm_sha256"]:
        raise CertificateError("global non-CM subcertificate digest mismatch")

    try:
        even7_digest = even7.validate(even7.load_json(ROOT / scope["even_7unit_local_type_path"]))
    except even7.CertificateError as exc:
        raise CertificateError(f"even 7-unit local-type certificate failed: {exc}") from exc
    if even7_digest != scope["even_7unit_local_type_sha256"]:
        raise CertificateError("even 7-unit local-type subcertificate digest mismatch")

    survivors = sorted(
        label for label, record in records.items()
        if has_prime_above_five_with_zero_trace(record)
    )
    residual = manifest["residual_filter"]
    if survivors != residual["survivors"]:
        raise CertificateError(
            f"norm-8 survivors differ: expected {residual['survivors']}, got {survivors}"
        )
    if (
        residual["prime_norm"] != 8
        or residual["required_hecke_eigenvalue_mod5"] != 0
        or residual["total_packets"] != len(records)
        or residual["survivor_count"] != len(survivors)
    ):
        raise CertificateError("residual-filter summary mismatch")
    if not all(records[label]["hecke_polynomial"] == "x" for label in survivors):
        raise CertificateError("a low-level survivor has non-rational Hecke field")
    if not all(records[label]["is_base_change"] == "yes" for label in survivors):
        raise CertificateError("a low-level survivor is not a base change")

    global_noncm = sorted(
        label for label in survivors if records[label]["is_CM"] == "no"
    )
    removed_cm = sorted(set(survivors) - set(global_noncm))
    noncm_manifest = manifest["global_noncm_filter"]
    if (
        removed_cm != noncm_manifest["cm_packets_removed"]
        or global_noncm != noncm_manifest["survivors"]
        or noncm_manifest["count"] != len(global_noncm)
        or noncm_manifest["all_survivors_non_cm"] is not True
    ):
        raise CertificateError("global non-CM low-level filter mismatch")

    local_manifest = manifest["even_7unit_local_type_filter"]
    removed_local = local_manifest["packet_removed"]
    if removed_local not in global_noncm:
        raise CertificateError("local-type packet is not in the non-CM frontier")
    post_local = sorted(set(global_noncm) - {removed_local})
    if (
        removed_local != "3.3.49.1-1323.1-a"
        or post_local != local_manifest["survivors"]
        or local_manifest["count"] != len(post_local)
        or "order 5" not in local_manifest["reason"]
    ):
        raise CertificateError("even 7-unit local-type filter mismatch")

    exponent3 = lambda label: int(records[label]["exponent_pair"][0])
    exponent7 = lambda label: int(records[label]["exponent_pair"][1])
    branches = manifest["branch_filters"]

    odd_pre = sorted(label for label in survivors if exponent3(label) in {2, 3})
    odd = sorted(label for label in post_local if exponent3(label) in {2, 3})
    odd_manifest = branches["odd_branch"]
    if (
        odd_pre != odd_manifest["pre_noncm_survivors"]
        or odd != odd_manifest["low_level_survivors"]
        or odd_manifest["count"] != 0
        or odd_manifest["conclusion"] != "the complete LMFDB low-level odd branch is empty"
    ):
        raise CertificateError("odd-branch low-level closure mismatch")

    even_pre = sorted(label for label in global_noncm if exponent3(label) in {1, 2})
    even = sorted(label for label in post_local if exponent3(label) in {1, 2})
    even_manifest = branches["even_branch"]
    if (
        even_pre != even_manifest["pre_7unit_local_type_survivors"]
        or even != even_manifest["low_level_survivors"]
        or even_manifest["count"] != len(even)
    ):
        raise CertificateError(f"even-branch low-level set mismatch: {even}")

    even_7_unit_pre = sorted(label for label in even_pre if exponent7(label) in {2, 3})
    even_7_unit = sorted(label for label in even if exponent7(label) in {2, 3})
    unit_manifest = branches["even_branch_7_unit"]
    if (
        even_7_unit_pre != unit_manifest["pre_local_type_survivors"]
        or even_7_unit != unit_manifest["low_level_survivors"]
        or unit_manifest["count"] != 0
        or unit_manifest["conclusion"] != "the complete LMFDB low-level even 7-unit branch is empty"
    ):
        raise CertificateError(f"even 7-unit low-level set mismatch: {even_7_unit}")

    even_7_divides = sorted(label for label in even if exponent7(label) == 1)
    divides_manifest = branches["even_branch_7_divides_C"]
    if (
        even_7_divides != divides_manifest["low_level_survivors"]
        or divides_manifest["count"] != len(even_7_divides)
    ):
        raise CertificateError(f"even 7-divisible low-level set mismatch: {even_7_divides}")

    return survivors, post_local, odd, even, even_7_unit, even_7_divides


def validate() -> tuple[list[str], list[str], list[str], list[str], list[str], list[str]]:
    inventory = load_json(INVENTORY)
    records = validate_inventory(inventory)
    return validate_filter(load_json(FILTER), inventory, records)


def self_test() -> None:
    inventory = load_json(INVENTORY)
    manifest = load_json(FILTER)
    records = validate_inventory(inventory)

    mutated = copy.deepcopy(manifest)
    mutated["residual_filter"]["survivors"].remove("3.3.49.1-189.1-a")
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    try:
        validate_filter(mutated, inventory, records)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a weakened survivor set")

    mutated = copy.deepcopy(manifest)
    mutated["global_noncm_filter"]["survivors"].append("3.3.49.1-729.1-b")
    mutated["global_noncm_filter"]["survivors"].sort()
    mutated["global_noncm_filter"]["count"] = 3
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    try:
        validate_filter(mutated, inventory, records)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a CM packet after the global non-CM theorem")

    mutated = copy.deepcopy(manifest)
    mutated["even_7unit_local_type_filter"]["packet_removed"] = "3.3.49.1-189.1-a"
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    try:
        validate_filter(mutated, inventory, records)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted elimination of the wrong local packet")

    mutated = copy.deepcopy(manifest)
    mutated["branch_filters"]["even_branch_7_unit"]["low_level_survivors"] = [
        "3.3.49.1-1323.1-a"
    ]
    mutated["branch_filters"]["even_branch_7_unit"]["count"] = 1
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    try:
        validate_filter(mutated, inventory, records)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the obsolete nonempty even 7-unit frontier")

    duplicate = '{"schema_version":3,"schema_version":3}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write(duplicate)
        path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)
    print("signature-357 low-level filter negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    all_survivors, final_survivors, odd, even, even_7_unit, even_7_divides = validate()
    print("LMFDB-complete levels: 8")
    print(f"packets: 14 -> {len(all_survivors)} after a_P=0 mod 5")
    print(f"after non-CM and local-type filters: {len(final_survivors)}")
    print("final complete-range survivor:", ", ".join(final_survivors))
    print("odd branch low-level frontier: empty")
    print("even branch low-level frontier:", ", ".join(even))
    print("even branch with 7∤C: empty")
    print("even branch with 7|C:", ", ".join(even_7_divides))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
