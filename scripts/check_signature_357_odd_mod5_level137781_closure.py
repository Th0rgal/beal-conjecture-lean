#!/usr/bin/env python3
"""Replay the level-137781 odd-branch mod-5 semilinear closure certificate."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "odd_mod5_level137781_semilinear_closure.json"
P = 5


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


def digest(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def trim(poly: list[int]) -> list[int]:
    out = [coefficient % P for coefficient in poly]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out or [0]


def sub(a: list[int], b: list[int]) -> list[int]:
    n = max(len(a), len(b))
    return trim([
        (a[i] if i < len(a) else 0) - (b[i] if i < len(b) else 0)
        for i in range(n)
    ])


def mul(a: list[int], b: list[int]) -> list[int]:
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] = (out[i + j] + x * y) % P
    return trim(out)


def divmod_poly(a: list[int], b: list[int]) -> tuple[list[int], list[int]]:
    a = trim(a)
    b = trim(b)
    if b == [0]:
        raise CertificateError("polynomial division by zero")
    quotient = [0] * max(1, len(a) - len(b) + 1)
    remainder = a[:]
    inv_lead = pow(b[-1], -1, P)
    while remainder != [0] and len(remainder) >= len(b):
        shift = len(remainder) - len(b)
        coefficient = remainder[-1] * inv_lead % P
        quotient[shift] = coefficient
        remainder = sub(
            remainder,
            [0] * shift + [(coefficient * c) % P for c in b],
        )
    return trim(quotient), trim(remainder)


def monic(poly: list[int]) -> list[int]:
    poly = trim(poly)
    if poly == [0]:
        return poly
    inv = pow(poly[-1], -1, P)
    return trim([(inv * coefficient) % P for coefficient in poly])


def gcd_poly(a: list[int], b: list[int]) -> list[int]:
    a = trim(a)
    b = trim(b)
    while b != [0]:
        _, remainder = divmod_poly(a, b)
        a, b = b, remainder
    return monic(a)


def derivative(poly: list[int]) -> list[int]:
    if len(poly) <= 1:
        return [0]
    return trim([(i * poly[i]) % P for i in range(1, len(poly))])


def mod_poly(poly: list[int], modulus: list[int]) -> list[int]:
    return divmod_poly(poly, modulus)[1]


def powmod_poly(base: list[int], exponent: int, modulus: list[int]) -> list[int]:
    result = [1]
    base = mod_poly(base, modulus)
    while exponent:
        if exponent & 1:
            result = mod_poly(mul(result, base), modulus)
        base = mod_poly(mul(base, base), modulus)
        exponent >>= 1
    return trim(result)


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def validate(value: dict[str, Any]) -> str:
    exact_keys(
        value,
        {
            "schema_version",
            "status",
            "scope",
            "imported_lemmas",
            "producer",
            "initial_residual_dimensions",
            "squarefree_local_polynomials_mod5",
            "semilinear_relations",
            "dimension_chain",
            "conclusion",
            "nonclaim",
            "certificate_sha256",
        },
        "manifest",
    )
    if value["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if value["status"] != "research-certificate-conditional-odd-mod5-level137781-closure":
        raise CertificateError("unexpected status")
    if digest(value) != value["certificate_sha256"]:
        raise CertificateError("certificate digest mismatch")

    scope = value["scope"]
    if (
        scope["equation"] != "A^3+B^5=C^7"
        or scope["field"] != "K7=Q(zeta_7)^+"
        or scope["residual_prime"] != 5
        or scope["level_exponents"] != [3, 1]
        or scope["level_norm"] != 137781
    ):
        raise CertificateError("scope mismatch")
    if 27**3 * 7 != scope["level_norm"]:
        raise CertificateError("level norm arithmetic mismatch")

    imported = value["imported_lemmas"]
    if not isinstance(imported, list) or len(imported) != 6:
        raise CertificateError("expected exactly six imported lemmas")

    producer = value["producer"]
    expected_producer = {
        "repository": "Th0rgal/beal-conjecture-lean",
        "script": "scripts/run_signature_357_magma_mod5_137781_semilinear_chain.py",
        "commit_sha": "a85e7ba70e26f290ac768746b8c4a87738baeb60",
        "calculator": "Magma V2.29-8 public calculator",
        "workflow_repository": "lfglabs-dev/starknetid.rs",
        "workflow_run_id": 30144123222,
        "artifact_id": 8615431184,
        "artifact_zip_sha256": "db69d2624ec81645bd3a43f5d46900ba52a68ab1592e75c20046443010e1c21b",
        "producer_certificate_sha256": "095b7cd6a6fea314556d65ad7462ee251027934eaad263d388d104f96d576dfe",
        "local_source_sha256": "c20e4d0d046df579a94e6e344e20a3bf2a87a563eb31d8ab7c58351b1d242e34",
    }
    if producer != expected_producer:
        raise CertificateError("producer/source pin mismatch")

    initial = value["initial_residual_dimensions"]
    if initial != {
        "newspace": 1352,
        "B_odd_trace0": 38,
        "B_even_trace_plus1": 46,
        "B_even_trace_minus1": 46,
        "parity_union": 130,
    }:
        raise CertificateError("initial dimension inventory mismatch")
    if (
        initial["B_odd_trace0"]
        + initial["B_even_trace_plus1"]
        + initial["B_even_trace_minus1"]
        != initial["parity_union"]
    ):
        raise CertificateError("initial parity dimensions do not add up")

    expected_degrees = {"13": 43, "29": 57, "41": 49}
    polynomials = value["squarefree_local_polynomials_mod5"]
    if set(polynomials) != set(expected_degrees):
        raise CertificateError("unexpected local-prime polynomial inventory")
    x = [0, 1]
    for prime, expected_degree in expected_degrees.items():
        record = polynomials[prime]
        exact_keys(
            record,
            {"coefficients_low_to_high", "degree", "derivation"},
            f"polynomial {prime}",
        )
        coefficients = record["coefficients_low_to_high"]
        if (
            not isinstance(coefficients, list)
            or not coefficients
            or any(not isinstance(c, int) or not 0 <= c < P for c in coefficients)
        ):
            raise CertificateError(f"malformed coefficients at {prime}")
        polynomial = trim(coefficients)
        if polynomial != coefficients:
            raise CertificateError(f"noncanonical polynomial at {prime}")
        if record["degree"] != len(polynomial) - 1 or record["degree"] != expected_degree:
            raise CertificateError(f"degree mismatch at {prime}")
        if polynomial[-1] != 1:
            raise CertificateError(f"polynomial at {prime} is not monic")
        if gcd_poly(polynomial, derivative(polynomial)) != [1]:
            raise CertificateError(f"polynomial at {prime} is not square-free")
        if powmod_poly(x, 125, polynomial) != mod_poly(x, polynomial):
            raise CertificateError(f"polynomial at {prime} does not divide X^125-X")
        if record["derivation"] != "gcd(complete local trace union, X^125-X)":
            raise CertificateError(f"derivation changed at {prime}")

    if value["semilinear_relations"] != [
        "a^125=a",
        "b+c=a^5+a^25",
        "b*c=a^30",
    ]:
        raise CertificateError("semilinear relations changed")

    chain = value["dimension_chain"]
    expected_chain = {
        "13": {"B_odd": 2, "B_even_plus1": 4, "B_even_minus1": 4, "total": 10},
        "29": {"B_odd": 0, "B_even_plus1": 3, "B_even_minus1": 3, "total": 6},
        "41": {"B_odd": 0, "B_even_plus1": 0, "B_even_minus1": 0, "total": 0},
    }
    if chain != expected_chain:
        raise CertificateError("dimension chain mismatch")
    previous = initial["parity_union"]
    for prime in ("13", "29", "41"):
        row = chain[prime]
        if row["B_odd"] + row["B_even_plus1"] + row["B_even_minus1"] != row["total"]:
            raise CertificateError(f"dimension total mismatch at {prime}")
        if row["total"] > previous:
            raise CertificateError(f"dimension increased at {prime}")
        previous = row["total"]

    conclusion = value["conclusion"]
    if conclusion != {
        "B_odd_final_dimension": 0,
        "B_even_final_dimension": 0,
        "total_final_dimension": 0,
        "level_eliminated": True,
    }:
        raise CertificateError("closure conclusion mismatch")
    if chain["41"]["total"] != conclusion["total_final_dimension"]:
        raise CertificateError("final dimension does not match the chain")
    if "does not reprove" not in value["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim missing")
    return value["certificate_sha256"]


def expect_rejection(value: dict[str, Any], label: str) -> None:
    value["certificate_sha256"] = digest(value)
    try:
        validate(value)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)
    validate(base)

    mutated = copy.deepcopy(base)
    mutated["dimension_chain"]["41"]["total"] = 1
    expect_rejection(mutated, "a nonzero final dimension")

    mutated = copy.deepcopy(base)
    mutated["semilinear_relations"][2] = "b*c=a^31"
    expect_rejection(mutated, "a mutated semilinear relation")

    mutated = copy.deepcopy(base)
    mutated["squarefree_local_polynomials_mod5"]["13"]["coefficients_low_to_high"][1] = 2
    expect_rejection(mutated, "a mutated local polynomial")

    with tempfile.NamedTemporaryFile("w", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
        path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("duplicate keys accepted")
    finally:
        path.unlink(missing_ok=True)

    print("level-137781 closure negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load_json(args.manifest))
    print("odd mod-5 level 137781 semilinear closure certificate valid")
    print("  residual dimension chain: 130 -> 10 -> 6 -> 0")
    print("  level 137781 eliminated conditional on six imported lemmas")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
