#!/usr/bin/env python3
"""Replay the local-type elimination of the low-level even 7-unit packet.

The finite arithmetic checks the branch orientation, the LMFDB j-invariant,
its normalized valuation in K7=Q(zeta_7)^+, and the prime-order mismatch in
residual inertia. Pacetti--Villagra Torcomian's local-type theorem and the Tate
curve ramification criterion remain explicit literature inputs.
"""
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
DEFAULT_MANIFEST = (
    ROOT / "Research" / "Signature357" / "mod5_even_7unit_local_type.json"
)


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


def valuation(value: int, prime: int) -> int:
    if value == 0:
        raise CertificateError("valuation of zero is not used in this certificate")
    value = abs(value)
    result = 0
    while value % prime == 0:
        result += 1
        value //= prime
    return result


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version", "status", "equation", "branch", "hgm_local_type",
            "candidate", "incompatibility", "nonclaim", "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "literature-assisted-even-7-unit-local-type-elimination":
        raise CertificateError("unexpected status")
    if data["equation"] != "A^3+B^5=C^7":
        raise CertificateError("unexpected equation")

    branch = data["branch"]
    exact_keys(branch, {"name", "conditions", "conclusion"}, "branch")
    if branch["name"] != "Dahmen--Siksek even branch with 7 not dividing C":
        raise CertificateError("unexpected branch")
    if branch["conditions"] != [
        "30 divides C",
        "7 does not divide A*B",
        "7 does not divide C",
        "gcd(A,B,C)=1",
    ]:
        raise CertificateError("branch hypotheses mismatch")
    if branch["conclusion"] != "A,B,C are all 7-adic units":
        raise CertificateError("7-unit conclusion mismatch")

    hgm = data["hgm_local_type"]
    exact_keys(
        hgm,
        {
            "orientation", "paper_variables", "source", "potential_reduction",
            "finite_inertia_prime_divisors", "residual_inertia_prime_to_5",
            "consequence",
        },
        "hgm_local_type",
    )
    if hgm["orientation"] != "(-C)^7+B^5+A^3=0":
        raise CertificateError("HGM orientation mismatch")
    if hgm["paper_variables"] != [
        "a=-C", "b=B", "c=A", "q=7", "p=5", "r=3"
    ]:
        raise CertificateError("paper-variable orientation mismatch")
    if not all(
        token in hgm["source"]
        for token in ("Proposition 3.10", "Corollary 3.11", "Proposition 3.14")
    ):
        raise CertificateError("local-type source chain is incomplete")
    if hgm["potential_reduction"] != "potentially good at the prime above 7":
        raise CertificateError("HGM potential-reduction type mismatch")
    inertia_primes = hgm["finite_inertia_prime_divisors"]
    if inertia_primes != [2, 7] or any(5 % prime == 0 for prime in inertia_primes):
        raise CertificateError("HGM finite inertia is not certified prime to 5")
    if hgm["residual_inertia_prime_to_5"] is not True:
        raise CertificateError("residual HGM inertia must be prime to 5")
    if hgm["consequence"] != "the residual inertia image has no element of order 5":
        raise CertificateError("HGM inertia consequence mismatch")

    candidate = data["candidate"]
    exact_keys(
        candidate,
        {
            "hmf_label", "elliptic_curve_label", "source", "j_invariant",
            "prime_7_ramification_index_in_K7", "valuation_at_prime_above_7",
            "potential_reduction", "tate_source", "residual_characteristic",
            "five_divides_negative_j_valuation", "consequence",
        },
        "candidate",
    )
    if candidate["hmf_label"] != "3.3.49.1-1323.1-a":
        raise CertificateError("unexpected HMF packet")
    if candidate["elliptic_curve_label"] != "3.3.49.1-1323.1-a6":
        raise CertificateError("unexpected elliptic-curve witness")
    if "LMFDB" not in candidate["source"]:
        raise CertificateError("LMFDB source is not pinned")

    j = candidate["j_invariant"]
    exact_keys(j, {"numerator", "denominator"}, "j_invariant")
    numerator = j["numerator"]
    denominator = j["denominator"]
    if numerator != 103_823 or denominator != 63 or math.gcd(numerator, denominator) != 1:
        raise CertificateError("j-invariant transcription mismatch")
    rational_v7 = valuation(numerator, 7) - valuation(denominator, 7)
    if rational_v7 != -1:
        raise CertificateError("rational 7-adic valuation of j must equal -1")
    ramification_index = candidate["prime_7_ramification_index_in_K7"]
    if ramification_index != 3:
        raise CertificateError("7 must be totally ramified with index 3 in K7")
    normalized_v7 = ramification_index * rational_v7
    if normalized_v7 != -3 or candidate["valuation_at_prime_above_7"] != normalized_v7:
        raise CertificateError("normalized K7 valuation of j must equal -3")
    if normalized_v7 >= 0 or candidate["potential_reduction"] != "potentially multiplicative":
        raise CertificateError("negative j-valuation must give potentially multiplicative reduction")
    if candidate["residual_characteristic"] != 5:
        raise CertificateError("unexpected residual characteristic")
    divides = (-normalized_v7) % 5 == 0
    if divides or candidate["five_divides_negative_j_valuation"] is not False:
        raise CertificateError("5 must not divide -v_p7(j)=3")
    if "Corollary 3.6" not in candidate["tate_source"]:
        raise CertificateError("Tate-curve ramification source is missing")
    if candidate["consequence"] != (
        "the residual inertia image contains a nontrivial unipotent element of order 5"
    ):
        raise CertificateError("candidate inertia consequence mismatch")

    incompatibility = data["incompatibility"]
    exact_keys(
        incompatibility,
        {
            "hgm_contains_order_5_inertia", "candidate_contains_order_5_inertia",
            "conclusion",
        },
        "incompatibility",
    )
    if incompatibility["hgm_contains_order_5_inertia"] is not False:
        raise CertificateError("HGM side must contain no order-5 inertia")
    if incompatibility["candidate_contains_order_5_inertia"] is not True:
        raise CertificateError("candidate side must contain order-5 inertia")
    if incompatibility["conclusion"] != (
        "the candidate 3.3.49.1-1323.1-a cannot match the even 7-unit HGM "
        "residual representation"
    ):
        raise CertificateError("local incompatibility conclusion mismatch")
    if "literature inputs" not in data["nonclaim"] or "does not prove" not in data["nonclaim"]:
        raise CertificateError("explicit nonclaim is missing")

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
    mutated["candidate"]["j_invariant"]["denominator"] = 441
    expect_rejection(mutated, "a mutated j-invariant")

    mutated = copy.deepcopy(source)
    mutated["candidate"]["valuation_at_prime_above_7"] = -1
    expect_rejection(mutated, "the rational rather than K7-normalized valuation")

    mutated = copy.deepcopy(source)
    mutated["hgm_local_type"]["finite_inertia_prime_divisors"].append(5)
    expect_rejection(mutated, "an HGM inertia group with 5-torsion")

    mutated = copy.deepcopy(source)
    mutated["incompatibility"]["conclusion"] = "the Beal conjecture is proved"
    expect_rejection(mutated, "an overclaimed conclusion")

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

    print("even 7-unit local-type negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.manifest))
    print("even 7-unit local-type certificate valid")
    print("  HGM residual inertia: finite, prime to 5")
    print("  packet 1323.1-a: potentially multiplicative, -v_p7(j)=3")
    print("  residual inertia mismatch: no order 5 versus order 5")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
