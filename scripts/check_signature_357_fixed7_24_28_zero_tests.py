#!/usr/bin/env python3
"""Replay the fixed-7 packet-24/28 zero-root predicates from coefficients."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "fixed7_packets_24_28_zero_tests.json"


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
        raise CertificateError("manifest root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def validate(data: dict[str, Any]) -> tuple[str, list[int]]:
    if data.get("schema_version") != 1 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != 4:
        raise CertificateError("expected four packet/prime rows")
    seen: set[tuple[int, int]] = set()
    computed: dict[int, list[bool]] = {24: [], 28: []}
    for row in rows:
        packet = row.get("packet")
        prime = row.get("prime")
        if packet not in computed or prime not in (13, 43):
            raise CertificateError("unexpected packet or prime")
        key = (packet, prime)
        if key in seen:
            raise CertificateError("duplicate packet/prime row")
        seen.add(key)
        coefficients = row.get("trace_coefficients_low_to_high")
        degree = row.get("trace_polynomial_degree")
        if not isinstance(coefficients, list) or len(coefficients) != degree + 1:
            raise CertificateError("coefficient count mismatch")
        zero_root = coefficients[0] % 7 == 0
        if zero_root != row.get("zero_root_mod7"):
            raise CertificateError("zero-root flag does not replay")
        computed[packet].append(zero_root)
    if seen != {(24, 13), (24, 43), (28, 13), (28, 43)}:
        raise CertificateError("packet/prime grid is incomplete")
    survivors = sorted(packet for packet, tests in computed.items() if all(tests))
    if survivors != data.get("surviving_packets"):
        raise CertificateError("survivor list mismatch")
    expected = (
        "the odd e3=2 block is eliminated"
        if not survivors
        else f"the decisive zero tests leave packets {survivors}"
    )
    if data.get("conclusion") != expected:
        raise CertificateError("conclusion mismatch")
    if "imported research inputs" not in data.get("nonclaim", ""):
        raise CertificateError("trust boundary missing")
    return data["certificate_sha256"], survivors


def expect_rejection(data: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = digest(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    if not MANIFEST.exists():
        print("produced manifest not present yet; static negative fixtures skipped")
        return
    base = load(MANIFEST)
    validate(base)
    bad = copy.deepcopy(base)
    bad["rows"][0]["zero_root_mod7"] = not bad["rows"][0]["zero_root_mod7"]
    expect_rejection(bad, "a flipped zero-root predicate")
    bad = copy.deepcopy(base)
    bad["surviving_packets"] = [] if base["surviving_packets"] else [24]
    expect_rejection(bad, "a forged survivor list")
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
    print("fixed-7 packet zero-test negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate, survivors = validate(load(MANIFEST))
    print("fixed-7 packet 24/28 zero tests valid")
    print("  surviving packets:", survivors)
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
