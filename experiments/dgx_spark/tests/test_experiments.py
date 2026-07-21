import hashlib
import math
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from bootstrap_provenance_history import branch_for_head
from cyclotomic_census import (
    cyclotomic_plus_cofactor,
    multiplicative_order,
    validate_ells,
    valuation,
)
from finite_field_support import power_subgroup, unit_solution_count
from lte_assumption_miner import lte_holds
from verify_results import VerificationError, check, is_prime


def install_shared_fixture(results: Path, outcome: str) -> None:
    """Upgrade only a copied historical fixture into a schema-v3 probe."""
    for artifact_name in (
        "cyclotomic_census.json", "finite_field_support.json", "lte_assumption_miner.json",
        "independent_reproduction.json", "cuda_modexp_calibration.json",
        "gpu_shared_residency_probe.json", "environment.json",
    ):
        artifact_path = results / artifact_name
        artifact = json.loads(artifact_path.read_text())
        artifact["provenance"].update({
            "run_started_at_utc": "2026-07-21T08:42:18Z",
            "source_branch": "research/dgx-computational-experiments-20260717",
        })
        artifact_path.write_text(json.dumps(artifact))
    shared_path = results / "gpu_shared_residency_probe.json"
    shared = json.loads(shared_path.read_text())
    source_hash = json.loads((results / "environment.json").read_text())["source_files_sha256"][
        "experiments/dgx_spark/cuda_modexp_bench.cu"
    ]
    health = {"service_label": "llama-router", "url": "http://127.0.0.1:18080/health", "exit_code": 0,
              "http_status": 200, "stdout": '{"ok":true}', "stderr": ""}
    health["stdout_sha256"] = hashlib.sha256(health["stdout"].encode()).hexdigest()
    health["stderr_sha256"] = hashlib.sha256(b"").hexdigest()
    environment_path = results / "environment.json"
    environment = json.loads(environment_path.read_text())
    environment["model_service"] = {
        "label": "llama-router", "health_url": health["url"], "required": "true",
    }
    environment_path.write_text(json.dumps(environment))
    shared.update({
        "schema_version": 3,
        "benchmark_binary_sha256": "a" * 64,
        "benchmark_source": "cuda_modexp_bench.cu",
        "benchmark_source_sha256": source_hash,
        "service_identity": {"label": "llama-router", "health_url": health["url"], "required": True},
        "service_health_before": health,
        "service_health_after": dict(health),
    })
    calibration_path = results / "cuda_modexp_calibration.json"
    calibration = json.loads(calibration_path.read_text())
    calibration["benchmark_binary_sha256"] = shared["benchmark_binary_sha256"]
    calibration_path.write_text(json.dumps(calibration))
    if outcome == "success":
        payload = json.loads((results / "cuda_modexp_calibration.json").read_text())
        payload.update({"count": 100_000, "repeats": 1, "mismatches_total": 0,
                        "mismatches_per_repeat": [0], "output_digest_per_repeat": [payload["cpu_output_digest"]]})
        payload["provenance"] = {**payload["provenance"], "run_id": shared["provenance"]["run_id"]}
        shared.update({"benchmark_exit_code": 0, "benchmark_exit_class": "success",
                       "benchmark_stdout": json.dumps(payload), "benchmark_stderr": ""})
    else:
        shared.update({"benchmark_exit_code": 2, "benchmark_exit_class": "cuda_oom",
                       "benchmark_stdout": "", "benchmark_stderr": "CUDA error: out of memory"})
    shared["benchmark_stdout_sha256"] = hashlib.sha256(shared["benchmark_stdout"].encode()).hexdigest()
    shared["benchmark_stderr_sha256"] = hashlib.sha256(shared["benchmark_stderr"].encode()).hexdigest()
    shared_path.write_text(json.dumps(shared))
    independent_path = results / "independent_reproduction.json"
    independent = json.loads(independent_path.read_text())
    independent.update({
        "finite_field_domain_reproduced": {"kernels": [3, 4, 5, 7, 11, 13], "prime_bound": 251},
        "lte_domain_reproduced": {"a_bound": 200, "prime_bound": 97, "n_bound": 31},
        "cyclotomic_domain_reproduced": {"ells": [3, 5, 7, 11], "base_bound": 100},
    })
    independent_path.write_text(json.dumps(independent))


def mutate_shared_success_payload(shared: dict, field: str, value: object) -> None:
    payload = json.loads(shared["benchmark_stdout"])
    if field in {"run_id", "source_commit", "producer_sha256"}:
        payload["provenance"][field] = value
    else:
        payload[field] = value
    shared["benchmark_stdout"] = json.dumps(payload)
    shared["benchmark_stdout_sha256"] = hashlib.sha256(
        shared["benchmark_stdout"].encode()
    ).hexdigest()


def shallow_clone_source(repo: Path, tmp_path: Path) -> tuple[Path, str]:
    """Expose the detached source HEAD under one branch without mutating it."""
    branch = branch_for_head(repo)
    source = tmp_path / "source.git"
    cloned = subprocess.run(
        ["git", "clone", "--bare", f"file://{repo}", str(source)],
        text=True, capture_output=True, check=False,
    )
    if cloned.returncode:
        promisor = subprocess.run(
            ["git", "-C", str(repo), "config", "--bool", "remote.origin.promisor"],
            text=True, capture_output=True, check=False,
        )
        if promisor.stdout.strip() == "true" and "lazy fetching disabled" in cloned.stderr:
            pytest.skip(
                "partial clone cannot serve a local bare source while lazy fetching is disabled"
            )
        cloned.check_returncode()
    subprocess.run(["git", "-C", str(source), "branch", "--force", branch, "HEAD"], check=True)
    return source, branch


def test_partial_clone_source_failure_is_explicitly_skipped(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    source = tmp_path / "source.git"
    failed_clone = subprocess.CompletedProcess(
        ["git", "clone"], 128, "", "fatal: lazy fetching disabled"
    )
    promisor = subprocess.CompletedProcess(
        ["git", "config"], 0, "true\n", ""
    )

    monkeypatch.setattr("test_experiments.branch_for_head", lambda _repo: "main")
    monkeypatch.setattr("test_experiments.subprocess.run", lambda args, **_kwargs:
                        failed_clone if args[1] == "clone" else promisor)

    with pytest.raises(pytest.skip.Exception, match="partial clone cannot serve"):
        shallow_clone_source(repo, tmp_path)
    assert not source.exists()


def test_non_partial_clone_source_failure_is_not_skipped(tmp_path, monkeypatch):
    failed_clone = subprocess.CompletedProcess(
        ["git", "clone"], 128, "", "fatal: unrelated clone failure"
    )
    non_promisor = subprocess.CompletedProcess(
        ["git", "config"], 0, "false\n", ""
    )

    monkeypatch.setattr("test_experiments.branch_for_head", lambda _repo: "main")
    monkeypatch.setattr("test_experiments.subprocess.run", lambda args, **_kwargs:
                        failed_clone if args[1] == "clone" else non_promisor)

    with pytest.raises(subprocess.CalledProcessError):
        shallow_clone_source(tmp_path / "repo", tmp_path)


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


def test_verifier_rejects_fixture_without_domain_snapshots(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    independent_path = results / "independent_reproduction.json"
    independent = json.loads(independent_path.read_text())
    for field in (
        "finite_field_domain_reproduced",
        "lte_domain_reproduced",
        "cyclotomic_domain_reproduced",
    ):
        del independent[field]
    independent_path.write_text(json.dumps(independent))
    with pytest.raises(VerificationError, match="domain snapshot missing"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


def test_verifier_rejects_lte_counterexample_under_wrong_removed_assumption(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    lte_path = results / "lte_assumption_miner.json"
    lte = json.loads(lte_path.read_text())
    cases = lte["minimal_counterexamples_when_assumption_removed"]
    cases["remove_odd_n"] = cases["remove_q_divides_sum"]
    lte_path.write_text(json.dumps(lte))

    with pytest.raises(VerificationError, match="does not match removed assumption"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


def test_verifier_rejects_null_required_lte_counterexample(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    lte_path = results / "lte_assumption_miner.json"
    lte = json.loads(lte_path.read_text())
    lte["minimal_counterexamples_when_assumption_removed"]["remove_odd_n"] = None
    lte_path.write_text(json.dumps(lte))

    with pytest.raises(VerificationError, match="required for removed assumption remove_odd_n"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


def test_verifier_rejects_wrong_lte_predicted_rhs_valuation(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    lte_path = results / "lte_assumption_miner.json"
    lte = json.loads(lte_path.read_text())
    for case in lte["minimal_counterexamples_when_assumption_removed"].values():
        if case is not None:
            case["rhs_valuation"] = 999
    lte_path.write_text(json.dumps(lte))

    with pytest.raises(VerificationError, match="RHS valuation mismatch"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("valid_hypothesis_violations", None, "valid_hypothesis_violations"),
        ("minimal_counterexamples_when_assumption_removed", None, "minimal counterexamples"),
        ("minimal_counterexamples_when_assumption_removed", {}, "assumption keys"),
    ],
)
def test_verifier_rejects_missing_or_malformed_mandatory_lte_evidence(
    tmp_path, field, replacement, message
):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    lte_path = results / "lte_assumption_miner.json"
    lte = json.loads(lte_path.read_text())
    if replacement is None:
        del lte[field]
    else:
        lte[field] = replacement
    lte_path.write_text(json.dumps(lte))

    with pytest.raises(VerificationError, match=message):
        check(results, cuda_policy="ignore", shared_policy="ignore")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda case: case.update(q="3"), "invalid value types"),
        (lambda case: case.pop("rhs_valuation"), "invalid fields"),
        (lambda case: case.update(unexpected=0), "invalid fields"),
    ],
)
def test_verifier_rejects_malformed_lte_counterexample_schema(tmp_path, mutation, message):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    lte_path = results / "lte_assumption_miner.json"
    lte = json.loads(lte_path.read_text())
    mutation(lte["minimal_counterexamples_when_assumption_removed"]["remove_odd_n"])
    lte_path.write_text(json.dumps(lte))

    with pytest.raises(VerificationError, match=message):
        check(results, cuda_policy="ignore", shared_policy="ignore")


def test_valid_lte_evidence_schema_passes_replay(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, "cuda_oom")
    report = check(results, cuda_policy="ignore", shared_policy="ignore")
    assert report["lte_counterexamples_replayed"] == 3


def test_cuda_producer_and_suite_cover_complete_provenance_contract():
    root = Path(__file__).resolve().parents[1]
    producer = (root / "cuda_modexp_bench.cu").read_text()
    suite = (root / "run_suite.sh").read_text()
    for option, output_field in (
        ("--run-started-at-utc", '\\"run_started_at_utc\\"'),
        ("--source-branch", '\\"source_branch\\"'),
    ):
        assert option in producer
        assert output_field in producer
        variable = "RUN_STARTED_AT_UTC" if "started" in option else "SOURCE_BRANCH"
        assert f'{option} "${variable}"' in suite


def test_shared_probe_passes_complete_provenance_to_benchmark(tmp_path):
    root = Path(__file__).resolve().parents[1]
    benchmark = tmp_path / "benchmark"
    benchmark.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$@\" > \"$CAPTURED_ARGS\"\n"
        "exit 0\n"
    )
    benchmark.chmod(0o755)
    curl = tmp_path / "curl"
    curl.write_text("#!/bin/sh\nprintf '{\\\"ok\\\":true}\\n200'\n")
    curl.chmod(0o755)
    output = tmp_path / "probe.json"
    captured = tmp_path / "benchmark.args"
    env = {
        **os.environ,
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "CAPTURED_ARGS": str(captured),
        "RUN_ID": "probe-test",
        "RUN_STARTED_AT_UTC": "2026-07-21T12:34:56Z",
        "SOURCE_BRANCH": "research/dgx-computational-experiments-20260717",
        "SOURCE_COMMIT": "c8c8014f381f7aa52d454ac4cb9a44f86e5c9bf0",
        "SOURCE_TREE_CLEAN": "true",
    }
    subprocess.run(
        [sys.executable, str(root / "gpu_residency_probe.py"),
         "--benchmark", str(benchmark), "--output", str(output),
         "--service-label", "test-service",
         "--service-health-url", "http://127.0.0.1/health"],
        env=env, check=True, capture_output=True, text=True,
    )

    arguments = captured.read_text().splitlines()
    assert arguments[arguments.index("--run-started-at-utc") + 1] == env["RUN_STARTED_AT_UTC"]
    assert arguments[arguments.index("--source-branch") + 1] == env["SOURCE_BRANCH"]
    assert json.loads(output.read_text())["benchmark_exit_class"] == "success"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("run_started_at_utc", None, "invalid run_started_at_utc"),
        ("run_started_at_utc", "not-a-UTC-timestamp", "invalid run_started_at_utc"),
        ("source_branch", None, "invalid source_branch"),
        ("source_branch", 7, "invalid source_branch"),
    ],
)
def test_verifier_rejects_missing_or_malformed_cuda_provenance(
    tmp_path, field, value, message
):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, "cuda_oom")
    cuda_path = results / "cuda_modexp_calibration.json"
    cuda = json.loads(cuda_path.read_text())
    if value is None:
        del cuda["provenance"][field]
    else:
        cuda["provenance"][field] = value
    cuda_path.write_text(json.dumps(cuda))

    with pytest.raises(VerificationError, match=message):
        check(results, cuda_policy="required", shared_policy="ignore")


def test_verifier_primality_check():
    assert is_prime(2) and is_prime(7789)
    assert not is_prime(1) and not is_prime(7 * 11)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("support_forcing", 491), "exceeds declared prime_bound"),
        (("prime_bound", 2), "exceeds declared prime_bound"),
        (("kernels", [4, 5, 7, 11, 13]), "outside declared finite-field kernels"),
    ],
)
def test_verifier_rejects_finite_field_witnesses_outside_declared_domain(
    tmp_path, mutation, message
):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    finite_path = results / "finite_field_support.json"
    finite = json.loads(finite_path.read_text())
    field, value = mutation
    if field == "support_forcing":
        row = next(row for row in finite[field] if row["signature"] == [7, 7, 7])
        row["support_forcing_primes"][0]["prime"] = value
    else:
        finite["parameters"][field] = value
    finite_path.write_text(json.dumps(finite))

    with pytest.raises(VerificationError, match=message):
        check(results, cuda_policy="ignore", shared_policy="ignore")


def test_verifier_rejects_duplicate_finite_field_witness(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    finite_path = results / "finite_field_support.json"
    finite = json.loads(finite_path.read_text())
    witnesses = next(
        row["support_forcing_primes"] for row in finite["support_forcing"]
        if len(row["support_forcing_primes"]) >= 2
    )
    witnesses[-1] = dict(witnesses[0])
    finite_path.write_text(json.dumps(finite))

    with pytest.raises(VerificationError, match="duplicate finite-field witness"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


@pytest.mark.parametrize(
    "field",
    ("factor_identity_failures", "gcd_failures", "order_failures", "congruence_failures"),
)
def test_verifier_rejects_missing_nonlist_or_nonempty_cyclotomic_failure_lists(tmp_path, field):
    source = Path(__file__).resolve().parents[1] / "results"
    for suffix, value in (("missing", None), ("nonlist", {}), ("nonempty", [{"failure": True}])):
        results = tmp_path / f"results-{field}-{suffix}"
        shutil.copytree(source, results)
        cyclo_path = results / "cyclotomic_census.json"
        cyclo = json.loads(cyclo_path.read_text())
        if suffix == "missing":
            del cyclo[field]
        else:
            cyclo[field] = value
        cyclo_path.write_text(json.dumps(cyclo))

        with pytest.raises(VerificationError, match=field):
            check(results, cuda_policy="ignore", shared_policy="ignore")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("base_bound", 100), "outside declared base_bound"),
        (("ells", [5, 7, 11]), "outside declared ells"),
    ],
)
def test_verifier_rejects_cyclotomic_witnesses_outside_declared_domain(
    tmp_path, mutation, message
):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    cyclo_path = results / "cyclotomic_census.json"
    cyclo = json.loads(cyclo_path.read_text())
    field, value = mutation
    cyclo["parameters"][field] = value
    if field == "base_bound":
        cyclo["higher_valuation_cases"].append({
            "ell": 3, "u": 101, "v": 8, "q": 7, "valuation": 2, "cofactor": "9457",
        })
        cyclo["higher_valuation_occurrences"] += 1
        independent_path = results / "independent_reproduction.json"
        independent = json.loads(independent_path.read_text())
        independent["cyclotomic_higher_valuation_occurrences_reproduced"] += 1
        independent_path.write_text(json.dumps(independent))
    cyclo_path.write_text(json.dumps(cyclo))

    with pytest.raises(VerificationError, match=message):
        check(results, cuda_policy="ignore", shared_policy="ignore")


def test_verifier_rejects_duplicate_cyclotomic_witness(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    cyclo_path = results / "cyclotomic_census.json"
    cyclo = json.loads(cyclo_path.read_text())
    cyclo["higher_valuation_cases"][-1] = dict(cyclo["higher_valuation_cases"][0])
    cyclo_path.write_text(json.dumps(cyclo))

    with pytest.raises(VerificationError, match="duplicate cyclotomic witness"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


def test_verifier_accepts_promoted_checkpoint_with_optional_gpu_artifacts_ignored():
    results = Path(__file__).resolve().parents[1] / "results"
    report = check(results, cuda_policy="ignore", shared_policy="ignore")
    assert report["verification"] == "passed"
    assert report["cuda_all_repeats_differentially_checked"] is False
    assert report["shared_residency_outcome_checked"] is False


@pytest.mark.parametrize("outcome", ("success", "cuda_oom"))
def test_verifier_accepts_each_shared_residency_outcome(tmp_path, outcome):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / outcome
    shutil.copytree(source, results)
    install_shared_fixture(results, outcome)
    report = check(results, cuda_policy="required", shared_policy="required")
    assert report["shared_residency_outcome_checked"] is True


@pytest.mark.parametrize(
    ("outcome", "mutate", "message"),
    [
        ("success", lambda shared: shared["service_identity"].update(label="other-service"),
         "service identity differs from environment manifest"),
        ("success", lambda shared: None,
         "shared-residency service identity differs from environment manifest"),
        ("cuda_oom", lambda shared: shared["service_health_after"].update(http_status=503),
         "did not positively observe service health after"),
        ("success", lambda shared: shared.update(benchmark_exit_class="cuda_oom"),
         "CUDA OOM exit class has zero exit code"),
        ("success", lambda shared: shared.update(benchmark_binary_sha256="not-a-hash"),
         "malformed benchmark binary hash"),
        ("success", lambda shared: shared.update(benchmark_source_sha256="0" * 64),
         "benchmark source hash differs"),
        ("success", lambda shared: mutate_shared_success_payload(shared, "run_id", "other-run"),
         "stdout run ID differs"),
        ("success", lambda shared: mutate_shared_success_payload(shared, "producer_sha256", "0" * 64),
         "stdout producer provenance differs"),
        ("success", lambda shared: shared.update(probe_count=1), "unexpected probe count"),
        ("success", lambda shared: shared.update(benchmark_exit_class="unexpected_error"),
         "unexpected benchmark exit class"),
    ],
)
def test_verifier_rejects_shared_residency_contract_mutants(tmp_path, outcome, mutate, message):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, outcome)
    path = results / "gpu_shared_residency_probe.json"
    shared = json.loads(path.read_text())
    mutate(shared)
    path.write_text(json.dumps(shared))
    if message == "shared-residency service identity differs from environment manifest":
        environment_path = results / "environment.json"
        environment = json.loads(environment_path.read_text())
        environment["model_service"]["label"] = "other-service"
        environment_path.write_text(json.dumps(environment))
    with pytest.raises(VerificationError, match=message):
        check(results, cuda_policy="required", shared_policy="required")


@pytest.mark.parametrize(
    ("artifact", "mutations"),
    [
        ("cuda_modexp_calibration.json", [{"count": 4_000_001}]),
        ("cuda_modexp_calibration.json", [{"exponent": 65_539}]),
        ("cuda_modexp_calibration.json", [{"modulus": 2_147_483_629}]),
        ("cuda_modexp_calibration.json", [{
            "cpu_output_digest": "0000000000000000",
            "output_digest_per_repeat": ["0000000000000000"] * 5,
        }]),
    ],
)
def test_verifier_rejects_mutated_required_gpu_calibration_or_post_probe_state(
    tmp_path, artifact, mutations
):
    source = Path(__file__).resolve().parents[1] / "results"
    for number, mutation in enumerate(mutations):
        results = tmp_path / f"results-{number}"
        shutil.copytree(source, results)
        artifact_path = results / artifact
        value = json.loads(artifact_path.read_text())
        value.update(mutation)
        artifact_path.write_text(json.dumps(value))

        with pytest.raises(VerificationError):
            check(results, cuda_policy="required", shared_policy="ignore")


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
    assert report["finite_field_domain_reproduced"] == {
        "kernels": [3, 4, 5, 7, 11, 13], "prime_bound": 251,
    }
    assert report["lte_domain_reproduced"] == {
        "a_bound": 200, "prime_bound": 97, "n_bound": 31,
    }
    assert report["cyclotomic_domain_reproduced"] == {
        "ells": [3, 5, 7, 11], "base_bound": 100,
    }


@pytest.mark.parametrize(
    ("artifact", "parameter", "widened", "family"),
    [
        ("finite_field_support.json", "prime_bound", 257, "finite-field"),
        ("lte_assumption_miner.json", "n_bound", 33, "LTE"),
        ("cyclotomic_census.json", "base_bound", 101, "cyclotomic"),
    ],
)
def test_verifier_rejects_widened_producer_domain_not_in_independent_snapshot(
    tmp_path, artifact, parameter, widened, family
):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, "cuda_oom")
    artifact_path = results / artifact
    value = json.loads(artifact_path.read_text())
    value["parameters"][parameter] = widened
    artifact_path.write_text(json.dumps(value))

    with pytest.raises(VerificationError, match=f"independent {family} domain snapshot differs"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


@pytest.mark.parametrize(
    ("snapshot", "parameter", "replacement", "family"),
    [
        ("finite_field_domain_reproduced", "prime_bound", 257, "finite-field"),
        ("lte_domain_reproduced", "a_bound", 201, "LTE"),
        ("cyclotomic_domain_reproduced", "ells", [3, 5, 7], "cyclotomic"),
    ],
)
def test_verifier_rejects_independent_domain_parameter_substitution(
    tmp_path, snapshot, parameter, replacement, family
):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, "cuda_oom")
    report_path = results / "independent_reproduction.json"
    report = json.loads(report_path.read_text())
    report[snapshot][parameter] = replacement
    report_path.write_text(json.dumps(report))

    with pytest.raises(VerificationError, match=f"independent {family} domain snapshot differs"):
        check(results, cuda_policy="ignore", shared_policy="ignore")


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
        check(results, cuda_policy="required", shared_policy="ignore")


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
        check(results, cuda_policy="required", shared_policy="ignore")


@pytest.mark.parametrize(
    ("artifact", "field", "bad_value", "message"),
    [
        ("cuda_modexp_calibration.json", "run_started_at_utc", "2026-07-21T08:42:19Z", "mixed run start times"),
        ("cuda_modexp_calibration.json", "source_branch", "other-branch", "mixed source branches"),
    ],
)
def test_verifier_rejects_mixed_required_run_provenance(tmp_path, artifact, field, bad_value, message):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, "cuda_oom")
    path = results / artifact
    value = json.loads(path.read_text())
    value["provenance"][field] = bad_value
    path.write_text(json.dumps(value))
    with pytest.raises(VerificationError, match=message):
        check(results, cuda_policy="required", shared_policy="required")


@pytest.mark.parametrize("mutate", [
    lambda source_hashes: source_hashes.pop("experiments/dgx_spark/README.md"),
    lambda source_hashes: source_hashes.update({"experiments/dgx_spark/stale.py": "0" * 64}),
])
def test_verifier_rejects_incomplete_or_stale_source_manifest(tmp_path, mutate):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, "cuda_oom")
    path = results / "environment.json"
    environment = json.loads(path.read_text())
    mutate(environment["source_files_sha256"])
    path.write_text(json.dumps(environment))
    with pytest.raises(VerificationError, match="source manifest is incomplete or contains stale paths"):
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
        check(results, cuda_policy="required", shared_policy="ignore")


def test_verifier_rejects_tree_oid_as_source_commit(tmp_path):
    source = Path(__file__).resolve().parents[1] / "results"
    results = tmp_path / "results"
    shutil.copytree(source, results)
    install_shared_fixture(results, "cuda_oom")
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
        check(results, cuda_policy="required", shared_policy="ignore")


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
        check(results, cuda_policy="required", shared_policy="ignore")


def test_shallow_clone_bootstrap_fetches_only_needed_producer_history(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    source, branch = shallow_clone_source(repo, tmp_path)
    shallow = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, "--single-branch",
         f"file://{source}", str(shallow)],
        check=True,
    )
    producer_commit = json.loads(
        (shallow / "experiments/dgx_spark/results/environment.json").read_text()
    )["provenance"]["source_commit"]
    assert subprocess.run(
        ["git", "-C", str(shallow), "cat-file", "-e", f"{producer_commit}^{{commit}}"],
        check=False,
    ).returncode != 0

    bootstrap = Path(__file__).resolve().parents[1] / "bootstrap_provenance_history.py"
    subprocess.run(
        [sys.executable, str(bootstrap), "--repo", str(shallow),
         "--results", str(shallow / "experiments/dgx_spark/results")],
        text=True, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "-C", str(shallow), "merge-base", "--is-ancestor", producer_commit, "HEAD"],
        check=True,
    )

    verifier = shallow / "experiments/dgx_spark/verify_results.py"
    env = {**os.environ,
           "SOURCE_TREE_CLEAN": "true", "SOURCE_COMMIT": subprocess.run(
               ["git", "-C", str(shallow), "rev-parse", "HEAD"], text=True,
               capture_output=True, check=True,
           ).stdout.strip(), "SOURCE_BRANCH": branch, "RUN_ID": "shallow-bootstrap-test",
           "RUN_STARTED_AT_UTC": "2026-07-17T00:00:00Z",
           "PYTHONPATH": str(shallow / "experiments/dgx_spark")}
    verified = subprocess.run(
        [sys.executable, str(verifier), "--results",
         str(shallow / "experiments/dgx_spark/results"), "--cuda-policy", "required",
         "--shared-policy", "ignore", "--output", str(tmp_path / "receipt.json")],
        text=True, capture_output=True, check=False, env=env,
    )
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["verification"] == "passed"


def test_detached_shallow_clone_bootstrap_uses_the_unique_origin_branch(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    source, branch = shallow_clone_source(repo, tmp_path)
    shallow = tmp_path / "detached-shallow"
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, "--single-branch",
         f"file://{source}", str(shallow)],
        check=True,
    )
    subprocess.run(["git", "-C", str(shallow), "checkout", "--detach"], check=True)
    producer_commit = json.loads(
        (shallow / "experiments/dgx_spark/results/environment.json").read_text()
    )["provenance"]["source_commit"]
    bootstrap = Path(__file__).resolve().parents[1] / "bootstrap_provenance_history.py"
    subprocess.run(
        [sys.executable, str(bootstrap), "--repo", str(shallow),
         "--results", str(shallow / "experiments/dgx_spark/results")],
        text=True, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "-C", str(shallow), "merge-base", "--is-ancestor", producer_commit, "HEAD"],
        check=True,
    )
    remote_refs = subprocess.run(
        ["git", "-C", str(shallow), "for-each-ref", "--format=%(refname:short) %(symref)",
         "--contains", "HEAD"],
        text=True, capture_output=True, check=True,
    ).stdout.splitlines()
    detached_branch = next(
        line.split()[0] for line in remote_refs
        if len(line.split()) == 1 and line.startswith("origin/")
    )
    assert detached_branch == f"origin/{branch}"
    verifier = shallow / "experiments/dgx_spark/verify_results.py"
    env = {**os.environ,
           "SOURCE_TREE_CLEAN": "true", "SOURCE_COMMIT": subprocess.run(
               ["git", "-C", str(shallow), "rev-parse", "HEAD"], text=True,
               capture_output=True, check=True,
           ).stdout.strip(), "SOURCE_BRANCH": detached_branch, "RUN_ID": "detached-bootstrap-test",
           "RUN_STARTED_AT_UTC": "2026-07-17T00:00:00Z",
           "PYTHONPATH": str(shallow / "experiments/dgx_spark")}
    verified = subprocess.run(
        [sys.executable, str(verifier), "--results",
         str(shallow / "experiments/dgx_spark/results"), "--cuda-policy", "required",
         "--shared-policy", "ignore", "--output", "/dev/null"],
        text=True, capture_output=True, check=False, env=env,
    )
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["verification"] == "passed"


def test_strict_checksum_accepts_the_promoted_checkpoint_receipt():
    repo = Path(__file__).resolve().parents[3]
    receipt = repo / "experiments/dgx_spark/results/SHA256SUMS"
    checked = subprocess.run(
        ["sha256sum", "--strict", "-c", str(receipt)],
        cwd=repo, text=True, capture_output=True, check=False,
    )
    assert checked.returncode == 0, checked.stderr
    assert "verify_results.py: OK" in checked.stdout


def test_strict_checksum_rejects_mutated_receipt_covered_source(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    relative = Path("experiments/dgx_spark/run_suite.sh")
    copied = tmp_path / relative
    copied.parent.mkdir(parents=True)
    shutil.copyfile(repo / relative, copied)
    expected = hashlib.sha256(copied.read_bytes()).hexdigest()
    receipt = tmp_path / "SHA256SUMS"
    receipt.write_text(f"{expected}  {relative}\n")
    copied.write_text(copied.read_text() + "# mutation\n")

    checked = subprocess.run(
        ["sha256sum", "--strict", "-c", str(receipt)],
        cwd=tmp_path, text=True, capture_output=True, check=False,
    )
    assert checked.returncode != 0
    assert f"{relative}: FAILED" in checked.stdout


def test_run_suite_tests_checkpoint_before_rewriting_results():
    script = (Path(__file__).resolve().parents[1] / "run_suite.sh").read_text()
    test_phase = script.index('python3 -m pytest -q "$ROOT/tests"')
    receipt_covered_rewrite = script.index('python3 "$ROOT/verify_results.py"')
    receipt_refresh = script.index('sha256sum "${manifest[@]}" > experiments/dgx_spark/results/SHA256SUMS')
    assert test_phase < receipt_covered_rewrite < receipt_refresh


def test_run_suite_override_contract_is_explicit_and_fail_closed():
    script = (Path(__file__).resolve().parents[1] / "run_suite.sh").read_text()
    # Caller-supplied source provenance is overwritten from the checkout.
    assert 'SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD)' in script
    assert 'SOURCE_BRANCH=$(git -C "$REPO_ROOT" branch --show-current)' in script
    # Execution-mode switches and the service-required switch reject unknown values,
    # rather than treating a typo as an omitted verification phase.
    assert 'for flag in RUN_CPU RUN_CUDA RUN_SHARED_PROBE RUN_TESTS; do' in script
    assert '"${!flag}" != "0" && "${!flag}" != "1"' in script
    assert 'MODEL_SERVICE_REQUIRED must be true or false' in script
    # A requested shared phase cannot run without an explicit service identity.
    assert 'MODEL_SERVICE_LABEL and MODEL_SERVICE_HEALTH_URL are required for shared probe' in script


def test_bootstrap_rejects_a_foreign_producer_commit(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    isolated = tmp_path / "isolated"
    # Keep this synthetic commit independent of the developer/CI Git config.
    # `commit-tree` needs an identity even though no working-tree commit is made.
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir()
    git_env = {
        **os.environ,
        "HOME": str(empty_home),
        "XDG_CONFIG_HOME": str(empty_home / "xdg-config"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "DGX test author",
        "GIT_AUTHOR_EMAIL": "dgx-test-author@example.invalid",
        "GIT_COMMITTER_NAME": "DGX test committer",
        "GIT_COMMITTER_EMAIL": "dgx-test-committer@example.invalid",
    }
    subprocess.run(["git", "clone", str(repo), str(isolated)], check=True, env=git_env)
    tree = subprocess.run(
        ["git", "-C", str(isolated), "write-tree"], text=True, capture_output=True, check=True,
    ).stdout.strip()
    foreign_commit = subprocess.run(
        ["git", "-C", str(isolated), "commit-tree", tree, "-m", "foreign producer"],
        text=True, capture_output=True, check=True, env=git_env,
    ).stdout.strip()
    results = tmp_path / "results"
    results.mkdir()
    (results / "environment.json").write_text(
        json.dumps({"provenance": {"source_commit": foreign_commit}})
    )
    bootstrap = Path(__file__).resolve().parents[1] / "bootstrap_provenance_history.py"
    rejected = subprocess.run(
        [sys.executable, str(bootstrap), "--repo", str(isolated), "--results", str(results)],
        text=True, capture_output=True, check=False,
    )
    assert rejected.returncode != 0
    assert "not an ancestor" in rejected.stderr
