#!/usr/bin/env python3
"""Record non-secret DGX environment and exact source provenance."""
from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from provenance import ProvenanceError, artifact_provenance, sha256_file


def command(args: list[str]) -> str:
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    return (proc.stdout or proc.stderr).strip()


def main() -> None:
    output = Path(os.environ.get("OUTPUT", "results/environment.json"))
    script_root = Path(__file__).resolve().parent
    repo_root = script_root.parents[1]
    declared_commit = os.environ.get("SOURCE_COMMIT", "")
    actual_commit = command(["git", "-C", str(repo_root), "rev-parse", "HEAD"])
    if not actual_commit or actual_commit != declared_commit:
        raise ProvenanceError(
            f"declared source commit {declared_commit!r} differs from checkout {actual_commit!r}"
        )
    source_paths = sorted(
        path for path in script_root.rglob("*")
        if path.is_file()
        and not any(part in {"results", "logs", "build", "smoke", "__pycache__", ".pytest_cache"}
                    for part in path.relative_to(script_root).parts)
    )
    source_hashes = {
        str(path.relative_to(repo_root)): sha256_file(path)
        for path in source_paths
    }
    data = {
        "schema_version": 2,
        "experiment": "dgx_environment_manifest",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "pari_gp": command(["gp", "--version"]).splitlines()[0],
        "cypari2_package": command(["dpkg-query", "-W", "-f=${Version}", "python3-cypari2"]),
        "sympy": command(["python3", "-c", "import sympy; print(sympy.__version__)"]),
        "cuda_nvcc": command(["/usr/local/cuda/bin/nvcc", "--version"]).splitlines()[-1],
        "gpu": command(["nvidia-smi", "--query-gpu=name,compute_cap,pstate,temperature.gpu,power.draw", "--format=csv,noheader"]),
        "model_service": {
            "label": os.environ.get("MODEL_SERVICE_LABEL", "not configured"),
            "health_url": os.environ.get("MODEL_SERVICE_HEALTH_URL", "not configured"),
            "required": os.environ.get("MODEL_SERVICE_REQUIRED", "true"),
        },
        "gpu_window": os.environ.get("GPU_WINDOW", "not recorded"),
        "cpu_policy": "cyclotomic workers=2; CUDA CPU reference OMP_NUM_THREADS=2",
        "git_status_at_probe": command(["git", "-C", str(repo_root), "status", "--short"]),
        "source_files_sha256": source_hashes,
        "provenance": artifact_provenance(__file__),
        "scope": "Measured execution metadata; bounded computational evidence, not a proof of Beal.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
