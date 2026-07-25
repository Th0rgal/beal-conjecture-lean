#!/usr/bin/env python3
"""Replay the Hasse-refined mod-5 level frontier for signature (3,5,7)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "branch_specific_level_frontier.json"
CLOSURE = ROOT / "Research" / "Signature357" / "low_level_complete_closure.json"


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
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(data: dict[str, Any], closure: dict[str, Any]) -> tuple[str, list[int]]:
    if data.get("schema_version") != 2:
        raise CertificateError("schema_version must equal 2")
    if digest(data) != data.get("certificate_sha256"):
        raise CertificateError("frontier certificate digest mismatch")

    scope = data["scope"]
    if scope["orientation"] != "a=-C,b=B,c=A,q=7,p=5,r=3":
        raise CertificateError("orientation mismatch")
    if scope["prime_norms"] != {"p3": 27, "p7": 7}:
        raise CertificateError("prime norm metadata mismatch")

    dependencies = data["source_dependencies"]
    hasse_path = ROOT / dependencies["fixed7_prime7_hasse_path"]
    hasse = load(hasse_path)
    if digest(hasse) != hasse.get("certificate_sha256"):
        raise CertificateError("prime-7 Hasse certificate digest mismatch")
    if hasse["certificate_sha256"] != dependencies["fixed7_prime7_hasse_sha256"]:
        raise CertificateError("frontier is not bound to the Hasse certificate")
    if hasse["scope"]["conclusion"] != "7 divides C":
        raise CertificateError("Hasse input does not force 7|C")

    even = data["branches"]["even"]
    odd = data["branches"]["odd"]
    if even["allowed_e3"] != [1, 2] or even["allowed_e7"] != [1]:
        raise CertificateError("even branch conductor range mismatch")
    if odd["allowed_e3"] != [2, 3] or odd["allowed_e7"] != [0, 1, 2]:
        raise CertificateError("odd branch conductor range mismatch")

    coarse = {(e3, e7) for e3 in range(4) for e7 in range(4)}
    even_pairs = {
        (e3, e7)
        for e3 in even["allowed_e3"]
        for e7 in even["allowed_e7"]
    }
    odd_pairs = {
        (e3, e7)
        for e3 in odd["allowed_e3"]
        for e7 in odd["allowed_e7"]
    }
    allowed = sorted(even_pairs | odd_pairs)
    removed = sorted(coarse - set(allowed))
    recorded_allowed = [tuple(pair) for pair in data["branch_specific_exponent_pairs"]]
    recorded_removed = [tuple(pair) for pair in data["removed_exponent_pairs"]]
    if allowed != recorded_allowed or removed != recorded_removed:
        raise CertificateError("branch-specific exponent-pair frontier mismatch")
    if (
        data["coarse_level_count"] != 16
        or data["branch_specific_level_count"] != len(allowed)
        or len(allowed) != 7
    ):
        raise CertificateError("level-count compression mismatch")

    norms = sorted({27**e3 * 7**e7 for e3, e7 in allowed})
    if norms != data["branch_specific_level_norms"]:
        raise CertificateError("branch-specific level norms mismatch")
    if max(norms) != data["maximum_level_norm"] or max(norms) != 964467:
        raise CertificateError("maximum level norm mismatch")
    if (
        27**3 * 7**3 // max(norms) != data["maximum_norm_reduction_factor"]
        or data["maximum_norm_reduction_factor"] != 7
    ):
        raise CertificateError("maximum norm reduction factor mismatch")

    if digest(closure) != closure.get("certificate_sha256"):
        raise CertificateError("closure manifest digest mismatch")
    closure_meta = data["complete_low_level_closure"]
    if closure["certificate_sha256"] != closure_meta["sha256"]:
        raise CertificateError("frontier is not bound to the low-level closure")
    bound = closure["scope"]["complete_level_norm_bound"]
    low = [norm for norm in norms if norm <= bound]
    if low != closure_meta["closed_admissible_norms_at_most_2059"] or low != [189, 729]:
        raise CertificateError("closed low-level norm list mismatch")
    high = [norm for norm in norms if norm > bound]
    if (
        high != data["remaining_high_level_norms"]
        or len(high) != data["remaining_high_level_count"]
        or len(high) != 5
    ):
        raise CertificateError("remaining high-level frontier mismatch")
    if data["even_branch_remaining_norms"] != [5103]:
        raise CertificateError("even branch was not concentrated at level 5103")
    if data["odd_branch_remaining_norms"] != high:
        raise CertificateError("odd branch high-level frontier mismatch")
    return data["certificate_sha256"], high


def self_test() -> None:
    base, closure = load(MANIFEST), load(CLOSURE)
    validate(base, closure)

    mutated = copy.deepcopy(base)
    mutated["branches"]["even"]["allowed_e7"] = [0, 1]
    mutated["certificate_sha256"] = digest(mutated)
    try:
        validate(mutated, closure)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted an even branch without 7|C")

    mutated = copy.deepcopy(base)
    mutated["remaining_high_level_norms"].append(250047)
    mutated["remaining_high_level_count"] += 1
    mutated["certificate_sha256"] = digest(mutated)
    try:
        validate(mutated, closure)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a Hasse-excluded level")

    duplicate = '{"schema_version":2,"schema_version":2}'
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
    print("signature-357 Hasse-refined level negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate, high = validate(load(MANIFEST), load(CLOSURE))
    print("Hasse-refined mod-5 level frontier valid")
    print("coarse levels: 16 -> branch-specific levels: 7")
    print("complete low levels: closed")
    print("remaining high levels:", ", ".join(map(str, high)))
    print("even branch remaining level: 5103")
    print("maximum remaining norm: 964467")
    print(f"certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
