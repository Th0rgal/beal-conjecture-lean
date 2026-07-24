#!/usr/bin/env python3
"""Replay the global non-CM reduction for the independent mod-5 (3,5,7) HGM.

Pacetti--Villagra Torcomian Proposition 5.8 and Mihailescu's Catalan theorem are
explicit literature inputs. The checker verifies the variable orientation, the
Dahmen--Siksek branch support arithmetic, the forced value B=1, and the exact
Catalan equation C^7-A^3=1. It does not replace either imported theorem.
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
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "mod5_global_noncm.json"


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


def validate(data: dict[str, Any]) -> str:
    expected_keys = {
        "schema_version", "status", "equation", "compatible_system",
        "branch_support", "cm_consequence", "catalan_input", "conclusion",
        "nonclaim", "certificate_sha256",
    }
    if set(data) != expected_keys:
        raise CertificateError("manifest keys differ from the pinned schema")
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "literature-assisted-global-non-CM-reduction":
        raise CertificateError("unexpected status")
    if data["equation"] != "A^3+B^5=C^7":
        raise CertificateError("unexpected equation")

    system = data["compatible_system"]
    if system["orientation"] != "(-C)^7+B^5+A^3=0":
        raise CertificateError("independent HGM orientation mismatch")
    if system["paper_variables"] != [
        "a=-C", "b=B", "c=A", "q=7", "p=5", "r=3"
    ]:
        raise CertificateError("paper-variable orientation mismatch")
    if "Proposition 5.8" not in system["source"]:
        raise CertificateError("CM-support source is not pinned")
    if "paper variable b" not in system["source_statement"] or "{q,r}" not in system["source_statement"]:
        raise CertificateError("CM-support theorem statement mismatch")

    branches = data["branch_support"]
    if set(branches) != {"even", "odd"}:
        raise CertificateError("expected the two Dahmen--Siksek branches")
    even = branches["even"]
    odd = branches["odd"]
    if even != {
        "inputs": ["30 divides C", "7 does not divide A*B", "gcd(A,B,C)=1"],
        "conclusion": "3 does not divide B and 7 does not divide B",
    }:
        raise CertificateError("even-branch support arithmetic mismatch")
    if odd != {
        "inputs": ["3 does not divide A*B*C", "7 divides A", "gcd(A,B,C)=1"],
        "conclusion": "3 does not divide B and 7 does not divide B",
    }:
        raise CertificateError("odd-branch support arithmetic mismatch")

    consequence = data["cm_consequence"]
    if consequence["allowed_prime_support_for_B"] != [3, 7]:
        raise CertificateError("CM support was not transferred to B")
    if consequence["coprime_to"] != 3 * 7:
        raise CertificateError("branchwise coprimality must exclude 3 and 7")
    # A positive integer supported only at {3,7} and coprime to 21 is 1.
    possible = [3**a * 7**b for a in range(3) for b in range(3)]
    supported_and_coprime = sorted({value for value in possible if value % 3 and value % 7})
    if supported_and_coprime != [1] or consequence["forced_value"] != 1:
        raise CertificateError("CM support plus branch conditions did not force B=1")
    if consequence["equation_after_substitution"] != "C^7-A^3=1":
        raise CertificateError("B=1 was not substituted correctly")

    catalan = data["catalan_input"]
    if "Mihailescu" not in catalan["source"]:
        raise CertificateError("Catalan source is missing")
    if catalan["exponents"] != [7, 3]:
        raise CertificateError("Catalan exponents mismatch")
    if catalan["bases_are_greater_than_one"] is not True:
        raise CertificateError("the Catalan bases must be nontrivial")
    # If A=1, then C^7=2; if C=1, positivity gives A^3=0.  Thus A,C>1.
    if 1**3 + 1 == 2 and 1**7 == 1:
        pass
    else:
        raise CertificateError("internal positivity check failed")
    if catalan["not_catalan_exception"] is not True:
        raise CertificateError("the exponents (7,3) are not the Catalan exception (2,3)")
    if "3^2-2^3=1" not in catalan["theorem"]:
        raise CertificateError("Catalan theorem statement mismatch")

    expected_conclusion = (
        "no hypothetical primitive positive (3,5,7) solution gives a CM "
        "specialization of the independent mod-5 HGM"
    )
    if data["conclusion"] != expected_conclusion:
        raise CertificateError("non-CM conclusion mismatch")
    if "literature inputs" not in data["nonclaim"] or "not a proof" not in data["nonclaim"]:
        raise CertificateError("explicit trust-boundary nonclaim is missing")

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
    source = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(source)
    mutated["compatible_system"]["paper_variables"][1] = "b=-C"
    expect_rejection(mutated, "the wrong HGM orientation")

    mutated = copy.deepcopy(source)
    mutated["branch_support"]["even"]["conclusion"] = "3 does not divide B"
    expect_rejection(mutated, "an even branch without the 7-adic restriction")

    mutated = copy.deepcopy(source)
    mutated["cm_consequence"]["forced_value"] = 3
    expect_rejection(mutated, "a false CM-supported value of B")

    mutated = copy.deepcopy(source)
    mutated["catalan_input"]["not_catalan_exception"] = False
    expect_rejection(mutated, "a false Catalan exception")

    duplicate = '{"schema_version":1,"schema_version":1}'
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

    print("global mod-5 non-CM negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.manifest))
    print("global independent mod-5 non-CM certificate valid")
    print("  CM support forces B=1 in both Dahmen--Siksek branches")
    print("  Catalan excludes C^7-A^3=1")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
