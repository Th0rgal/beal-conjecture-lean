#!/usr/bin/env python3
"""Fetch the bounded producer history needed to verify committed artifacts.

The verifier deliberately reads recorded producer sources from the producing
Git commit.  A depth-one clone therefore needs this explicit, bounded bootstrap
before verification; it never treats an unconnected fetched object as trusted.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


HEX_40 = re.compile(r"[0-9a-f]{40}")
MAX_INCREMENTAL_DEEPENS = 16


class BootstrapError(RuntimeError):
    pass


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=False
    )


def producer_commit(results: Path) -> str:
    try:
        environment = json.loads((results / "environment.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"cannot read environment provenance: {exc}") from exc
    provenance = environment.get("provenance")
    commit = provenance.get("source_commit") if isinstance(provenance, dict) else None
    if not isinstance(commit, str) or HEX_40.fullmatch(commit) is None:
        raise BootstrapError("environment has invalid producer source_commit")
    return commit


def is_ancestor(repo: Path, commit: str) -> bool:
    return git(repo, "merge-base", "--is-ancestor", commit, "HEAD").returncode == 0


def branch_for_head(repo: Path) -> str:
    """Return the one branch that names HEAD without guessing a fetch ref."""
    branch = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch.returncode == 0 and branch.stdout.strip():
        return branch.stdout.strip()

    remote_refs = git(
        repo,
        "for-each-ref",
        "--format=%(refname:short)",
        "--points-at",
        "HEAD",
        "refs/remotes/origin",
    )
    candidates = [
        ref.removeprefix("origin/")
        for ref in remote_refs.stdout.splitlines()
        if ref.startswith("origin/") and ref != "origin/HEAD"
    ]
    if remote_refs.returncode != 0 or len(candidates) != 1:
        raise BootstrapError(
            "a named local branch or one origin branch pointing at HEAD is required "
            "to deepen shallow history"
        )
    return candidates[0]


def bootstrap(repo: Path, results: Path) -> str:
    if git(repo, "rev-parse", "--git-dir").returncode != 0:
        raise BootstrapError(f"not a Git repository: {repo}")
    commit = producer_commit(results)
    if is_ancestor(repo, commit):
        return commit
    shallow = git(repo, "rev-parse", "--is-shallow-repository")
    if shallow.returncode != 0 or shallow.stdout.strip() != "true":
        raise BootstrapError(f"producer commit is not an ancestor of HEAD: {commit}")
    branch = branch_for_head(repo)

    for _ in range(MAX_INCREMENTAL_DEEPENS):
        fetched = git(repo, "fetch", "--no-tags", "--deepen=1", "origin", branch)
        if fetched.returncode != 0:
            detail = fetched.stderr.strip() or fetched.stdout.strip()
            raise BootstrapError(f"bounded producer-history fetch failed: {detail}")
        if is_ancestor(repo, commit):
            return commit
    raise BootstrapError(
        f"producer commit was not reached after {MAX_INCREMENTAL_DEEPENS} bounded deepens: {commit}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--results", type=Path, default=Path("experiments/dgx_spark/results"))
    args = parser.parse_args()
    try:
        commit = bootstrap(args.repo.resolve(), args.results.resolve())
    except BootstrapError as exc:
        raise SystemExit(f"PROVENANCE BOOTSTRAP FAILED: {exc}") from exc
    print(f"provenance producer history ready: {commit}")


if __name__ == "__main__":
    main()
