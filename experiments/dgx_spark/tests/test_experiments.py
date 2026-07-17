import math
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from cyclotomic_census import (
    cyclotomic_plus_cofactor,
    multiplicative_order,
    validate_ells,
    valuation,
)
from finite_field_support import power_subgroup, unit_solution_count
from lte_assumption_miner import lte_holds
from verify_results import VerificationError, check, is_prime


def test_cyclotomic_plus_cofactor_exact_identity():
    for ell in (3, 5, 7):
        for u in range(1, 8):
            for v in range(1, 8):
                q = cyclotomic_plus_cofactor(u, v, ell)
                assert (u + v) * q == u**ell + v**ell


def test_cyclotomic_gcd_and_order_examples():
    assert cyclotomic_plus_cofactor(3, 1, 3) == 7
    assert math.gcd(3 + 1, cyclotomic_plus_cofactor(3, 1, 3)) == 1
    assert multiplicative_order((3 * pow(1, -1, 7)) % 7, 7) == 6
    assert multiplicative_order((-3 * pow(1, -1, 7)) % 7, 7) == 3
    assert valuation(cyclotomic_plus_cofactor(3, 1, 3), 7) == 1


def test_finite_field_unit_branch_and_zero_branch_trap():
    assert power_subgroup(7, 3) == {1, 6}
    # No all-unit solution for X^3 + Y^3 = Z^3 mod 7.
    assert unit_solution_count(7, 3, 3, 3) == 0
    # The support branch A = 0, B = C = 1 survives every exponent signature.
    for q in (3, 5, 7, 11):
        for x, y, z in ((3, 4, 5), (5, 5, 7), (4, 7, 11)):
            assert (pow(0, x, q) + pow(1, y, q) - pow(1, z, q)) % q == 0


def test_lte_valid_and_missing_assumption_counterexamples():
    assert lte_holds(3, 1, 2, 3)
    assert lte_holds(5, 2, 3, 5)
    # Removing odd n, q | a+b, or the base/unit coprimality conditions produces failures.
    assert not lte_holds(3, 1, 2, 2)
    assert not lte_holds(3, 1, 1, 3)
    assert not lte_holds(3, 3, 3, 3)


def test_verifier_primality_check():
    assert is_prime(2) and is_prime(7789)
    assert not is_prime(1) and not is_prime(7 * 11)


def test_verifier_can_ignore_stale_optional_gpu_artifacts():
    results = Path(__file__).resolve().parents[1] / "results"
    report = check(results, cuda_policy="ignore", shared_policy="ignore")
    assert report["cuda_differential_result_checked"] is False
    assert report["shared_residency_failure_checked"] is False


def test_cyclotomic_ell_validation_requires_distinct_odd_primes():
    assert validate_ells([3, 5, 7]) == [3, 5, 7]
    with pytest.raises(ValueError):
        validate_ells([3, 9])
    with pytest.raises(ValueError):
        validate_ells([3, 3])


def test_verifier_failure_cannot_be_disabled_by_python_optimization(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    finite_path = results / "finite_field_support.json"
    finite = json.loads(finite_path.read_text())
    finite["unit_empty_branch_occurrences"] += 1
    finite_path.write_text(json.dumps(finite))

    with pytest.raises(VerificationError):
        check(results, cuda_policy="ignore", shared_policy="ignore")

    verifier = Path(__file__).resolve().parents[1] / "verify_results.py"
    proc = subprocess.run(
        [sys.executable, "-O", str(verifier), "--results", str(results),
         "--cuda-policy", "ignore", "--shared-policy", "ignore"],
        text=True, capture_output=True, check=False,
    )
    assert proc.returncode != 0
    assert '"verification": "passed"' not in proc.stdout


def test_committed_results_have_one_exact_clean_producer():
    results = Path(__file__).resolve().parents[1] / "results"
    artifacts = [
        "cyclotomic_census.json", "finite_field_support.json",
        "lte_assumption_miner.json", "cuda_modexp_calibration.json",
        "gpu_shared_residency_probe.json",
    ]
    provenance = [json.loads((results / name).read_text())["provenance"] for name in artifacts]
    assert len({item["run_id"] for item in provenance}) == 1
    assert len({item["source_commit"] for item in provenance}) == 1
    assert all(item["source_tree_clean"] is True for item in provenance)
    assert provenance[0]["source_commit"] != "d83704e0904c504ef314bc9cabe08ffd7f67c8a8"


def test_independent_reproduction_is_complete_and_passed():
    results = Path(__file__).resolve().parents[1] / "results"
    report = json.loads((results / "independent_reproduction.json").read_text())
    assert report["verification"] == "passed"
    assert report["finite_field_checks_reproduced"] == 11664
    assert report["lte_cases_reproduced"] == 422340
    assert report["cyclotomic_cases_reproduced"] == 24348
