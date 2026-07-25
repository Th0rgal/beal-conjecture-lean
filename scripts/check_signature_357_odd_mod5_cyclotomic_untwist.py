#!/usr/bin/env python3
"""Replay the finite part of the odd mod-5 cyclotomic untwist.

The automorphic/local-type statements remain imported.  This checker verifies
the quadratic extension, conductor and level arithmetic, bound source digests,
and the parity-specific trace filter at the unique prime above 2.
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
MANIFEST = ROOT / "Research" / "Signature357" / "odd_mod5_cyclotomic_untwist.json"


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError(f"{path} root must be an object")
    return value


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def bound_source(path: pathlib.Path, expected_digest: str, label: str) -> dict[str, Any]:
    source = load(path)
    if canonical_sha256(source) != source.get("certificate_sha256"):
        raise CertificateError(f"{label} source digest mismatch")
    if source["certificate_sha256"] != expected_digest:
        raise CertificateError(f"manifest is not bound to the {label} source")
    return source


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 2:
        raise CertificateError("schema_version must equal 2")
    if canonical_sha256(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    sources = data["source_dependencies"]
    odd = bound_source(
        ROOT / sources["odd_prime7_type_path"],
        sources["odd_prime7_type_sha256"],
        "odd-p7 local type",
    )
    low = bound_source(
        ROOT / sources["low_level_filter_path"],
        sources["low_level_filter_sha256"],
        "low-level filter",
    )
    if odd["local_conclusion"] != {
        "congruence_twist_at_7": "unramified (indeed locally trivial)",
        "odd_branch_residual_conductor_exponent_at_7": 2,
        "reason": (
            "Remark 3.12 fixes the first-row exponent at 2 under an unramified "
            "congruence twist; the ramified quadratic character survives reduction modulo 5"
        ),
    }:
        raise CertificateError("odd-p7 local type input changed")

    character = data["cyclotomic_character"]
    if character["extension"] != "Q(zeta_7)/K7" or character["degree"] != 2:
        raise CertificateError("cyclotomic quadratic extension mismatch")
    relative_discriminant_norm = 7**5 // (7**2) ** 2
    if relative_discriminant_norm != 7 or character["finite_ramification_support"] != [7]:
        raise CertificateError("relative discriminant or ramification support changed")
    if character["trivial_on_full_trace_field"] is not True:
        raise CertificateError("full-cyclotomic trace invariance changed")

    local = data["local_untwist"]
    if (
        local["original_residual_conductor_exponent"] != 2
        or "ramified quadratic" not in local["original_type_at_7"]
        or local["twisted_residual_conductor_exponents"] != [0, 1]
    ):
        raise CertificateError("local untwist metadata changed")
    ramified = [(0, 1), (1, 1)]
    products = {
        ((a + c) % 2, (b + d) % 2)
        for a, b in ramified
        for c, d in ramified
    }
    if products != {(0, 0), (1, 0)}:
        raise CertificateError("ramified quadratic products are not unramified")

    preserved = data["preserved_properties"]
    if preserved["prime3_conductor_exponents"] != [2, 3]:
        raise CertificateError("prime-3 exponents changed")
    if preserved["absolute_irreducibility"] is not True:
        raise CertificateError("absolute irreducibility was not preserved")
    if preserved["determinant"] != "cyclotomic, since eta_7^2=1":
        raise CertificateError("determinant statement changed")
    if "unchanged" not in preserved["full_cyclotomic_local_trace_polynomials"]:
        raise CertificateError("full-cyclotomic trace invariance is missing")
    if "norm8_zero_trace_filter" in preserved:
        raise CertificateError("obsolete parity-blind norm-8 filter remains")
    expected_prime2 = {
        "B_odd": "a_P2=0 mod 5",
        "B_even": "a_P2 is 1 or 4 mod 5",
        "cyclotomic_untwist_value_at_2": 1,
        "reason": (
            "ord_7(2)=3, so the unique prime above 2 in K7 splits in "
            "Q(zeta_7)/K7"
        ),
    }
    if preserved.get("prime2_trace_filter") != expected_prime2:
        raise CertificateError("parity-specific prime-2 trace filter changed")
    if pow(2, 3, 7) != 1 or pow(2, 1, 7) in {1, 6} or pow(2, 2, 7) in {1, 6}:
        raise CertificateError("prime-2 residue-degree computation changed")

    levels = data["level_compression"]
    original_pairs = [(2, 2), (3, 2)]
    twisted_pairs = [(2, 0), (2, 1), (3, 0), (3, 1)]
    if [tuple(pair) for pair in levels["untwisted_exponent_pairs"]] != original_pairs:
        raise CertificateError("untwisted pair list mismatch")
    if [tuple(pair) for pair in levels["twisted_exponent_pairs"]] != twisted_pairs:
        raise CertificateError("twisted pair list mismatch")
    original_norms = [27**a * 7**b for a, b in original_pairs]
    twisted_norms = [27**a * 7**b for a, b in twisted_pairs]
    if levels["untwisted_level_norms"] != original_norms:
        raise CertificateError("untwisted level norms changed")
    if levels["twisted_level_norms"] != twisted_norms:
        raise CertificateError("twisted level norms changed")
    if (
        levels["maximum_norm_before"] != max(original_norms)
        or levels["maximum_norm_after"] != max(twisted_norms)
        or levels["maximum_norm_reduction_factor"] != 7
    ):
        raise CertificateError("maximum-norm compression changed")

    odd_low = low["branch_filters"]["odd_branch"]
    if odd_low["low_level_survivors"] != [] or odd_low["count"] != 0:
        raise CertificateError("odd low-level filter is no longer empty")
    if "3.3.49.1-729.1-b" not in odd_low["pre_noncm_survivors"]:
        raise CertificateError("norm-729 packet is missing from the low-level input")
    if "3.3.49.1-729.1-b" not in low["global_noncm_filter"]["cm_packets_removed"]:
        raise CertificateError("norm-729 packet was not removed")
    if levels["low_level_norm_eliminated"] != 729:
        raise CertificateError("wrong low-level norm elimination")
    if levels["remaining_twisted_level_norms"] != [5103, 19683, 137781]:
        raise CertificateError("remaining twisted frontier changed")

    expected_conclusion = (
        "the odd branch can be studied through an absolutely irreducible "
        "cyclotomic quadratic twist whose lowered mod-5 level is one of "
        "5103, 19683 or 137781"
    )
    if data["conclusion"] != expected_conclusion:
        raise CertificateError("conclusion changed")
    if "imported theorems" not in data["nonclaim"] or "not a proof" not in data["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim missing")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = canonical_sha256(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    source = load(MANIFEST)
    validate(source)
    mutated = copy.deepcopy(source)
    mutated["cyclotomic_character"]["finite_ramification_support"] = [3, 7]
    expect_rejection(mutated, "a twist with extra finite ramification")
    mutated = copy.deepcopy(source)
    mutated["local_untwist"]["twisted_residual_conductor_exponents"] = [0, 1, 2]
    expect_rejection(mutated, "a conductor-two untwisted local type")
    mutated = copy.deepcopy(source)
    mutated["preserved_properties"]["prime2_trace_filter"]["B_even"] = "a_P2=0 mod 5"
    expect_rejection(mutated, "the obsolete parity-blind norm-8 trace")
    mutated = copy.deepcopy(source)
    mutated["level_compression"]["remaining_twisted_level_norms"].append(35721)
    expect_rejection(mutated, "the obsolete high level")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":2,"schema_version":2}')
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
    print("odd mod-5 cyclotomic untwist negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(MANIFEST))
    print("odd mod-5 cyclotomic untwist certificate valid")
    print("  original levels: 35721, 964467")
    print("  remaining twisted levels: 5103, 19683, 137781")
    print("  norm-8 traces: B odd -> 0; B even -> 1 or 4 modulo 5")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
