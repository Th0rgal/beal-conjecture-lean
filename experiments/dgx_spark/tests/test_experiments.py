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
    assert report["cuda_all_repeats_differentially_checked"] is False
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


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("finite_field_empty_witnesses_reproduced", 0),
        ("lte_violations_reproduced", 1),
        ("cyclotomic_factor_occurrences_reproduced", 0),
        ("cyclotomic_exceptional_occurrences_reproduced", 0),
        ("cyclotomic_higher_valuation_occurrences_reproduced", 0),
    ],
)
def test_verifier_rejects_false_independent_aggregate(tmp_path, field, bad_value):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    report_path = results / "independent_reproduction.json"
    report = json.loads(report_path.read_text())
    report[field] = bad_value
    report_path.write_text(json.dumps(report))
    with pytest.raises(VerificationError):
        check(results, cuda_policy="required", shared_policy="required")


@pytest.mark.parametrize(
    ("artifact", "provenance_field", "bad_value"),
    [
        ("finite_field_support.json", "producer", "not-the-producer.py"),
        ("finite_field_support.json", "producer_sha256", "0" * 64),
        ("finite_field_support.json", "source_commit", "z" * 40),
    ],
)
def test_verifier_rejects_false_producer_provenance(
    tmp_path, artifact, provenance_field, bad_value
):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    artifact_path = results / artifact
    value = json.loads(artifact_path.read_text())
    value["provenance"][provenance_field] = bad_value
    artifact_path.write_text(json.dumps(value))
    with pytest.raises(VerificationError):
        check(results, cuda_policy="required", shared_policy="required")


def test_verifier_rejects_source_dirty_at_environment_probe(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    environment_path = results / "environment.json"
    environment = json.loads(environment_path.read_text())
    environment["git_status_at_probe"] += "\n M experiments/dgx_spark/verify_results.py\n"
    environment_path.write_text(json.dumps(environment))
    with pytest.raises(VerificationError):
        check(results, cuda_policy="required", shared_policy="required")


def test_verifier_rejects_tree_oid_as_source_commit(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    producer_commit = json.loads((results / "environment.json").read_text())[
        "provenance"
    ]["source_commit"]
    repo = Path(__file__).resolve().parents[3]
    tree_oid = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", f"{producer_commit}^{{tree}}"],
        text=True, capture_output=True, check=True,
    ).stdout.strip()
    for artifact in (
        "cyclotomic_census.json", "finite_field_support.json",
        "lte_assumption_miner.json", "independent_reproduction.json",
        "cuda_modexp_calibration.json", "gpu_shared_residency_probe.json",
        "environment.json",
    ):
        path = results / artifact
        value = json.loads(path.read_text())
        value["provenance"]["source_commit"] = tree_oid
        path.write_text(json.dumps(value))
    with pytest.raises(VerificationError, match="not a Git commit"):
        check(results, cuda_policy="required", shared_policy="required")


def test_verifier_checks_both_sides_of_dirty_rename(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    environment_path = results / "environment.json"
    environment = json.loads(environment_path.read_text())
    environment["git_status_at_probe"] += (
        "\nR  experiments/dgx_spark/verify_results.py -> "
        "experiments/dgx_spark/results/renamed.py\n"
    )
    environment_path.write_text(json.dumps(environment))
    with pytest.raises(VerificationError):
        check(results, cuda_policy="required", shared_policy="required")
