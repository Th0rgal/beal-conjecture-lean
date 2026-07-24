#!/usr/bin/env python3
"""Replay the finite arithmetic in the prime-71 closure of the (3,5,7) even branch.

The checker does not reprove the imported modularity, level-lowering, cyclic
base-change, conductor, or fixed-7 ray/Hasse theorems. It validates their pinned
repository inputs and independently recomputes:

* the rational curve invariants and its trace at 71;
* the trace after residue-degree doubling;
* the Jacobi sums defining every u=0 mod-5 HGM trace at 71;
* the reduction of all character classes and Galois embeddings in F_(5^6);
* the incompatibility 3 not in the zero-specialization trace set.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "Research" / "Signature357" / "even_branch_prime71_closure.json"


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


def canonical_digest(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop("certificate_sha256", None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# F_(71^2) = F_71[w]/(w^2-7).
def f71_sub(x: tuple[int, int], y: tuple[int, int]) -> tuple[int, int]:
    return ((x[0] - y[0]) % 71, (x[1] - y[1]) % 71)


def f71_mul(x: tuple[int, int], y: tuple[int, int]) -> tuple[int, int]:
    a, b = x
    c, d = y
    return ((a * c + 7 * b * d) % 71, (a * d + b * c) % 71)


def f71_pow(x: tuple[int, int], exponent: int) -> tuple[int, int]:
    result = (1, 0)
    while exponent:
        if exponent & 1:
            result = f71_mul(result, x)
        x = f71_mul(x, x)
        exponent //= 2
    return result


# F_(5^6) = F_5[z]/(z^6+z^5+z^4+1).
F5_ONE = (1, 0, 0, 0, 0, 0)


def f5_add(x: tuple[int, ...], y: tuple[int, ...]) -> tuple[int, ...]:
    return tuple((x[index] + y[index]) % 5 for index in range(6))


def f5_mul(x: tuple[int, ...], y: tuple[int, ...]) -> tuple[int, ...]:
    coefficients = [0] * 11
    for i, left in enumerate(x):
        for j, right in enumerate(y):
            coefficients[i + j] = (coefficients[i + j] + left * right) % 5
    # z^6 = -z^5-z^4-1.
    for degree in range(10, 5, -1):
        leading = coefficients[degree] % 5
        if leading:
            coefficients[degree] = 0
            for offset in (0, 4, 5):
                coefficients[degree - 6 + offset] = (
                    coefficients[degree - 6 + offset] - leading
                ) % 5
    return tuple(coefficients[:6])


def f5_pow(x: tuple[int, ...], exponent: int) -> tuple[int, ...]:
    result = F5_ONE
    while exponent:
        if exponent & 1:
            result = f5_mul(result, x)
        x = f5_mul(x, x)
        exponent //= 2
    return result


def f5_scale(scalar: int, x: tuple[int, ...]) -> tuple[int, ...]:
    return tuple((scalar * value) % 5 for value in x)


def jacobi_counts(
    logarithm: dict[tuple[int, int], int], left: int, right: int
) -> list[int]:
    counts = [0] * 21
    for x, log_x in logarithm.items():
        one_minus_x = f71_sub((1, 0), x)
        if one_minus_x == (0, 0):
            continue
        exponent = (left * log_x + right * logarithm[one_minus_x]) % 21
        counts[exponent] += 1
    return counts


def legendre(value: int, prime: int) -> int:
    value %= prime
    if value == 0:
        return 0
    symbol = pow(value, (prime - 1) // 2, prime)
    return -1 if symbol == prime - 1 else 1


def elliptic_trace(prime: int, ainvariants: list[int]) -> tuple[int, int]:
    a1, a2, a3, a4, a6 = (value % prime for value in ainvariants)
    points = 1
    for x in range(prime):
        linear = (a1 * x + a3) % prime
        rhs = (x**3 + a2 * x * x + a4 * x + a6) % prime
        discriminant = (linear * linear + 4 * rhs) % prime
        points += 1 + legendre(discriminant, prime)
    return prime + 1 - points, points


def compute_zero_traces() -> dict[str, Any]:
    generator_71 = (1, 1)
    order_71 = 71**2 - 1
    if f71_pow(generator_71, order_71) != (1, 0):
        raise CertificateError("F_71^2 generator has the wrong order")
    for prime_divisor in (2, 3, 5, 7):
        if f71_pow(generator_71, order_71 // prime_divisor) == (1, 0):
            raise CertificateError("F_71^2 generator is not primitive")

    logarithm: dict[tuple[int, int], int] = {}
    value = (1, 0)
    for exponent in range(order_71):
        if value in logarithm:
            raise CertificateError("duplicate discrete logarithm")
        logarithm[value] = exponent
        value = f71_mul(value, generator_71)
    if len(logarithm) != order_71 or value != (1, 0):
        raise CertificateError("F_71^2 logarithm table is incomplete")

    jacobi_1 = jacobi_counts(logarithm, 4, -10)
    jacobi_2 = jacobi_counts(logarithm, -6, 10)
    if sum(jacobi_1) != 71**2 - 2 or sum(jacobi_2) != 71**2 - 2:
        raise CertificateError("Jacobi sums have the wrong number of terms")

    generator_5 = (0, 0, 0, 0, 1, 1)
    order_5 = 5**6 - 1
    if f5_pow(generator_5, order_5) != F5_ONE:
        raise CertificateError("F_5^6 generator has the wrong order")
    for prime_divisor in (2, 3, 7, 31):
        if f5_pow(generator_5, order_5 // prime_divisor) == F5_ONE:
            raise CertificateError("F_5^6 generator is not primitive")

    zeta_21 = f5_pow(generator_5, order_5 // 21)
    if f5_pow(zeta_21, 21) != F5_ONE:
        raise CertificateError("coefficient field lacks the pinned 21st root")
    powers = [f5_pow(zeta_21, exponent) for exponent in range(21)]
    embeddings = [value for value in range(1, 21) if math.gcd(value, 21) == 1]

    traces: set[tuple[int, ...]] = set()
    # Restriction of the order-seven character from F_(71^2) to F_71
    # multiplies its order-seven exponent by 2, giving shifts +/-6*i in
    # zeta_21 coordinates.
    for parameter_class in range(1, 8):
        for automorphism in embeddings:
            total = (0, 0, 0, 0, 0, 0)
            for exponent, count in enumerate(jacobi_1):
                root = powers[(automorphism * (exponent - 6 * parameter_class)) % 21]
                total = f5_add(total, f5_scale(count % 5, root))
            for exponent, count in enumerate(jacobi_2):
                root = powers[(automorphism * (exponent + 6 * parameter_class)) % 21]
                total = f5_add(total, f5_scale(count % 5, root))
            # Jacobi2 has a leading minus sign and q=71^2=1 modulo 5.
            traces.add(tuple((-coordinate) % 5 for coordinate in total))

    scalar_traces = sorted(
        trace[0] for trace in traces if trace[1:] == (0, 0, 0, 0, 0)
    )
    return {
        "jacobi_1_counts": jacobi_1,
        "jacobi_2_counts": jacobi_2,
        "distinct_trace_value_count": len(traces),
        "scalar_trace_residues_mod5": scalar_traces,
    }


def verify_curve(data: dict[str, Any]) -> dict[str, int]:
    curve = data["source_chain"]["base_change_identification"]
    ainvariants = curve["ainvariants"]
    if ainvariants != [1, -1, 0, 9, 0]:
        raise CertificateError("unexpected curve model")
    a1, a2, a3, a4, a6 = ainvariants
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    c4 = b2 * b2 - 24 * b4
    discriminant = -b2 * b2 * b8 - 8 * b4**3 - 27 * b6**2 + 9 * b2 * b4 * b6
    if (b2, b4, b6, b8, c4, discriminant) != (-3, 18, 0, -81, -423, -45927):
        raise CertificateError("curve invariants changed")
    if discriminant != -(3**8) * 7 or c4 != -(3**2) * 47:
        raise CertificateError("curve factorization metadata changed")
    trace, points = elliptic_trace(71, ainvariants)
    return {"trace": trace, "points": points}


def verify_dependency(path: str, expected_digest: str) -> dict[str, Any]:
    value = load(ROOT / path)
    if canonical_digest(value) != value.get("certificate_sha256"):
        raise CertificateError(f"dependency digest invalid: {path}")
    if value["certificate_sha256"] != expected_digest:
        raise CertificateError(f"dependency was not pinned: {path}")
    return value


def validate(data: dict[str, Any]) -> str:
    if data.get("schema_version") != 1 or canonical_digest(data) != data.get("certificate_sha256"):
        raise CertificateError("certificate schema or digest mismatch")
    if data.get("equation") != "A^3+B^5=C^7":
        raise CertificateError("equation mismatch")

    sources = data["source_chain"]
    frontier_meta = sources["branch_frontier"]
    frontier = verify_dependency(frontier_meta["path"], frontier_meta["sha256"])
    if frontier.get("even_branch_remaining_norms") != [5103]:
        raise CertificateError("even branch is not concentrated at 5103")

    hasse_meta = sources["fixed7_prime7_hasse"]
    hasse = verify_dependency(hasse_meta["path"], hasse_meta["sha256"])
    if hasse["scope"]["conclusion"] != "7 divides C":
        raise CertificateError("prime-7 Hasse input changed")

    sieve_meta = sources["fixed7_global_sieve"]
    sieve = verify_dependency(sieve_meta["path"], sieve_meta["sha256"])
    if "71" not in sieve["conclusion"]["forced_divisibility"]:
        raise CertificateError("global fixed-7 sieve no longer forces 71|C")

    magma = sources["level5103_magma"]["facts"]
    if magma != {
        "level_exponents": [2, 1],
        "space_dimension": 73,
        "packet_count": 10,
        "packet_dimensions": [1, 2, 3, 3, 6, 6, 6, 6, 6, 12],
        "norm8_survivors": [1],
        "marginal_local_survivors": [1],
    }:
        raise CertificateError("pinned level-5103 computation changed")
    if magma["packet_dimensions"].count(1) != 1:
        raise CertificateError("level 5103 does not have a unique rational packet")

    curve = verify_curve(data)
    packet = data["packet_trace_at_71"]
    if curve["trace"] != packet["base_trace"] or curve["points"] != packet["curve_point_count"]:
        raise CertificateError("curve point count mismatch")
    if 71 % 7 != 1 or packet["residue_degree_K7"] != 1 or packet["residue_degree_F21"] != 2:
        raise CertificateError("residue-degree metadata changed")
    full_trace = curve["trace"] ** 2 - 2 * 71
    if full_trace != packet["full_trace"] or full_trace % 5 != packet["full_trace_mod5"]:
        raise CertificateError("full-cyclotomic trace mismatch")

    computed = compute_zero_traces()
    zero = data["zero_hgm_computation"]
    for key in ("jacobi_1_counts", "jacobi_2_counts", "distinct_trace_value_count", "scalar_trace_residues_mod5"):
        if computed[key] != zero[key]:
            raise CertificateError(f"zero-HGM computation mismatch: {key}")
    target = packet["full_trace_mod5"]
    if zero["target_trace_mod5"] != target or zero["target_absent"] is not True:
        raise CertificateError("target exclusion metadata mismatch")
    if target in computed["scalar_trace_residues_mod5"]:
        raise CertificateError("packet trace survives the zero HGM trace set")
    if data["conclusion"]["result"] != "the Dahmen--Siksek even branch is empty":
        raise CertificateError("even-branch conclusion mismatch")
    if "imported results" not in data["nonclaim"] or "not a proof of the odd branch" not in data["nonclaim"]:
        raise CertificateError("trust-boundary statement missing")
    return data["certificate_sha256"]


def expect_rejection(data: dict[str, Any], label: str) -> None:
    data["certificate_sha256"] = canonical_digest(data)
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {label}")


def self_test() -> None:
    base = load(DEFAULT)
    validate(base)
    mutated = copy.deepcopy(base)
    mutated["packet_trace_at_71"]["full_trace_mod5"] = 4
    expect_rejection(mutated, "the wrong packet trace")
    mutated = copy.deepcopy(base)
    mutated["zero_hgm_computation"]["scalar_trace_residues_mod5"] = [3, 4]
    expect_rejection(mutated, "a reintroduced zero-HGM trace")
    mutated = copy.deepcopy(base)
    mutated["source_chain"]["level5103_magma"]["facts"]["marginal_local_survivors"] = [1, 2]
    expect_rejection(mutated, "a weakened level-5103 frontier")
    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        handle.write('{"schema_version":1,"schema_version":1}')
        path = pathlib.Path(handle.name)
    try:
        try:
            load(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)
    print("even-branch prime-71 closure negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    certificate = validate(load(args.manifest))
    print("signature (3,5,7) even-branch prime-71 closure valid")
    print("  level 5103 has one marginal packet")
    print("  71|C forces u=0")
    print("  packet full trace: 3 mod 5")
    print("  zero-HGM scalar trace set: {4}")
    print("  even branch: empty")
    print(f"  certificate sha256: {certificate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
