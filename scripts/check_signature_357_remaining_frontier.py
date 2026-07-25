#!/usr/bin/env python3
"""Replay the exact twisted odd frontier and its audited prime-2 split."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Research" / "Signature357" / "signature357_remaining_frontier.json"


class CertificateError(ValueError):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


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
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def bound(path: str, expected: str, label: str) -> dict[str, Any]:
    value = load(ROOT / path)
    if digest(value) != value.get("certificate_sha256"):
        raise CertificateError(f"invalid {label} digest")
    if value["certificate_sha256"] != expected:
        raise CertificateError(f"frontier is not bound to the {label}")
    return value


def validate(data: dict[str, Any]) -> tuple[str, list[int]]:
    expected_keys = {
        "schema_version",
        "status",
        "equation",
        "branch_status",
        "compression",
        "conclusion",
        "next_computation",
        "nonclaim",
        "certificate_sha256",
    }
    if set(data) != expected_keys:
        raise CertificateError("manifest keys differ from schema")
    if data.get("schema_version") != 4 or digest(data) != data.get("certificate_sha256"):
        raise CertificateError("schema or frontier digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    branches = data["branch_status"]
    even = branches["even"]
    even_source = bound(
        even["certificate_path"], even["certificate_sha256"], "even-branch closure"
    )
    if even["conclusion"] != "empty" or even_source["conclusion"] != (
        "there is no primitive positive solution in the Dahmen--Siksek even branch"
    ):
        raise CertificateError("even branch is not closed")

    odd = branches["odd"]
    if odd["allowed_e3"] != [2, 3] or odd["closed_e3"] != [2] or odd["remaining_e3"] != [3]:
        raise CertificateError("odd e3 status changed")
    irreducibility = bound(
        odd["global_mod5_irreducibility_path"],
        odd["global_mod5_irreducibility_sha256"],
        "mod-5 irreducibility certificate",
    )
    if "absolutely irreducible" not in irreducibility["conclusion"]:
        raise CertificateError("mod-5 irreducibility conclusion missing")

    untwist = bound(
        odd["cyclotomic_untwist_path"],
        odd["cyclotomic_untwist_sha256"],
        "cyclotomic untwist certificate",
    )
    if untwist["local_untwist"]["twisted_residual_conductor_exponents"] != [0, 1]:
        raise CertificateError("twisted prime-7 conductor split changed")
    if untwist["preserved_properties"].get("prime2_trace_filter") != {
        "B_odd": "a_P2=0 mod 5",
        "B_even": "a_P2 is 1 or 4 mod 5",
        "cyclotomic_untwist_value_at_2": 1,
        "reason": (
            "ord_7(2)=3, so the unique prime above 2 in K7 splits in "
            "Q(zeta_7)/K7"
        ),
    }:
        raise CertificateError("untwist retains an incorrect prime-2 filter")

    monodromy = bound(
        odd["exact_monodromy_path"],
        odd["exact_monodromy_sha256"],
        "exact-monodromy certificate",
    )
    if monodromy["exact_conductor"]["cases"] != [
        {"e7_twisted": 0, "valuation_class": "v7(A)=3 mod 5"},
        {"e7_twisted": 1, "valuation_class": "v7(A)!=3 mod 5"},
    ]:
        raise CertificateError("monodromy valuation split changed")
    if monodromy["automorphic_frontier"]["remaining_level_norms"] != [5103, 19683, 137781]:
        raise CertificateError("monodromy level frontier changed")

    parity_meta = odd["prime2_parity_split"]
    parity = bound(parity_meta["path"], parity_meta["sha256"], "prime-2 parity certificate")
    if parity.get("schema_version") != 2:
        raise CertificateError("prime-2 parity schema changed")
    pairs = parity["parity_branches"]
    if [row["name"] for row in pairs] != ["B_odd", "B_even"]:
        raise CertificateError("prime-2 parity inventory changed")
    b_odd, b_even = pairs
    if (
        b_odd["mod5_base_trace_mod5"] != 0
        or b_odd["fixed7_trace_mod7"] != 6
        or b_odd["residual_trace_pairs_mod5_mod7"] != [[0, 6]]
        or b_odd["mod5_full_to_base_transform"] != "-16=a_P^2-2*8"
    ):
        raise CertificateError("B-odd trace pair changed")
    if (
        b_even["mod5_level_lowered_hecke_targets_mod5"] != [1, 4]
        or b_even["fixed7_trace_mod7"] != 0
        or b_even["residual_trace_pairs_mod5_mod7"] != [[1, 0], [4, 0]]
    ):
        raise CertificateError("B-even trace targets changed")
    expected_parity_meta = {
        "path": "Research/Signature357/two_frey_prime2_parity_split.json",
        "sha256": parity["certificate_sha256"],
        "B_odd": {
            "mod5_trace_mod5": 0,
            "fixed7_trace_mod7": 6,
            "target": "eliminate the trace-zero subspaces at levels 19683 and 137781",
        },
        "B_even": {
            "mod5_trace_mod5": [1, 4],
            "fixed7_trace_mod7": 0,
            "target": "eliminate the trace-zero subspace at fixed-7 level (3,3)",
        },
        "residual_trace_pairs_mod5_mod7": [[0, 6], [1, 0], [4, 0]],
    }
    if parity_meta != expected_parity_meta:
        raise CertificateError("frontier parity strategy changed")

    split = odd["valuation_split"]
    zero = split["v7A_congruent_3_mod5"]
    nonzero = split["other_v7A_classes"]
    if zero != {
        "twisted_e7": 0,
        "candidate_pairs": [[2, 0], [3, 0]],
        "candidate_level_norms": [729, 19683],
        "closed_level_norms": [729],
        "remaining_pairs": [[3, 0]],
        "remaining_level_norms": [19683],
    }:
        raise CertificateError("valuation-3 mod-5 block changed")
    if nonzero != {
        "twisted_e7": 1,
        "candidate_pairs": [[2, 1], [3, 1]],
        "candidate_level_norms": [5103, 137781],
        "closed_level_norms": [5103],
        "remaining_pairs": [[3, 1]],
        "remaining_level_norms": [137781],
    }:
        raise CertificateError("nonzero-monodromy block changed")
    remaining_pairs = sorted(zero["remaining_pairs"] + nonzero["remaining_pairs"])
    remaining_norms = sorted(zero["remaining_level_norms"] + nonzero["remaining_level_norms"])
    if remaining_pairs != [[3, 0], [3, 1]] or remaining_pairs != odd["remaining_exponent_pairs"]:
        raise CertificateError("remaining exponent pairs changed")
    if remaining_norms != [19683, 137781] or remaining_norms != odd["remaining_level_norms"]:
        raise CertificateError("remaining level norms changed")

    e32 = odd["fixed7_pairing"]["e3_2"]
    closure = bound(
        e32["prime29_closure_path"],
        e32["prime29_closure_sha256"],
        "odd-e3=2 closure",
    )
    if e32["closed_levels"] != [[2, 2], [2, 3]] or e32["remaining_packets"]:
        raise CertificateError("e3=2 fixed-7 closure changed")
    if closure["conclusion"]["surviving_packets"] != []:
        raise CertificateError("e3=2 closure has a survivor")

    e33 = odd["fixed7_pairing"]["e3_3"]
    level32 = bound(e33["closure_path"], e33["closure_sha256"], "level-(3,2) closure")
    if e33["closed_level"] != [3, 2] or e33["remaining_level"] != [3, 3]:
        raise CertificateError("e3=3 fixed-7 pairing changed")
    if level32["public_magma"]["non_cm_superspecial_survivors"] != []:
        raise CertificateError("fixed-7 level (3,2) is not closed")

    if data["compression"] != {
        "obsolete_untwisted_odd_levels": [35721, 964467],
        "twisted_candidate_level_norms": [729, 5103, 19683, 137781],
        "closed_level_norms": [729, 5103],
        "final_remaining_level_count": 2,
        "final_remaining_level_norms": [19683, 137781],
        "maximum_level_norm": 137781,
        "maximum_norm_reduction_from_untwisted_frontier": 7,
    }:
        raise CertificateError("compression metadata changed")
    if data["next_computation"].get("prime2_parity_strategy") != (
        "B odd is closed by zero mod-5 trace kernels at both remaining levels; "
        "B even is closed by a zero fixed-7 trace kernel at level (3,3)"
    ):
        raise CertificateError("prime-2 completion strategy changed")
    if "+/-8 mod 5" not in data["next_computation"]["level_19683"]:
        raise CertificateError("removed-prime trace condition missing")
    if "does not prove" not in data["nonclaim"]:
        raise CertificateError("explicit nonclaim missing")
    return data["certificate_sha256"], remaining_norms


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
    mutated["branch_status"]["odd"]["closed_e3"] = []
    expect_rejection(mutated, "a reopened e3=2 block")
    mutated = copy.deepcopy(base)
    mutated["branch_status"]["odd"]["prime2_parity_split"]["B_even"]["mod5_trace_mod5"] = [0]
    expect_rejection(mutated, "a parity-blind norm-8 target")
    mutated = copy.deepcopy(base)
    mutated["branch_status"]["odd"]["fixed7_pairing"]["e3_2"]["remaining_packets"] = [24]
    expect_rejection(mutated, "a fabricated e3=2 survivor")
    mutated = copy.deepcopy(base)
    mutated["compression"]["final_remaining_level_norms"].append(5103)
    expect_rejection(mutated, "the closed level 5103")
    with tempfile.NamedTemporaryFile("w", delete=False) as fixture:
        fixture.write('{"schema_version":4,"schema_version":4}')
        path = pathlib.Path(fixture.name)
    try:
        try:
            load(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("duplicate JSON keys accepted")
    finally:
        path.unlink(missing_ok=True)
    print("signature-357 audited final-frontier negative fixtures passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate, norms = validate(load(MANIFEST))
    print("signature-357 audited final frontier valid")
    print("  even branch: closed")
    print("  odd e3=2 block: closed")
    print("  B odd target: mod-5 trace-zero kernels at", ", ".join(map(str, norms)))
    print("  B even target: fixed-7 trace-zero kernel at level (3,3)")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
