#!/usr/bin/env python3
"""Replay the final two-level automorphic frontier for signature (3,5,7)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "signature357_remaining_frontier.json"


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
        raise CertificateError(f"{path} root must be an object")
    return value


def digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(data: dict[str, Any]) -> tuple[str, list[int]]:
    expected = {
        "schema_version",
        "status",
        "equation",
        "branch_status",
        "compression",
        "next_computation",
        "conclusion",
        "nonclaim",
        "certificate_sha256",
    }
    if set(data) != expected:
        raise CertificateError("manifest keys differ from schema")
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if digest(data) != data["certificate_sha256"]:
        raise CertificateError("frontier certificate digest mismatch")
    if data["equation"] != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    branches = data["branch_status"]
    even = branches["even"]
    even_manifest = load(ROOT / even["certificate_path"])
    if digest(even_manifest) != even_manifest.get("certificate_sha256"):
        raise CertificateError("even-branch certificate digest mismatch")
    if even_manifest["certificate_sha256"] != even["certificate_sha256"]:
        raise CertificateError("frontier not bound to the even-branch certificate")
    if even_manifest["conclusion"] != (
        "there is no primitive positive solution in the Dahmen--Siksek even branch"
    ):
        raise CertificateError("even branch is not closed")
    if even["conclusion"] != "empty":
        raise CertificateError("even branch status mismatch")

    odd = branches["odd"]
    irreducibility = load(ROOT / odd["global_mod5_irreducibility_path"])
    if irreducibility.get("certificate_sha256") != odd[
        "global_mod5_irreducibility_sha256"
    ]:
        raise CertificateError("mod-5 irreducibility dependency mismatch")
    if "absolutely irreducible" not in irreducibility["conclusion"]:
        raise CertificateError("odd mod-5 irreducibility conclusion missing")

    twist = load(ROOT / odd["exact_prime7_conductor_path"])
    if digest(twist) != twist.get("certificate_sha256"):
        raise CertificateError("odd prime-7 twist certificate digest mismatch")
    if twist["certificate_sha256"] != odd["exact_prime7_conductor_sha256"]:
        raise CertificateError("frontier not bound to odd prime-7 certificate")
    if twist["local_conclusion"]["odd_branch_residual_conductor_exponent_at_7"] != 2:
        raise CertificateError("odd e7 is not exactly 2")

    if odd["allowed_e3"] != [2, 3] or odd["exact_e7"] != 2:
        raise CertificateError("odd conductor exponent metadata mismatch")
    pairs = sorted((e3, odd["exact_e7"]) for e3 in odd["allowed_e3"])
    if pairs != [tuple(pair) for pair in odd["remaining_exponent_pairs"]]:
        raise CertificateError("remaining exponent-pair mismatch")
    norms = [27**e3 * 7**e7 for e3, e7 in pairs]
    if norms != odd["remaining_level_norms"] or norms != [35721, 964467]:
        raise CertificateError("remaining level-norm mismatch")

    compression = data["compression"]
    if compression["final_remaining_level_norms"] != norms:
        raise CertificateError("compressed final norm list mismatch")
    if compression["final_remaining_level_count"] != 2:
        raise CertificateError("final level count must equal two")
    if compression["maximum_level_norm"] != max(norms):
        raise CertificateError("maximum level norm mismatch")
    old = set(compression["previous_branch_specific_level_norms"])
    removed = set(compression["even_branch_levels_removed_by_complete_closure"])
    removed |= set(compression["odd_levels_removed_by_exact_e7"])
    if old - removed != set(norms):
        raise CertificateError("frontier set subtraction does not replay")
    if "does not prove" not in data["nonclaim"]:
        raise CertificateError("explicit nonclaim missing")
    return data["certificate_sha256"], norms


def self_test() -> None:
    source = load(MANIFEST)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["branch_status"]["odd"]["exact_e7"] = 1
    mutated["certificate_sha256"] = digest(mutated)
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted an obsolete odd e7 value")

    mutated = copy.deepcopy(source)
    mutated["compression"]["final_remaining_level_norms"].append(5103)
    mutated["compression"]["final_remaining_level_count"] = 3
    mutated["certificate_sha256"] = digest(mutated)
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the removed odd level 5103")

    duplicate = '{"schema_version":1,"schema_version":1}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write(duplicate)
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
    print("signature-357 remaining-frontier negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate, norms = validate(load(MANIFEST))
    print("signature-357 two-level remaining frontier valid")
    print("  even branch: closed")
    print("  odd mod-5 levels:", ", ".join(map(str, norms)))
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
