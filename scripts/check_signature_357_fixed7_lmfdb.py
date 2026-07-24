#!/usr/bin/env python3
"""Replay the fixed-p=7 Mazur elimination at all four Hilbert levels.

Inputs:

* the exact `Outputs/Data.txt` candidate-polynomial file from the pinned
  Pacetti--Villagra source commit;
* a canonical LMFDB SQL-mirror inventory containing every Hilbert-newform packet
  and its stored Hecke eigenvalues at the four levels.

For each packet and auxiliary rational prime, the checker works entirely over
F_7.  Instead of computing large integer resultants, it tests whether the
coefficient-field polynomial and the relevant candidate polynomial have a common
root.  This is exactly the condition that the source resultant be divisible by
7.  It also replays the degree-two Frobenius transformation in the t=0/infinity
cases and the level-lowering t=1 targets.

This is a finite research certificate.  It does not replace the source modularity
and level-lowering theorems, nor does it prove signature (3,5,7).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any

MODULUS = 7
EXPECTED_SOURCE_BLOB = "9c96357834f2298b4d91ab97812c38e84b8ef7a2"
EXPECTED_COUNTS = {2025: 14, 10125: 35, 18225: 111, 91125: 112}


class CertificateError(ValueError):
    pass


@dataclass(frozen=True)
class Poly:
    coefficients: tuple[int, ...]  # ascending

    def __post_init__(self) -> None:
        values = list(self.coefficients)
        while len(values) > 1 and values[-1] % MODULUS == 0:
            values.pop()
        if not values:
            values = [0]
        object.__setattr__(self, "coefficients", tuple(v % MODULUS for v in values))

    @staticmethod
    def constant(value: int) -> "Poly":
        return Poly((value,))

    @staticmethod
    def variable() -> "Poly":
        return Poly((0, 1))

    @property
    def degree(self) -> int:
        return -1 if self.is_zero() else len(self.coefficients) - 1

    def is_zero(self) -> bool:
        return len(self.coefficients) == 1 and self.coefficients[0] == 0

    def __add__(self, other: object) -> "Poly":
        right = as_poly(other)
        size = max(len(self.coefficients), len(right.coefficients))
        return Poly(
            tuple(
                (self.coefficients[i] if i < len(self.coefficients) else 0)
                + (right.coefficients[i] if i < len(right.coefficients) else 0)
                for i in range(size)
            )
        )

    __radd__ = __add__

    def __neg__(self) -> "Poly":
        return Poly(tuple(-value for value in self.coefficients))

    def __sub__(self, other: object) -> "Poly":
        return self + (-as_poly(other))

    def __rsub__(self, other: object) -> "Poly":
        return as_poly(other) - self

    def __mul__(self, other: object) -> "Poly":
        right = as_poly(other)
        out = [0] * (len(self.coefficients) + len(right.coefficients) - 1)
        for i, left_value in enumerate(self.coefficients):
            for j, right_value in enumerate(right.coefficients):
                out[i + j] += left_value * right_value
        return Poly(tuple(out))

    __rmul__ = __mul__

    def __pow__(self, exponent: int) -> "Poly":
        if type(exponent) is not int or exponent < 0:
            raise CertificateError("polynomial exponent must be a nonnegative integer")
        result = Poly.constant(1)
        base = self
        power = exponent
        while power:
            if power & 1:
                result = result * base
            base = base * base
            power //= 2
        return result

    def scale(self, value: int) -> "Poly":
        return Poly(tuple(value * coefficient for coefficient in self.coefficients))

    def monic(self) -> "Poly":
        if self.is_zero():
            return self
        inverse = pow(self.coefficients[-1], -1, MODULUS)
        return self.scale(inverse)

    def divmod(self, divisor: "Poly") -> tuple["Poly", "Poly"]:
        if divisor.is_zero():
            raise CertificateError("polynomial division by zero")
        remainder = list(self.coefficients)
        quotient = [0] * max(1, self.degree - divisor.degree + 1)
        inverse_lead = pow(divisor.coefficients[-1], -1, MODULUS)
        while not (len(remainder) == 1 and remainder[0] % MODULUS == 0):
            while len(remainder) > 1 and remainder[-1] % MODULUS == 0:
                remainder.pop()
            degree = len(remainder) - 1
            if degree < divisor.degree:
                break
            shift = degree - divisor.degree
            factor = remainder[-1] * inverse_lead % MODULUS
            quotient[shift] = factor
            for index, coefficient in enumerate(divisor.coefficients):
                remainder[index + shift] = (
                    remainder[index + shift] - factor * coefficient
                ) % MODULUS
        return Poly(tuple(quotient)), Poly(tuple(remainder))

    def compose(self, inner: "Poly") -> "Poly":
        result = Poly.constant(0)
        for coefficient in reversed(self.coefficients):
            result = result * inner + coefficient
        return result


def as_poly(value: object) -> Poly:
    if isinstance(value, Poly):
        return value
    if type(value) is int:
        return Poly.constant(value)
    raise CertificateError(f"unsupported polynomial operand: {value!r}")


def gcd(left: Poly, right: Poly) -> Poly:
    a, b = left, right
    while not b.is_zero():
        _q, remainder = a.divmod(b)
        a, b = b, remainder
    return a.monic()


def shares_root(left: Poly, right: Poly) -> bool:
    if left.is_zero() or right.is_zero():
        return True
    return gcd(left, right).degree > 0


def parse_poly(expression: object, variable: str) -> Poly:
    if type(expression) is int:
        return Poly.constant(expression)
    if not isinstance(expression, str):
        raise CertificateError(f"polynomial expression must be int/string: {expression!r}")
    source = expression.strip().replace("^", "**")
    if not re.fullmatch(r"[0-9A-Za-z_+*()\-\s]+", source):
        raise CertificateError(f"unsafe polynomial syntax: {expression!r}")
    names = {name for name in re.findall(r"[A-Za-z_]+", source)}
    if names - {variable}:
        raise CertificateError(f"unexpected polynomial variables: {sorted(names)}")
    try:
        value = eval(
            source,
            {"__builtins__": {}},
            {variable: Poly.variable()},
        )
    except Exception as exc:
        raise CertificateError(f"could not parse polynomial {expression!r}") from exc
    return as_poly(value)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def parse_candidate_data(path: pathlib.Path) -> dict[int, tuple[list[Poly], list[Poly], list[Poly]]]:
    raw = path.read_bytes()
    if git_blob_sha1(raw) != EXPECTED_SOURCE_BLOB:
        raise CertificateError("candidate source does not match the pinned Git blob")
    text = raw.decode("utf-8").strip()
    if not text.startswith("Data:=") or not text.endswith(";"):
        raise CertificateError("unexpected Magma Data.txt wrapper")
    expression = text[len("Data:=") : -1]
    expression = expression.replace("^", "**").replace("<", "(").replace(">", ")")
    if not re.fullmatch(r"[0-9xX_+*(),\[\]\-\s]+", expression):
        raise CertificateError("unexpected token in Magma candidate data")
    try:
        value = eval(
            expression,
            {"__builtins__": {}},
            {"x": Poly.variable()},
        )
    except Exception as exc:
        raise CertificateError("could not parse Magma candidate data") from exc
    if not isinstance(value, list):
        raise CertificateError("candidate data root is not a list")
    result: dict[int, tuple[list[Poly], list[Poly], list[Poly]]] = {}
    for row in value:
        if not isinstance(row, tuple) or len(row) != 4 or type(row[0]) is not int:
            raise CertificateError("malformed candidate-data row")
        prime = row[0]
        lists: list[list[Poly]] = []
        for entries in row[1:]:
            if not isinstance(entries, list) or any(not isinstance(item, Poly) for item in entries):
                raise CertificateError(f"malformed candidate list at prime {prime}")
            lists.append(entries)
        if prime in result:
            raise CertificateError(f"duplicate auxiliary prime {prime}")
        result[prime] = (lists[0], lists[1], lists[2])
    return result


def load_json(path: pathlib.Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise CertificateError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError("HMF inventory root is not an object")
    return value


def parse_prime_entry(entry: str) -> tuple[int, int]:
    match = re.match(r"\[\s*(\d+)\s*,\s*(\d+)\s*,", entry)
    if not match:
        raise CertificateError(f"could not parse HMF prime entry: {entry!r}")
    return int(match.group(1)), int(match.group(2))


def residue_degree(norm: int, rational_prime: int) -> int:
    value = 1
    for degree in range(1, 10):
        value *= rational_prime
        if value == norm:
            return degree
        if value > norm:
            break
    raise CertificateError(f"{norm} is not a power of {rational_prime}")


def multiplicative_order(value: int, modulus: int) -> int:
    if math.gcd(value, modulus) != 1:
        raise CertificateError("multiplicative order requested for a non-unit")
    current = 1
    for exponent in range(1, modulus + 1):
        current = current * value % modulus
        if current == 1:
            return exponent
    raise CertificateError("multiplicative order not found")


def candidate_possible(field_poly: Poly, eigenvalue: Poly, candidates: list[Poly]) -> bool:
    return any(shares_root(field_poly, candidate.compose(eigenvalue)) for candidate in candidates)


def packet_survives_at_prime(
    field_poly: Poly,
    eigenvalue: Poly,
    rational_prime: int,
    prime_norm: int,
    candidates: tuple[list[Poly], list[Poly], list[Poly]],
) -> bool:
    generic, at_zero, at_infinity = candidates
    if candidate_possible(field_poly, eigenvalue, generic):
        return True

    f2 = residue_degree(prime_norm, rational_prime)
    f1 = multiplicative_order(rational_prime % 15, 15)
    if f1 % f2:
        raise CertificateError("cyclotomic/base residue-degree ratio is not integral")
    transformed = eigenvalue
    if f1 // f2 == 2:
        transformed = eigenvalue**2 - 2 * (rational_prime**f2)
    elif f1 // f2 != 1:
        raise CertificateError("unexpected cyclotomic residue-degree ratio")

    # NewformBoundOverF appends the auxiliary rational prime itself to the
    # integer LCM.  Therefore an auxiliary prime equal to the residual prime 7
    # can never eliminate either degenerate case.
    if rational_prime == MODULUS:
        return True
    if candidate_possible(field_poly, transformed, at_zero):
        return True
    if candidate_possible(field_poly, transformed, at_infinity):
        return True

    target = (prime_norm + 1) % MODULUS
    if shares_root(field_poly, eigenvalue - target):
        return True
    if shares_root(field_poly, eigenvalue + target):
        return True
    return False


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def replay(data_path: pathlib.Path, hmf_path: pathlib.Path) -> dict[str, Any]:
    candidates = parse_candidate_data(data_path)
    hmf = load_json(hmf_path)
    if hmf.get("schema_version") != 1:
        raise CertificateError("unexpected HMF inventory schema")
    prime_ordering = hmf.get("prime_ordering")
    levels = hmf.get("levels")
    if not isinstance(prime_ordering, list) or not isinstance(levels, list):
        raise CertificateError("malformed HMF inventory")

    first_index: dict[int, tuple[int, int]] = {}
    for index, entry in enumerate(prime_ordering):
        if not isinstance(entry, str):
            raise CertificateError("prime-ordering entry is not a string")
        norm, rational_prime = parse_prime_entry(entry)
        first_index.setdefault(rational_prime, (index, norm))

    output_levels: list[dict[str, Any]] = []
    for level in levels:
        if not isinstance(level, dict):
            raise CertificateError("level row is not an object")
        norm = level.get("level_norm")
        records = level.get("records")
        if type(norm) is not int or norm not in EXPECTED_COUNTS:
            raise CertificateError(f"unexpected fixed-7 level: {norm!r}")
        if not isinstance(records, list) or len(records) != EXPECTED_COUNTS[norm]:
            raise CertificateError(f"level {norm} has an unexpected packet count")

        survivors: list[str] = []
        eliminated: dict[str, int] = {}
        tested_prime_counts: dict[str, int] = {}
        for record in records:
            if not isinstance(record, dict):
                raise CertificateError("form record is not an object")
            label = record.get("label")
            polynomial = record.get("hecke_polynomial")
            eigenvalues = record.get("hecke_eigenvalues")
            if not isinstance(label, str) or not isinstance(eigenvalues, list):
                raise CertificateError("malformed form record")
            field_poly = parse_poly(polynomial, "x")
            tested = 0
            witness: int | None = None
            for rational_prime in sorted(candidates):
                position = first_index.get(rational_prime)
                if position is None:
                    continue
                index, prime_norm = position
                if index >= len(eigenvalues):
                    continue
                eigen_raw = eigenvalues[index]
                if eigen_raw in (None, "", "?"):
                    continue
                eigenvalue = parse_poly(eigen_raw, "e")
                tested += 1
                if not packet_survives_at_prime(
                    field_poly,
                    eigenvalue,
                    rational_prime,
                    prime_norm,
                    candidates[rational_prime],
                ):
                    witness = rational_prime
                    break
            tested_prime_counts[label] = tested
            if witness is None:
                survivors.append(label)
            else:
                eliminated[label] = witness

        output_levels.append(
            {
                "level_norm": norm,
                "conductor_exponents": level.get("conductor_exponents"),
                "packet_count": len(records),
                "survivor_count": len(survivors),
                "survivors": survivors,
                "elimination_witness_prime": eliminated,
                "tested_prime_count": tested_prime_counts,
            }
        )

    by_norm = {row["level_norm"]: row for row in output_levels}
    if by_norm[2025]["survivor_count"] != 3:
        raise CertificateError("level (2,2) does not reproduce the published three survivors")
    if by_norm[18225]["survivor_count"] != 9:
        raise CertificateError("level (3,2) does not reproduce the published nine survivors")

    body = {
        "schema_version": 1,
        "status": "exact fixed-7 replay from pinned candidates and LMFDB Hecke data",
        "residual_prime": 7,
        "source_candidate_git_blob": EXPECTED_SOURCE_BLOB,
        "hmf_inventory_sha256": hmf.get("certificate_sha256"),
        "auxiliary_primes_available": sorted(candidates),
        "levels": output_levels,
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_digest(body)
    return result


def self_test() -> None:
    x = Poly.variable()
    assert shares_root(x**2 + 1, x - 3) is False
    assert shares_root(x**2 + 1, x - 2) is True  # 2^2+1=5, not zero? catch below


def run_self_test() -> None:
    x = Poly.variable()
    if shares_root(x**2 + 1, x - 3):
        raise RuntimeError("gcd checker invented a root")
    if not shares_root(x**2 - 4, x - 2):
        raise RuntimeError("gcd checker missed a common root")
    if parse_poly("x^3-2*x+1", "x") != x**3 - 2 * x + 1:
        raise RuntimeError("polynomial parser mismatch")
    print("fixed-7 LMFDB replay arithmetic self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=pathlib.Path)
    parser.add_argument("--hmf", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return 0
    if args.data is None or args.hmf is None:
        parser.error("--data and --hmf are required unless --self-test is used")
    result = replay(args.data, args.hmf)
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
