#!/usr/bin/env python3
"""Replay the local collapse of the odd e3=2 two-Frey block."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "odd_e3_2_local_collapse.json"


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


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
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def legendre(value: int, prime: int) -> int:
    value %= prime
    if value == 0:
        return 0
    symbol = pow(value, (prime - 1) // 2, prime)
    return -1 if symbol == prime - 1 else 1


def elliptic_trace(ainvariants: list[int], prime: int) -> int:
    if len(ainvariants) != 5:
        raise CertificateError("expected five Weierstrass a-invariants")
    a1, a2, a3, a4, a6 = (value % prime for value in ainvariants)
    points = 1
    for x in range(prime):
        linear = (a1 * x + a3) % prime
        rhs = (x**3 + a2 * x * x + a4 * x + a6) % prime
        points += 1 + legendre(linear * linear + 4 * rhs, prime)
    return prime + 1 - points


def eta7(prime: int) -> int:
    residue = prime % 7
    if residue == 1:
        return 1
    if residue == 6:
        return -1
    raise CertificateError(f"selected prime {prime} does not split in K7")


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1:
        raise CertificateError("schema version mismatch")
    if canonical_sha256(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    source = data["source_dependencies"]
    regimes = load(ROOT / source["mod5_regime_path"])
    if canonical_sha256(regimes) != regimes.get("certificate_sha256"):
        raise CertificateError("mod-5 regime dependency digest mismatch")
    if regimes["certificate_sha256"] != source["mod5_regime_sha256"]:
        raise CertificateError("manifest is not bound to the regime certificate")
    if source["corrected_joint_output_sha256"] != (
        "d57dc6beda18427159ae5ae6bb76c9f1498e679cf804cb86783ed29974553188"
    ):
        raise CertificateError("corrected joint producer output changed")

    scope = data["scope"]
    if scope["twisted_mod5_level_exponents"] != [2, 1]:
        raise CertificateError("wrong twisted level")
    if scope["twisted_mod5_level_norm"] != 27**2 * 7:
        raise CertificateError("wrong twisted level norm")
    if scope["unique_norm8_and_marginal_packet"] != 1:
        raise CertificateError("unique packet changed")

    ainvariants = source["curve_ainvariants"]
    expected_traces = {13: -2, 29: 2, 41: -2, 43: -4}
    computed_traces = {
        prime: elliptic_trace(ainvariants, prime) for prime in expected_traces
    }
    if computed_traces != expected_traces:
        raise CertificateError(f"packet point counts changed: {computed_traces}")

    expected_regimes = {
        13: "generic",
        29: "zero",
        41: "multiplicative",
        43: "multiplicative",
    }
    for prime, packet_trace in computed_traces.items():
        entry = data["auxiliary_primes"][str(prime)]
        character = eta7(prime)
        original_trace = character * packet_trace % 5
        if entry["packet_trace"] != packet_trace:
            raise CertificateError(f"packet trace mismatch at {prime}")
        if entry["eta7_value"] != character:
            raise CertificateError(f"eta_7 value mismatch at {prime}")
        if entry["original_hgm_trace_mod5"] != original_trace:
            raise CertificateError(f"untwisted trace mismatch at {prime}")

        possible: list[str] = []
        for regime, metadata in regimes["primes"][str(prime)]["regimes"].items():
            if original_trace in metadata["base_trace_roots_mod5"]:
                possible.append(regime)
        if possible != [expected_regimes[prime]]:
            raise CertificateError(
                f"unexpected local regimes at {prime}: {possible}"
            )
        if entry["forced_regime"] != expected_regimes[prime]:
            raise CertificateError(f"recorded regime mismatch at {prime}")

    at13 = data["auxiliary_primes"]["13"]
    evaluations = at13["corrected_row_evaluations_at_trace2_mod5"]
    if [row["u"] for row in evaluations] != list(range(2, 13)):
        raise CertificateError("prime-13 parameter coverage mismatch")
    zeros = [row["u"] for row in evaluations if row["value"] % 5 == 0]
    if zeros != [2] or at13["corrected_generic_u_values"] != [2]:
        raise CertificateError("prime-13 parameter is not unique")
    if at13["forced_v_mod13"] != 12 or (2 + 12) % 13 != 1:
        raise CertificateError("prime-13 coupled parameter mismatch")
    if at13["forced_fixed7_trace_polynomial"] != "x":
        raise CertificateError("prime-13 fixed-7 trace target changed")

    conclusion = data["conclusion"]
    if conclusion["forced_divisibility"] != "29 divides C and 41*43 divides B":
        raise CertificateError("forced divisibility conclusion mismatch")
    if "packets 24 and 28" not in conclusion["decisive_remaining_test"]:
        raise CertificateError("decisive packet test missing")
    if "imported research inputs" not in data["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim missing")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = canonical_sha256(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load(MANIFEST)
    validate(base)

    mutated = copy.deepcopy(base)
    mutated["auxiliary_primes"]["13"]["corrected_row_evaluations_at_trace2_mod5"][1]["value"] = 0
    expect_rejection(mutated, "a second prime-13 parameter")

    mutated = copy.deepcopy(base)
    mutated["auxiliary_primes"]["41"]["forced_regime"] = "generic"
    expect_rejection(mutated, "the wrong prime-41 regime")

    mutated = copy.deepcopy(base)
    mutated["conclusion"]["forced_divisibility"] = "29 divides C"
    expect_rejection(mutated, "a weakened divisibility conclusion")

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
    print("odd e3=2 local-collapse negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    value = validate(load(MANIFEST))
    print("odd e3=2 local-collapse certificate valid")
    print("  29 divides C; 41*43 divides B")
    print("  u=2 mod 13, so fixed-7 trace at the inert prime over 13 is 0 mod 7")
    print("  remaining test: packets 24 and 28 at one prime")
    print(f"  certificate sha256: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
