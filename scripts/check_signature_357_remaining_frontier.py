#!/usr/bin/env python3
"""Replay the exact twisted odd frontier after closing the e3=2 block."""
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


def bound_source(path: str, expected: str, label: str) -> dict[str, Any]:
    source = load(ROOT / path)
    if digest(source) != source.get("certificate_sha256"):
        raise CertificateError(f"{label} source digest mismatch")
    if source["certificate_sha256"] != expected:
        raise CertificateError(f"frontier is not bound to the {label} source")
    return source


def validate(data: dict[str, Any]) -> tuple[str, list[int]]:
    expected_keys = {
        "schema_version",
        "status",
        "equation",
        "branch_status",
        "compression",
        "conclusion",
        "next_computation",
        "nonclaim",
        "certificate_sha256",
    }
    if set(data) != expected_keys:
        raise CertificateError("manifest keys differ from schema")
    if data.get("schema_version") != 3 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or frontier digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    branches = data["branch_status"]
    even = branches["even"]
    even_source = bound_source(
        even["certificate_path"], even["certificate_sha256"], "even-branch closure"
    )
    if even_source["conclusion"] != (
        "there is no primitive positive solution in the Dahmen--Siksek even branch"
    ) or even["conclusion"] != "empty":
        raise CertificateError("even branch is not closed")

    odd = branches["odd"]
    if odd["allowed_e3"] != [2, 3] or odd["closed_e3"] != [2] or odd["remaining_e3"] != [3]:
        raise CertificateError("odd e3 status mismatch")
    irreducibility = bound_source(
        odd["global_mod5_irreducibility_path"],
        odd["global_mod5_irreducibility_sha256"],
        "mod-5 irreducibility",
    )
    if "absolutely irreducible" not in irreducibility["conclusion"]:
        raise CertificateError("odd mod-5 irreducibility conclusion missing")
    untwist = bound_source(
        odd["cyclotomic_untwist_path"],
        odd["cyclotomic_untwist_sha256"],
        "cyclotomic untwist",
    )
    if untwist["local_untwist"]["twisted_residual_conductor_exponents"] != [0, 1]:
        raise CertificateError("twisted prime-7 conductor bound mismatch")
    monodromy = bound_source(
        odd["exact_monodromy_path"],
        odd["exact_monodromy_sha256"],
        "exact monodromy",
    )
    if monodromy["exact_conductor"]["cases"] != [
        {"e7_twisted": 0, "valuation_class": "v7(A)=3 mod 5"},
        {"e7_twisted": 1, "valuation_class": "v7(A)!=3 mod 5"},
    ]:
        raise CertificateError("exact monodromy split mismatch")
    if monodromy["automorphic_frontier"]["remaining_level_norms"] != [5103, 19683, 137781]:
        raise CertificateError("exact-monodromy candidate frontier changed")

    split = odd["valuation_split"]
    zero = split["v7A_congruent_3_mod5"]
    nonzero = split["other_v7A_classes"]
    if zero != {
        "twisted_e7": 0,
        "candidate_pairs": [[2, 0], [3, 0]],
        "candidate_level_norms": [729, 19683],
        "closed_level_norms": [729],
        "remaining_pairs": [[3, 0]],
        "remaining_level_norms": [19683],
    }:
        raise CertificateError("valuation-3 mod-5 block mismatch")
    if nonzero != {
        "twisted_e7": 1,
        "candidate_pairs": [[2, 1], [3, 1]],
        "candidate_level_norms": [5103, 137781],
        "closed_level_norms": [5103],
        "remaining_pairs": [[3, 1]],
        "remaining_level_norms": [137781],
    }:
        raise CertificateError("nonzero-monodromy block mismatch")

    candidate_pairs = zero["candidate_pairs"] + nonzero["candidate_pairs"]
    candidate_norms = [27**e3 * 7**e7 for e3, e7 in candidate_pairs]
    if candidate_norms != [729, 19683, 5103, 137781]:
        raise CertificateError("candidate-level arithmetic mismatch")
    remaining_pairs = sorted(zero["remaining_pairs"] + nonzero["remaining_pairs"])
    remaining_norms = sorted(zero["remaining_level_norms"] + nonzero["remaining_level_norms"])
    if remaining_pairs != odd["remaining_exponent_pairs"] or remaining_pairs != [[3, 0], [3, 1]]:
        raise CertificateError("remaining exponent-pair mismatch")
    if remaining_norms != odd["remaining_level_norms"] or remaining_norms != [19683, 137781]:
        raise CertificateError("remaining level-norm mismatch")

    pairing = odd["fixed7_pairing"]
    first = pairing["e3_2"]
    closure = bound_source(
        first["prime29_closure_path"],
        first["prime29_closure_sha256"],
        "odd-e3=2 prime-29 closure",
    )
    if first["closed_levels"] != [[2, 2], [2, 3]] or first["remaining_packets"] != []:
        raise CertificateError("e3=2 fixed-7 closure metadata mismatch")
    if closure["conclusion"]["surviving_packets"] != [] or closure["conclusion"]["statement"] != (
        "the Dahmen--Siksek odd e3=2 block is empty"
    ):
        raise CertificateError("e3=2 block is not closed")

    second = pairing["e3_3"]
    level32 = bound_source(
        second["closure_path"], second["closure_sha256"], "fixed-7 level-(3,2) closure"
    )
    if second["closed_level"] != [3, 2] or second["remaining_level"] != [3, 3]:
        raise CertificateError("e3=3 fixed-7 pairing mismatch")
    if level32["public_magma"]["non_cm_superspecial_survivors"] != []:
        raise CertificateError("fixed-7 level (3,2) is not closed")

    compression = data["compression"]
    if compression != {
        "obsolete_untwisted_odd_levels": [35721, 964467],
        "twisted_candidate_level_norms": [729, 5103, 19683, 137781],
        "closed_level_norms": [729, 5103],
        "final_remaining_level_count": 2,
        "final_remaining_level_norms": [19683, 137781],
        "maximum_level_norm": 137781,
        "maximum_norm_reduction_from_untwisted_frontier": 7,
    }:
        raise CertificateError("compression metadata mismatch")
    if "level_5103" in data["next_computation"]:
        raise CertificateError("closed level 5103 remains scheduled")
    if "+/-8 mod 5" not in data["next_computation"]["level_19683"]:
        raise CertificateError("removed-prime trace condition missing")
    if "does not prove" not in data["nonclaim"]:
        raise CertificateError("explicit nonclaim missing")
    return data["certificate_sha256"], remaining_norms


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
    mutated["branch_status"]["odd"]["closed_e3"] = []
    expect_rejection(mutated, "a reopened e3=2 block")
    mutated = copy.deepcopy(source)
    mutated["branch_status"]["odd"]["fixed7_pairing"]["e3_2"]["remaining_packets"] = [24]
    expect_rejection(mutated, "a fabricated e3=2 packet survivor")
    mutated = copy.deepcopy(source)
    mutated["compression"]["final_remaining_level_norms"].append(5103)
    expect_rejection(mutated, "the closed level 5103")
    duplicate = '{"schema_version":3,"schema_version":3}'
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
    print("signature-357 post-e3=2 frontier negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate, norms = validate(load(MANIFEST))
    print("signature-357 post-e3=2 paired frontier valid")
    print("  even branch: closed")
    print("  odd e3=2 block: closed")
    print("  remaining odd mod-5 levels:", ", ".join(map(str, norms)))
    print("  remaining fixed-7 level: (3,3)")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
