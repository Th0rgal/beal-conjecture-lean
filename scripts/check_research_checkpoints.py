#!/usr/bin/env python3
"""Fail-closed validator for versioned research checkpoint manifests.

Every artifact is read from its recorded historical commit with ``git show``;
the working tree is never accepted as evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"historical-source", "merged-source"}
REQUIRED = {
    "schema_version", "id", "status", "source_commit", "artifacts",
    "verification_commands", "non_claims", "trust_boundary_evidence",
    "validation_evidence", "last_audit",
}


def fail(message: str) -> None:
    raise ValueError(message)


def git(root: Path, *args: str, text: bool = False) -> bytes | str:
    run = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, check=False)
    if run.returncode:
        fail(run.stderr.decode("utf-8", "replace").strip() or "git command failed")
    return run.stdout.decode("utf-8") if text else run.stdout


def safe_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        fail("artifact path must be a nonempty string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts or len(path.parts) < 2:
        fail(f"unsafe or unstable artifact path: {value!r}")
    return value


def strings(name: str, value: object, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value) or not all(isinstance(x, str) and x for x in value):
        fail(f"{name} must be a nonempty array of nonempty strings")
    return value


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_manifest(root: Path, path: Path, seen_ids: set[str]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=reject_duplicate_keys)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path}: {exc}")
    if not isinstance(data, dict) or set(data) != REQUIRED or data.get("schema_version") != 1:
        fail(f"{path}: expected exactly the version-1 checkpoint schema")
    checkpoint_id = data["id"]
    if not isinstance(checkpoint_id, str) or not checkpoint_id or checkpoint_id in seen_ids:
        fail(f"{path}: duplicate or invalid id")
    seen_ids.add(checkpoint_id)
    if data["status"] not in STATUSES:
        fail(f"{path}: unsupported status")
    source = data["source_commit"]
    if not isinstance(source, str) or not SHA1.fullmatch(source):
        fail(f"{path}: source_commit must be a full lowercase SHA")
    head = git(root, "rev-parse", "HEAD", text=True).strip()
    if source == head:
        fail(f"{path}: source_commit must be historical, not HEAD")
    git(root, "cat-file", "-e", f"{source}^{{commit}}")
    if subprocess.run(["git", "merge-base", "--is-ancestor", source, "HEAD"], cwd=root).returncode:
        fail(f"{path}: source_commit is not an ancestor of HEAD")
    artifacts = data["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        fail(f"{path}: artifacts must be a nonempty array")
    paths: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"}:
            fail(f"{path}: each artifact needs exactly path and sha256")
        artifact_path = safe_path(artifact["path"])
        digest = artifact["sha256"]
        if artifact_path in paths or not isinstance(digest, str) or not SHA256.fullmatch(digest):
            fail(f"{path}: duplicate path or malformed SHA-256")
        paths.add(artifact_path)
        contents = git(root, "show", f"{source}:{artifact_path}")
        if hashlib.sha256(contents).hexdigest() != digest:
            fail(f"{path}: SHA-256 mismatch for {artifact_path}")
    commands = strings("verification_commands", data["verification_commands"])
    strings("non_claims", data["non_claims"])
    boundary = strings("trust_boundary_evidence", data["trust_boundary_evidence"])
    validation = strings("validation_evidence", data["validation_evidence"])
    if not any("check_trusted_boundary.py" in item for item in boundary):
        fail(f"{path}: missing trust-boundary validation evidence")
    if not any("check_research_checkpoints.py" in item for item in validation):
        fail(f"{path}: missing checkpoint validation evidence")
    for artifact_path in paths:
        required = f"git show {source}:{artifact_path}"
        if not any(required in command for command in commands):
            fail(f"{path}: verification_commands must use {required}")
    if not isinstance(data["last_audit"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["last_audit"]):
        fail(f"{path}: last_audit must be YYYY-MM-DD")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    directory = root / "Research" / "checkpoints"
    manifests = sorted(directory.glob("*.json")) if directory.is_dir() else []
    if not manifests:
        fail("no checkpoint manifests found")
    seen_ids: set[str] = set()
    for manifest in manifests:
        validate_manifest(root, manifest, seen_ids)
    print(f"research checkpoint validation passed ({len(manifests)} manifests)")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"research checkpoint validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
