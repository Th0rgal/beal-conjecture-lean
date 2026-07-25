#!/usr/bin/env python3
"""Replay the prime-7 local certificate for the (3,5,7) Frey curve.

This checker uses only Python's standard library. It verifies:
- the exact completed-square identity for the Pacetti--Villagra Frey model;
- the odd-branch reduction modulo 7;
- square-freeness of the resulting sextic for every B in F_7^*;
- vanishing of the four Cartier--Manin coefficients;
- exact point counts over F_7 and F_49;
- the genus-2 Weil polynomial and the induced RM constituent trace.

It also validates the audited even-branch reduction metadata. The checker does
not prove the Dahmen--Siksek dichotomy, modularity, residual irreducibility, or
the local-global compatibility theorem needed to eliminate Hilbert newforms.
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
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "prime7_local.json"
P = 7


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


# Sparse multivariate polynomials in (x, y, A, B).
Monomial = tuple[int, int, int, int]
Polynomial = dict[Monomial, int]


def poly_var(index: int) -> Polynomial:
    exponent = [0, 0, 0, 0]
    exponent[index] = 1
    return {tuple(exponent): 1}


def poly_const(value: int) -> Polynomial:
    return {} if value == 0 else {(0, 0, 0, 0): value}


def poly_add(left: Polynomial, right: Polynomial) -> Polynomial:
    out = dict(left)
    for monomial, coefficient in right.items():
        out[monomial] = out.get(monomial, 0) + coefficient
        if out[monomial] == 0:
            del out[monomial]
    return out


def poly_neg(value: Polynomial) -> Polynomial:
    return {monomial: -coefficient for monomial, coefficient in value.items()}


def poly_sub(left: Polynomial, right: Polynomial) -> Polynomial:
    return poly_add(left, poly_neg(right))


def poly_mul(left: Polynomial, right: Polynomial) -> Polynomial:
    out: Polynomial = {}
    for a, ca in left.items():
        for b, cb in right.items():
            monomial = tuple(x + y for x, y in zip(a, b))
            out[monomial] = out.get(monomial, 0) + ca * cb
            if out[monomial] == 0:
                del out[monomial]
    return out


def poly_scale(value: Polynomial, scalar: int) -> Polynomial:
    return {} if scalar == 0 else {m: scalar * c for m, c in value.items()}


def poly_pow(value: Polynomial, exponent: int) -> Polynomial:
    if exponent < 0:
        raise CertificateError("negative polynomial exponent")
    result = poly_const(1)
    base = value
    power = exponent
    while power:
        if power & 1:
            result = poly_mul(result, base)
        base = poly_mul(base, base)
        power //= 2
    return result


def verify_completed_square_identity() -> None:
    x = poly_var(0)
    y = poly_var(1)
    A = poly_var(2)
    B = poly_var(3)
    x3 = poly_pow(x, 3)
    x6 = poly_pow(x, 6)
    Bx3 = poly_mul(B, x3)
    Ax = poly_mul(A, x)
    B2 = poly_pow(B, 2)

    completed = poly_add(poly_add(poly_scale(y, 2), x3), B)
    target = poly_add(
        poly_add(poly_add(x6, poly_scale(Bx3, 10)), poly_scale(Ax, 12)),
        poly_scale(B2, 5),
    )
    left = poly_sub(poly_pow(completed, 2), target)

    original = poly_sub(
        poly_add(poly_pow(y, 2), poly_mul(y, poly_add(x3, B))),
        poly_add(poly_add(poly_scale(Bx3, 2), poly_scale(Ax, 3)), B2),
    )
    right = poly_scale(original, 4)
    if left != right:
        raise CertificateError("completed-square identity failed")


def univariate_mul_mod(left: list[int], right: list[int], modulus: int) -> list[int]:
    out = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            out[i + j] = (out[i + j] + a * b) % modulus
    return out


def univariate_pow_mod(value: list[int], exponent: int, modulus: int) -> list[int]:
    result = [1]
    base = value
    power = exponent
    while power:
        if power & 1:
            result = univariate_mul_mod(result, base, modulus)
        base = univariate_mul_mod(base, base, modulus)
        power //= 2
    return result


def eval_sextic_mod7(x: int, B: int) -> int:
    return (pow(x, 6, P) + 3 * B * pow(x, 3, P) + 5 * B * B) % P


def derivative_sextic_mod7(x: int, B: int) -> int:
    return (6 * pow(x, 5, P) + 9 * B * pow(x, 2, P)) % P


def legendre_symbol(value: int) -> int:
    value %= P
    if value == 0:
        return 0
    return 1 if pow(value, (P - 1) // 2, P) == 1 else -1


# F_49 = F_7[w]/(w^2+1); -1 is nonsquare modulo 7.
F49 = tuple[int, int]


def f49_add(left: F49, right: F49) -> F49:
    return ((left[0] + right[0]) % P, (left[1] + right[1]) % P)


def f49_mul(left: F49, right: F49) -> F49:
    a, b = left
    c, d = right
    return ((a * c - b * d) % P, (a * d + b * c) % P)


def f49_pow(value: F49, exponent: int) -> F49:
    result: F49 = (1, 0)
    base = value
    power = exponent
    while power:
        if power & 1:
            result = f49_mul(result, base)
        base = f49_mul(base, base)
        power //= 2
    return result


def f49_character(value: F49) -> int:
    if value == (0, 0):
        return 0
    return 1 if f49_pow(value, 24) == (1, 0) else -1


def f49_scalar(value: int) -> F49:
    return (value % P, 0)


def eval_sextic_f49(x: F49, B: int) -> F49:
    x3 = f49_pow(x, 3)
    x6 = f49_mul(x3, x3)
    return f49_add(
        f49_add(x6, f49_mul(f49_scalar(3 * B), x3)),
        f49_scalar(5 * B * B),
    )


def count_points_f7(B: int) -> int:
    # Even-degree monic sextic: two rational points at infinity.
    return P + sum(legendre_symbol(eval_sextic_mod7(x, B)) for x in range(P)) + 2


def count_points_f49(B: int) -> int:
    elements = [(a, b) for a in range(P) for b in range(P)]
    return 49 + sum(f49_character(eval_sextic_f49(x, B)) for x in elements) + 2


def canonical_rows(rows: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        {"rows": rows}, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def computed_row(B: int) -> dict[str, Any]:
    for x in range(P):
        if eval_sextic_mod7(x, B) == 0 and derivative_sextic_mod7(x, B) == 0:
            raise CertificateError(f"reduced sextic is not squarefree for B={B}")

    sextic = [5 * B * B % P, 0, 0, 3 * B % P, 0, 0, 1]
    cube = univariate_pow_mod(sextic, 3, P)
    cartier_exponents = [5, 6, 12, 13]
    cartier = [cube[e] if e < len(cube) else 0 for e in cartier_exponents]
    if cartier != [0, 0, 0, 0]:
        raise CertificateError(
            f"Cartier--Manin coefficients do not vanish for B={B}: {cartier}"
        )

    n1 = count_points_f7(B)
    n2 = count_points_f49(B)
    a1 = P + 1 - n1
    if a1 != 0:
        raise CertificateError(f"unexpected F_7 trace for B={B}: {a1}")
    numerator = n2 - P * P - 1
    if numerator % 2:
        raise CertificateError("nonintegral genus-2 Weil coefficient")
    a2 = numerator // 2
    full_f49_trace = P * P + 1 - n2
    if full_f49_trace % 2:
        raise CertificateError("F_49 trace does not split into two RM constituents")
    rm_trace = full_f49_trace // 2
    return {
        "B_mod_7": B,
        "points_F7": n1,
        "points_F49": n2,
        "weil_polynomial": [1, -a1, a2, -P * a1, P * P],
        "rm_constituent_trace_at_prime_over_7": rm_trace,
    }


def validate_metadata(data: dict[str, Any]) -> None:
    require_exact_keys(
        data,
        {"schema_version", "sources", "branch_audit", "field_model", "expected"},
        "manifest",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise CertificateError("schema_version must be the integer 1")

    sources = data["sources"]
    if not isinstance(sources, dict):
        raise CertificateError("sources must be an object")
    require_exact_keys(sources, {"dahmen_siksek", "pacetti_villagra"}, "sources")
    ds = sources["dahmen_siksek"]
    pv = sources["pacetti_villagra"]
    require_exact_keys(
        ds, {"title", "url", "theorem", "orientation"}, "Dahmen--Siksek source"
    )
    require_exact_keys(pv, {"arxiv", "frey_model"}, "Pacetti--Villagra source")
    if (
        ds["title"] != "On the generalized Fermat equation x^5 + y^3 = z^7"
        or ds["url"] != "https://few.vu.nl/~sdn249/GFE357.pdf"
        or ds["theorem"] != "Theorem 1"
        or ds["orientation"] != "x=B, y=A, z=C for A^3+B^5=C^7"
        or pv["arxiv"] != "2512.17845"
        or pv["frey_model"]
        != "y^2 + y*(x^3+B) = 2*B*x^3 + 3*A*x + B^2"
    ):
        raise CertificateError("source metadata does not match the audited statements")

    branches = data["branch_audit"]
    require_exact_keys(branches, {"even", "odd"}, "branch_audit")
    even = branches["even"]
    odd = branches["odd"]
    require_exact_keys(
        even,
        {
            "necessary_conditions",
            "pvt_orientation",
            "forced_level_exponents",
            "fixed7_survivors",
            "certified_conclusion",
        },
        "even branch",
    )
    require_exact_keys(
        odd,
        {
            "necessary_conditions",
            "completed_square_variable",
            "integral_model",
            "reduced_model_mod_7",
            "required_local_filter",
        },
        "odd branch",
    )
    if (
        even["necessary_conditions"] != ["30|C", "7∤A*B"]
        or even["pvt_orientation"] != ["a=B", "b=-C", "c=A", "p=7"]
        or even["forced_level_exponents"] != [2, 2]
        or even["fixed7_survivors"] != [3, 9, 12]
        or even["certified_conclusion"]
        != "an even-branch primitive solution can exist only if the associated residual mod-7 representation is reducible"
        or odd["necessary_conditions"]
        != ["C odd", "3∤A*B*C", "5∤A*C", "7|A"]
        or odd["completed_square_variable"] != "Y=2*y+x^3+B"
        or odd["integral_model"] != "Y^2=x^6+10*B*x^3+12*A*x+5*B^2"
        or odd["reduced_model_mod_7"] != "Y^2=x^6+3*B*x^3+5*B^2"
        or odd["required_local_filter"]
        != "a_p ≡ 0 mod p at the unique prime p over 7 in Q(sqrt(5))"
    ):
        raise CertificateError("branch metadata does not match the audited reduction")

    field_model = data["field_model"]
    require_exact_keys(
        field_model,
        {
            "prime",
            "quadratic_extension",
            "points_at_infinity",
            "cartier_manin_exponents",
        },
        "field_model",
    )
    if field_model != {
        "prime": 7,
        "quadratic_extension": "F_7[w]/(w^2+1)",
        "points_at_infinity": 2,
        "cartier_manin_exponents": [5, 6, 12, 13],
    }:
        raise CertificateError("unexpected finite-field model")


def validate_data(data: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    validate_metadata(data)
    verify_completed_square_identity()
    expected = data["expected"]
    require_exact_keys(expected, {"rows", "family_sha256"}, "expected")
    if not isinstance(expected["rows"], list) or len(expected["rows"]) != 6:
        raise CertificateError("expected.rows must contain the six nonzero B residues")
    actual = [computed_row(B) for B in range(1, 7)]
    if expected["rows"] != actual:
        raise CertificateError("point-count/local-type table does not match exact replay")
    digest = canonical_rows(actual)
    if expected["family_sha256"] != digest:
        raise CertificateError(
            f"family digest mismatch: expected {expected['family_sha256']}, got {digest}"
        )
    if any(row["rm_constituent_trace_at_prime_over_7"] % 7 for row in actual):
        raise CertificateError("the RM local trace is not divisible by 7")
    return actual, digest


def validate(path: pathlib.Path) -> tuple[list[dict[str, Any]], str]:
    return validate_data(load_json(path))


def self_test() -> None:
    base = load_json(DEFAULT_MANIFEST)

    mutated = copy.deepcopy(base)
    mutated["expected"]["rows"][0]["points_F49"] += 1
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated point count")

    mutated = copy.deepcopy(base)
    mutated["branch_audit"]["odd"]["necessary_conditions"][-1] = "7∤A"
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated branch condition")

    mutated = copy.deepcopy(base)
    mutated["expected"]["family_sha256"] = "0" * 64
    try:
        validate_data(mutated)
    except CertificateError:
        pass
    else:
        raise RuntimeError("checker accepted a mutated family digest")

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

    print("prime-7 local negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    rows, digest = validate(args.manifest)
    print("signature (3,5,7) prime-7 local certificate passed")
    print(f"  residues checked: {len(rows)}")
    print("  Cartier--Manin matrices: zero for every B in F_7^*")
    print("  F_7 point counts: 8 for every nonzero B")
    print("  F_49 point counts: 22 for B=±2, 64 otherwise")
    print("  RM traces at the prime over 7: 14 for B=±2, -7 otherwise")
    print(f"  family sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
