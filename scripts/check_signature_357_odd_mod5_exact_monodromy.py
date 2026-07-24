#!/usr/bin/env python3
"""Replay the finite cluster arithmetic behind the exact odd mod-5 monodromy.

The imported mathematical inputs are the conductor-paper cluster identification,
the DDMM length-pairing theorem and Grothendieck's integral monodromy pairing for
semistable GL2-type abelian varieties.  The checker verifies their specialization
to the odd (3,5,7) branch, the diagonal length matrix and the exact residual
conductor/level split.
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
MANIFEST = ROOT / "Research" / "Signature357" / "odd_mod5_exact_monodromy.json"


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


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
    if data.get("schema_version") != 1 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or certificate digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    sources = data["source_dependencies"]
    for path_key, hash_key, label in (
        ("odd_p7_type_path", "odd_p7_type_sha256", "odd-p7 type"),
        ("cyclotomic_untwist_path", "cyclotomic_untwist_sha256", "untwist"),
        ("low_level_filter_path", "low_level_filter_sha256", "low-level filter"),
    ):
        source = load(ROOT / sources[path_key])
        if digest(source) != source.get("certificate_sha256"):
            raise CertificateError(f"{label} source digest mismatch")
        if source["certificate_sha256"] != sources[hash_key]:
            raise CertificateError(f"manifest is not bound to the {label} source")

    specialization = data["darmon_specialization"]
    if specialization["r"] != 7 or specialization["v7_Delta"] != "3*a":
        raise CertificateError("Darmon discriminant specialization mismatch")
    if "interchange q and r" not in specialization["prime7_swap"]:
        raise CertificateError("prime-7 q/r interchange is missing")

    cluster = data["semistable_cluster_picture"]
    if cluster["top_cluster_depth"] != 1 or cluster["twin_count"] != 3:
        raise CertificateError("semistable cluster shape mismatch")
    if cluster["homology_rank"] != 3 or "inertia-invariant" not in cluster["inertia_stability"]:
        raise CertificateError("cluster homology or inertia stability mismatch")

    pairing = data["monodromy_pairing"]
    if pairing["off_diagonal"] != 0 or pairing["basis"] != ["ell_1", "ell_2", "ell_3"]:
        raise CertificateError("monodromy basis mismatch")
    for a in range(1, 31):
        v_delta = 3 * a
        # Corollary 3.5(6) gives n=(6*v_delta-14)/4.  The displayed
        # relative depth may be half-integral, while the graph edge length
        # entering the integral monodromy pairing is exactly 2*n.
        twice_depth = (6 * v_delta - 14) // 2
        if 2 * (6 * v_delta - 14) % 4 != 0:
            raise CertificateError(f"twice-depth integrality failed at a={a}")
        if twice_depth != 9 * a - 7:
            raise CertificateError(f"twin length mismatch at a={a}")
        matrix = [
            [twice_depth if i == j else 0 for j in range(3)]
            for i in range(3)
        ]
        if any(matrix[i][j] for i in range(3) for j in range(3) if i != j):
            raise CertificateError("off-diagonal monodromy entry appeared")
        vanishes = all(entry % 5 == 0 for row in matrix for entry in row)
        if vanishes != (a % 5 == 3):
            raise CertificateError(f"residual monodromy class mismatch at a={a}")

    if pairing["diagonal"] != "2*n=9*a-7" or pairing["matrix"] != "(9*a-7)*I_3":
        raise CertificateError("recorded pairing formula mismatch")
    if pairing["equivalent_valuation_class"] != "a=3 mod 5":
        raise CertificateError("valuation class mismatch")

    exact = data["exact_conductor"]
    if exact["cases"] != [
        {"e7_twisted": 0, "valuation_class": "v7(A)=3 mod 5"},
        {"e7_twisted": 1, "valuation_class": "v7(A)!=3 mod 5"},
    ]:
        raise CertificateError("exact residual conductor cases mismatch")

    frontier = data["automorphic_frontier"]
    expected = {
        (2, 0): 729,
        (2, 1): 5103,
        (3, 0): 19683,
        (3, 1): 137781,
    }
    recorded = {
        tuple(frontier["e3_2"]["valuation_class_3_mod5"]["level_exponents"]):
            frontier["e3_2"]["valuation_class_3_mod5"]["level_norm"],
        tuple(frontier["e3_2"]["other_valuation_classes"]["level_exponents"]):
            frontier["e3_2"]["other_valuation_classes"]["level_norm"],
        tuple(frontier["e3_3"]["valuation_class_3_mod5"]["level_exponents"]):
            frontier["e3_3"]["valuation_class_3_mod5"]["level_norm"],
        tuple(frontier["e3_3"]["other_valuation_classes"]["level_exponents"]):
            frontier["e3_3"]["other_valuation_classes"]["level_norm"],
    }
    if recorded != expected:
        raise CertificateError("exact level split mismatch")
    for pair, norm in recorded.items():
        if norm != 27 ** pair[0] * 7 ** pair[1]:
            raise CertificateError(f"level norm arithmetic mismatch at {pair}")
    if frontier["remaining_level_norms"] != [5103, 19683, 137781]:
        raise CertificateError("remaining exact frontier mismatch")
    if frontier["maximum_level_norm"] != 137781:
        raise CertificateError("maximum exact level norm mismatch")

    low = load(ROOT / sources["low_level_filter_path"])
    if low["branch_filters"]["odd_branch"]["low_level_survivors"] != []:
        raise CertificateError("norm-729 odd low-level branch is no longer empty")
    if "3.3.49.1-729.1-b" not in low["global_noncm_filter"]["cm_packets_removed"]:
        raise CertificateError("the norm-729 CM packet was not removed")

    if data["gl2_constituent"]["prime5_behavior"] != (
        "5 is inert in K7, so there is a unique coefficient prime with residue field F_125"
    ):
        raise CertificateError("unique residual coefficient prime statement mismatch")
    if "imported literature inputs" not in data["nonclaim"] or "not a proof" not in data["nonclaim"]:
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
    source = load(MANIFEST)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["darmon_specialization"]["v7_Delta"] = "a"
    expect_rejection(mutated, "the wrong discriminant valuation")

    mutated = copy.deepcopy(source)
    mutated["monodromy_pairing"]["off_diagonal"] = 1
    expect_rejection(mutated, "a nonzero off-diagonal pairing")

    mutated = copy.deepcopy(source)
    mutated["exact_conductor"]["cases"][0]["valuation_class"] = "v7(A)=2 mod 5"
    expect_rejection(mutated, "the wrong monodromy-drop class")

    mutated = copy.deepcopy(source)
    mutated["automorphic_frontier"]["remaining_level_norms"].append(964467)
    expect_rejection(mutated, "the obsolete untwisted level")

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
    print("odd mod-5 exact monodromy negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(MANIFEST))
    print("odd mod-5 exact residual monodromy certificate valid")
    print("  e7_twisted=0 iff v7(A)=3 mod 5")
    print("  e7_twisted=1 otherwise")
    print("  remaining levels: 5103, 19683, 137781")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
