#!/usr/bin/env python3
"""Replay finite consequences of the odd-branch 7-adic Kummer theorem."""
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
MANIFEST = ROOT / "Research" / "Signature357" / "odd_7adic_kummer.json"


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: pathlib.Path) -> dict[str, Any]:
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


def digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1:
        raise CertificateError("schema_version must equal 1")
    if digest(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    finite = data["finite_replay"]
    units343 = [value for value in range(1, 343) if value % 7]
    if len(units343) != 294 or len(units343) != finite["unit_count_mod343"]:
        raise CertificateError("unit count modulo 343 mismatch")

    pairs = [
        (base, right)
        for base in units343
        for right in units343
        if pow(right, 7, 343) == pow(base, 5, 343)
    ]
    if len(pairs) != 294 or len(pairs) != finite["solution_pair_count_mod343"]:
        raise CertificateError("power-equation pair count modulo 343 mismatch")
    if any(pow(base, 42, 343) != 1 for base, _right in pairs):
        raise CertificateError("a local solution violates B^42=1 modulo 343")
    if any(pow(base, 6, 49) != 1 for base, _right in pairs):
        raise CertificateError("a local solution violates B^6=1 modulo 49")

    roots49 = [value for value in range(1, 49) if value % 7 and pow(value, 6, 49) == 1]
    image49 = sorted({pow(value, 7, 49) for value in range(1, 49) if value % 7})
    expected = finite["roots_X6_minus_1_mod49"]
    if roots49 != expected or image49 != expected:
        raise CertificateError("seventh-power image modulo 49 mismatch")
    if len(image49) != finite["seventh_power_image_size_mod49"] or len(image49) != 6:
        raise CertificateError("seventh-power image size mismatch")

    phi = 6 * 7**2
    if phi != finite["euler_phi_343"] or math.gcd(5 * phi // 7, phi) != 42:
        raise CertificateError("Euler/gcd derivation mismatch")
    if finite["derived_gcd"] != 42:
        raise CertificateError("recorded exponent gcd mismatch")

    theorem = data["theorem"]
    if theorem["finite_consequences"]["B_residues_mod49"] != expected:
        raise CertificateError("theorem residue list mismatch")
    if theorem["finite_consequences"]["B^42_mod343"] != 1:
        raise CertificateError("B^42 theorem consequence changed")
    if theorem["finite_consequences"]["B^6_mod49"] != 1:
        raise CertificateError("B^6 theorem consequence changed")

    # The common-power construction for x^7=y^5 uses 3*7-4*5=1.
    if 3 * 7 - 4 * 5 != 1:
        raise CertificateError("Bezout common-power identity failed")
    if "cube" not in theorem["cube_condition"]:
        raise CertificateError("normalized cube conclusion is missing")
    if "does not prove the odd branch" not in data["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim is missing")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = digest(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    source = load(MANIFEST)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["finite_replay"]["roots_X6_minus_1_mod49"][1] = 17
    expect_rejection(mutated, "a corrupted seventh-power residue")

    mutated = copy.deepcopy(source)
    mutated["finite_replay"]["solution_pair_count_mod343"] = 293
    expect_rejection(mutated, "an incomplete local power-equation count")

    mutated = copy.deepcopy(source)
    mutated["theorem"]["finite_consequences"]["B^42_mod343"] = 0
    expect_rejection(mutated, "the loss of the modulo-343 consequence")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
        path = pathlib.Path(fixture.name)
    try:
        try:
            load(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)
    print("signature-357 odd 7-adic Kummer negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(MANIFEST))
    print("signature-357 odd 7-adic Kummer certificate valid")
    print("  B is a seventh power in Z_7^*")
    print("  B mod 49 is one of 1,18,19,30,31,48")
    print("  the normalized C-z^5 difference is a cube")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
