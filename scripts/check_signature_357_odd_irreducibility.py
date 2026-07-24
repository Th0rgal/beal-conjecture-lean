#!/usr/bin/env python3
"""Replay odd-branch fixed-7 irreducibility from corrected prime-2 traces."""
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
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 4 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or certificate digest mismatch")
    if data.get("status") != (
        "research-certificate-with-imported-reducibility-theorem-and-"
        "corrected-prime2-traces"
    ):
        raise CertificateError("unexpected status")

    expected_scope = {
        "claim": "the plus residual mod-7 Frey representation is absolutely irreducible",
        "equation": "A^3+B^5=C^7",
        "field": "K=Q(sqrt(5))",
        "hypotheses": ["pairwise coprime positive A,B,C", "C odd"],
        "orientation": "B^5+(-C)^7+A^3=0",
        "residual_prime": 7,
    }
    if data.get("scope") != expected_scope:
        raise CertificateError("scope changed")

    correction = data["trace_correction"]
    dependency_path = ROOT / correction["path"]
    dependency = load(dependency_path)
    if digest(dependency) != dependency.get("certificate_sha256"):
        raise CertificateError("trace-correction dependency digest is invalid")
    if dependency["certificate_sha256"] != correction["sha256"]:
        raise CertificateError("trace-correction dependency changed")
    if dependency["corrected_trace_set"] != [0, -1]:
        raise CertificateError("corrected base traces changed")
    obstruction = dependency["irreducibility_obstruction"]
    if (
        correction["corrected_base_traces"] != [0, -1]
        or correction["corrected_absolute_norm_obstruction"] != 900
        or correction["prime_support"] != [2, 3, 5]
        or obstruction["absolute_norm"] != 900
        or obstruction["corrected_bound_C2"] != 5
    ):
        raise CertificateError("corrected obstruction metadata mismatch")
    if 900 % 7 == 0:
        raise CertificateError("7 unexpectedly divides the corrected obstruction")

    withdrawn = data["withdrawn"]
    if withdrawn != {
        "old_bound_C2": 13,
        "old_obstruction": 6084,
        "published_trace_pair": [-1, -8],
        "reason": (
            "the published pair mixes the base trace -1 from one parity case with "
            "the degree-two trace -8 from the other; the exact base traces are 0 and -1"
        ),
    }:
        raise CertificateError("withdrawal record changed")

    conclusion = data["conclusion"]
    if conclusion != {
        "arithmetic": "7 does not divide 900",
        "representation": "the residual mod-7 plus-Frey representation is absolutely irreducible",
        "strengthening": "the corrected finite computation gives C(2)=5 rather than the published value 13",
    }:
        raise CertificateError("conclusion changed")
    if len(data.get("imported_lemmas", [])) != 3:
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
    mutated["trace_correction"]["corrected_absolute_norm_obstruction"] = 6084
    expect_rejection(mutated, "the obsolete obstruction")

    mutated = copy.deepcopy(base)
    mutated["withdrawn"]["published_trace_pair"] = [0, -1]
    expect_rejection(mutated, "a falsified publication audit")

    mutated = copy.deepcopy(base)
    mutated["conclusion"]["arithmetic"] = "7 divides 900"
    expect_rejection(mutated, "a fabricated divisibility statement")

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
    print("  corrected base traces at the norm-4 prime: 0 and -1")
    print("  corrected resultant norm: 900; residual prime support {2,3,5}")
    print("  conclusion: residual characteristic 7 is absolutely irreducible")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
