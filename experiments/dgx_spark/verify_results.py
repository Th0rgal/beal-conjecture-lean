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
UTC_SECOND = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

# These are the fixed inputs of the documented GB10 differential calibration,
# rather than merely internally consistent fields in an artifact.
CUDA_CALIBRATION_COUNT = 4_000_000
CUDA_CALIBRATION_EXPONENT = 65_537
CUDA_CALIBRATION_MODULUS = 2_147_483_647
# FNV-1a over the little-endian uint32 outputs for the fixed workload above.
CUDA_CALIBRATION_OUTPUT_DIGEST = "b03df39b05355ebb"

# The residency probe must invoke the calibrated binary with this fixed probe
# size.  These are verifier-owned expectations, not artifact-owned claims.
GPU_RESIDENCY_PROBE_COUNT = 100_000
GPU_RESIDENCY_SCHEMA_VERSION = 3
# FNV-1a over the little-endian uint32 outputs for the fixed residency workload.
# This verifier-owned value prevents coordinated mutation of both digest fields.
GPU_RESIDENCY_PROBE_OUTPUT_DIGEST = "50acfa71f6907f64"
LTE_REMOVED_ASSUMPTIONS = {
    "remove_odd_n",
    "remove_q_divides_sum",
    "remove_base_coprimality",
    "allow_q_two_with_odd_n",
}
LTE_REQUIRED_COUNTEREXAMPLES = {
    "remove_odd_n",
    "remove_q_divides_sum",
    "remove_base_coprimality",
}
LTE_COUNTEREXAMPLE_FIELDS = {"q", "a", "b", "n", "lhs_valuation", "rhs_valuation"}


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


def is_lte_counterexample_for_removed_assumption(
    key: str, q: int, a: int, b: int, n: int
) -> bool:
    """Check the precise hypothesis omitted by an LTE miner counterexample."""
    if key == "remove_odd_n":
        return (
            is_prime(q) and q != 2 and n % 2 == 0 and math.gcd(a, b) == 1
            and (a + b) % q == 0 and (a * b) % q != 0
        )
    if key == "remove_q_divides_sum":
        return (
            is_prime(q) and q != 2 and n % 2 == 1 and math.gcd(a, b) == 1
            and (a + b) % q != 0 and (a * b) % q != 0
        )
    if key == "remove_base_coprimality":
        return (
            is_prime(q) and q != 2 and n % 2 == 1
            and (a + b) % q == 0 and (a * b) % q == 0
        )
    if key == "allow_q_two_with_odd_n":
        return (
            q == 2 and n % 2 == 1 and math.gcd(a, b) == 1
            and (a + b) % q == 0 and (a * b) % q != 0
        )
    return False


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


def require_independent_domain_snapshot(
    independent: dict, field: str, declared: dict, family: str
) -> None:
    """Bind aggregate reproduction to the exact producer domain it covered."""
    snapshot = independent.get(field)
    require(isinstance(snapshot, dict),
            f"independent {family} domain snapshot missing or invalid")
    require(snapshot == declared,
            f"independent {family} domain snapshot differs from declared parameters")


def service_health_is_positive(value: object, identity: dict) -> bool:
    """Require a successful HTTP observation of the configured model service."""
    return (
        isinstance(value, dict)
        and value.get("service_label") == identity.get("label")
        and value.get("url") == identity.get("health_url")
        and value.get("exit_code") == 0
        and isinstance(value.get("http_status"), int)
        and 200 <= value["http_status"] < 300
        and isinstance(value.get("stdout"), str)
        and isinstance(value.get("stderr"), str)
        and value.get("stdout_sha256") == hashlib.sha256(value["stdout"].encode()).hexdigest()
        and value.get("stderr_sha256") == hashlib.sha256(value["stderr"].encode()).hexdigest()
    )


def require_shared_success_payload(shared: dict, source_commit: str, producer_hash: str) -> None:
    try:
        payload = json.loads(shared["benchmark_stdout"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise VerificationError("shared-residency success stdout is not calibration JSON") from exc
    require(isinstance(payload, dict), "shared-residency success stdout is not a JSON object")
    require(payload.get("experiment") == "cuda_modexp_calibration",
            "shared-residency success stdout has unexpected calibration schema")
    require(payload.get("count") == GPU_RESIDENCY_PROBE_COUNT,
            "shared-residency success stdout has unexpected probe count")
    require(payload.get("repeats") == 1,
            "shared-residency success stdout has unexpected repeat count")
    require(payload.get("exponent") == CUDA_CALIBRATION_EXPONENT,
            "shared-residency success stdout has unexpected exponent")
    require(payload.get("modulus") == CUDA_CALIBRATION_MODULUS,
            "shared-residency success stdout has unexpected modulus")
    require(payload.get("mismatches_total") == 0,
            "shared-residency success calibration has mismatches")
    require(payload.get("mismatches_per_repeat") == [0],
            "shared-residency success calibration repeats have mismatches")
    require(payload.get("cpu_output_digest") == GPU_RESIDENCY_PROBE_OUTPUT_DIGEST,
            "shared-residency success CPU output digest differs from fixed workload")
    require(payload.get("output_digest_per_repeat") ==
            [GPU_RESIDENCY_PROBE_OUTPUT_DIGEST],
            "shared-residency success output digest differs from fixed workload")
    provenance = payload.get("provenance")
    require(isinstance(provenance, dict), "shared-residency success stdout lacks provenance")
    require(provenance.get("run_id") == shared["provenance"]["run_id"],
            "shared-residency success stdout run ID differs from probe")
    require(provenance.get("source_commit") == source_commit,
            "shared-residency success stdout source commit differs from probe")
    require(provenance.get("source_tree_clean") is True,
            "shared-residency success stdout was not produced from clean source")
    require(provenance.get("producer") == "cuda_modexp_bench.cu" and
            provenance.get("producer_sha256") == producer_hash,
            "shared-residency success stdout producer provenance differs from probe source")


def git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise VerificationError(f"cannot read {path} from source commit {commit}")
    return process.stdout


def committed_source_paths(repo_root: Path, commit: str) -> set[str]:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "ls-tree", "-r", "--name-only", commit,
         "--", "experiments/dgx_spark"],
        text=True, capture_output=True, check=False,
    )
    if process.returncode:
        raise VerificationError(f"cannot list DGX sources from source commit {commit}")
    excluded_parts = {"results", "logs", "build", "smoke", "__pycache__", ".pytest_cache"}
    return {
        path for path in process.stdout.splitlines()
        if path and not (set(Path(path).parts) & excluded_parts)
    }


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
    run_started_at: set[str] = set()
    branches: set[str] = set()
    provenances: dict[str, dict] = {}
    for name, artifact in named_artifacts.items():
        provenance = artifact.get("provenance")
        if not isinstance(provenance, dict):
            raise VerificationError(f"{name} lacks provenance")
        run_id = provenance.get("run_id")
        commit = provenance.get("source_commit")
        started = provenance.get("run_started_at_utc")
        branch = provenance.get("source_branch")
        if not isinstance(run_id, str) or not run_id:
            raise VerificationError(f"{name} has invalid run_id")
        if not isinstance(commit, str) or HEX_40.fullmatch(commit) is None:
            raise VerificationError(f"{name} has invalid source_commit")
        if not isinstance(started, str) or UTC_SECOND.fullmatch(started) is None:
            raise VerificationError(f"{name} has invalid run_started_at_utc")
        if not isinstance(branch, str) or not branch:
            raise VerificationError(f"{name} has invalid source_branch")
        require(provenance.get("source_tree_clean") is True, f"{name} was not produced from clean source")
        producer_hash = provenance.get("producer_sha256")
        if not isinstance(producer_hash, str) or HEX_64.fullmatch(producer_hash) is None:
            raise VerificationError(f"{name} has invalid producer_sha256")
        run_ids.add(run_id)
        commits.add(commit)
        run_started_at.add(started)
        branches.add(branch)
        provenances[name] = provenance
    require(len(run_ids) == 1, f"mixed run IDs: {sorted(run_ids)}")
    require(len(commits) == 1, f"mixed source commits: {sorted(commits)}")
    require(len(run_started_at) == 1, f"mixed run start times: {sorted(run_started_at)}")
    require(len(branches) == 1, f"mixed source branches: {sorted(branches)}")
    run_id, commit = next(iter(run_ids)), next(iter(commits))

    source_hashes = environment.get("source_files_sha256")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise VerificationError("environment lacks source_files_sha256")
    repo_root = Path(__file__).resolve().parents[2]
    require_commit_object(repo_root, commit)
    require_commit_ancestor(repo_root, commit)
    expected_paths = committed_source_paths(repo_root, commit)
    require(set(source_hashes) == expected_paths,
            "environment source manifest is incomplete or contains stale paths")
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
    finite_signatures: set[tuple[int, int, int]] = set()
    finite_witnesses: set[tuple[tuple[int, int, int], int]] = set()
    for row in finite.get("support_forcing", []):
        signature = row.get("signature")
        require(isinstance(signature, list) and len(signature) == 3, "invalid signature row")
        x, y, z = signature
        signature_key = (x, y, z)
        require(signature_key not in finite_signatures,
                f"duplicate finite-field signature: {signature}")
        finite_signatures.add(signature_key)
        require(all(isinstance(exponent, int) and exponent in kernel_set
                    for exponent in signature),
                f"signature outside declared finite-field kernels: {signature}")
        for witness in row.get("support_forcing_primes", []):
            q = witness.get("prime")
            require(isinstance(q, int) and is_prime(q), "nonprime finite-field witness")
            require(q <= prime_bound,
                    f"finite-field witness q={q} exceeds declared prime_bound={prime_bound}")
            witness_key = (signature_key, q)
            require(witness_key not in finite_witnesses,
                    f"duplicate finite-field witness: signature={signature}, q={q}")
            finite_witnesses.add(witness_key)
            require(unit_solution_count(q, x, y, z) == 0,
                    f"nonempty recorded support witness q={q}, signature={signature}")
            require((pow(0, x, q) + pow(1, y, q) - pow(1, z, q)) % q == 0,
                    "permanent zero branch failed")
            finite_rows += 1
    require(finite_rows == finite.get("unit_empty_branch_occurrences"),
            "finite-field witness count mismatch")
    require(not finite.get("zero_branch_failures"), "finite-field zero-branch failures recorded")

    lte_parameters = lte.get("parameters")
    require(isinstance(lte_parameters, dict), "LTE parameters missing")
    lte_a_bound = lte_parameters.get("a_bound")
    lte_prime_bound = lte_parameters.get("prime_bound")
    lte_n_bound = lte_parameters.get("n_bound")
    require(all(isinstance(value, int) and value >= 1
                for value in (lte_a_bound, lte_prime_bound, lte_n_bound)),
            "invalid LTE parameters")
    violations = lte.get("valid_hypothesis_violations")
    require(isinstance(violations, list),
            "missing or invalid LTE valid_hypothesis_violations list")
    require(not violations, "LTE violations recorded")
    removed_assumption_cases = lte.get("minimal_counterexamples_when_assumption_removed")
    require(isinstance(removed_assumption_cases, dict),
            "missing or invalid LTE minimal counterexamples object")
    require(set(removed_assumption_cases) == LTE_REMOVED_ASSUMPTIONS,
            "LTE minimal counterexamples have missing or unexpected assumption keys")
    lte_counterexamples = 0
    for key, case in removed_assumption_cases.items():
        if case is None:
            require(key not in LTE_REQUIRED_COUNTEREXAMPLES,
                    f"LTE counterexample is required for removed assumption {key}")
            continue
        require(isinstance(case, dict) and set(case) == LTE_COUNTEREXAMPLE_FIELDS,
                f"LTE counterexample has invalid fields for {key}")
        require(all(type(case[field]) is int for field in LTE_COUNTEREXAMPLE_FIELDS),
                f"LTE counterexample has invalid value types for {key}")
        q, a, b, n = (case[key] for key in ("q", "a", "b", "n"))
        require(is_lte_counterexample_for_removed_assumption(key, q, a, b, n),
                f"LTE counterexample does not match removed assumption {key}: {case}")
        require(not lte_holds(q, a, b, n), f"invalid LTE counterexample: {case}")
        require(valuation(a**n + b**n, q) == case.get("lhs_valuation"),
                "LTE counterexample valuation mismatch")
        require(valuation(a + b, q) + valuation(n, q) == case.get("rhs_valuation"),
                "LTE counterexample RHS valuation mismatch")
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
    cyclotomic_witnesses: set[tuple[int, int, int, int]] = set()
    for case in higher_cases:
        ell, u, v, q, exponent = (case[key] for key in ("ell", "u", "v", "q", "valuation"))
        witness_key = (ell, u, v, q)
        require(witness_key not in cyclotomic_witnesses,
                f"duplicate cyclotomic witness: {witness_key}")
        cyclotomic_witnesses.add(witness_key)
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
    cuda: dict | None = None
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
        require(shared.get("schema_version") == GPU_RESIDENCY_SCHEMA_VERSION,
                "shared-residency artifact schema is obsolete; rerun the physical DGX probe")
        binary_hash = shared.get("benchmark_binary_sha256")
        require(isinstance(binary_hash, str) and HEX_64.fullmatch(binary_hash),
                "shared-residency probe has malformed benchmark binary hash")
        require(shared.get("benchmark_source") == "cuda_modexp_bench.cu",
                "shared-residency probe names unexpected benchmark source")
        source_hashes = environment.get("source_files_sha256")
        require(isinstance(source_hashes, dict), "environment lacks source_files_sha256")
        benchmark_source_path = "experiments/dgx_spark/cuda_modexp_bench.cu"
        expected_source_hash = source_hashes.get(benchmark_source_path)
        require(isinstance(expected_source_hash, str) and HEX_64.fullmatch(expected_source_hash),
                "environment lacks benchmark source hash")
        require(shared.get("benchmark_source_sha256") == expected_source_hash,
                "shared-residency benchmark source hash differs from committed provenance")
        if cuda is not None:
            calibration_binary_hash = cuda.get("benchmark_binary_sha256")
            require(isinstance(calibration_binary_hash, str) and HEX_64.fullmatch(calibration_binary_hash),
                    "CUDA calibration lacks a valid benchmark binary hash")
            require(calibration_binary_hash == binary_hash,
                    "shared-residency and CUDA calibration benchmark binaries differ")
        require(shared.get("probe_count") == GPU_RESIDENCY_PROBE_COUNT,
                "shared-residency probe used an unexpected probe count")
        stdout, stderr = shared.get("benchmark_stdout"), shared.get("benchmark_stderr")
        require(isinstance(stdout, str) and isinstance(stderr, str),
                "shared-residency probe lacks benchmark output")
        require(shared.get("benchmark_stdout_sha256") == hashlib.sha256(stdout.encode()).hexdigest() and
                shared.get("benchmark_stderr_sha256") == hashlib.sha256(stderr.encode()).hexdigest(),
                "shared-residency probe benchmark output hashes differ")
        identity = shared.get("service_identity")
        require(isinstance(identity, dict) and isinstance(identity.get("label"), str) and
                identity["label"] and isinstance(identity.get("health_url"), str) and
                identity["health_url"] and isinstance(identity.get("required"), bool),
                "shared-residency probe has invalid service identity")
        environment_service = environment.get("model_service")
        require(isinstance(environment_service, dict) and
                environment_service.get("label") == identity["label"] and
                environment_service.get("health_url") == identity["health_url"] and
                environment_service.get("required") == str(identity["required"]).lower(),
                "shared-residency service identity differs from environment manifest")
        if identity["required"]:
            require(service_health_is_positive(shared.get("service_health_before"), identity),
                    "shared-residency probe did not positively observe service health before")
            require(service_health_is_positive(shared.get("service_health_after"), identity),
                    "shared-residency probe did not positively observe service health after")
        exit_class = shared.get("benchmark_exit_class")
        if exit_class == "success":
            require(shared.get("benchmark_exit_code") == 0,
                    "shared-residency success exit class has nonzero exit code")
            require_shared_success_payload(shared, shared["provenance"]["source_commit"], expected_source_hash)
        elif exit_class == "cuda_oom":
            require(isinstance(shared.get("benchmark_exit_code"), int) and
                    shared["benchmark_exit_code"] != 0,
                    "shared-residency CUDA OOM exit class has zero exit code")
            require("cuda" in stderr.lower() and "out of memory" in stderr.lower(),
                    "shared-residency probe did not record recognized CUDA OOM")
            require(not stdout.strip(), "shared-residency CUDA OOM included a successful calibration payload")
        else:
            raise VerificationError("shared-residency probe has unexpected benchmark exit class")
        shared_checked = True

    require(independent.get("verification") == "passed", "independent reproduction did not pass")
    require_independent_domain_snapshot(
        independent, "finite_field_domain_reproduced",
        {"kernels": kernels, "prime_bound": prime_bound}, "finite-field",
    )
    require_independent_domain_snapshot(
        independent, "lte_domain_reproduced",
        {
            "a_bound": lte_a_bound,
            "prime_bound": lte_prime_bound,
            "n_bound": lte_n_bound,
        }, "LTE",
    )
    require_independent_domain_snapshot(
        independent, "cyclotomic_domain_reproduced",
        {"ells": ells, "base_bound": base_bound}, "cyclotomic",
    )
    require(independent.get("finite_field_checks_reproduced") == finite.get("signature_prime_checks"),
            "independent finite-field coverage mismatch")
    require(independent.get("finite_field_empty_witnesses_reproduced") ==
            finite.get("unit_empty_branch_occurrences"),
            "independent finite-field witness count mismatch")
    require(independent.get("lte_cases_reproduced") == lte.get("valid_hypothesis_cases_tested"),
            "independent LTE coverage mismatch")
    require(independent.get("lte_violations_reproduced") ==
            len(violations),
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
        "shared_residency_outcome_checked": shared_checked,
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
