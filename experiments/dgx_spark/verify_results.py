#!/usr/bin/env python3
"""Independent lightweight checker for DGX experiment result artifacts."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from finite_field_support import unit_solution_count
from lte_assumption_miner import lte_holds, valuation


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def cyclotomic_plus_cofactor(u: int, v: int, ell: int) -> int:
    numerator = pow(u, ell) + pow(v, ell)
    denominator = u + v
    assert numerator % denominator == 0
    return numerator // denominator


def check(results: Path) -> dict:
    finite = json.loads((results / "finite_field_support.json").read_text())
    lte = json.loads((results / "lte_assumption_miner.json").read_text())
    cyclo = json.loads((results / "cyclotomic_census.json").read_text())

    finite_rows = 0
    for row in finite["support_forcing"]:
        x, y, z = row["signature"]
        for witness in row["support_forcing_primes"]:
            q = witness["prime"]
            assert is_prime(q)
            assert unit_solution_count(q, x, y, z) == 0
            assert (pow(0, x, q) + pow(1, y, q) - pow(1, z, q)) % q == 0
            finite_rows += 1
    assert finite_rows == finite["unit_empty_branch_occurrences"]
    assert not finite["zero_branch_failures"]

    assert not lte["valid_hypothesis_violations"]
    lte_counterexamples = 0
    for case in lte["minimal_counterexamples_when_assumption_removed"].values():
        if case is None:
            continue
        assert not lte_holds(case["q"], case["a"], case["b"], case["n"])
        assert valuation(case["a"] ** case["n"] + case["b"] ** case["n"], case["q"]) == case["lhs_valuation"]
        lte_counterexamples += 1

    for key in ("factor_identity_failures", "gcd_failures", "order_failures", "congruence_failures"):
        assert not cyclo[key]
    higher_cases = cyclo["higher_valuation_cases"]
    assert len(higher_cases) == cyclo["higher_valuation_occurrences"]
    for case in higher_cases:
        ell, u, v, q, exponent = (case[k] for k in ("ell", "u", "v", "q", "valuation"))
        assert is_prime(ell) and is_prime(q)
        cofactor = cyclotomic_plus_cofactor(u, v, ell)
        assert str(cofactor) == case["cofactor"]
        assert math.gcd(u, v) == 1
        assert pow(q, exponent) <= cofactor and cofactor % pow(q, exponent) == 0
        assert cofactor % pow(q, exponent + 1) != 0
        assert q != ell
        ratio = (u * pow(v, -1, q)) % q
        # ell is prime in this experiment. ratio^ell = -1 and ratio != -1
        # certify exact order 2*ell without reusing the producer's order routine.
        assert pow(ratio, ell, q) == q - 1
        assert ratio != q - 1
        assert (q - 1) % (2 * ell) == 0

    cuda_checked = False
    cuda_path = results / "cuda_modexp_calibration.json"
    if cuda_path.exists():
        cuda = json.loads(cuda_path.read_text())
        assert cuda["mismatches"] == 0
        assert cuda["compute_capability"] == "12.1"
        assert cuda["count"] > 0 and cuda["repeats"] > 0
        cuda_checked = True

    shared_checked = False
    shared_path = results / "gpu_shared_residency_probe.json"
    if shared_path.exists():
        shared = json.loads(shared_path.read_text())
        assert shared["exit_code"] != 0
        assert "out of memory" in shared["stderr"].lower()
        assert shared["vllm_container_status"] == "running"
        shared_checked = True

    return {
        "schema_version": 1,
        "verification": "passed",
        "finite_field_support_witnesses_replayed": finite_rows,
        "lte_counterexamples_replayed": lte_counterexamples,
        "cyclotomic_higher_valuation_cases_replayed": len(higher_cases),
        "primality_checks": finite_rows + 2 * len(higher_cases),
        "cuda_differential_result_checked": cuda_checked,
        "shared_residency_failure_checked": shared_checked,
        "scope": "Artifact consistency and witness replay; does not prove unrestricted claims or replace Lean certification.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = check(args.results)
    output = args.output or args.results / "verification_report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
