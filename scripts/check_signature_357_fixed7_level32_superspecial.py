#!/usr/bin/env python3
"""Replay the odd-branch superspecial closure of fixed-7 level (3,2)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "fixed7_level32_superspecial_closure.json"
CM_FILTER = ROOT / "Research" / "Signature357" / "odd_branch_cm_filter.json"
FRONTIER = ROOT / "Research" / "Signature357" / "fixed7_frontier.json"


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


def digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def validate(data: dict[str, Any], cm: dict[str, Any], frontier: dict[str, Any]) -> str:
    if data.get("schema_version") != 1 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("manifest schema or digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")
    if digest(cm) != cm.get("certificate_sha256"):
        raise CertificateError("CM-filter digest mismatch")
    if cm["certificate_sha256"] != data["source_dependencies"]["odd_cm_filter_sha256"]:
        raise CertificateError("closure is not bound to the CM filter")

    level = next(
        row for row in frontier["levels"] if row["level_exponents"] == [3, 2]
    )
    expected_fixed = level["fixed7_survivors"]
    if expected_fixed != data["source_dependencies"]["fixed7_survivors"]:
        raise CertificateError("fixed-7 survivor input mismatch")

    magma = data["public_magma"]
    if magma["workflow_run_id"] != 30118103950:
        raise CertificateError("unexpected workflow run")
    if magma["workflow_head_sha"] != "a60d3a1a6659565b8f4277c07cd2ed12139065ed":
        raise CertificateError("workflow head mismatch")
    if magma["artifact_id"] != 8606283423:
        raise CertificateError("artifact id mismatch")
    if magma["artifact_sha256"] != "289fbafdbe8106a627df1722a6d020986a7d27e3710bfbea130fa41bf69deb8e":
        raise CertificateError("artifact digest mismatch")
    if magma["output_certificate_sha256"] != "154f7110373c4844ac251d769bde314006c3fda1131f81e07aa378ca67d8f9e8":
        raise CertificateError("producer-output digest mismatch")
    if magma["space_dimension"] != 405 or magma["packet_count"] != 111:
        raise CertificateError("fixed-7 space summary mismatch")
    if magma["fixed7_survivors_input"] != expected_fixed:
        raise CertificateError("Magma fixed-7 input mismatch")

    cm_row = next(row for row in cm["levels"] if row["level_exponents"] == [3, 2])
    cm_intersection = cm_row["cm_intersection"]
    non_cm = cm_row["odd_branch_survivors_after_cm_filter"]
    if magma["non_cm_survivors_input"] != non_cm:
        raise CertificateError("non-CM input mismatch")
    if magma["superspecial_survivors"] != cm_intersection or cm_intersection != [65, 78]:
        raise CertificateError("superspecial survivors are not exactly the CM intersection")
    if magma["non_cm_superspecial_survivors"] != []:
        raise CertificateError("a non-CM packet remains superspecial")
    if sorted(set(magma["superspecial_survivors"]) & set(non_cm)):
        raise CertificateError("CM/non-CM survivor sets overlap")

    if data["conclusion"] != "the Dahmen--Siksek odd branch has no solution lowering to fixed-7 level (3,2)":
        raise CertificateError("closure conclusion mismatch")
    if "only fixed-7 level (3,3) remains" not in data["impact"]:
        raise CertificateError("frontier impact is missing")
    if "imported research inputs" not in data["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim is missing")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], cm: dict[str, Any], frontier: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = digest(data)
    try:
        validate(data, cm, frontier)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    data, cm, frontier = load(MANIFEST), load(CM_FILTER), load(FRONTIER)
    validate(data, cm, frontier)

    bad = copy.deepcopy(data)
    bad["public_magma"]["non_cm_superspecial_survivors"] = [21]
    expect_rejection(bad, cm, frontier, "a surviving non-CM packet")

    bad = copy.deepcopy(data)
    bad["public_magma"]["superspecial_survivors"] = [65]
    expect_rejection(bad, cm, frontier, "an incomplete superspecial list")

    bad = copy.deepcopy(data)
    bad["public_magma"]["packet_count"] = 110
    expect_rejection(bad, cm, frontier, "a corrupted packet count")

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
    print("fixed-7 level-(3,2) superspecial negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    value = validate(load(MANIFEST), load(CM_FILTER), load(FRONTIER))
    print("fixed-7 level-(3,2) closed in the odd branch")
    print("  nine fixed-7 survivors -> two superspecial survivors")
    print("  the two superspecial survivors are exactly the CM packets 65 and 78")
    print("  CM support excludes both in the odd branch")
    print(f"  certificate sha256: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
