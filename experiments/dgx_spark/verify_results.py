#!/usr/bin/env python3
"""Artifact consistency checker for DGX experiment outputs.

Completeness is established separately by ``independent_reproduce.py``. This
checker never relies on Python ``assert`` and remains active under ``python -O``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from provenance import artifact_provenance


class VerificationError(RuntimeError):
    pass


EXPECTED_PRODUCERS = {
    "finite_field_support.json": "finite_field_support.py",
    "lte_assumption_miner.json": "lte_assumption_miner.py",
    "cyclotomic_census.json": "cyclotomic_census.py",
    "environment.json": "environment_probe.py",
    "independent_reproduction.json": "independent_reproduce.py",
    "cuda_modexp_calibration.json": "cuda_modexp_bench.cu",
    "gpu_shared_residency_probe.json": "gpu_residency_probe.py",
}

HEX_40 = re.compile(r"[0-9a-f]{40}")
HEX_64 = re.compile(r"[0-9a-f]{64}")

# These are the fixed inputs of the documented GB10 differential calibration,
# rather than merely internally consistent fields in an artifact.
CUDA_CALIBRATION_COUNT = 4_000_000
CUDA_CALIBRATION_EXPONENT = 65_537
CUDA_CALIBRATION_MODULUS = 2_147_483_647
# FNV-1a over the little-endian uint32 outputs for the fixed workload above.
CUDA_CALIBRATION_OUTPUT_DIGEST = "b03df39b05355ebb"


def require(condition: object, message: str) -> None:
    if not condition:
        raise VerificationError(message)


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


def valuation(n: int, p: int) -> int:
    require(n > 0 and p > 1, "valuation domain error")
    value = 0
    while n % p == 0:
        n //= p
        value += 1
    return value


def lte_holds(q: int, a: int, b: int, n: int) -> bool:
    return valuation(a**n + b**n, q) == valuation(a + b, q) + valuation(n, q)


def power_values(q: int, exponent: int) -> set[int]:
    return {pow(a, exponent, q) for a in range(1, q)}


def unit_solution_count(q: int, x: int, y: int, z: int) -> int:
    hx, hy, hz = power_values(q, x), power_values(q, y), power_values(q, z)
    return sum(1 for a in hx for b in hy if (a + b) % q in hz)


def cyclotomic_plus_cofactor(u: int, v: int, ell: int) -> int:
    numerator = pow(u, ell) + pow(v, ell)
    denominator = u + v
    quotient, remainder = divmod(numerator, denominator)
    require(remainder == 0, "cyclotomic factor identity failed")
    return quotient


def load_json(path: Path) -> dict:
    require(path.exists(), f"missing artifact: {path.name}")
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid artifact {path.name}: {exc}") from exc
    require(isinstance(value, dict), f"artifact {path.name} is not a JSON object")
    return value


def vllm_health_is_ok(value: object) -> bool:
    """Accept only the recorded successful JSON response from vLLM's health API."""
    if not isinstance(value, str):
        return False
    try:
        health = json.loads(value)
    except json.JSONDecodeError:
        return False
    return isinstance(health, dict) and health.get("status") == "ok"


def git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise VerificationError(f"cannot read {path} from source commit {commit}")
    return process.stdout


def require_commit_object(repo_root: Path, commit: str) -> None:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-t", commit],
        capture_output=True,
        check=False,
    )
    require(process.returncode == 0 and process.stdout.strip() == b"commit",
            f"source object is not a Git commit: {commit}")


def require_commit_ancestor(repo_root: Path, commit: str) -> None:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
        check=False,
    )
    require(process.returncode == 0, f"source commit is not an ancestor of HEAD: {commit}")


def check_provenance(
    named_artifacts: dict[str, dict], environment: dict
) -> tuple[str, str, int, int]:
    run_ids: set[str] = set()
    commits: set[str] = set()
    provenances: dict[str, dict] = {}
    for name, artifact in named_artifacts.items():
        provenance = artifact.get("provenance")
        if not isinstance(provenance, dict):
            raise VerificationError(f"{name} lacks provenance")
        run_id = provenance.get("run_id")
        commit = provenance.get("source_commit")
        if not isinstance(run_id, str) or not run_id:
            raise VerificationError(f"{name} has invalid run_id")
        if not isinstance(commit, str) or HEX_40.fullmatch(commit) is None:
            raise VerificationError(f"{name} has invalid source_commit")
        require(provenance.get("source_tree_clean") is True, f"{name} was not produced from clean source")
        producer_hash = provenance.get("producer_sha256")
        if not isinstance(producer_hash, str) or HEX_64.fullmatch(producer_hash) is None:
            raise VerificationError(f"{name} has invalid producer_sha256")
        run_ids.add(run_id)
        commits.add(commit)
        provenances[name] = provenance
    require(len(run_ids) == 1, f"mixed run IDs: {sorted(run_ids)}")
    require(len(commits) == 1, f"mixed source commits: {sorted(commits)}")
    run_id, commit = next(iter(run_ids)), next(iter(commits))

    source_hashes = environment.get("source_files_sha256")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise VerificationError("environment lacks source_files_sha256")
    repo_root = Path(__file__).resolve().parents[2]
    require_commit_object(repo_root, commit)
    require_commit_ancestor(repo_root, commit)
    paths_by_basename: dict[str, list[str]] = {}
    for path, expected_hash in source_hashes.items():
        if not isinstance(path, str) or not path.startswith("experiments/dgx_spark/"):
            raise VerificationError(f"invalid environment source path: {path!r}")
        if not isinstance(expected_hash, str) or HEX_64.fullmatch(expected_hash) is None:
            raise VerificationError(f"invalid environment source hash for {path}")
        actual_hash = hashlib.sha256(git_blob(repo_root, commit, path)).hexdigest()
        require(actual_hash == expected_hash, f"source hash differs from Git commit for {path}")
        paths_by_basename.setdefault(Path(path).name, []).append(path)

    for name, provenance in provenances.items():
        expected_producer = EXPECTED_PRODUCERS.get(name)
        if expected_producer is None:
            raise VerificationError(f"no expected producer mapping for {name}")
        require(provenance.get("producer") == expected_producer,
                f"{name} names unexpected producer {provenance.get('producer')!r}")
        matching_paths = paths_by_basename.get(expected_producer, [])
        require(len(matching_paths) == 1,
                f"environment does not identify one source path for {expected_producer}")
        expected_hash = source_hashes[matching_paths[0]]
        require(provenance.get("producer_sha256") == expected_hash,
                f"{name} producer hash differs from source manifest")

    status = environment.get("git_status_at_probe")
    if not isinstance(status, str):
        raise VerificationError("environment lacks git_status_at_probe")
    for line in status.splitlines():
        parts = line.strip().split(maxsplit=1)
        require(len(parts) == 2, f"invalid git status line: {line!r}")
        for changed_path in parts[1].split(" -> "):
            require(changed_path.startswith("experiments/dgx_spark/results/"),
                    f"producer source was dirty at environment probe: {changed_path}")

    return run_id, commit, len(source_hashes), len(provenances)


def check(results: Path, cuda_policy: str = "auto", shared_policy: str = "auto") -> dict:
    finite = load_json(results / "finite_field_support.json")
    lte = load_json(results / "lte_assumption_miner.json")
    cyclo = load_json(results / "cyclotomic_census.json")
    environment = load_json(results / "environment.json")
    independent = load_json(results / "independent_reproduction.json")
    artifacts = {
        "finite_field_support.json": finite,
        "lte_assumption_miner.json": lte,
        "cyclotomic_census.json": cyclo,
        "environment.json": environment,
        "independent_reproduction.json": independent,
    }

    finite_rows = 0
    finite_parameters = finite.get("parameters")
    require(isinstance(finite_parameters, dict), "finite-field parameters missing")
    prime_bound = finite_parameters.get("prime_bound")
    kernels = finite_parameters.get("kernels")
    require(isinstance(prime_bound, int) and prime_bound >= 2,
            "invalid finite-field prime_bound")
    require(isinstance(kernels, list) and kernels and
            all(isinstance(kernel, int) and kernel > 0 for kernel in kernels),
            "invalid finite-field kernels")
    kernel_set = set(kernels)
    for row in finite.get("support_forcing", []):
        signature = row.get("signature")
        require(isinstance(signature, list) and len(signature) == 3, "invalid signature row")
        x, y, z = signature
        require(all(isinstance(exponent, int) and exponent in kernel_set
                    for exponent in signature),
                f"signature outside declared finite-field kernels: {signature}")
        for witness in row.get("support_forcing_primes", []):
            q = witness.get("prime")
            require(isinstance(q, int) and is_prime(q), "nonprime finite-field witness")
            require(q <= prime_bound,
                    f"finite-field witness q={q} exceeds declared prime_bound={prime_bound}")
            require(unit_solution_count(q, x, y, z) == 0,
                    f"nonempty recorded support witness q={q}, signature={signature}")
            require((pow(0, x, q) + pow(1, y, q) - pow(1, z, q)) % q == 0,
                    "permanent zero branch failed")
            finite_rows += 1
    require(finite_rows == finite.get("unit_empty_branch_occurrences"),
            "finite-field witness count mismatch")
    require(not finite.get("zero_branch_failures"), "finite-field zero-branch failures recorded")

    require(not lte.get("valid_hypothesis_violations"), "LTE violations recorded")
    lte_counterexamples = 0
    for case in lte.get("minimal_counterexamples_when_assumption_removed", {}).values():
        if case is None:
            continue
        q, a, b, n = (case[key] for key in ("q", "a", "b", "n"))
        require(not lte_holds(q, a, b, n), f"invalid LTE counterexample: {case}")
        require(valuation(a**n + b**n, q) == case.get("lhs_valuation"),
                "LTE counterexample valuation mismatch")
        lte_counterexamples += 1

    for key in ("factor_identity_failures", "gcd_failures", "order_failures", "congruence_failures"):
        failures = cyclo.get(key)
        require(isinstance(failures, list), f"missing or invalid cyclotomic {key} list")
        require(not failures, f"cyclotomic producer recorded {key}")
    cyclo_parameters = cyclo.get("parameters")
    require(isinstance(cyclo_parameters, dict), "cyclotomic parameters missing")
    base_bound = cyclo_parameters.get("base_bound")
    ells = cyclo_parameters.get("ells")
    require(isinstance(base_bound, int) and base_bound >= 1,
            "invalid cyclotomic base_bound")
    require(isinstance(ells, list) and ells and all(isinstance(ell, int) for ell in ells),
            "invalid cyclotomic ells")
    higher_cases = cyclo.get("higher_valuation_cases")
    if not isinstance(higher_cases, list):
        raise VerificationError("missing higher-valuation witness list")
    require(len(higher_cases) == cyclo.get("higher_valuation_occurrences"),
            "higher-valuation count mismatch")
    for case in higher_cases:
        ell, u, v, q, exponent = (case[key] for key in ("ell", "u", "v", "q", "valuation"))
        require(ell in ells, f"cyclotomic witness ell={ell} outside declared ells")
        require(1 <= u <= base_bound and 1 <= v <= base_bound,
                f"cyclotomic witness outside declared base_bound={base_bound}")
        require(is_prime(ell) and is_prime(q), "nonprime cyclotomic witness")
        cofactor = cyclotomic_plus_cofactor(u, v, ell)
        require(str(cofactor) == case.get("cofactor"), "cofactor witness mismatch")
        require(math.gcd(u, v) == 1, "noncoprime cyclotomic witness")
        require(cofactor % pow(q, exponent) == 0, "claimed cyclotomic valuation is too high")
        require(cofactor % pow(q, exponent + 1) != 0, "claimed cyclotomic valuation is too low")
        require(q != ell, "exceptional prime listed as nonexceptional high valuation")
        ratio = (u * pow(v, -1, q)) % q
        require(pow(ratio, ell, q) == q - 1 and ratio != q - 1,
                "cyclotomic exact-order witness failed")
        require((q - 1) % (2 * ell) == 0, "cyclotomic congruence witness failed")

    cuda_checked = False
    cuda_path = results / "cuda_modexp_calibration.json"
    if cuda_policy == "required":
        require(cuda_path.exists(), "required CUDA artifact missing")
    if cuda_policy != "ignore" and cuda_path.exists():
        cuda = load_json(cuda_path)
        artifacts["cuda_modexp_calibration.json"] = cuda
        repeat_mismatches = cuda.get("mismatches_per_repeat")
        repeat_digests = cuda.get("output_digest_per_repeat")
        repeats = cuda.get("repeats")
        if not isinstance(repeats, int) or repeats <= 0:
            raise VerificationError("invalid CUDA repeat count")
        if not isinstance(repeat_mismatches, list) or len(repeat_mismatches) != repeats:
            raise VerificationError("CUDA repeat mismatch vector missing")
        require(all(value == 0 for value in repeat_mismatches), "CUDA repeat mismatch detected")
        require(cuda.get("mismatches_total") == 0, "CUDA total mismatch detected")
        if not isinstance(repeat_digests, list) or len(repeat_digests) != repeats:
            raise VerificationError("CUDA digest vector missing")
        require(cuda.get("cpu_output_digest") == CUDA_CALIBRATION_OUTPUT_DIGEST,
                "CUDA CPU digest differs from fixed workload digest")
        require(all(value == CUDA_CALIBRATION_OUTPUT_DIGEST for value in repeat_digests),
                "CUDA repeat digest differs from fixed workload digest")
        require(cuda.get("count") == CUDA_CALIBRATION_COUNT,
                "unexpected CUDA calibration count")
        require(cuda.get("exponent") == CUDA_CALIBRATION_EXPONENT,
                "unexpected CUDA calibration exponent")
        require(cuda.get("modulus") == CUDA_CALIBRATION_MODULUS,
                "unexpected CUDA calibration modulus")
        require(cuda.get("compute_capability") == "12.1", "unexpected CUDA capability")
        cuda_checked = True

    shared_checked = False
    shared_path = results / "gpu_shared_residency_probe.json"
    if shared_policy == "required":
        require(shared_path.exists(), "required shared-residency artifact missing")
    if shared_policy != "ignore" and shared_path.exists():
        shared = load_json(shared_path)
        artifacts["gpu_shared_residency_probe.json"] = shared
        require(shared.get("benchmark_exit_code") != 0, "resident-service CUDA probe unexpectedly succeeded")
        require("out of memory" in str(shared.get("benchmark_stderr", "")).lower(),
                "shared-residency probe did not record CUDA OOM")
        require(shared.get("vllm_container_status_before") == "running",
                "shared-residency probe did not observe running vLLM")
        require(vllm_health_is_ok(shared.get("vllm_health_before")),
                "shared-residency probe did not observe healthy vLLM")
        require(shared.get("vllm_container_status_after") == "running",
                "shared-residency probe did not leave vLLM running")
        require(vllm_health_is_ok(shared.get("vllm_health_after")),
                "shared-residency probe did not leave vLLM healthy")
        shared_checked = True

    require(independent.get("verification") == "passed", "independent reproduction did not pass")
    require(independent.get("finite_field_checks_reproduced") == finite.get("signature_prime_checks"),
            "independent finite-field coverage mismatch")
    require(independent.get("finite_field_empty_witnesses_reproduced") ==
            finite.get("unit_empty_branch_occurrences"),
            "independent finite-field witness count mismatch")
    require(independent.get("lte_cases_reproduced") == lte.get("valid_hypothesis_cases_tested"),
            "independent LTE coverage mismatch")
    require(independent.get("lte_violations_reproduced") ==
            len(lte.get("valid_hypothesis_violations", [])),
            "independent LTE violation count mismatch")
    require(independent.get("cyclotomic_cases_reproduced") == cyclo.get("pairs_tested"),
            "independent cyclotomic coverage mismatch")
    require(independent.get("cyclotomic_factor_occurrences_reproduced") ==
            cyclo.get("distinct_prime_factor_occurrences_tested"),
            "independent cyclotomic factor count mismatch")
    require(independent.get("cyclotomic_exceptional_occurrences_reproduced") ==
            cyclo.get("ell_exception_factor_occurrences"),
            "independent cyclotomic exceptional count mismatch")
    require(independent.get("cyclotomic_higher_valuation_occurrences_reproduced") ==
            cyclo.get("higher_valuation_occurrences"),
            "independent cyclotomic higher-valuation count mismatch")

    run_id, source_commit, source_files_checked, producer_hashes_checked = check_provenance(
        artifacts, environment
    )
    return {
        "schema_version": 2,
        "verification": "passed",
        "run_id": run_id,
        "source_commit": source_commit,
        "finite_field_support_witnesses_replayed": finite_rows,
        "lte_counterexamples_replayed": lte_counterexamples,
        "cyclotomic_higher_valuation_cases_replayed": len(higher_cases),
        "primality_checks": finite_rows + 2 * len(higher_cases),
        "independent_complete_domain_reproduction_checked": True,
        "source_files_checked_against_git_commit": source_files_checked,
        "artifact_producer_hashes_checked": producer_hashes_checked,
        "cuda_all_repeats_differentially_checked": cuda_checked,
        "shared_residency_failure_checked": shared_checked,
        "scope": "Artifact consistency plus a separately implemented complete-domain reproduction; not Lean certification or an unrestricted proof.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cuda-policy", choices=("auto", "required", "ignore"), default="auto")
    parser.add_argument("--shared-policy", choices=("auto", "required", "ignore"), default="auto")
    args = parser.parse_args()
    try:
        report = check(args.results, cuda_policy=args.cuda_policy, shared_policy=args.shared_policy)
        report["provenance"] = artifact_provenance(__file__)
        output = args.output or args.results / "verification_report.json"
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
    except VerificationError as exc:
        raise SystemExit(f"VERIFICATION FAILED: {exc}") from exc


if __name__ == "__main__":
    main()
