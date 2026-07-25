#!/usr/bin/env python3
"""Replay the source anchor for the PARI/GP finite-HGM parameter convention.

This checker does not prove the p-adic Gross--Koblitz implementation.  It checks
that the pinned producer output is consistent with the published Frobenius
anchor at mathematical parameter t=3 and prime norm 29, and derives the exact
coordinate relation required by the two-Frey producer.
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
MANIFEST = ROOT / "Research" / "Signature357" / "gp_parameter_convention.json"


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
    expected = {
        "schema_version",
        "status",
        "source_anchor",
        "legacy_producer_observation",
        "deduction",
        "correct_two_frey_coordinates",
        "impact",
        "nonclaim",
        "certificate_sha256",
    }
    if set(data) != expected:
        raise CertificateError("manifest keys differ from schema")
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if canonical_sha256(data) != data["certificate_sha256"]:
        raise CertificateError("certificate digest mismatch")

    anchor = data["source_anchor"]
    if anchor["mathematical_parameter"] != 3 or anchor["prime_norm"] != 29:
        raise CertificateError("published anchor metadata mismatch")
    genus2 = anchor["genus2_frobenius_polynomial_coefficients_ascending"]
    if genus2 != [841, -58, 14, -2, 1]:
        raise CertificateError("Table 7.1 polynomial was transcribed incorrectly")
    trace_poly = anchor["rm_trace_polynomial_coefficients_ascending"]
    if trace_poly != [-44, -2, 1]:
        raise CertificateError("RM trace polynomial mismatch")
    # If a,a' are the RM traces, (T^2-aT+29)(T^2-a'T+29) has
    # a+a'=2 and aa'=-44, exactly the published genus-two polynomial.
    s, product = 2, -44
    reconstructed = [29 * 29, -29 * s, product + 58, -s, 1]
    if reconstructed != genus2:
        raise CertificateError("RM trace polynomial does not reconstruct Table 7.1")

    observation = data["legacy_producer_observation"]
    prime = observation["prime"]
    if prime != 29:
        raise CertificateError("legacy observation must use prime 29")
    inverse = pow(anchor["mathematical_parameter"], -1, prime)
    if inverse != 10 or observation["inverse_parameter_mod_prime"] != inverse:
        raise CertificateError("3 inverse modulo 29 must equal 10")
    expected_poly = anchor["rm_trace_polynomial"]
    if observation["gp_argument_10_polynomial"] != expected_poly:
        raise CertificateError("the reciprocal GP argument does not match the source anchor")
    if observation["gp_argument_3_polynomial"] == expected_poly:
        raise CertificateError("the uncorrected GP label unexpectedly matches the source anchor")
    if observation["gp_argument_3_polynomial"] != "x^2-8*x+11":
        raise CertificateError("legacy z=3 polynomial mismatch")

    deduction = data["deduction"]
    if deduction["gp_argument"] != "z=t0^(-1)":
        raise CertificateError("reciprocal convention missing")
    if deduction["source_anchor_verified"] is not True:
        raise CertificateError("source anchor not marked verified")

    coords = data["correct_two_frey_coordinates"]
    if coords != {
        "mathematical_parameters": ["u=C^7/A^3", "v=-B^5/A^3", "u+v=1"],
        "gp_arguments": ["z5=u^(-1)", "z7=v^(-1)"],
        "gp_relation": "(z5-1)*(z7-1)=1",
    }:
        raise CertificateError("corrected two-Frey coordinate identity mismatch")
    # Exhaustively replay the finite-field identity at the three producer primes.
    for prime in (13, 29, 41):
        for u in range(2, prime):
            v = (1 - u) % prime
            z5, z7 = pow(u, -1, prime), pow(v, -1, prime)
            if ((z5 - 1) * (z7 - 1)) % prime != 1:
                raise CertificateError(f"GP-coordinate identity failed at {prime}")
    return data["certificate_sha256"]


def self_test() -> None:
    source = load(MANIFEST)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["legacy_producer_observation"]["inverse_parameter_mod_prime"] = 3
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the non-reciprocal parameter label")

    mutated = copy.deepcopy(source)
    mutated["correct_two_frey_coordinates"]["gp_relation"] = "z5+z7=1"
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the obsolete Cartesian parameter relation")

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
    print("signature-357 GP parameter-convention negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load(MANIFEST))
    print("signature-357 GP reciprocal parameter convention valid")
    print("  mathematical t0=3 at norm 29 matches GP argument 10=3^(-1)")
    print("  corrected two-Frey GP relation: (z5-1)*(z7-1)=1")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
