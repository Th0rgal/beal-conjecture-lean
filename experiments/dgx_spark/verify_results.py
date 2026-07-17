#!/usr/bin/env python3
"""Artifact consistency checker for DGX experiment outputs.

Completeness is established separately by ``independent_reproduce.py``. This
checker never relies on Python ``assert`` and remains active under ``python -O``.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from provenance import artifact_provenance


class VerificationError(RuntimeError):
    pass


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


def check_provenance(named_artifacts: dict[str, dict]) -> tuple[str, str]:
    run_ids: set[str] = set()
    commits: set[str] = set()
    for name, artifact in named_artifacts.items():
        provenance = artifact.get("provenance")
        if not isinstance(provenance, dict):
            raise VerificationError(f"{name} lacks provenance")
        run_id = provenance.get("run_id")
        commit = provenance.get("source_commit")
        if not isinstance(run_id, str) or not run_id:
            raise VerificationError(f"{name} has invalid run_id")
        if not isinstance(commit, str) or len(commit) != 40:
            raise VerificationError(f"{name} has invalid source_commit")
        require(provenance.get("source_tree_clean") is True, f"{name} was not produced from clean source")
        producer_hash = provenance.get("producer_sha256")
        require(isinstance(producer_hash, str) and len(producer_hash) == 64,
                f"{name} has invalid producer_sha256")
        run_ids.add(run_id)
        commits.add(commit)
    require(len(run_ids) == 1, f"mixed run IDs: {sorted(run_ids)}")
    require(len(commits) == 1, f"mixed source commits: {sorted(commits)}")
    return next(iter(run_ids)), next(iter(commits))


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
    for row in finite.get("support_forcing", []):
        signature = row.get("signature")
        require(isinstance(signature, list) and len(signature) == 3, "invalid signature row")
        x, y, z = signature
        for witness in row.get("support_forcing_primes", []):
            q = witness.get("prime")
            require(isinstance(q, int) and is_prime(q), "nonprime finite-field witness")
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
        require(not cyclo.get(key), f"cyclotomic producer recorded {key}")
    higher_cases = cyclo.get("higher_valuation_cases")
    if not isinstance(higher_cases, list):
        raise VerificationError("missing higher-valuation witness list")
    require(len(higher_cases) == cyclo.get("higher_valuation_occurrences"),
            "higher-valuation count mismatch")
    for case in higher_cases:
        ell, u, v, q, exponent = (case[key] for key in ("ell", "u", "v", "q", "valuation"))
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
        require(all(value == cuda.get("cpu_output_digest") for value in repeat_digests),
                "CUDA repeat digest differs from CPU reference")
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
        shared_checked = True

    require(independent.get("verification") == "passed", "independent reproduction did not pass")
    require(independent.get("finite_field_checks_reproduced") == finite.get("signature_prime_checks"),
            "independent finite-field coverage mismatch")
    require(independent.get("lte_cases_reproduced") == lte.get("valid_hypothesis_cases_tested"),
            "independent LTE coverage mismatch")
    require(independent.get("cyclotomic_cases_reproduced") == cyclo.get("pairs_tested"),
            "independent cyclotomic coverage mismatch")

    run_id, source_commit = check_provenance(artifacts)
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
