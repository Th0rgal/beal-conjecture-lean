#!/usr/bin/env python3
"""Replay the exact arithmetic in the odd `(3,5,7)` irreducibility reduction.

Pacetti--Villagra Torcomian's Corollary 7.7 proof first establishes, through
Theorem 6.1 and equation (34), that a reducible residual representation forces
the residual rational prime p to divide an explicitly computed resultant
product. At the auxiliary prime ell=2 this product is 6084.

For the Dahmen--Siksek odd branch, C is odd and the paper orientation is
(a,b,c)=(B,-C,A), so ell=2 does not divide b. This checker validates the source
metadata, orientation, exact prime factorization of 6084, and the contradiction
7 does not divide 6084.

The source implication itself remains a literature theorem. The checker does not
reprove Theorem 6.1, potential good reduction, or modularity.
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
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "odd_irreducibility.json"


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
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(data, dict):
        raise CertificateError("manifest root must be an object")
    return data


def require_exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def canonical_digest(data: dict[str, Any]) -> str:
    payload = {key: value for key, value in data.items() if key != "certificate_sha256"}
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def reconstruct_factorization(factors: dict[str, Any]) -> int:
    product = 1
    for prime_text, exponent in factors.items():
        if not prime_text.isdigit() or str(int(prime_text)) != prime_text:
            raise CertificateError("prime-factor keys must be canonical positive integers")
        prime = int(prime_text)
        if prime < 2 or any(prime % divisor == 0 for divisor in range(2, int(prime**0.5) + 1)):
            raise CertificateError(f"factor key is not prime: {prime}")
        if type(exponent) is not int or exponent <= 0:
            raise CertificateError("prime-factor exponents must be positive integers")
        product *= prime**exponent
    return product


def validate_data(data: dict[str, Any]) -> tuple[int, str]:
    require_exact_keys(
        data,
        {
            "schema_version",
            "residual_prime",
            "auxiliary_prime",
            "source",
            "orientation",
            "resultant_product",
            "prime_factorization",
            "conclusion",
            "certificate_sha256",
        },
        "manifest",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise CertificateError("schema_version must be the integer 1")
    if data["residual_prime"] != 7 or data["auxiliary_prime"] != 2:
        raise CertificateError("this certificate is specifically the residual-7/auxiliary-2 case")

    source = data["source"]
    if not isinstance(source, dict):
        raise CertificateError("source must be an object")
    require_exact_keys(
        source,
        {"paper_arxiv", "result", "lines", "solution_hypothesis"},
        "source",
    )
    if source != {
        "paper_arxiv": "2512.17845v1",
        "result": "Corollary 7.7 and equation (34)",
        "lines": "the reducible case forces p to divide the local-factor resultant product; for ell=2 this product is 6084",
        "solution_hypothesis": "ell does not divide b",
    }:
        raise CertificateError("source metadata does not match the audited proof step")

    orientation = data["orientation"]
    if not isinstance(orientation, dict):
        raise CertificateError("orientation must be an object")
    require_exact_keys(
        orientation,
        {
            "beal_equation",
            "paper_variables",
            "odd_branch_condition",
            "derived_auxiliary_condition",
        },
        "orientation",
    )
    if orientation != {
        "beal_equation": "A^3+B^5=C^7",
        "paper_variables": ["a=B", "b=-C", "c=A", "p=7"],
        "odd_branch_condition": "C odd",
        "derived_auxiliary_condition": "2 does not divide b",
    }:
        raise CertificateError("orientation does not match the audited substitution")

    product = data["resultant_product"]
    if type(product) is not int or product != 6084:
        raise CertificateError("resultant_product must be the exact integer 6084")
    factors = data["prime_factorization"]
    if not isinstance(factors, dict) or factors != {"2": 2, "3": 2, "13": 2}:
        raise CertificateError("unexpected prime factorization metadata")
    if reconstruct_factorization(factors) != product:
        raise CertificateError("prime factorization does not reconstruct 6084")
    if product % data["residual_prime"] == 0:
        raise CertificateError("the residual prime unexpectedly divides the resultant product")

    expected_conclusion = (
        "the residual mod-7 representation attached to every odd-branch primitive "
        "solution is absolutely irreducible"
    )
    if data["conclusion"] != expected_conclusion:
        raise CertificateError("unexpected conclusion text")

    digest = canonical_digest(data)
    claimed = data["certificate_sha256"]
    if (
        not isinstance(claimed, str)
        or len(claimed) != 64
        or any(character not in "0123456789abcdef" for character in claimed)
        or claimed != digest
    ):
        raise CertificateError(
            f"certificate digest mismatch: expected {claimed!r}, computed {digest}"
        )
    return product, digest


def validate(path: pathlib.Path) -> tuple[int, str]:
    return validate_data(load_json(path))


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["resultant_product"] = 6083
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated resultant product")

    mutated = copy.deepcopy(base)
    mutated["orientation"]["odd_branch_condition"] = "C even"
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated branch orientation")

    mutated = copy.deepcopy(base)
    mutated["residual_prime"] = 13
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a residual prime dividing 6084")

    duplicate = '{"schema_version":1,"schema_version":1}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write(duplicate)
        duplicate_path = pathlib.Path(handle.name)
    try:
        try:
            load_json(duplicate_path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        duplicate_path.unlink(missing_ok=True)

    print("odd-branch irreducibility negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    product, digest = validate(args.manifest)
    print("signature (3,5,7) odd-branch irreducibility certificate passed")
    print(f"  reducibility divisor: {product} = 2^2 * 3^2 * 13^2")
    print("  residual prime: 7")
    print("  7 divides 6084: false")
    print("  conclusion: odd-branch residual representation is absolutely irreducible")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
