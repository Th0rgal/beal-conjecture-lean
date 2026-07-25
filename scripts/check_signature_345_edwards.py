#!/usr/bin/env python3
"""Replay the exact Edwards binary-form identities used for signature (3,4,5).

This checker is deliberately independent of Magma/Sage/SymPy. It reconstructs
the 27 base dodecics from Table 1 of Siksek--Stoll, derives the degree-20 and
degree-30 covariants by exact rational arithmetic, expands the 22 sign variants,
and verifies all 49 identities

    f_i^2 + g_i^3 + h_i^5 = 0.

It certifies algebraic identities and transcription integrity only. It does not
certify Edwards' completeness theorem, local-solubility computations, partial
Selmer sets, Mordell--Weil ranks, or rational-point determinations.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature345" / "edwards_forms.json"


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


def parse_fraction(value: Any) -> Fraction:
    if not isinstance(value, str) or not value:
        raise CertificateError(f"coefficient must be a non-empty string, got {value!r}")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise CertificateError(f"invalid rational coefficient: {value!r}") from exc
    canonical = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    if value != canonical:
        raise CertificateError(
            f"non-canonical rational coefficient {value!r}; expected {canonical!r}"
        )
    return result


@dataclass(frozen=True)
class HomogeneousPolynomial:
    """Coefficient i is for u^i v^(degree-i)."""

    degree: int
    coefficients: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if self.degree < 0 or len(self.coefficients) != self.degree + 1:
            raise CertificateError("malformed homogeneous polynomial")

    @staticmethod
    def one() -> "HomogeneousPolynomial":
        return HomogeneousPolynomial(0, (Fraction(1),))

    def derivative_u(self) -> "HomogeneousPolynomial":
        if self.degree == 0:
            return HomogeneousPolynomial(0, (Fraction(0),))
        out = [Fraction(0)] * self.degree
        for i, coefficient in enumerate(self.coefficients):
            if i:
                out[i - 1] += i * coefficient
        return HomogeneousPolynomial(self.degree - 1, tuple(out))

    def derivative_v(self) -> "HomogeneousPolynomial":
        if self.degree == 0:
            return HomogeneousPolynomial(0, (Fraction(0),))
        out = [Fraction(0)] * self.degree
        for i, coefficient in enumerate(self.coefficients):
            exponent_v = self.degree - i
            if exponent_v:
                out[i] += exponent_v * coefficient
        return HomogeneousPolynomial(self.degree - 1, tuple(out))

    def __add__(self, other: "HomogeneousPolynomial") -> "HomogeneousPolynomial":
        if self.degree != other.degree:
            raise CertificateError("cannot add homogeneous polynomials of different degrees")
        return HomogeneousPolynomial(
            self.degree,
            tuple(a + b for a, b in zip(self.coefficients, other.coefficients)),
        )

    def __sub__(self, other: "HomogeneousPolynomial") -> "HomogeneousPolynomial":
        if self.degree != other.degree:
            raise CertificateError("cannot subtract homogeneous polynomials of different degrees")
        return HomogeneousPolynomial(
            self.degree,
            tuple(a - b for a, b in zip(self.coefficients, other.coefficients)),
        )

    def __mul__(self, other: "HomogeneousPolynomial") -> "HomogeneousPolynomial":
        out = [Fraction(0)] * (self.degree + other.degree + 1)
        for i, left in enumerate(self.coefficients):
            if left == 0:
                continue
            for j, right in enumerate(other.coefficients):
                if right:
                    out[i + j] += left * right
        return HomogeneousPolynomial(self.degree + other.degree, tuple(out))

    def scale(self, scalar: Fraction | int) -> "HomogeneousPolynomial":
        factor = Fraction(scalar)
        return HomogeneousPolynomial(
            self.degree, tuple(factor * c for c in self.coefficients)
        )

    def __pow__(self, exponent: int) -> "HomogeneousPolynomial":
        if exponent < 0:
            raise CertificateError("negative polynomial exponent")
        result = HomogeneousPolynomial.one()
        base = self
        power = exponent
        while power:
            if power & 1:
                result = result * base
            base = base * base
            power //= 2
        return result

    def is_zero(self) -> bool:
        return all(c == 0 for c in self.coefficients)

    def is_integral(self) -> bool:
        return all(c.denominator == 1 for c in self.coefficients)

    def canonical_coefficients(self) -> list[str]:
        return [
            str(c.numerator)
            if c.denominator == 1
            else f"{c.numerator}/{c.denominator}"
            for c in self.coefficients
        ]


def dodecic(alpha: list[Fraction]) -> HomogeneousPolynomial:
    if len(alpha) != 13:
        raise CertificateError(f"expected 13 dodecic entries, got {len(alpha)}")
    coefficients = tuple(Fraction(math.comb(12, i)) * alpha[i] for i in range(13))
    return HomogeneousPolynomial(12, coefficients)


def edwards_covariants(
    h: HomogeneousPolynomial,
) -> tuple[HomogeneousPolynomial, HomogeneousPolynomial, HomogeneousPolynomial]:
    h_u = h.derivative_u()
    h_v = h.derivative_v()
    h_uu = h_u.derivative_u()
    h_uv = h_u.derivative_v()
    h_vv = h_v.derivative_v()
    g = (h_uu * h_vv - h_uv * h_uv).scale(Fraction(1, 132**2))
    f = (
        h_u * g.derivative_v() - h_v * g.derivative_u()
    ).scale(Fraction(1, 240))
    return f, g, h


def canonical_payload(
    form_id: int,
    f: HomogeneousPolynomial,
    g: HomogeneousPolynomial,
    h: HomogeneousPolynomial,
    *,
    source_id: int | None = None,
    negate_f: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": form_id,
        "f": f.canonical_coefficients(),
        "g": g.canonical_coefficients(),
        "h": h.canonical_coefficients(),
    }
    if source_id is not None:
        payload["source_id"] = source_id
        payload["negate_f"] = negate_f
    return payload


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require_exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def validate_data(data: dict[str, Any]) -> tuple[int, str]:
    require_exact_keys(
        data,
        {"schema_version", "source", "base_forms", "derived_variants", "expected"},
        "manifest",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise CertificateError("schema_version must be the integer 1")

    source = data["source"]
    if not isinstance(source, dict):
        raise CertificateError("source must be an object")
    require_exact_keys(
        source, {"title", "authors", "arxiv", "doi", "table", "formula"}, "source"
    )
    if source["arxiv"] != "1103.1979v1" or source["doi"] != "10.1112/blms/bdr086":
        raise CertificateError("unexpected source locator")
    formula = source["formula"]
    if not isinstance(formula, dict):
        raise CertificateError("source.formula must be an object")
    require_exact_keys(
        formula,
        {"h", "g_denominator", "f_denominator", "identity"},
        "source.formula",
    )
    if (
        formula["g_denominator"] != 132**2
        or formula["f_denominator"] != 240
        or formula["identity"] != "f^2 + g^3 + h^5 = 0"
    ):
        raise CertificateError("formula metadata does not match the audited construction")

    base_forms = data["base_forms"]
    if not isinstance(base_forms, list) or len(base_forms) != 27:
        raise CertificateError("base_forms must contain exactly 27 entries")
    triples: dict[int, tuple[HomogeneousPolynomial, HomogeneousPolynomial, HomogeneousPolynomial]] = {}
    payloads: dict[int, dict[str, Any]] = {}

    for expected_id, entry in enumerate(base_forms, start=1):
        if not isinstance(entry, dict):
            raise CertificateError("base form entry must be an object")
        require_exact_keys(entry, {"id", "alpha"}, f"base form {expected_id}")
        if type(entry["id"]) is not int or entry["id"] != expected_id:
            raise CertificateError(
                f"base form IDs must be exactly 1..27; expected {expected_id}"
            )
        if not isinstance(entry["alpha"], list):
            raise CertificateError(f"base form {expected_id} alpha must be an array")
        alpha = [parse_fraction(value) for value in entry["alpha"]]
        h = dodecic(alpha)
        f, g, h = edwards_covariants(h)
        if (f.degree, g.degree, h.degree) != (30, 20, 12):
            raise CertificateError(f"form {expected_id} has incorrect degrees")
        if not (f.is_integral() and g.is_integral() and h.is_integral()):
            raise CertificateError(f"form {expected_id} has a non-integral coefficient")
        if not (f**2 + g**3 + h**5).is_zero():
            raise CertificateError(
                f"form {expected_id} fails f^2 + g^3 + h^5 = 0"
            )
        triples[expected_id] = (f, g, h)
        payloads[expected_id] = canonical_payload(expected_id, f, g, h)

    variants = data["derived_variants"]
    if not isinstance(variants, list) or len(variants) != 22:
        raise CertificateError("derived_variants must contain exactly 22 entries")
    expected_variant_ids = list(range(28, 50))
    for expected_id, entry in zip(expected_variant_ids, variants):
        if not isinstance(entry, dict):
            raise CertificateError("derived variant entry must be an object")
        require_exact_keys(
            entry, {"id", "source_id", "negate_f"}, f"derived variant {expected_id}"
        )
        if type(entry["id"]) is not int or entry["id"] != expected_id:
            raise CertificateError("derived variant IDs must be exactly 28..49")
        source_id = entry["source_id"]
        if type(source_id) is not int or source_id not in triples:
            raise CertificateError(f"variant {expected_id} has invalid source_id")
        if entry["negate_f"] is not True:
            raise CertificateError(f"variant {expected_id} must negate f")
        f, g, h = triples[source_id]
        f = f.scale(-1)
        if not (f**2 + g**3 + h**5).is_zero():
            raise CertificateError(f"variant {expected_id} fails the Edwards identity")
        payloads[expected_id] = canonical_payload(
            expected_id, f, g, h, source_id=source_id, negate_f=True
        )

    expected_sources = {
        **{i: i - 27 for i in range(28, 30)},
        **{i: i - 25 for i in range(30, 42)},
        **{i: i - 23 for i in range(42, 50)},
    }
    actual_sources = {entry["id"]: entry["source_id"] for entry in variants}
    if actual_sources != expected_sources:
        raise CertificateError("derived variant source mapping does not match the paper")

    expected = data["expected"]
    if not isinstance(expected, dict):
        raise CertificateError("expected must be an object")
    require_exact_keys(expected, {"form_sha256", "family_sha256"}, "expected")
    digests = expected["form_sha256"]
    if not isinstance(digests, dict) or set(digests) != {
        str(i) for i in range(1, 50)
    }:
        raise CertificateError("expected.form_sha256 must cover IDs 1..49 exactly")

    family: list[dict[str, Any]] = []
    for form_id in range(1, 50):
        payload = payloads[form_id]
        digest = sha256_json(payload)
        if digests[str(form_id)] != digest:
            raise CertificateError(
                f"form {form_id} digest mismatch: expected {digests[str(form_id)]}, got {digest}"
            )
        family.append({**payload, "sha256": digest})

    family_digest = sha256_json(family)
    if expected["family_sha256"] != family_digest:
        raise CertificateError(
            "family digest mismatch: "
            f"expected {expected['family_sha256']}, got {family_digest}"
        )
    return len(family), family_digest


def validate(path: pathlib.Path) -> tuple[int, str]:
    return validate_data(load_json(path))


def self_test(path: pathlib.Path) -> None:
    data = load_json(path)

    mutated_coefficient = copy.deepcopy(data)
    mutated_coefficient["base_forms"][0]["alpha"][1] = "2"
    try:
        validate_data(mutated_coefficient)
    except CertificateError:
        pass
    else:
        raise RuntimeError("mutated source coefficient was accepted")

    mutated_variant = copy.deepcopy(data)
    mutated_variant["derived_variants"][0]["source_id"] = 2
    try:
        validate_data(mutated_variant)
    except CertificateError:
        pass
    else:
        raise RuntimeError("mutated variant mapping was accepted")

    mutated_digest = copy.deepcopy(data)
    mutated_digest["expected"]["family_sha256"] = "0" * 64
    try:
        validate_data(mutated_digest)
    except CertificateError:
        pass
    else:
        raise RuntimeError("mutated family digest was accepted")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
        fixture_path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(fixture_path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("duplicate JSON key was accepted")
    finally:
        fixture_path.unlink(missing_ok=True)

    print("signature (3,4,5) Edwards negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        nargs="?",
        type=pathlib.Path,
        default=DEFAULT_MANIFEST,
        help="path to the Edwards manifest",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test(args.manifest)
    count, digest = validate(args.manifest)
    print(f"checked {count} Edwards triples; family sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
