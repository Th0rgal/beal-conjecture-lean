import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

from cyclotomic_census import (
    cyclotomic_plus_cofactor,
    multiplicative_order,
    valuation,
)
from finite_field_support import power_subgroup, unit_solution_count
from lte_assumption_miner import lte_holds
from verify_results import check, is_prime


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


def test_run_suite_manifest_scopes_cpu_and_cuda_artifacts(tmp_path):
    source = Path(__file__).resolve().parents[1]
    suite = tmp_path / "suite"
    suite.mkdir()
    shutil.copy2(source / "run_suite.sh", suite / "run_suite.sh")
    results = suite / "results"
    results.mkdir()
    for name in (
        "cyclotomic_census.json",
        "finite_field_support.json",
        "lte_assumption_miner.json",
        "cuda_modexp_calibration.json",
        "gpu_shared_residency_probe.json",
    ):
        (results / name).write_text('{"stale": true}\n')

    mock_python = tmp_path / "python3"
    mock_python.write_text(
        f"#!{sys.executable}\n"
        "import os\n"
        "import pathlib\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "if args[:2] == ['-m', 'json.tool']:\n"
        "    print(pathlib.Path(args[2]).read_text(), end='')\n"
        "elif args[:2] != ['-m', 'pytest']:\n"
        "    name = pathlib.Path(args[0]).name\n"
        "    if name in {'finite_field_support.py', 'lte_assumption_miner.py', 'cyclotomic_census.py'}:\n"
        "        pathlib.Path(os.environ['MOCK_CALLS']).open('a').write(name + '\\n')\n"
        "    if name == 'environment_probe.py':\n"
        "        output = pathlib.Path(os.environ['OUTPUT'])\n"
        "    else:\n"
        "        output = pathlib.Path(args[args.index('--output') + 1])\n"
        "    output.write_text('{\\\"generated\\\": true}\\n')\n"
    )
    mock_python.chmod(mock_python.stat().st_mode | stat.S_IXUSR)

    mock_nvcc = tmp_path / "nvcc"
    mock_nvcc.write_text(
        f"#!{sys.executable}\n"
        "import pathlib\n"
        "import stat\n"
        "import sys\n"
        "output = pathlib.Path(sys.argv[sys.argv.index('-o') + 1])\n"
        "output.write_text('#!/bin/sh\\nprintf \\\'{\\\"mismatches\\\": 0}\\\\n\\\'\\n')\n"
        "output.chmod(output.stat().st_mode | stat.S_IXUSR)\n"
    )
    mock_nvcc.chmod(mock_nvcc.stat().st_mode | stat.S_IXUSR)

    def run(cpu: str, cuda: str) -> set[str]:
        calls = tmp_path / f"calls-{cpu}-{cuda}.log"
        env = os.environ | {
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "RUN_CPU": cpu,
            "RUN_CUDA": cuda,
            "NVCC": str(mock_nvcc),
            "MOCK_CALLS": str(calls),
        }
        subprocess.run(["bash", str(suite / "run_suite.sh")], check=True, env=env)
        manifest = (results / "SHA256SUMS").read_text().splitlines()
        return {line.split("  ", 1)[1] for line in manifest}

    cuda_only = run("0", "1")
    assert cuda_only == {
        "results/cuda_modexp_calibration.json",
        "results/environment.json",
        "results/verification_report.json",
    }
    assert not (tmp_path / "calls-0-1.log").exists()

    cpu_only = run("1", "0")
    assert cpu_only == {
        "results/cyclotomic_census.json",
        "results/environment.json",
        "results/finite_field_support.json",
        "results/lte_assumption_miner.json",
        "results/verification_report.json",
    }
