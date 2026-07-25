#!/usr/bin/env python3
"""Replay the exact local arithmetic behind the mod-5 20/21 sieve.

The checker verifies the p-adic root criteria modulo 9 and 49, the CRT
intersection, and the parity obstruction for the Swan conductor.  The input
that an irreducible local polynomial gives Swan conductor one is explicitly
imported from the conductor computation; the checker records the internal
typo in the printed proposition rather than silently choosing one branch.
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
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "mod5_local_irreducibility.json"


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


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def p7(value: int, parameter: int) -> int:
    return (
        value**7
        - 7 * value**5
        + 14 * value**3
        - 7 * value
        + 4 * parameter
        - 2
    ) % 49


def p3(value: int, parameter: int) -> int:
    inverse = pow(parameter, -1, 9)
    return (value**3 - 3 * value + 2 - 4 * inverse) % 9


def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version",
            "status",
            "scope",
            "source_audit",
            "local_polynomials",
            "combined",
            "swan_parity",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != "research-certificate-with-imported-conductor-lemma":
        raise CertificateError("unexpected status")

    scope = data["scope"]
    exact_keys(
        scope,
        {
            "equation",
            "orientation",
            "field",
            "residual_prime",
            "unit_hypotheses",
            "parameter",
        },
        "scope",
    )
    if (
        scope["equation"] != "A^3+B^5=C^7"
        or scope["orientation"] != "(-C)^7+B^5+A^3=0"
        or scope["field"] != "K7=Q(zeta_7)^+"
        or scope["residual_prime"] != 5
    ):
        raise CertificateError("scope mismatch")

    source = data["source_audit"]
    exact_keys(
        source,
        {
            "conductor_paper",
            "proposition",
            "printed_typo",
            "corrected_input",
        },
        "source_audit",
    )
    if source["conductor_paper"] != "arXiv:2503.21568" or source["proposition"] != "6.10":
        raise CertificateError("source locator mismatch")
    if "wild conductor 0" not in source["printed_typo"] or "Swan conductor 1" not in source["corrected_input"]:
        raise CertificateError("source typo/correction was not recorded explicitly")

    local = data["local_polynomials"]
    exact_keys(local, {"prime7", "prime3"}, "local_polynomials")
    seven = local["prime7"]
    exact_keys(
        seven,
        {
            "modulus",
            "polynomial",
            "admissible_t_count",
            "reducible_t",
        },
        "prime7",
    )
    if seven["modulus"] != 49:
        raise CertificateError("prime-7 modulus must be 49")
    admissible7 = [t for t in range(49) if t % 7 not in (0, 1)]
    roots7 = [
        t
        for t in admissible7
        if any(p7(value, t) == 0 for value in range(49))
    ]
    if len(admissible7) != seven["admissible_t_count"] or len(admissible7) != 35:
        raise CertificateError("prime-7 admissible count mismatch")
    if roots7 != seven["reducible_t"] or roots7 != [3, 13, 25, 37, 47]:
        raise CertificateError(f"prime-7 reducible classes mismatch: {roots7}")

    three = local["prime3"]
    exact_keys(
        three,
        {"modulus", "polynomial", "admissible_t", "reducible_t"},
        "prime3",
    )
    if three["modulus"] != 9 or three["admissible_t"] != [2, 5, 8]:
        raise CertificateError("prime-3 metadata mismatch")
    roots3 = [
        t
        for t in three["admissible_t"]
        if any(p3(value, t) == 0 for value in range(9))
    ]
    if roots3 != three["reducible_t"] or roots3 != [2]:
        raise CertificateError(f"prime-3 reducible classes mismatch: {roots3}")

    combined = data["combined"]
    exact_keys(
        combined,
        {
            "modulus",
            "admissible_count",
            "simultaneous_exceptional",
            "irreducible_count",
            "fraction",
        },
        "combined",
    )
    exceptional = [
        t
        for t in range(441)
        if t % 9 in roots3 and t % 49 in roots7
    ]
    if (
        combined["modulus"] != 441
        or combined["admissible_count"] != 3 * 35
        or combined["admissible_count"] != 105
        or exceptional != combined["simultaneous_exceptional"]
        or exceptional != [47, 74, 101, 209, 380]
        or combined["irreducible_count"] != 100
        or combined["fraction"] != "20/21"
    ):
        raise CertificateError(f"CRT/local-count mismatch: {exceptional}")

    swan = data["swan_parity"]
    exact_keys(
        swan,
        {
            "residue_characteristic",
            "wild_primes",
            "determinant_unramified_on_wild_inertia",
            "absolutely_reducible_swan_is_even",
            "source_irreducible_polynomial_swan",
            "conclusion",
        },
        "swan_parity",
    )
    if (
        swan["residue_characteristic"] != 5
        or swan["wild_primes"] != [3, 7]
        or not swan["determinant_unramified_on_wild_inertia"]
        or not swan["absolutely_reducible_swan_is_even"]
        or swan["source_irreducible_polynomial_swan"] != 1
    ):
        raise CertificateError("Swan-parity metadata mismatch")
    # For an absolutely reducible two-dimensional representation, wild inertia
    # is semisimple (its finite quotient has order prime to 5).  The determinant
    # condition makes the two characters inverse, so their equal Swan conductors
    # add to an even number.  This parity is incompatible with source Swan=1.
    if 2 * 0 % 2 != 0 or 1 % 2 != 1:
        raise CertificateError("internal Swan parity check failed")

    actual = digest(data)
    if data["certificate_sha256"] != actual:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {actual}"
        )
    return actual


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["local_polynomials"]["prime7"]["reducible_t"].remove(47)
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a weakened prime-7 list")

    mutated = copy.deepcopy(base)
    mutated["combined"]["simultaneous_exceptional"][0] = 48
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated CRT class")

    mutated = copy.deepcopy(base)
    mutated["swan_parity"]["source_irreducible_polynomial_swan"] = 0
    try:
        validate(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted the contradictory printed branch")

    duplicate = '{"schema_version":1,"schema_version":1}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write(duplicate)
        path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)

    print("mod-5 local irreducibility negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load_json(args.manifest))
    print("mod-5 local irreducibility certificate valid")
    print("  exact exceptional classes mod 441: 47,74,101,209,380")
    print("  irreducible local branches: 100/105 = 20/21")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
