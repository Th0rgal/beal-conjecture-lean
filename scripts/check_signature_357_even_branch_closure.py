#!/usr/bin/env python3
"""Replay the literature-assisted complete closure of the (3,5,7) even branch."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "even_branch_complete_closure.json"


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


def digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1:
        raise CertificateError("schema_version must equal 1")
    if digest(data) != data.get("certificate_sha256"):
        raise CertificateError("even-branch closure digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    sources = data["sources"]
    dependencies: dict[str, dict[str, Any]] = {}
    for name, path_key, digest_key in (
        ("frontier", "branch_frontier_path", "branch_frontier_sha256"),
        ("closure", "low_level_closure_path", "low_level_closure_sha256"),
        ("ray", "fixed7_global_path", "fixed7_global_sha256"),
        ("hasse", "fixed7_hasse_path", "fixed7_hasse_sha256"),
    ):
        dependency = load(ROOT / sources[path_key])
        if digest(dependency) != dependency.get("certificate_sha256"):
            raise CertificateError(f"{name} dependency digest mismatch")
        if dependency["certificate_sha256"] != sources[digest_key]:
            raise CertificateError(f"closure is not bound to the {name} dependency")
        dependencies[name] = dependency

    ray = dependencies["ray"]
    if ray["conclusion"]["unique_reducibility_character"] != "psi_(2,0)":
        raise CertificateError("fixed-7 reducibility character changed")
    hasse = dependencies["hasse"]
    if hasse["scope"]["conclusion"] != "7 divides C":
        raise CertificateError("Hasse input does not force 7|C")
    frontier = dependencies["frontier"]
    if frontier["even_branch_remaining_norms"] != [5103]:
        raise CertificateError("even branch is not concentrated at norm 5103")
    if frontier["branches"]["even"]["allowed_e3"] != [1, 2]:
        raise CertificateError("even e3 range mismatch")
    if frontier["branches"]["even"]["allowed_e7"] != [1]:
        raise CertificateError("even e7 range mismatch")
    closure = dependencies["closure"]
    if closure["scope"]["complete_level_norm_bound"] != 2059:
        raise CertificateError("low-level completeness bound changed")
    if closure["scope"]["only_preclosure_packet"] != "3.3.49.1-189.1-a":
        raise CertificateError("the preclosure low-level packet changed")
    if "frontier is empty" not in closure["conclusion"]:
        raise CertificateError("the complete low-level frontier is not closed")

    branch = data["branch"]
    if branch["mod5_level_norms_before_low_level_closure"] != [189, 5103]:
        raise CertificateError("pre-closure even level list mismatch")
    if (
        branch["low_level_norm_closed"] != 189
        or branch["only_remaining_level_norm"] != 5103
        or branch["only_remaining_level_exponents"] != [2, 1]
    ):
        raise CertificateError("remaining even level mismatch")

    magma = data["public_magma"]
    if magma["workflow_run_id"] != 30109225690:
        raise CertificateError("unexpected workflow run")
    if magma["workflow_head_sha"] != "1f3037002af96788fa165b575f3a3c73a12769c9":
        raise CertificateError("workflow head mismatch")
    if magma["artifact_id"] != 8602997281:
        raise CertificateError("artifact id mismatch")
    if magma["artifact_sha256"] != "e50e069b349eb6a4f82e67656439f153bf288a18892664cd79a5998464f7f0cd":
        raise CertificateError("artifact digest mismatch")
    if magma["output_certificate_sha256"] != "3fddd62def7f5f63d2c9a0872b93b0332323fcd50ac500256f52b9241d7dd271":
        raise CertificateError("public-Magma output digest mismatch")
    if magma["level_exponents"] != [2, 1] or magma["level_norm"] != 5103:
        raise CertificateError("Magma level mismatch")
    if magma["space_dimension"] != 73 or magma["packet_count"] != 10:
        raise CertificateError("Magma space summary mismatch")
    if sum(magma["packet_dimensions"]) != 73 or len(magma["packet_dimensions"]) != 10:
        raise CertificateError("packet dimensions do not replay")
    if magma["norm8_survivors"] != [1] or magma["marginal_local_survivors"] != [1]:
        raise CertificateError("marginal survivor chain mismatch")
    if magma["coefficient_field_safe_even_coupled_survivors"] != []:
        raise CertificateError("a packet still survives the even two-Frey sieve")
    if magma["coupled_primes"] != [13, 29, 41]:
        raise CertificateError("coupled auxiliary-prime list mismatch")

    if data["conclusion"] != "there is no primitive positive solution in the Dahmen--Siksek even branch":
        raise CertificateError("even-branch conclusion mismatch")
    if data["impact"] != "the full (3,5,7) problem is reduced to the odd branch":
        raise CertificateError("impact statement mismatch")
    if "imported research inputs" not in data["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim is missing")
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
    mutated["public_magma"]["coefficient_field_safe_even_coupled_survivors"] = [1]
    expect_rejection(mutated, "a surviving even packet")

    mutated = copy.deepcopy(base)
    mutated["public_magma"]["packet_dimensions"][0] = 2
    expect_rejection(mutated, "a corrupted packet dimension")

    mutated = copy.deepcopy(base)
    mutated["branch"]["only_remaining_level_norm"] = 9261
    expect_rejection(mutated, "the wrong remaining level")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
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
    print("signature-357 even-branch closure negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(MANIFEST))
    print("signature-357 even branch closed")
    print("  low level 189: closed")
    print("  high level 5103: 10 packets -> 1 marginal -> 0 coupled")
    print("  remaining global branch: odd only")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
