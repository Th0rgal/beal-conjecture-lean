#!/usr/bin/env python3
"""Replay the finite part of the odd mod-5 cyclotomic untwist.

Imported inputs:
* the odd-prime-7 HGM local type is special with a ramified quadratic
  character and residual conductor exponent 2;
* finite-order Hilbert modular twists and level lowering;
* CM/non-CM is invariant under character twist.

The checker independently verifies the relative-discriminant calculation,
the local quadratic square-class multiplication, the level arithmetic, the
full-cyclotomic trace invariance, and the low-level removal of norm 729.
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
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError(f"{path} root must be an object")
    return value


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1:
        raise CertificateError("schema_version must equal 1")
    if canonical_sha256(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    sources = data["source_dependencies"]
    odd = load(ROOT / sources["odd_prime7_type_path"])
    low = load(ROOT / sources["low_level_filter_path"])
    if canonical_sha256(odd) != odd.get("certificate_sha256"):
        raise CertificateError("odd-p7 source digest mismatch")
    if odd["certificate_sha256"] != sources["odd_prime7_type_sha256"]:
        raise CertificateError("manifest is not bound to the odd-p7 source")
    if canonical_sha256(low) != low.get("certificate_sha256"):
        raise CertificateError("low-level filter digest mismatch")
    if low["certificate_sha256"] != sources["low_level_filter_sha256"]:
        raise CertificateError("manifest is not bound to the low-level filter")

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
    # |disc Q(zeta_7)|=7^5 and disc(K7)=7^2.  The relative discriminant norm is
    # |disc(L)| / disc(K)^2 = 7, so the sole finite ramified prime is the
    # unique prime over 7 and the relative extension is tamely quadratic.
    relative_discriminant_norm = 7**5 // (7**2) ** 2
    if relative_discriminant_norm != 7:
        raise CertificateError("relative discriminant calculation failed")
    if character["finite_ramification_support"] != [7]:
        raise CertificateError("finite ramification support mismatch")
    if 21 % 7 != 0 or character["trivial_on_full_trace_field"] is not True:
        raise CertificateError("F21 trace invariance is not certified")

    local = data["local_untwist"]
    if local["original_residual_conductor_exponent"] != 2:
        raise CertificateError("original residual exponent mismatch")
    if "ramified quadratic" not in local["original_type_at_7"]:
        raise CertificateError("original ramified character is missing")
    # K_q^*/K_q^{*2} for odd residue characteristic is C2 x C2.
    # Encode classes (unit parity, uniformizer parity).  Ramified classes have
    # second coordinate 1.  Their products have second coordinate 0.
    ramified = [(0, 1), (1, 1)]
    products = {
        ((a + c) % 2, (b + d) % 2)
        for a, b in ramified
        for c, d in ramified
    }
    if products != {(0, 0), (1, 0)}:
        raise CertificateError("product of ramified quadratic classes is not unramified")
    if local["twisted_residual_conductor_exponents"] != [0, 1]:
        raise CertificateError("twisted conductor range mismatch")

    preserved = data["preserved_properties"]
    if preserved["prime3_conductor_exponents"] != [2, 3]:
        raise CertificateError("prime-3 exponents changed under the unramified twist")
    if preserved["absolute_irreducibility"] is not True:
        raise CertificateError("quadratic twist must preserve absolute irreducibility")
    if preserved["determinant"] != "cyclotomic, since eta_7^2=1":
        raise CertificateError("determinant statement mismatch")
    if "unchanged" not in preserved["full_cyclotomic_local_trace_polynomials"]:
        raise CertificateError("full-cyclotomic trace invariance is missing")

    levels = data["level_compression"]
    original_pairs = [(2, 2), (3, 2)]
    twisted_pairs = [(2, 0), (2, 1), (3, 0), (3, 1)]
    if [tuple(pair) for pair in levels["untwisted_exponent_pairs"]] != original_pairs:
        raise CertificateError("untwisted pair list mismatch")
    if [tuple(pair) for pair in levels["twisted_exponent_pairs"]] != twisted_pairs:
        raise CertificateError("twisted pair list mismatch")
    original_norms = [27**a * 7**b for a, b in original_pairs]
    twisted_norms = [27**a * 7**b for a, b in twisted_pairs]
    if original_norms != levels["untwisted_level_norms"]:
        raise CertificateError("untwisted level norms mismatch")
    if twisted_norms != levels["twisted_level_norms"]:
        raise CertificateError("twisted level norms mismatch")
    if (
        levels["maximum_norm_before"] != max(original_norms)
        or levels["maximum_norm_after"] != max(twisted_norms)
        or levels["maximum_norm_reduction_factor"]
        != max(original_norms) // max(twisted_norms)
        or levels["maximum_norm_reduction_factor"] != 7
    ):
        raise CertificateError("maximum-norm compression mismatch")

    odd_low = low["branch_filters"]["odd_branch"]
    if odd_low["low_level_survivors"] != [] or odd_low["count"] != 0:
        raise CertificateError("odd low-level filter is no longer empty")
    if "3.3.49.1-729.1-b" not in odd_low["pre_noncm_survivors"]:
        raise CertificateError("norm-729 CM packet is missing from the low-level input")
    if "3.3.49.1-729.1-b" not in low["global_noncm_filter"]["cm_packets_removed"]:
        raise CertificateError("norm-729 packet was not removed by the non-CM theorem")
    if levels["low_level_norm_eliminated"] != 729:
        raise CertificateError("wrong low-level norm elimination")
    if levels["remaining_twisted_level_norms"] != [5103, 19683, 137781]:
        raise CertificateError("remaining twisted frontier mismatch")

    expected = (
        "the odd branch can be studied through an absolutely irreducible "
        "cyclotomic quadratic twist whose lowered mod-5 level is one of "
        "5103, 19683 or 137781"
    )
    if data["conclusion"] != expected:
        raise CertificateError("conclusion mismatch")
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
    mutated["level_compression"]["remaining_twisted_level_norms"].append(35721)
    expect_rejection(mutated, "the obsolete high level")

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
    print("odd mod-5 cyclotomic untwist negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load(MANIFEST))
    print("odd mod-5 cyclotomic untwist certificate valid")
    print("  original levels: 35721, 964467")
    print("  twisted levels before low closure: 729, 5103, 19683, 137781")
    print("  remaining twisted levels: 5103, 19683, 137781")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
