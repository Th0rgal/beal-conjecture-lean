#!/usr/bin/env python3
"""Record non-secret DGX execution environment metadata."""
from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path


def command(args: list[str]) -> str:
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    return (proc.stdout or proc.stderr).strip()


def main() -> None:
    output = Path(os.environ.get("OUTPUT", "results/environment.json"))
    data = {
        "schema_version": 1,
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "source_commit": os.environ.get("SOURCE_COMMIT", "unknown"),
        "source_branch": os.environ.get("SOURCE_BRANCH", "unknown"),
        "pari_gp": command(["gp", "--version"]).splitlines()[0],
        "cypari2_package": command(["dpkg-query", "-W", "-f=${Version}", "python3-cypari2"]),
        "cuda_nvcc": command(["/usr/local/cuda/bin/nvcc", "--version"]).splitlines()[-1],
        "gpu": command(["nvidia-smi", "--query-gpu=name,compute_cap,pstate,temperature.gpu,power.draw", "--format=csv,noheader"]),
        "vllm_container_state": command(["docker", "ps", "--filter", "name=vllm-backend", "--format", "{{.Names}}|{{.Status}}"]),
        "gpu_window": os.environ.get("GPU_WINDOW", "not recorded"),
        "cpu_policy": "OMP_NUM_THREADS=2 for the CUDA CPU baseline; cyclotomic census workers=2",
        "notes": "CPU experiments ran beside resident vLLM. CUDA calibration used an exclusive GPU window. Results are bounded computational evidence, not a proof of Beal.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
