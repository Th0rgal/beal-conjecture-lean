#!/usr/bin/env python3
"""Validate the retained coupled HGM trace-polynomial producer output.

The artifact keeps the parameter labels for the two Frey systems and records
trace polynomials at auxiliary primes 13, 29, and 41 with t5=u and t7=1-u.
This checker verifies the pinned producer source, complete parameter rows,
residue degrees, basic polynomial syntax, and canonical digest.

It deliberately makes no packet-elimination claim: candidate newform traces
must still be compared with these coupled rows.
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
DEFAULT_ARTIFACT = ROOT / "Research" / "Signature357" / "joint_hgm_traces.json"
EXPECTED_PRIMES = [13, 29, 41]
POLYNOMIAL_RE = re.compile(r"^-?\d*(?:\*?x(?:\^\d+)?)?(?:[+-]\d*(?:\*?x(?:\^\d+)?)?)*$")


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
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("artifact root must be an object")
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


def validate_polynomial(text: Any, context: str) -> None:
    if not isinstance(text, str):
        raise CertificateError(f"{context} must be a string")
    compact = text.replace(" ", "")
    if not compact or not POLYNOMIAL_RE.fullmatch(compact):
        raise CertificateError(f"unsupported polynomial syntax in {context}: {text!r}")
    if "x" not in compact:
        raise CertificateError(f"{context} must be a nonconstant trace polynomial")


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version", "status", "source", "parameter_identity", "primes",
            "row_count", "rows", "certificate_sha256",
        },
        "artifact",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "coupled finite-HGM trace-polynomial producer output":
        raise CertificateError("unexpected producer status")
    if data["parameter_identity"] != "t5=u,t7=1-u":
        raise CertificateError("the exact two-Frey parameter identity is missing")
    if data["primes"] != EXPECTED_PRIMES:
        raise CertificateError("unexpected auxiliary-prime list")

    source = data["source"]
    exact_keys(
        source,
        {"repository", "commit", "path", "git_blob_sha1", "pari_version"},
        "source",
    )
    if source != {
        "repository": "lucasvillagra/GFE-5p3",
        "commit": "e88f914c577ab6cf9a45e5cdd82c1993477fb423",
        "path": "Codes/GPcode.gp",
        "git_blob_sha1": "d829dbdfd5b710b2164f74ee5e1c1f92adae58d2",
        "pari_version": "2.15.4",
    }:
        raise CertificateError("producer source is not pinned")

    rows = data["rows"]
    if not isinstance(rows, list) or data["row_count"] != len(rows):
        raise CertificateError("row_count does not match rows")
    if len(rows) != sum(prime - 2 for prime in EXPECTED_PRIMES):
        raise CertificateError("the artifact lacks a complete nondegenerate parameter grid")

    by_prime: dict[int, dict[int, dict[str, Any]]] = {prime: {} for prime in EXPECTED_PRIMES}
    expected_degrees = {
        13: (1, 2),
        29: (1, 1),
        41: (1, 1),
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise CertificateError(f"row {index} must be an object")
        exact_keys(
            row,
            {
                "prime", "u_mod_prime", "t7_mod_prime", "residue_degree_K7",
                "residue_degree_K5", "mod5_trace_polynomial",
                "fixed7_trace_polynomial",
            },
            f"row {index}",
        )
        prime = row["prime"]
        u = row["u_mod_prime"]
        t7 = row["t7_mod_prime"]
        if prime not in by_prime or type(u) is not int or not (2 <= u <= prime - 1):
            raise CertificateError(f"invalid prime/parameter in row {index}")
        if u in by_prime[prime]:
            raise CertificateError(f"duplicate u={u} row at prime {prime}")
        if t7 != (1 - u) % prime or t7 in {0, 1}:
            raise CertificateError(f"row {index} violates t7=1-u")
        if (
            row["residue_degree_K7"], row["residue_degree_K5"]
        ) != expected_degrees[prime]:
            raise CertificateError(f"residue-degree mismatch at prime {prime}")
        validate_polynomial(row["mod5_trace_polynomial"], "mod-5 polynomial")
        validate_polynomial(row["fixed7_trace_polynomial"], "fixed-7 polynomial")
        by_prime[prime][u] = row

    for prime, prime_rows in by_prime.items():
        if sorted(prime_rows) != list(range(2, prime)):
            raise CertificateError(f"prime {prime} does not contain u=2,...,{prime-1}")

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
    source = load_json(DEFAULT_ARTIFACT)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["rows"][0]["t7_mod_prime"] = 1
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "a broken parameter coupling")

    mutated = copy.deepcopy(source)
    mutated["rows"].pop()
    mutated["row_count"] -= 1
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "an incomplete parameter grid")

    mutated = copy.deepcopy(source)
    mutated["source"]["git_blob_sha1"] = "0" * 40
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "an unpinned GP source")

    mutated = copy.deepcopy(source)
    mutated["rows"][0]["mod5_trace_polynomial"] = "not-a-polynomial"
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "malformed trace-polynomial syntax")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
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

    print("signature-357 coupled-HGM negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=pathlib.Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.artifact))
    print("coupled HGM trace-polynomial artifact valid")
    print("  parameter identity: t5=u, t7=1-u")
    print("  auxiliary primes: 13, 29, 41")
    print("  rows: 11 + 27 + 39 = 77")
    print("  nonclaim: candidate packet traces have not yet been compared")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
