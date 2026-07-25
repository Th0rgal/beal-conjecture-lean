#!/usr/bin/env python3
"""Replay the parity-labelled two-Frey trace pairs at the prime above 2."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "Research" / "Signature357" / "two_frey_prime2_parity_split.json"


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
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("manifest root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def multiplicative_order(value: int, modulus: int) -> int:
    residue = value % modulus
    if residue == 0:
        raise CertificateError("zero has no multiplicative order")
    running = 1
    for candidate in range(1, modulus):
        running = running * residue % modulus
        if running == 1:
            return candidate
    raise CertificateError("multiplicative order was not found")


def validate_dependency(path: pathlib.Path, expected_digest: str) -> dict[str, Any]:
    value = load(path)
    if digest(value) != value.get("certificate_sha256"):
        raise CertificateError(f"invalid dependency digest: {path}")
    if value["certificate_sha256"] != expected_digest:
        raise CertificateError(f"dependency changed: {path}")
    return value


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation changed")
    if data.get("status") != "literature-assisted-exact-two-Frey-prime2-parity-split":
        raise CertificateError("status changed")

    fixed_meta = data["fixed7_dependency"]
    fixed = validate_dependency(ROOT / fixed_meta["path"], fixed_meta["certificate_sha256"])
    fixed_traces = {record["name"]: record["rm_trace"] for record in fixed.get("cases", [])}
    if fixed_traces != {"A_odd_B_even": 0, "A_even_B_odd": -1}:
        raise CertificateError("fixed-7 trace dependency changed")

    mod5_meta = data["mod5_b_odd_dependency"]
    mod5 = validate_dependency(ROOT / mod5_meta["path"], mod5_meta["certificate_sha256"])
    if mod5.get("scope", {}).get("hypotheses") != [
        "pairwise coprime positive A,B,C",
        "B odd",
    ]:
        raise CertificateError("mod-5 B-odd scope changed")
    a_even_branch = mod5.get("trace_branches", {}).get("A_even", {})
    if a_even_branch.get("weight2_trace") != -16 or a_even_branch.get("weight2_trace_mod5") != 4:
        raise CertificateError("mod-5 A-even full trace changed")
    q5 = mod5.get("character_certificate", {}).get("K7_prime_2_norm")
    if q5 != 8:
        raise CertificateError("mod-5 norm at 2 changed")
    if (a_even_branch["weight2_trace"] + 2 * q5) % 5 != 0:
        raise CertificateError("B-odd mod-5 base trace is not forced to zero")

    fields = data["local_fields"]
    if fields["fixed7"] != {
        "field": "Q(sqrt(5))",
        "prime_norm": 4,
        "residual_characteristic": 7,
    }:
        raise CertificateError("fixed-7 local field metadata changed")
    mod5_field = fields["mod5"]
    full_degree = multiplicative_order(2, 7)
    real_degree = next(n for n in range(1, 7) if pow(2, n, 7) in {1, 6})
    if full_degree != 3 or real_degree != 3:
        raise CertificateError("residue-degree calculation at 2 changed")
    if (
        mod5_field["full_cyclotomic_residue_degree"] != full_degree
        or mod5_field["real_subfield_residue_degree"] != real_degree
        or mod5_field["cyclotomic_untwist_value_at_2"] != 1
        or mod5_field["prime_norm"] != 8
    ):
        raise CertificateError("mod-5 local field or untwist metadata changed")

    primitive_parities = []
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                if (a + b - c) % 2 == 0 and c == 1 and (a, b) in {(0, 1), (1, 0)}:
                    primitive_parities.append((a, b, c))
    if primitive_parities != [(0, 1, 1), (1, 0, 1)]:
        raise CertificateError("odd-C parity enumeration changed")

    branches = data.get("parity_branches")
    if not isinstance(branches, list) or [branch.get("name") for branch in branches] != [
        "B_odd",
        "B_even",
    ]:
        raise CertificateError("parity branch inventory changed")
    odd = branches[0]
    if odd.get("parity") != {"A_mod2": 0, "B_mod2": 1, "C_mod2": 1}:
        raise CertificateError("B-odd parity changed")
    if (
        odd.get("fixed7_trace_integer") != -1
        or odd.get("fixed7_trace_mod7") != 6
        or odd.get("mod5_trace_integer") != 0
        or odd.get("mod5_trace_mod5") != 0
        or odd.get("residual_trace_pairs_mod5_mod7") != [[0, 6]]
    ):
        raise CertificateError("B-odd trace pair changed")

    even = branches[1]
    if even.get("parity") != {"A_mod2": 1, "B_mod2": 0, "C_mod2": 1}:
        raise CertificateError("B-even parity changed")
    multiplicative = [-(q5 + 1), q5 + 1]
    multiplicative_mod5 = sorted({value % 5 for value in multiplicative})
    if (
        even.get("fixed7_trace_integer") != 0
        or even.get("fixed7_trace_mod7") != 0
        or even.get("mod5_trace_integers") != multiplicative
        or even.get("mod5_trace_mod5") != multiplicative_mod5
        or even.get("residual_trace_pairs_mod5_mod7") != [[1, 0], [4, 0]]
    ):
        raise CertificateError("B-even trace pairs changed")
    if "5*v_2(B)>0" not in even.get("mod5_parameter_behavior", ""):
        raise CertificateError("B-even multiplicative parameter condition missing")

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
    base = load(DEFAULT)
    validate(base)
    mutated = copy.deepcopy(base)
    mutated["parity_branches"][0]["fixed7_trace_mod7"] = 0
    expect_rejection(mutated, "a mutated B-odd fixed-7 trace")
    mutated = copy.deepcopy(base)
    mutated["parity_branches"][1]["mod5_trace_mod5"] = [0]
    expect_rejection(mutated, "a mutated multiplicative trace set")
    mutated = copy.deepcopy(base)
    mutated["local_fields"]["mod5"]["full_cyclotomic_residue_degree"] = 6
    expect_rejection(mutated, "a mutated residue degree")
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
    print("two-Frey prime-2 parity negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(args.manifest))
    print("two-Frey prime-2 parity certificate valid")
    print("  B odd:  (a_5,a_7)=(0,6)")
    print("  B even: (a_5,a_7)=(1,0) or (4,0)")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
