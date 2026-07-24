#!/usr/bin/env python3
"""Replay the complete low-level closure for signature (3,5,7).

The checker combines the pinned complete LMFDB low-level filter with two exact
auxiliary-prime calculations at 41:

* the independent residual-5 HGM trace sets force u=C^7/A^3 to reduce to 1,
  hence 41|B;
* primitivity then forces the fixed-7 parameter -B^5/A^3 to reduce to 0, but
  none of the pinned t=0 trace polynomials can meet the reducible target mod 7.

The even-branch implication to reducibility and the Mazur trace criterion remain
explicit literature inputs in the manifest.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "low_level_complete_closure.json"
LOW_FILTER = ROOT / "Research" / "Signature357" / "lmfdb_low_level_filter.json"


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


def canonical_sha256(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def polynomial_terms(poly: str) -> dict[int, int]:
    compact = poly.replace(" ", "").replace("-", "+-")
    if compact.startswith("+-"):
        compact = compact[1:]
    result: dict[int, int] = {}
    for term in compact.split("+"):
        if not term:
            continue
        if "x" not in term:
            degree, coefficient = 0, int(term)
        else:
            if "*x" in term:
                coefficient_text, rest = term.split("*x", 1)
                coefficient = int(coefficient_text)
            else:
                rest = term.split("x", 1)[1]
                prefix = term[: term.index("x")]
                coefficient = -1 if prefix == "-" else 1
            degree = int(rest[1:]) if rest.startswith("^") else 1
        result[degree] = result.get(degree, 0) + coefficient
    return result


def evaluate(poly: str, value: int, modulus: int) -> int:
    return sum(
        coefficient * pow(value, degree, modulus)
        for degree, coefficient in polynomial_terms(poly).items()
    ) % modulus


def product(values: list[int], modulus: int) -> int:
    result = 1
    for value in values:
        result = result * value % modulus
    return result


def validate(manifest: dict[str, Any], low: dict[str, Any]) -> str:
    if manifest.get("schema_version") != 2:
        raise CertificateError("manifest schema_version must equal 2")
    if canonical_sha256(manifest) != manifest.get("certificate_sha256"):
        raise CertificateError("manifest digest mismatch")
    scope = manifest["scope"]

    if (
        canonical_sha256(low) != low.get("certificate_sha256")
        or low["certificate_sha256"] != scope["low_level_filter_sha256"]
    ):
        raise CertificateError("low-level filter hash mismatch")
    if low.get("schema_version") != 3:
        raise CertificateError("expected schema-3 low-level filter")
    odd = low["branch_filters"]["odd_branch"]["low_level_survivors"]
    even_unit = low["branch_filters"]["even_branch_7_unit"]["low_level_survivors"]
    even_div = low["branch_filters"]["even_branch_7_divides_C"][
        "low_level_survivors"
    ]
    if odd != [] or even_unit != [] or even_div != [scope["only_preclosure_packet"]]:
        raise CertificateError("preclosure low-level frontier changed")

    mod5 = manifest["mod5_prime41_filter"]
    prime = mod5["rational_prime"]
    if mod5["residue_degree_base"] != 1 or mod5["residue_degree_full"] != 2:
        raise CertificateError("prime-41 residue metadata mismatch")
    base_trace = mod5["packet_trace_base"]
    full_trace = base_trace * base_trace - 2 * prime
    if (
        full_trace != mod5["packet_trace_full"]
        or full_trace % 5 != mod5["packet_trace_full_mod5"]
    ):
        raise CertificateError("base-change trace calculation mismatch")

    for name, expected_count, expected_product in (
        ("generic", 39, mod5["generic_evaluation_product_mod5"]),
        ("zero", 7, mod5["zero_evaluation_product_mod5"]),
        ("infinity", 3, mod5["infinity_evaluation_product_mod5"]),
    ):
        polynomials = mod5[f"{name}_candidate_polynomials"]
        if len(polynomials) != expected_count:
            raise CertificateError(f"{name} candidate count mismatch")
        evaluations = [evaluate(poly, full_trace, 5) for poly in polynomials]
        if 0 in evaluations or product(evaluations, 5) != expected_product:
            raise CertificateError(f"{name} reduction was not eliminated")

    targets = sorted({(prime + 1) % 5, (-(prime + 1)) % 5})
    if (
        targets != mod5["multiplicative_targets_mod5"]
        or base_trace % 5 not in targets
    ):
        raise CertificateError("u=1 multiplicative regime does not survive exactly as recorded")
    if mod5["only_surviving_reduction_regime"] != "u=1":
        raise CertificateError("unexpected surviving mod-5 regime")

    fixed7 = manifest["fixed7_prime41_obstruction"]
    if prime % 5 not in {1, 4} or pow(13, 2, prime) != 5:
        raise CertificateError("41 should split in Q(sqrt(5))")
    order_mod15 = next(n for n in range(1, 15) if pow(prime, n, 15) == 1)
    if (
        order_mod15 != 2
        or fixed7["residue_degree_base"] != 1
        or fixed7["residue_degree_full"] != 2
    ):
        raise CertificateError("fixed-7 residue-degree calculation mismatch")
    base_target = (prime + 1) % 7
    full_target = (prime * prime + 1) % 7
    if (
        base_target != fixed7["reducible_trace_base_mod7"]
        or full_target != fixed7["reducible_trace_full_mod7"]
    ):
        raise CertificateError("fixed-7 reducible target mismatch")
    polynomials = fixed7["zero_candidate_polynomials"]
    evaluations = [evaluate(poly, full_target, 7) for poly in polynomials]
    if (
        evaluations != fixed7["evaluations_mod7"]
        or 0 in evaluations
        or product(evaluations, 7) != fixed7["evaluation_product_mod7"]
    ):
        raise CertificateError("fixed-7 t=0 obstruction mismatch")
    if fixed7["forced_reduction_regime"] != "t7=0":
        raise CertificateError("fixed-7 parameter regime mismatch")

    if len(manifest["imported_implications"]) != 4:
        raise CertificateError("all imported implications must remain explicit")
    return manifest["certificate_sha256"]


def self_test() -> None:
    manifest, low = load(MANIFEST), load(LOW_FILTER)
    validate(manifest, low)

    mutated = copy.deepcopy(manifest)
    mutated["fixed7_prime41_obstruction"]["zero_candidate_polynomials"][0] = (
        "x^2-4*x-5113"
    )
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    try:
        validate(mutated, low)
    except CertificateError:
        pass
    else:
        raise RuntimeError(
            "checker accepted a fixed-7 polynomial with a root at the target"
        )

    mutated_manifest = copy.deepcopy(manifest)
    mutated_manifest["mod5_prime41_filter"]["generic_candidate_polynomials"][0] = (
        "x-2"
    )
    mutated_manifest["certificate_sha256"] = canonical_sha256(mutated_manifest)
    try:
        validate(mutated_manifest, low)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted an extra generic mod-5 regime")

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
    print("signature-357 complete low-level closure negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load(MANIFEST), load(LOW_FILTER))
    print("complete LMFDB low-level mod-5 frontier is empty")
    print("prime 41 forces u=1 modulo 41, hence 41 divides B")
    print("the fixed-7 t=0 trace set excludes the reducible target modulo 7")
    print(f"certificate sha256: {digest}")
    print("conclusion conditional on four explicitly imported implications")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
