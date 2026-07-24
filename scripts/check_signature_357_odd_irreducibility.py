#!/usr/bin/env python3
"""Replay odd-branch fixed-7 irreducibility and the prime-2 correction.

The irreducibility conclusion now rests on the source resultant obstruction
6084, not on the withdrawn direct prime-2 character argument.  The checker also
verifies that the degenerate values -1 and -8 are full-cyclotomic traces and
force base trace zero modulo 7 after the relative degree-two transformation.
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
MANIFEST = ROOT / "Research" / "Signature357" / "odd_irreducibility.json"


class CertificateError(ValueError):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("manifest root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 3:
        raise CertificateError("schema_version must equal 3")
    if digest(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate digest mismatch")
    if data.get("status") != (
        "research-certificate-with-imported-source-resultant-lemma-and-"
        "corrected-prime2-normalization"
    ):
        raise CertificateError("unexpected status")

    scope = data["scope"]
    if scope != {
        "claim": "the residual mod-7 plus-Frey representation is absolutely irreducible",
        "equation": "A^3+B^5=C^7",
        "field": "K=Q(sqrt(5))",
        "hypotheses": ["pairwise coprime positive A,B,C", "C odd"],
        "orientation": "B^5+(-C)^7+A^3=0",
        "residual_prime": 7,
    }:
        raise CertificateError("scope changed")

    source = data["source_irreducibility"]
    obstruction = source["exact_resultant_obstruction"]
    if obstruction != 6084 or obstruction != 2**2 * 3**2 * 13**2:
        raise CertificateError("resultant obstruction factorization mismatch")
    if source["factorization"] != {"2": 2, "3": 2, "13": 2}:
        raise CertificateError("recorded factorization changed")
    if obstruction % 7 == 0 or source["residual_prime_divides_obstruction"]:
        raise CertificateError("7 incorrectly divides the obstruction")
    if source["paper_variable_b"] != "-C" or source["oddness_condition"] != "C odd implies b odd":
        raise CertificateError("orientation or parity implication changed")
    if "reducible" not in source["imported_implication"] or "6084" not in source["imported_implication"]:
        raise CertificateError("source reducibility implication missing")

    correction = data["prime2_normalization_correction"]
    if (
        correction["base_residue_degree"] != 2
        or correction["full_residue_degree"] != 4
        or correction["relative_residue_degree"] != 2
        or correction["base_prime_norm"] != 4
    ):
        raise CertificateError("residue-degree metadata mismatch")
    full = correction["full_cyclotomic_trace_candidates"]
    squares = [trace + 2 * correction["base_prime_norm"] for trace in full]
    if full != [-1, -8] or squares != [7, 0]:
        raise CertificateError("base/full trace transformation mismatch")
    if squares != correction["base_trace_square_candidates"]:
        raise CertificateError("recorded base trace squares changed")
    if any(value % 7 for value in squares) or correction["base_trace_mod7"] != 0:
        raise CertificateError("full traces do not force base trace zero")
    withdrawn = correction["withdrawn_argument"]
    if "incorrectly treated" not in withdrawn or "withdrawn" not in withdrawn:
        raise CertificateError("withdrawal of the old direct argument is missing")
    if "a_P=0 mod 7" not in correction["new_use"]:
        raise CertificateError("corrected Hecke condition missing")

    if len(data.get("imported_lemmas", [])) != 4:
        raise CertificateError("imported-lemma boundary changed")
    if "imported literature inputs" not in data.get("nonclaim", ""):
        raise CertificateError("trust-boundary nonclaim missing")
    return data["certificate_sha256"]


def expect_rejection(value: dict[str, Any], label: str) -> None:
    value["certificate_sha256"] = digest(value)
    try:
        validate(value)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load(MANIFEST)
    validate(base)

    mutated = copy.deepcopy(base)
    mutated["prime2_normalization_correction"]["full_residue_degree"] = 2
    expect_rejection(mutated, "a mutated full residue degree")

    mutated = copy.deepcopy(base)
    mutated["prime2_normalization_correction"]["full_cyclotomic_trace_candidates"][0] = 0
    expect_rejection(mutated, "a mutated full-cyclotomic trace")

    mutated = copy.deepcopy(base)
    mutated["source_irreducibility"]["exact_resultant_obstruction"] *= 7
    expect_rejection(mutated, "a fabricated divisible obstruction")

    with tempfile.NamedTemporaryFile("w", delete=False) as fixture:
        fixture.write('{"x":1,"x":2}')
        path = pathlib.Path(fixture.name)
    try:
        try:
            load(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("duplicate keys accepted")
    finally:
        path.unlink(missing_ok=True)

    print("corrected fixed-7 irreducibility fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(MANIFEST))
    print("fixed-7 odd-branch irreducibility certificate valid")
    print("  irreducibility source: exact obstruction 6084, with 7 not dividing it")
    print("  corrected prime-2 consequence: base trace is 0 modulo 7")
    print("  withdrawn: direct character contradiction from x^2+x+4")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
