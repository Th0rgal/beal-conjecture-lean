#!/usr/bin/env python3
"""Independent complete-domain reproduction using SymPy.

This module intentionally imports none of the producer or artifact-checker code.
It reconstructs each finite domain from JSON parameters and compares complete
counts/witness sets against the committed producer artifacts.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import sympy
from sympy import factorint, primerange
from sympy.ntheory import n_order

from provenance import artifact_provenance


class ReproductionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReproductionError(message)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ReproductionError(f"cannot read {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path.name} is not a JSON object")
    return value


def valuation(n: int, p: int) -> int:
    require(n > 0 and p > 1, "valuation domain error")
    value = 0
    while n % p == 0:
        n //= p
        value += 1
    return value


def finite_domain_snapshot(params: dict) -> dict:
    """Return the exact finite-field domain consumed by this independent run."""
    kernels = params.get("kernels")
    prime_bound = params.get("prime_bound")
    require(isinstance(kernels, list) and kernels and
            all(isinstance(value, int) and value > 0 for value in kernels),
            "invalid finite-field kernel domain")
    require(isinstance(prime_bound, int) and prime_bound >= 2,
            "invalid finite-field prime bound")
    return {"kernels": list(kernels), "prime_bound": prime_bound}


def lte_domain_snapshot(params: dict) -> dict:
    """Return the exact LTE domain consumed by this independent run."""
    a_bound = params.get("a_bound")
    prime_bound = params.get("prime_bound")
    n_bound = params.get("n_bound")
    require(all(isinstance(value, int) and value >= 1
                for value in (a_bound, prime_bound, n_bound)),
            "invalid LTE domain")
    return {
        "a_bound": a_bound,
        "prime_bound": prime_bound,
        "n_bound": n_bound,
    }


def cyclotomic_domain_snapshot(params: dict) -> dict:
    """Return the exact cyclotomic domain consumed by this independent run."""
    ells = params.get("ells")
    base_bound = params.get("base_bound")
    require(isinstance(ells, list) and ells and
            all(isinstance(value, int) for value in ells),
            "invalid cyclotomic ell domain")
    require(isinstance(base_bound, int) and base_bound >= 1,
            "invalid cyclotomic base bound")
    return {"ells": list(ells), "base_bound": base_bound}


def reproduce_finite(artifact: dict) -> dict:
    params = artifact["parameters"]
    domain = finite_domain_snapshot(params)
    kernels = domain["kernels"]
    primes = [int(value) for value in primerange(2, domain["prime_bound"] + 1)]
    recorded = {
        tuple(row["signature"]): {entry["prime"] for entry in row["support_forcing_primes"]}
        for row in artifact["support_forcing"]
    }
    reproduced: dict[tuple[int, int, int], set[int]] = {}
    checks = empty = 0
    for x in kernels:
        for y in kernels:
            for z in kernels:
                forcing: set[int] = set()
                for q in primes:
                    checks += 1
                    require((pow(0, x, q) + pow(1, y, q) - pow(1, z, q)) % q == 0,
                            "permanent finite-field zero branch failed")
                    hx = {pow(a, x, q) for a in range(1, q)}
                    hy = {pow(b, y, q) for b in range(1, q)}
                    hz = {pow(c, z, q) for c in range(1, q)}
                    has_unit_solution = any((a + b) % q in hz for a in hx for b in hy)
                    if not has_unit_solution:
                        forcing.add(q)
                        empty += 1
                if forcing:
                    reproduced[(x, y, z)] = forcing
    require(checks == artifact["signature_prime_checks"], "finite-field coverage count differs")
    require(empty == artifact["unit_empty_branch_occurrences"], "finite-field empty count differs")
    require(reproduced == recorded, "finite-field witness map differs")
    return {"checks": checks, "empty_witnesses": empty, "domain": domain}


def reproduce_lte(artifact: dict) -> dict:
    params = artifact["parameters"]
    domain = lte_domain_snapshot(params)
    a_bound = domain["a_bound"]
    odd_primes = [int(value) for value in primerange(3, domain["prime_bound"] + 1)]
    odd_ns = range(3, domain["n_bound"] + 1, 2)
    cases = violations = 0
    for q in odd_primes:
        for a in range(1, a_bound + 1):
            for b in range(1, a_bound + 1):
                if math.gcd(a, b) != 1 or (a + b) % q or (a * b) % q == 0:
                    continue
                for n in odd_ns:
                    cases += 1
                    lhs = valuation(a**n + b**n, q)
                    rhs = valuation(a + b, q) + valuation(n, q)
                    violations += lhs != rhs
    require(cases == artifact["valid_hypothesis_cases_tested"], "LTE coverage count differs")
    require(violations == len(artifact["valid_hypothesis_violations"]), "LTE violation count differs")
    require(violations == 0, "independent LTE violation found")
    for case in artifact["minimal_counterexamples_when_assumption_removed"].values():
        if case is None:
            continue
        lhs = valuation(case["a"] ** case["n"] + case["b"] ** case["n"], case["q"])
        rhs = valuation(case["a"] + case["b"], case["q"]) + valuation(case["n"], case["q"])
        require(lhs == case["lhs_valuation"] and rhs == case["rhs_valuation"] and lhs != rhs,
                "recorded LTE counterexample differs")
    return {"cases": cases, "violations": violations, "domain": domain}


def reproduce_cyclotomic(artifact: dict) -> dict:
    params = artifact["parameters"]
    domain = cyclotomic_domain_snapshot(params)
    ells = domain["ells"]
    bound = domain["base_bound"]
    require(len(ells) == len(set(ells)) and all(sympy.isprime(ell) and ell % 2 for ell in ells),
            "cyclotomic ell domain is not distinct odd primes")
    cases = factor_occurrences = exceptional = 0
    high: list[dict] = []
    failures: list[dict] = []
    for ell in ells:
        for u in range(1, bound + 1):
            for v in range(1, bound + 1):
                if math.gcd(u, v) != 1:
                    continue
                cases += 1
                numerator = u**ell + v**ell
                cofactor, remainder = divmod(numerator, u + v)
                if remainder or (u + v) * cofactor != numerator:
                    failures.append({"kind": "identity", "ell": ell, "u": u, "v": v})
                    continue
                if ell % math.gcd(u + v, cofactor):
                    failures.append({"kind": "gcd", "ell": ell, "u": u, "v": v})
                factors = {int(q): int(exponent) for q, exponent in factorint(cofactor).items()}
                factor_occurrences += len(factors)
                for q, exponent in factors.items():
                    require(sympy.isprime(q), "SymPy returned nonprime factor")
                    if q == ell:
                        exceptional += 1
                        continue
                    ratio = (u * pow(v, -1, q)) % q
                    minus_ratio = (-u * pow(v, -1, q)) % q
                    if n_order(ratio, q) != 2 * ell or n_order(minus_ratio, q) != ell:
                        failures.append({"kind": "order", "ell": ell, "u": u, "v": v, "q": q})
                    if (q - 1) % (2 * ell):
                        failures.append({"kind": "congruence", "ell": ell, "u": u, "v": v, "q": q})
                    if exponent > 1:
                        high.append({
                            "ell": ell, "u": u, "v": v, "q": q,
                            "valuation": exponent, "cofactor": str(cofactor),
                        })
    high.sort(key=lambda item: (item["ell"], item["u"], item["v"], item["q"]))
    require(not failures, f"independent cyclotomic failures: {failures[:3]}")
    require(cases == artifact["pairs_tested"], "cyclotomic coverage count differs")
    require(factor_occurrences == artifact["distinct_prime_factor_occurrences_tested"],
            "cyclotomic factor-occurrence count differs")
    require(exceptional == artifact["ell_exception_factor_occurrences"],
            "cyclotomic exceptional count differs")
    require(high == artifact["higher_valuation_cases"], "cyclotomic high-valuation witness list differs")
    return {
        "cases": cases,
        "factor_occurrences": factor_occurrences,
        "exceptional_factor_occurrences": exceptional,
        "higher_valuation_occurrences": len(high),
        "domain": domain,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        finite = reproduce_finite(load(args.results / "finite_field_support.json"))
        lte = reproduce_lte(load(args.results / "lte_assumption_miner.json"))
        cyclo = reproduce_cyclotomic(load(args.results / "cyclotomic_census.json"))
        report = {
            "schema_version": 1,
            "experiment": "independent_complete_domain_reproduction",
            "verification": "passed",
            "sympy_version": sympy.__version__,
            "finite_field_checks_reproduced": finite["checks"],
            "finite_field_empty_witnesses_reproduced": finite["empty_witnesses"],
            "finite_field_domain_reproduced": finite["domain"],
            "lte_cases_reproduced": lte["cases"],
            "lte_violations_reproduced": lte["violations"],
            "lte_domain_reproduced": lte["domain"],
            "cyclotomic_cases_reproduced": cyclo["cases"],
            "cyclotomic_factor_occurrences_reproduced": cyclo["factor_occurrences"],
            "cyclotomic_exceptional_occurrences_reproduced": cyclo["exceptional_factor_occurrences"],
            "cyclotomic_higher_valuation_occurrences_reproduced": cyclo["higher_valuation_occurrences"],
            "cyclotomic_domain_reproduced": cyclo["domain"],
            "elapsed_seconds": time.perf_counter() - started,
            "provenance": artifact_provenance(__file__),
            "scope": "Independent bounded reproduction using SymPy; not Lean certification or an unrestricted theorem.",
        }
        output = args.output or args.results / "independent_reproduction.json"
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
    except ReproductionError as exc:
        raise SystemExit(f"INDEPENDENT REPRODUCTION FAILED: {exc}") from exc


if __name__ == "__main__":
    main()
