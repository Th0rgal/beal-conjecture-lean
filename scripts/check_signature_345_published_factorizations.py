#!/usr/bin/env python3
"""Audit the printed low-genus factorizations in the (3,4,5) source.

The script imports the independent Edwards identity checker, reconstructs the
relevant f-forms, rebuilds the exact factorizations printed in Sections 6.2--6.4
of Siksek--Stoll, and identifies which reconstructed form each printed
factorization actually equals.

This is a source-index certificate. It does not certify the Selmer sets,
Mordell--Weil computations, or rational-point conclusions in those sections.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

import check_signature_345_edwards as ed

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature345" / "published_factorizations.json"
EDWARDS_MANIFEST = ROOT / "Research" / "Signature345" / "edwards_forms.json"


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
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(data, dict):
        raise CertificateError("manifest root must be an object")
    return data


def require_exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def homogeneous(degree: int, terms: dict[int, int]) -> ed.HomogeneousPolynomial:
    coefficients = [0] * (degree + 1)
    for exponent_u, coefficient in terms.items():
        if not 0 <= exponent_u <= degree:
            raise CertificateError("homogeneous term has invalid exponent")
        coefficients[exponent_u] = coefficient
    return ed.HomogeneousPolynomial(
        degree, tuple(ed.Fraction(value) for value in coefficients)
    )


def printed_f2() -> ed.HomogeneousPolynomial:
    factor1 = homogeneous(10, {10: 20736, 0: 1})
    factor2 = homogeneous(
        20,
        {
            20: 429981696,
            15: 1558683648,
            10: -207484416,
            5: -75168,
            0: 1,
        },
    )
    return factor1 * factor2


def printed_f3() -> ed.HomogeneousPolynomial:
    factor1 = homogeneous(6, {6: 320, 0: 1})
    factor2 = homogeneous(
        12, {12: 102400, 9: 32000, 6: 16440, 3: -100, 0: 1}
    )
    factor3 = homogeneous(
        12, {12: 102400, 9: 896000, 6: -140160, 3: -2800, 0: 1}
    )
    return factor1 * factor2 * factor3


def printed_f5() -> ed.HomogeneousPolynomial:
    factors = [
        homogeneous(1, {0: 1}),
        homogeneous(1, {1: 1}),
        homogeneous(4, {4: 45, 0: -1}),
        homogeneous(4, {4: 405, 2: 30, 0: 1}),
        homogeneous(4, {4: 15, 2: 10, 0: 3}),
        homogeneous(8, {8: 405, 6: -540, 4: 846, 2: -60, 0: 5}),
        homogeneous(8, {8: 50625, 6: -13500, 4: 4230, 2: -60, 0: 1}),
    ]
    result = ed.HomogeneousPolynomial.one().scale(2)
    for factor in factors:
        result = result * factor
    return result


def reconstruct_edwards() -> tuple[
    dict[
        int,
        tuple[
            ed.HomogeneousPolynomial,
            ed.HomogeneousPolynomial,
            ed.HomogeneousPolynomial,
        ],
    ],
    dict[int, dict[str, Any]],
]:
    data = ed.load_json(EDWARDS_MANIFEST)
    ed.validate_data(data)

    triples: dict[
        int,
        tuple[
            ed.HomogeneousPolynomial,
            ed.HomogeneousPolynomial,
            ed.HomogeneousPolynomial,
        ],
    ] = {}
    payloads: dict[int, dict[str, Any]] = {}

    for entry in data["base_forms"]:
        alpha = [ed.parse_fraction(value) for value in entry["alpha"]]
        f, g, h = ed.edwards_covariants(ed.dodecic(alpha))
        form_id = entry["id"]
        triples[form_id] = (f, g, h)
        payloads[form_id] = ed.canonical_payload(form_id, f, g, h)

    for entry in data["derived_variants"]:
        source_id = entry["source_id"]
        f, g, h = triples[source_id]
        if entry["negate_f"]:
            f = f.scale(-1)
        form_id = entry["id"]
        triples[form_id] = (f, g, h)
        payloads[form_id] = ed.canonical_payload(
            form_id,
            f,
            g,
            h,
            source_id=source_id,
            negate_f=entry["negate_f"],
        )
    return triples, payloads


def canonical_mapping(matches: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        {"matches": matches}, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_data(data: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    require_exact_keys(
        data,
        {
            "schema_version",
            "source",
            "matches",
            "literal_same_id_matches",
            "mapping_sha256",
        },
        "manifest",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise CertificateError("schema_version must be the integer 1")

    source = data["source"]
    require_exact_keys(source, {"arxiv", "sections", "claim"}, "source")
    if (
        source["arxiv"] != "1103.1979v1"
        or source["sections"] != ["6.2", "6.3", "6.4"]
        or source["claim"]
        != "exact equality between printed later-section factorizations and independently reconstructed Edwards forms"
    ):
        raise CertificateError("unexpected source metadata")

    matches = data["matches"]
    if not isinstance(matches, list) or len(matches) != 3:
        raise CertificateError("matches must contain exactly three entries")
    expected_pairs = [(2, 28), (3, 2), (5, 3)]
    for entry, pair in zip(matches, expected_pairs):
        if not isinstance(entry, dict):
            raise CertificateError("mapping entry must be an object")
        require_exact_keys(
            entry,
            {"published_label", "reconstructed_form_id", "expected_form_sha256"},
            "mapping entry",
        )
        if (entry["published_label"], entry["reconstructed_form_id"]) != pair:
            raise CertificateError("mapping entry does not match the audited pair")
        digest = entry["expected_form_sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            raise CertificateError("expected_form_sha256 must be lowercase SHA-256")

    if data["literal_same_id_matches"] is not False:
        raise CertificateError("literal_same_id_matches must remain false")

    triples, payloads = reconstruct_edwards()
    printed = {2: printed_f2(), 3: printed_f3(), 5: printed_f5()}

    actual: list[dict[str, Any]] = []
    for entry in matches:
        published_label = entry["published_label"]
        reconstructed_id = entry["reconstructed_form_id"]
        reconstructed_f = triples[reconstructed_id][0]
        if printed[published_label] != reconstructed_f:
            raise CertificateError(
                f"printed f_{published_label} does not equal reconstructed form "
                f"{reconstructed_id}"
            )
        if triples[published_label][0] == printed[published_label]:
            raise CertificateError(
                f"literal same-ID equality unexpectedly holds for f_{published_label}"
            )
        digest = ed.sha256_json(payloads[reconstructed_id])
        if digest != entry["expected_form_sha256"]:
            raise CertificateError(
                f"full Edwards triple digest mismatch for reconstructed form {reconstructed_id}"
            )
        actual.append(dict(entry))

    digest = canonical_mapping(actual)
    if data["mapping_sha256"] != digest:
        raise CertificateError(
            f"mapping digest mismatch: expected {data['mapping_sha256']}, got {digest}"
        )
    return actual, digest


def validate(path: pathlib.Path) -> tuple[list[dict[str, Any]], str]:
    return validate_data(load_json(path))


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["matches"][0]["reconstructed_form_id"] = 1
    try:
        validate_data(mutated)
    except (CertificateError, ed.CertificateError):
        pass
    else:
        raise RuntimeError("checker accepted a mutated curve mapping")

    mutated = copy.deepcopy(base)
    mutated["matches"][1]["expected_form_sha256"] = "0" * 64
    try:
        validate_data(mutated)
    except (CertificateError, ed.CertificateError):
        pass
    else:
        raise RuntimeError("checker accepted a mutated Edwards digest")

    duplicate = '{"schema_version":1,"schema_version":1}'
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write(duplicate)
        duplicate_path = pathlib.Path(handle.name)
    try:
        try:
            load_json(duplicate_path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        duplicate_path.unlink(missing_ok=True)

    print("published-factorization negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    matches, digest = validate(args.manifest)
    print("signature (3,4,5) printed-factorization audit passed")
    for entry in matches:
        print(
            f"  printed f_{entry['published_label']} = reconstructed Edwards "
            f"form {entry['reconstructed_form_id']}"
        )
    print("  literal same-ID matches: false for labels 2, 3, 5")
    print(f"  mapping sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
