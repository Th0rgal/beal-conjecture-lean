#!/usr/bin/env python3
"""Replay the complete LMFDB-covered low-level mod-5 HMF filter for (3,5,7).

The input is a pinned response from the public LMFDB SQL mirror.  The checker
validates the eight candidate levels whose norms are inside LMFDB's documented
complete degree-three range, verifies the canonical response digest, and applies
the residual norm-8 condition a_P = 0 modulo a prime above 5.

This is a database/certificate check, not a proof that the remaining higher
levels are empty and not a proof of the (3,5,7) equation.
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

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "lmfdb_low_levels.json"
EXPECTED_LEVELS = [1, 7, 27, 49, 189, 343, 729, 1323]
EXPECTED_SURVIVORS = [
    "3.3.49.1-49.1-a",
    "3.3.49.1-189.1-a",
    "3.3.49.1-729.1-b",
    "3.3.49.1-1323.1-a",
]


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
        raise CertificateError("manifest root must be an object")
    return value


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def polynomial_constant(polynomial: str) -> int:
    """Parse the constant coefficient of the small LMFDB polynomials in this file."""
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
        # The coefficient field is Q[e]/(f(e)).  A prime above 5 with e=0 exists
        # exactly when x divides f(x) modulo 5, i.e. when f(0)=0 modulo 5.
        return polynomial_constant(record["hecke_polynomial"]) % 5 == 0
    raise CertificateError(
        f"unsupported norm-8 eigenvalue encoding for {record.get('label')}: {value!r}"
    )


def validate(data: dict[str, Any]) -> tuple[list[str], str]:
    expected_root = {
        "candidate_levels_within_bound", "certificate_sha256", "level_count",
        "levels", "prime_ordering", "schema_version", "source", "status",
        "total_coefficient_field_dimension", "total_record_count",
    }
    if set(data) != expected_root:
        raise CertificateError("manifest keys differ from the pinned schema")
    if data["schema_version"] != 2:
        raise CertificateError("schema_version must equal 2")
    if data["candidate_levels_within_bound"] != EXPECTED_LEVELS:
        raise CertificateError("candidate level list mismatch")
    if data["level_count"] != 8 or len(data["levels"]) != 8:
        raise CertificateError("expected exactly eight complete-range levels")
    if data["total_record_count"] != 14:
        raise CertificateError("expected exactly fourteen HMF packets")
    if data["total_coefficient_field_dimension"] != 26:
        raise CertificateError("unexpected total coefficient-field dimension")

    source = data["source"]
    if source != {
        "database": "LMFDB public SQL mirror",
        "documented_degree3_completeness_bound": 2059,
        "field_label": "3.3.49.1",
        "global_level_bound": "p3^3*p7^3",
        "parallel_weight": 2,
        "tables": ["hmf_fields", "hmf_forms", "hmf_hecke"],
    }:
        raise CertificateError("source metadata mismatch")
    if data["prime_ordering"] != {
        "norm8_index_zero_based": 1,
        "norm8_prime": "[8, 2, 2]",
    }:
        raise CertificateError("norm-8 prime metadata mismatch")

    labels: list[str] = []
    dimension_sum = 0
    record_count = 0
    for expected_norm, level in zip(EXPECTED_LEVELS, data["levels"]):
        if level["level_norm"] != expected_norm:
            raise CertificateError("level records are not in canonical norm order")
        records = level["records"]
        if level["record_count"] != len(records):
            raise CertificateError(f"record count mismatch at level {expected_norm}")
        local_dimension = sum(int(record["dimension"]) for record in records)
        if level["total_coefficient_field_dimension"] != local_dimension:
            raise CertificateError(f"dimension sum mismatch at level {expected_norm}")
        dimension_sum += local_dimension
        record_count += len(records)
        for record in records:
            required = {
                "dimension", "hecke_eigenvalue_norm8", "hecke_polynomial",
                "is_CM", "is_base_change", "label", "level_ideal",
                "level_norm", "parallel_weight",
            }
            if set(record) != required:
                raise CertificateError(f"record keys differ for {record.get('label')}")
            if record["level_norm"] != expected_norm or record["parallel_weight"] != 2:
                raise CertificateError(f"level/weight mismatch for {record['label']}")
            if record["label"] in labels:
                raise CertificateError(f"duplicate HMF label: {record['label']}")
            labels.append(record["label"])

    if record_count != 14 or dimension_sum != 26:
        raise CertificateError("aggregate HMF totals do not replay")
    if labels != sorted(labels, key=lambda label: (int(label.split("-")[1].split(".")[0]), label)):
        # The source is ordered first by level norm and then label.
        raise CertificateError("HMF records are not canonically ordered")

    survivors = sorted(
        record["label"]
        for level in data["levels"]
        for record in level["records"]
        if has_prime_above_five_with_zero_trace(record)
    )
    if survivors != sorted(EXPECTED_SURVIVORS):
        raise CertificateError(
            f"norm-8 survivor mismatch: expected {EXPECTED_SURVIVORS}, got {survivors}"
        )

    digest = canonical_sha256(data)
    if digest != data["certificate_sha256"]:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {digest}"
        )
    return survivors, digest


def expect_rejection(data: dict[str, Any], description: str) -> None:
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {description}")


def self_test() -> None:
    source = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(source)
    mutated["levels"][2]["records"][0]["hecke_eigenvalue_norm8"] = 0
    expect_rejection(mutated, "a forged norm-8 survivor")

    mutated = copy.deepcopy(source)
    mutated["levels"][6]["records"][1]["hecke_eigenvalue_norm8"] = 1
    expect_rejection(mutated, "a deleted genuine survivor")

    mutated = copy.deepcopy(source)
    mutated["levels"][7]["records"][2]["hecke_polynomial"] = "x^2 + 2*x"
    expect_rejection(mutated, "a forged coefficient-field prime above five")

    mutated = copy.deepcopy(source)
    mutated["total_record_count"] = 13
    expect_rejection(mutated, "an incomplete packet inventory")

    duplicate = '{"schema_version":2,"schema_version":2}'
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

    print("LMFDB low-level signature-(3,5,7) negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    survivors, digest = validate(load_json(args.manifest))
    print("LMFDB complete low-level signature-(3,5,7) inventory valid")
    print("  complete levels: 8; packets: 14; coefficient-field dimension: 26")
    print("  norm-8 mod-5 survivors: 4")
    for label in survivors:
        print(f"    {label}")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
