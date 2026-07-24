#!/usr/bin/env python3
"""Replay the global mod-5 automorphic reduction for signature (3,5,7).

The checker composes two independently replayed local irreducibility certificates
with the Dahmen--Siksek branch dichotomy, then verifies the finite conductor and
level arithmetic over Q(zeta_7)^+. The cited dichotomy, modularity, compatible-
system, conductor and Hilbert level-lowering theorems remain explicit literature
inputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

import check_signature_357_mod5_bodd as bodd
import check_signature_357_mod5_irreducibility as at3

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "mod5_global_frontier.json"


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


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version", "status", "equation", "field", "branch_inputs",
            "global_irreducibility_conclusion", "automorphic_input",
            "prime_to_5_conductor", "finite_frontier", "nonclaim",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "literature-assisted-finite-automorphic-reduction":
        raise CertificateError("unexpected status")
    if data["equation"] != "A^3+B^5=C^7":
        raise CertificateError("unexpected equation")

    field = data["field"]
    exact_keys(
        field,
        {"name", "lmfdb_label", "degree", "discriminant", "class_number"},
        "field",
    )
    if field != {
        "name": "K7=Q(zeta_7)^+",
        "lmfdb_label": "3.3.49.1",
        "degree": 3,
        "discriminant": 49,
        "class_number": 1,
    }:
        raise CertificateError("base-field metadata mismatch")

    inputs = data["branch_inputs"]
    exact_keys(
        inputs,
        {"Dahmen_Siksek_dichotomy", "even_branch_certificate", "odd_branch_certificate"},
        "branch_inputs",
    )
    dichotomy = inputs["Dahmen_Siksek_dichotomy"]
    if dichotomy != {
        "even": "30 divides C and 7 does not divide A*B",
        "odd": "C odd, 3 does not divide A*B*C, 5 does not divide A*C, and 7 divides A",
    }:
        raise CertificateError("Dahmen--Siksek branch metadata mismatch")

    even = inputs["even_branch_certificate"]
    odd = inputs["odd_branch_certificate"]
    exact_keys(even, {"path", "sha256", "coverage"}, "even_branch_certificate")
    exact_keys(odd, {"path", "sha256", "coverage"}, "odd_branch_certificate")
    if even["path"] != "Research/Signature357/mod5_prime2_b_odd.json":
        raise CertificateError("unexpected even-branch certificate path")
    if odd["path"] != "Research/Signature357/mod5_irducibility_at3.json":
        # Preserve fail-closed behavior while accepting the correctly spelled path below.
        if odd["path"] != "Research/Signature357/mod5_irreducibility_at3.json":
            raise CertificateError("unexpected odd-branch certificate path")

    try:
        even_digest = bodd.validate(bodd.load_json(ROOT / even["path"]))
    except bodd.CertificateError as exc:
        raise CertificateError(f"even-branch certificate failed: {exc}") from exc
    try:
        _classes, odd_digest = at3.validate(ROOT / odd["path"])
    except at3.CertificateError as exc:
        raise CertificateError(f"odd-branch certificate failed: {exc}") from exc
    if even_digest != even["sha256"] or odd_digest != odd["sha256"]:
        raise CertificateError("subcertificate digest mismatch")
    if "C even" not in even["coverage"] or "B odd" not in even["coverage"]:
        raise CertificateError("even branch is not covered by the B-odd theorem")
    if "3 not dividing" not in odd["coverage"]:
        raise CertificateError("odd branch is not covered by the at-3 theorem")

    expected_conclusion = (
        "every hypothetical primitive positive (3,5,7) solution carries an absolutely "
        "irreducible residual mod-5 plus HGM representation"
    )
    if data["global_irreducibility_conclusion"] != expected_conclusion:
        raise CertificateError("global irreducibility conclusion mismatch")

    automorphic = data["automorphic_input"]
    exact_keys(
        automorphic,
        {
            "orientation", "original_parameter", "inverted_parameter", "motive",
            "modularity_source", "modularity_hypothesis_check", "finite_flat_source",
            "residual_unramified_source", "conductor_bound_source",
            "level_lowering_dependency",
        },
        "automorphic_input",
    )
    if automorphic["orientation"] != "A^3+B^5+(-C)^7=0":
        raise CertificateError("automorphic orientation mismatch")
    if automorphic["original_parameter"] != "t=A^3/C^7":
        raise CertificateError("original automorphic parameter mismatch")
    if automorphic["inverted_parameter"] != "u=t^(-1)=C^7/A^3":
        raise CertificateError("inverted automorphic parameter mismatch")
    if "Theorem 6.2" not in automorphic["modularity_source"]:
        raise CertificateError("modularity source missing")
    if automorphic["modularity_hypothesis_check"] != "r=7 does not divide the coefficient 1 of A^3":
        raise CertificateError("modularity hypothesis was not discharged")
    if "Theorem 4.2" not in automorphic["residual_unramified_source"]:
        raise CertificateError("residual ramification source missing")
    if not (
        "Theorem 7.4" in automorphic["conductor_bound_source"]
        and "Corollary 7.5" in automorphic["conductor_bound_source"]
    ):
        raise CertificateError("exact conductor bounds are not pinned")

    conductor = data["prime_to_5_conductor"]
    exact_keys(
        conductor,
        {
            "support_rational_primes", "prime_3", "prime_7", "maximum_level",
            "maximum_level_norm", "possible_exponent_pairs",
            "possible_level_divisor_count", "parallel_weight",
        },
        "prime_to_5_conductor",
    )
    if conductor["support_rational_primes"] != [3, 7]:
        raise CertificateError("prime-to-5 conductor support must be {3,7}")

    p3 = conductor["prime_3"]
    p7 = conductor["prime_7"]
    exact_keys(p3, {"splitting", "residue_degree", "norm", "maximum_exponent"}, "prime_3")
    exact_keys(p7, {"splitting", "residue_degree", "norm", "maximum_exponent"}, "prime_7")
    if at3.real_cyclotomic_residue_degree(3, 7) != 3:
        raise CertificateError("3 must have residue degree 3 in K7")
    if p3 != {
        "splitting": "inert in K7", "residue_degree": 3,
        "norm": 27, "maximum_exponent": 5,
    }:
        raise CertificateError("prime-3 conductor metadata mismatch")
    if p7 != {
        "splitting": "totally ramified in K7", "residue_degree": 1,
        "norm": 7, "maximum_exponent": 3,
    }:
        raise CertificateError("prime-7 conductor metadata mismatch")

    pairs = [[a, b] for a in range(6) for b in range(4)]
    if conductor["possible_exponent_pairs"] != pairs:
        raise CertificateError("level-divisor exponent pairs are not complete")
    if conductor["possible_level_divisor_count"] != len(pairs) or len(pairs) != 24:
        raise CertificateError("unexpected number of level divisors")
    maximum_norm = (p3["norm"] ** p3["maximum_exponent"]) * (
        p7["norm"] ** p7["maximum_exponent"]
    )
    if maximum_norm != 4_921_675_101 or conductor["maximum_level_norm"] != maximum_norm:
        raise CertificateError("maximum level norm mismatch")
    if conductor["maximum_level"] != "p3^5*p7^3":
        raise CertificateError("maximum level ideal mismatch")
    if conductor["parallel_weight"] != [2, 2, 2]:
        raise CertificateError("parallel weight mismatch")

    if "joint mod-5/mod-7 trace graph" not in data["finite_frontier"]:
        raise CertificateError("finite joint-trace frontier is missing")
    if "does not prove" not in data["nonclaim"]:
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
    mutated["branch_inputs"]["even_branch_certificate"]["coverage"] = "C even"
    expect_rejection(mutated, "an uncovered even branch")

    mutated = copy.deepcopy(source)
    mutated["prime_to_5_conductor"]["maximum_level_norm"] -= 1
    expect_rejection(mutated, "a false maximum level norm")

    mutated = copy.deepcopy(source)
    mutated["prime_to_5_conductor"]["possible_exponent_pairs"].pop()
    expect_rejection(mutated, "an incomplete level list")

    mutated = copy.deepcopy(source)
    mutated["prime_to_5_conductor"]["prime_3"]["maximum_exponent"] = 3
    expect_rejection(mutated, "the over-optimistic old prime-3 bound")

    mutated = copy.deepcopy(source)
    mutated["global_irreducibility_conclusion"] = "the Beal conjecture is proved"
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

    print("global mod-5 frontier negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.manifest))
    print("global signature-(3,5,7) mod-5 frontier certificate valid")
    print("  irreducibility: every Dahmen--Siksek branch covered")
    print("  modularity: Golfieri--Pacetti Theorem 6.2")
    print("  prime-to-5 level divides p3^5*p7^3 over Q(zeta_7)^+")
    print("  maximum level norm: 4921675101; level divisors: 24")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
