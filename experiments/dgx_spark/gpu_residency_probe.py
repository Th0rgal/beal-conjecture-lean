#!/usr/bin/env python3
"""Reproducible CUDA allocation probe while the resident model is running."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from provenance import artifact_provenance, sha256_file


def service_health(label: str, url: str) -> dict:
    """Record an HTTP health observation without assuming a service runtime."""
    proc = subprocess.run(
        ["curl", "-sS", "-o", "-", "-w", "\\n%{http_code}", url],
        text=True, capture_output=True, check=False,
    )
    body, separator, status = proc.stdout.rpartition("\n")
    return {
        "service_label": label,
        "url": url,
        "exit_code": proc.returncode,
        "http_status": int(status) if separator and status.isdigit() else None,
        "stdout": body,
        "stderr": proc.stderr.strip(),
        "stdout_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr.strip().encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--service-label", required=True)
    parser.add_argument("--service-health-url", required=True)
    parser.add_argument("--service-required", choices=("true", "false"), default="true")
    args = parser.parse_args()
    if args.count <= 0 or not args.benchmark.exists():
        raise SystemExit("invalid count or missing benchmark")

    service_identity = {
        "label": args.service_label,
        "health_url": args.service_health_url,
        "required": args.service_required == "true",
    }
    before_health = service_health(args.service_label, args.service_health_url)
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run([
        str(args.benchmark), "--count", str(args.count), "--repeats", "1",
        "--run-id", os.environ["RUN_ID"],
        "--run-started-at-utc", os.environ["RUN_STARTED_AT_UTC"],
        "--source-branch", os.environ["SOURCE_BRANCH"],
        "--source-commit", os.environ["SOURCE_COMMIT"],
        "--source-tree-clean", os.environ["SOURCE_TREE_CLEAN"],
        "--producer-sha256", sha256_file(Path(__file__).with_name("cuda_modexp_bench.cu")),
    ], text=True, capture_output=True, check=False)
    finished = datetime.now(timezone.utc).isoformat()
    after_health = service_health(args.service_label, args.service_health_url)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode == 0:
        exit_class = "success"
    elif "cuda" in stderr.lower() and "out of memory" in stderr.lower():
        exit_class = "cuda_oom"
    else:
        exit_class = "unexpected_error"
    result = {
        "schema_version": 3,
        "experiment": "gpu_shared_residency_probe",
        "started_at_utc": started,
        "finished_at_utc": finished,
        "probe_count": args.count,
        "benchmark_binary_sha256": sha256_file(args.benchmark),
        "benchmark_source": "cuda_modexp_bench.cu",
        "benchmark_source_sha256": sha256_file(Path(__file__).with_name("cuda_modexp_bench.cu")),
        "benchmark_exit_code": proc.returncode,
        "benchmark_exit_class": exit_class,
        "benchmark_stdout": stdout,
        "benchmark_stderr": stderr,
        "benchmark_stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "benchmark_stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "service_identity": service_identity,
        "service_health_before": before_health,
        "service_health_after": after_health,
        "provenance": artifact_provenance(__file__),
        "scope": "Platform co-residency observation; not a CUDA arithmetic certificate.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "benchmark_exit_code": proc.returncode,
        "benchmark_stderr": stderr,
        "service_identity": service_identity,
        "service_health_before": before_health,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
