#!/usr/bin/env python3
"""Validate the normalized retained public-Magma replay at level (2,3).

The producer recomputes all 35 Hilbert-newform packets in three independent
batches, tests the published candidate-polynomial conditions directly over
F_7, and applies the odd-branch superspecial condition at the prime above 7.
This checker is offline and fail-closed.  It validates the pinned source,
batch partition, intersections, output markers, and canonical digest.

The artifact is computational research evidence.  It does not identify CM
packets by itself and does not prove signature (3,5,7).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = ROOT / "Research" / "Signature357" / "fixed7_level23_online.json"
EXPECTED_FIXED7 = [1, 5, 7, 11, 12, 13, 16, 17, 21, 24, 28]
EXPECTED_SUPERSPECIAL = [1, 7, 11, 12, 13, 16, 21, 24, 28]
EXPECTED_PRIMES = [
    7, 11, 13, 17, 19, 29, 31, 41, 59, 61, 71, 79, 89, 101, 109,
    131, 139, 149, 151, 179, 181, 191, 199, 211, 229, 239, 241, 251,
    269, 271, 281, 311, 331, 349, 359, 379, 389,
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
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("artifact root must be an object")
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


def positive_sorted_unique(value: Any, context: str) -> list[int]:
    if (
        not isinstance(value, list)
        or any(type(item) is not int or item <= 0 for item in value)
        or value != sorted(set(value))
    ):
        raise CertificateError(f"{context} must be a sorted list of distinct positives")
    return value


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version", "status", "source", "github_actions_artifact",
            "level_exponents", "packet_count", "batches", "fixed7_survivors",
            "superspecial_survivors", "nonclaim", "certificate_sha256",
        },
        "artifact",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != (
        "retained-public-Magma fixed-7 and superspecial replay summary"
    ):
        raise CertificateError("unexpected artifact status")
    if data["level_exponents"] != [2, 3] or data["packet_count"] != 35:
        raise CertificateError("unexpected Hilbert level or packet count")

    source = data["source"]
    exact_keys(
        source,
        {"calculator", "source_candidate_git_blob", "source_commit"},
        "source",
    )
    if source != {
        "calculator": "https://magma.maths.usyd.edu.au/calc/",
        "source_candidate_git_blob": "9c96357834f2298b4d91ab97812c38e84b8ef7a2",
        "source_commit": "e88f914c577ab6cf9a45e5cdd82c1993477fb423",
    }:
        raise CertificateError("upstream source is not the pinned public computation")

    artifact = data["github_actions_artifact"]
    if artifact != {
        "name": "signature357-fixed7-level23-online",
        "digest": "sha256:ba92658b9cd44f7b7d35b7b3282b9a90b7b6d0d9028373c970705b8f7822add9",
        "workflow_run_id": 30099726697,
    }:
        raise CertificateError("retained GitHub Actions artifact is not pinned")
    batches = data["batches"]
    if not isinstance(batches, list) or len(batches) != 3:
        raise CertificateError("expected exactly three public-calculator batches")

    seen_primes: list[int] = []
    fixed_intersection: set[int] | None = None
    superspecial_intersection: set[int] | None = None
    for expected_number, batch in enumerate(batches, start=1):
        if not isinstance(batch, dict):
            raise CertificateError("batch entry must be an object")
        exact_keys(
            batch,
            {
                "batch", "auxiliary_primes", "input_bytes", "survivors",
                "superspecial_survivors", "output_tail_sha256",
            },
            f"batch {expected_number}",
        )
        if batch["batch"] != expected_number:
            raise CertificateError("batch numbering is not canonical")
        primes = positive_sorted_unique(
            batch["auxiliary_primes"], f"batch {expected_number} primes"
        )
        if set(primes) & set(seen_primes):
            raise CertificateError("auxiliary-prime batches overlap")
        seen_primes.extend(primes)
        if type(batch["input_bytes"]) is not int or not (1 <= batch["input_bytes"] < 50_000):
            raise CertificateError("public-calculator input-size bound is not replayed")

        survivors = positive_sorted_unique(
            batch["survivors"], f"batch {expected_number} survivors"
        )
        superspecial = positive_sorted_unique(
            batch["superspecial_survivors"],
            f"batch {expected_number} superspecial survivors",
        )
        if any(packet > 35 for packet in survivors + superspecial):
            raise CertificateError("packet index exceeds the 35-packet space")
        if not set(superspecial) <= set(survivors):
            raise CertificateError("batch superspecial set is not a survivor subset")
        tail_digest = batch["output_tail_sha256"]
        if (
            not isinstance(tail_digest, str) or len(tail_digest) != 64
            or any(character not in "0123456789abcdef" for character in tail_digest)
        ):
            raise CertificateError("retained calculator output-tail digest is malformed")

        current = set(survivors)
        current_superspecial = set(superspecial)
        fixed_intersection = (
            current if fixed_intersection is None else fixed_intersection & current
        )
        superspecial_intersection = (
            current_superspecial
            if superspecial_intersection is None
            else superspecial_intersection & current_superspecial
        )

    if sorted(seen_primes) != EXPECTED_PRIMES:
        raise CertificateError("the three batches do not partition the 37 pinned prime rows")

    fixed7 = positive_sorted_unique(data["fixed7_survivors"], "fixed7_survivors")
    superspecial = positive_sorted_unique(
        data["superspecial_survivors"], "superspecial_survivors"
    )
    if fixed7 != sorted(fixed_intersection or set()) or fixed7 != EXPECTED_FIXED7:
        raise CertificateError("fixed-7 intersection differs from the retained result")
    if (
        superspecial != sorted(superspecial_intersection or set())
        or superspecial != EXPECTED_SUPERSPECIAL
    ):
        raise CertificateError("superspecial intersection differs from the retained result")
    if not set(superspecial) <= set(fixed7):
        raise CertificateError("final superspecial set is not a fixed-7 subset")

    digest = canonical_sha256(data)
    if digest != data["certificate_sha256"]:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {digest}"
        )
    return digest


def expect_rejection(data: dict[str, Any], description: str) -> None:
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {description}")


def self_test() -> None:
    source = load_json(DEFAULT_ARTIFACT)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["fixed7_survivors"].remove(28)
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "a weakened fixed-7 intersection")

    mutated = copy.deepcopy(source)
    mutated["superspecial_survivors"].append(5)
    mutated["superspecial_survivors"].sort()
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "a false superspecial packet")

    mutated = copy.deepcopy(source)
    mutated["batches"][0]["auxiliary_primes"].remove(239)
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "an incomplete auxiliary-prime partition")

    mutated = copy.deepcopy(source)
    mutated["source"]["source_commit"] = "0" * 40
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "an unpinned upstream source")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
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

    if "does not by itself prove" not in source["nonclaim"]:
        raise RuntimeError("normalized artifact lacks its nonclaim")
    print("signature-357 fixed-7 level-(2,3) negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=pathlib.Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.artifact))
    print("fixed-7 level-(2,3) public-Magma certificate valid")
    print("  packets: 35 -> 11 fixed-7 -> 9 superspecial")
    print("  fixed-7 survivors:", ", ".join(map(str, EXPECTED_FIXED7)))
    print("  superspecial survivors:", ", ".join(map(str, EXPECTED_SUPERSPECIAL)))
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
