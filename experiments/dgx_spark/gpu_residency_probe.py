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


def command(args: list[str]) -> str:
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    return (proc.stdout or proc.stderr).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=100_000)
    args = parser.parse_args()
    if args.count <= 0 or not args.benchmark.exists():
        raise SystemExit("invalid count or missing benchmark")

    before_arbiter = command(["systemctl", "is-active", "spark-arbiter.service"])
    before_vllm = command(["docker", "inspect", "-f", "{{.State.Status}}", "vllm-backend"])
    before_health = command(["curl", "-fsS", "http://127.0.0.1:8000/health"])
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run([
        str(args.benchmark), "--count", str(args.count), "--repeats", "1",
        "--run-id", os.environ["RUN_ID"],
        "--source-commit", os.environ["SOURCE_COMMIT"],
        "--source-tree-clean", os.environ["SOURCE_TREE_CLEAN"],
        "--producer-sha256", sha256_file(Path(__file__).with_name("cuda_modexp_bench.cu")),
    ], text=True, capture_output=True, check=False)
    finished = datetime.now(timezone.utc).isoformat()
    after_arbiter = command(["systemctl", "is-active", "spark-arbiter.service"])
    after_vllm = command(["docker", "inspect", "-f", "{{.State.Status}}", "vllm-backend"])
    after_health = command(["curl", "-fsS", "http://127.0.0.1:8000/health"])
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    result = {
        "schema_version": 2,
        "experiment": "gpu_shared_residency_probe",
        "started_at_utc": started,
        "finished_at_utc": finished,
        "probe_count": args.count,
        "benchmark_binary_sha256": sha256_file(args.benchmark),
        "benchmark_exit_code": proc.returncode,
        "benchmark_stdout": stdout,
        "benchmark_stderr": stderr,
        "benchmark_stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "benchmark_stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "spark_arbiter_status_before": before_arbiter,
        "spark_arbiter_status_after": after_arbiter,
        "vllm_container_status_before": before_vllm,
        "vllm_container_status_after": after_vllm,
        "vllm_health_before": before_health,
        "vllm_health_after": after_health,
        "provenance": artifact_provenance(__file__),
        "scope": "Platform co-residency observation; not a CUDA arithmetic certificate.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "benchmark_exit_code": proc.returncode,
        "benchmark_stderr": stderr,
        "vllm_container_status_before": before_vllm,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
