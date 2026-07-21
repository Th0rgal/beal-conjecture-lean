#!/usr/bin/env python3
"""Shared exact-run provenance for DGX experiment artifacts."""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


class ProvenanceError(RuntimeError):
    pass


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ProvenanceError(f"required provenance variable {name} is missing")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_provenance(producer: str | Path) -> dict:
    producer_path = Path(producer).resolve()
    clean_text = _required("SOURCE_TREE_CLEAN").lower()
    if clean_text not in {"true", "false"}:
        raise ProvenanceError("SOURCE_TREE_CLEAN must be true or false")
    return {
        "run_id": _required("RUN_ID"),
        "run_started_at_utc": _required("RUN_STARTED_AT_UTC"),
        "produced_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": _required("SOURCE_COMMIT"),
        "source_branch": _required("SOURCE_BRANCH"),
        "source_tree_clean": clean_text == "true",
        "producer": producer_path.name,
        "producer_sha256": sha256_file(producer_path),
    }
