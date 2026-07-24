#!/usr/bin/env python3
"""Replay the explicit prime-2 Hecke filter for four K7 packets.

The checker counts points on the listed generalized Weierstrass equations over
F_8, derives the norm-8 Hecke eigenvalues, and compares them with the exact
B-odd prime-2 trace conditions. It deliberately makes no completeness claim for
Hilbert-newform enumeration.
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
DEFAULT_MANIFEST = (
    ROOT / "Research" / "Signature357" / "mod5_prime2_hecke_filter.json"
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


GF8_MODULUS = 0b1101  # x^3+x^2+1


def gf8_mul(left: int, right: int) -> int:
    result = 0
    a = left
    b = right
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & 0b1000:
            a ^= GF8_MODULUS
    return result & 0b111


def gf8_pow(value: int, exponent: int) -> int:
    result = 1
    base = value
    while exponent:
        if exponent & 1:
            result = gf8_mul(result, base)
        base = gf8_mul(base, base)
        exponent >>= 1
    return result


def count_generalized_weierstrass(ainvs: list[int]) -> int:
    if len(ainvs) != 5 or any(type(value) is not int or not 0 <= value < 8 for value in ainvs):
        raise CertificateError("ainvs_F8 must contain five canonical F8 integers")
    a1, a2, a3, a4, a6 = ainvs
    count = 1  # point at infinity
    for x in range(8):
        x2 = gf8_mul(x, x)
        x3 = gf8_mul(x2, x)
        rhs = x3 ^ gf8_mul(a2, x2) ^ gf8_mul(a4, x) ^ a6
        for y in range(8):
            lhs = gf8_mul(y, y) ^ gf8_mul(a1, gf8_mul(x, y)) ^ gf8_mul(a3, y)
            if lhs == rhs:
                count += 1
    return count


def expected_classification(trace: int, branch_conditions: dict[str, Any]) -> str:
    c_allowed = set(branch_conditions["C_even"]["allowed_K7_hecke_eigenvalues"])
    a_allowed = set(branch_conditions["A_even"]["allowed_K7_hecke_eigenvalues"])
    in_c = trace in c_allowed
    in_a = trace in a_allowed
    if in_c and in_a:
        return "compatible with both B-odd parity branches"
    if in_c:
        return "compatible only with the C-even branch"
    if in_a:
        return "compatible only with the A-even branch"
    return "eliminated in both B-odd parity branches"


def validate(data: dict[str, Any]) -> tuple[list[tuple[str, int, str]], str]:
    exact_keys(
        data,
        {
            "schema_version", "status", "scope", "source", "finite_field",
            "branch_conditions", "packets", "summary", "nonclaim",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "research-certificate-explicit-packets-only":
        raise CertificateError("unexpected status")

    scope = data["scope"]
    exact_keys(scope, {"equation", "field", "prime", "residue_field", "claim"}, "scope")
    if scope["equation"] != "A^3+B^5=C^7" or scope["prime"] != 2:
        raise CertificateError("scope metadata mismatch")

    source = data["source"]
    exact_keys(
        source,
        {
            "number_field_label", "number_field_polynomial",
            "curve_form_correspondence", "base_change_formula",
        },
        "source",
    )
    if source["number_field_label"] != "3.3.49.1":
        raise CertificateError("unexpected number field")

    field = data["finite_field"]
    exact_keys(
        field,
        {
            "characteristic", "degree", "modulus_binary", "generator",
            "generator_polynomial_relation", "field_size",
        },
        "finite_field",
    )
    if field != {
        "characteristic": 2,
        "degree": 3,
        "modulus_binary": GF8_MODULUS,
        "generator": 2,
        "generator_polynomial_relation": "a^3+a^2+1=0",
        "field_size": 8,
    }:
        raise CertificateError("F8 metadata mismatch")
    if gf8_pow(2, 7) != 1 or any(gf8_pow(2, exponent) == 1 for exponent in range(1, 7)):
        raise CertificateError("selected F8 generator does not have order 7")

    branches = data["branch_conditions"]
    exact_keys(branches, {"formula", "C_even", "A_even"}, "branch_conditions")
    for name in ("C_even", "A_even"):
        exact_keys(
            branches[name],
            {"full_extension_trace", "allowed_K7_hecke_eigenvalues"},
            f"branch_conditions.{name}",
        )
    norm = 8
    for name in ("C_even", "A_even"):
        full_trace = branches[name]["full_extension_trace"]
        actual = [a for a in range(-5, 6) if a * a - 2 * norm == full_trace]
        if actual != branches[name]["allowed_K7_hecke_eigenvalues"]:
            raise CertificateError(f"{name} Hecke solutions mismatch: {actual}")

    packets = data["packets"]
    if not isinstance(packets, list) or len(packets) != 4:
        raise CertificateError("expected exactly four explicit packets")
    seen: set[str] = set()
    results: list[tuple[str, int, str]] = []
    for packet in packets:
        exact_keys(
            packet,
            {
                "hmf_label", "curve_label", "source_curve", "level_norm",
                "ainvs_F8", "expected_point_count", "expected_hecke_eigenvalue",
                "classification",
            },
            "packet",
        )
        label = packet["hmf_label"]
        if not isinstance(label, str) or label in seen:
            raise CertificateError("packet labels must be unique strings")
        seen.add(label)
        points = count_generalized_weierstrass(packet["ainvs_F8"])
        trace = 8 + 1 - points
        if points != packet["expected_point_count"]:
            raise CertificateError(f"{label}: point count mismatch, got {points}")
        if trace != packet["expected_hecke_eigenvalue"]:
            raise CertificateError(f"{label}: Hecke trace mismatch, got {trace}")
        classification = expected_classification(trace, branches)
        if classification != packet["classification"]:
            raise CertificateError(f"{label}: classification mismatch")
        results.append((label, trace, classification))

    summary = data["summary"]
    exact_keys(
        summary,
        {
            "explicit_packets_checked", "eliminated_in_both", "C_even_only",
            "A_even_only", "allowed_trace_union",
        },
        "summary",
    )
    counts = {
        "eliminated_in_both": sum("eliminated in both" in row[2] for row in results),
        "C_even_only": sum("only with the C-even" in row[2] for row in results),
        "A_even_only": sum("only with the A-even" in row[2] for row in results),
    }
    if summary["explicit_packets_checked"] != len(results):
        raise CertificateError("summary packet count mismatch")
    for key, value in counts.items():
        if summary[key] != value:
            raise CertificateError(f"summary {key} mismatch")
    allowed_union = sorted(
        set(branches["C_even"]["allowed_K7_hecke_eigenvalues"])
        | set(branches["A_even"]["allowed_K7_hecke_eigenvalues"])
    )
    if summary["allowed_trace_union"] != allowed_union:
        raise CertificateError("allowed trace union mismatch")
    if "not claimed to be a complete enumeration" not in data["nonclaim"]:
        raise CertificateError("explicit incompleteness statement missing")

    digest = canonical_sha256(data)
    if digest != data["certificate_sha256"]:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {digest}"
        )
    return results, digest


def self_test() -> None:
    source = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(source)
    mutated["packets"][0]["ainvs_F8"][4] = 0
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated elliptic curve")

    mutated = copy.deepcopy(source)
    mutated["packets"][1]["classification"] = "eliminated in both B-odd parity branches"
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a false packet classification")

    mutated = copy.deepcopy(source)
    mutated["summary"]["explicit_packets_checked"] = 5
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a false summary")

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

    print("explicit mod-5 Hecke filter negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    results, digest = validate(load_json(args.manifest))
    print("explicit signature-(3,5,7) mod-5 Hecke filter valid")
    for label, trace, classification in results:
        print(f"  {label}: a_2={trace}; {classification}")
    print(f"certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
