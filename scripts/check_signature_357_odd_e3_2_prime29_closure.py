#!/usr/bin/env python3
"""Replay the coupled prime-29 closure of the odd e3=2 (3,5,7) block."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "odd_e3_2_prime29_closure.json"


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
        raise CertificateError(f"{path} root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    payload = copy.deepcopy(value)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate(coefficients: list[int], value: int, modulus: int) -> int:
    result = 0
    for coefficient in reversed(coefficients):
        result = (result * value + coefficient) % modulus
    return result


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    scope = data["scope"]
    if scope != {
        "branch": "Dahmen--Siksek odd branch",
        "fixed7_level_exponents": [2, 3],
        "prime3_conductor_exponent": 2,
        "surviving_packets_before_prime29": [24, 28],
    }:
        raise CertificateError("scope changed")

    source = data["source_dependencies"]
    dependency = load(ROOT / source["local_collapse_path"])
    if digest(dependency) != dependency.get("certificate_sha256"):
        raise CertificateError("local-collapse dependency digest is invalid")
    if dependency["certificate_sha256"] != source["local_collapse_sha256"]:
        raise CertificateError("local-collapse dependency changed")
    at29 = dependency["auxiliary_primes"]["29"]
    if at29["forced_regime"] != "zero" or at29["divisibility"] != "29 divides C":
        raise CertificateError("prime-29 local forcing changed")
    if source["two_frey_identity"] != "u+v=1":
        raise CertificateError("two-Frey identity changed")

    producer = (ROOT / source["marginal_fixed7_producer"]).read_text(encoding="utf-8")
    if (
        "if Common(P,x-(q+1)) or Common(P,x+(q+1)) then return true; end if;"
        not in producer
    ):
        raise CertificateError("multiplicative fixed-7 trace rule changed")

    local = data["local_forcing"]
    prime = local["rational_prime"]
    if prime != 29 or local["forced_u_mod29"] != 0:
        raise CertificateError("wrong prime or zero parameter")
    v = (1 - local["forced_u_mod29"]) % prime
    if local["forced_v_mod29"] != v or v != 1:
        raise CertificateError("coupled parameter is not v=1")
    if local["fixed7_parameter"] != "t7=v=1":
        raise CertificateError("fixed-7 multiplicative parameter changed")
    norm = prime ** local["residue_degree_K5"]
    if local["norm_prime"] != norm:
        raise CertificateError("prime norm changed")
    targets = [-(norm + 1), norm + 1]
    residues = [target % 7 for target in targets]
    if local["permitted_base_traces_integers"] != targets:
        raise CertificateError("integer trace targets changed")
    if local["permitted_base_traces_mod7"] != residues:
        raise CertificateError("residual trace targets changed")
    if len(set(residues)) != 2:
        raise CertificateError("multiplicative target does not split distinctly")

    expected_sources = {
        24: (8608407293, "69b0c00b833d5876f7bba6b25611582bc372eddb452ea3de8e6e8a748875a9ac", "8d862a2c248e58b2178d4d52f06061c810b78b933085dbbfa33208898c60461d"),
        28: (8608382387, "486eeddc97347f580aebb2bb14845ff9bc7b7e5b2b8a89a73abd979458b4543f", "cf28e3a8d39c3708b14d7b0b61e5e5cf22cfd45aeaf22a0304a739e4be3f6534"),
    }
    rows = data["packet_rows"]
    if [row["packet"] for row in rows] != [24, 28]:
        raise CertificateError("packet rows changed")
    survivors: list[int] = []
    for row in rows:
        packet = row["packet"]
        artifact_id, zip_sha, source_sha = expected_sources[packet]
        if (row["artifact_id"], row["artifact_zip_sha256"], row["source_certificate_sha256"]) != (
            artifact_id,
            zip_sha,
            source_sha,
        ):
            raise CertificateError(f"packet {packet} source metadata changed")
        coefficients = row["base_trace_coefficients_low_to_high"]
        if coefficients != [196, 0, -98, 0, 1]:
            raise CertificateError(f"packet {packet} Hecke polynomial changed")
        evaluations = {str(target): evaluate(coefficients, target, 7) for target in targets}
        if row["evaluations_at_permitted_traces_mod7"] != evaluations:
            raise CertificateError(f"packet {packet} trace evaluations changed")
        survives = any(value == 0 for value in evaluations.values())
        if row["gcd_with_multiplicative_target_degree_mod7"] != int(survives):
            raise CertificateError(f"packet {packet} gcd record changed")
        if row["survives"] != survives:
            raise CertificateError(f"packet {packet} survivor flag changed")
        if survives:
            survivors.append(packet)

    conclusion = data["conclusion"]
    if survivors or conclusion["surviving_packets"]:
        raise CertificateError(f"unexpected prime-29 survivors: {survivors}")
    if conclusion["statement"] != "the Dahmen--Siksek odd e3=2 block is empty":
        raise CertificateError("closure statement changed")
    if "imported research inputs" not in data["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim missing")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = digest(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load(MANIFEST)
    validate(base)
    mutated = copy.deepcopy(base)
    mutated["packet_rows"][0]["base_trace_coefficients_low_to_high"][0] += 1
    expect_rejection(mutated, "a mutated Hecke polynomial")
    mutated = copy.deepcopy(base)
    mutated["local_forcing"]["forced_v_mod29"] = 0
    expect_rejection(mutated, "the wrong coupled parameter")
    mutated = copy.deepcopy(base)
    mutated["conclusion"]["surviving_packets"] = [24]
    expect_rejection(mutated, "a fabricated survivor")
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
    print("odd e3=2 prime-29 closure negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    value = validate(load(MANIFEST))
    print("odd e3=2 prime-29 closure certificate valid")
    print("  packets 24 and 28 both fail a_p = +/-30 mod 7")
    print("  conclusion: the odd e3=2 block is empty")
    print(f"  certificate sha256: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
