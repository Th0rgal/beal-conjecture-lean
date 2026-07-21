#!/usr/bin/env python3
"""Fail-closed validator for the checked Beal signature registry.

Solved entries must name declarations in the *imported public trusted
environment*, rather than merely names that happen to occur somewhere in the
working tree.  The Lean command shared with the trusted-boundary gate checks
their transitive axiom dependencies against the same allowlist.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "signatures" / "registry.json"
AXIOM_AUDITOR = ROOT / "scripts" / "Axioms.lean"
REQUIRED = {"id", "signature", "status", "formal_declaration", "assumptions",
            "literature_source", "certificate_dependency", "last_audit"}
SOLVED_STATUSES = {"solved", "reduction-solved"}
STATUSES = SOLVED_STATUSES | {"open_source_audit_pending"}


def fail(message: str) -> None:
    raise ValueError(message)


def build_public_root() -> None:
    result = subprocess.run(["lake", "build", "BealUnified"], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        fail("could not build public trusted root:\n" + result.stdout)


def audit_trusted_declaration(declaration: str) -> None:
    """Ask Lean whether declaration is loaded and allowed by Trusted's environment."""
    auditor = AXIOM_AUDITOR.read_text(encoding="utf-8")
    suffix = "#audit_trusted_axioms\n"
    if not auditor.endswith(suffix):
        fail("axiom auditor has an unexpected standalone layout")
    source = auditor.removesuffix(suffix) + f"#audit_trusted_registry_declaration {declaration}\n"
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=ROOT, delete=False) as probe:
        probe.write(source)
        probe_path = pathlib.Path(probe.name)
    try:
        result = subprocess.run(["lake", "env", "lean", str(probe_path)], cwd=ROOT, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    finally:
        probe_path.unlink(missing_ok=True)
    if result.returncode:
        fail(f"declaration is not a trusted, allowlisted registry target: {declaration}\n"
             + result.stdout)


def validate(registry: pathlib.Path) -> int:
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(str(exc))
    if data.get("schema_version") != 1 or not isinstance(data.get("entries"), list):
        fail("expected schema_version 1 and entries array")
    ids, signatures = set(), set()
    trusted_declarations = []
    for entry in data["entries"]:
        if not isinstance(entry, dict) or set(entry) != REQUIRED:
            fail("every entry must have exactly the required schema fields")
        if entry["id"] in ids or entry["signature"] in signatures:
            fail("duplicate id or signature")
        ids.add(entry["id"]); signatures.add(entry["signature"])
        if entry["status"] not in STATUSES:
            fail(f"unknown status for {entry['id']}")
        declaration = entry["formal_declaration"]
        if entry["status"] in SOLVED_STATUSES:
            if not isinstance(declaration, str) or not declaration:
                fail(f"{entry['status']} entry lacks a formal declaration: {entry['id']}")
            trusted_declarations.append(declaration)
        elif declaration is not None:
            fail(f"open entry must not claim a formal declaration: {entry['id']}")
    build_public_root()
    for declaration in trusted_declarations:
        audit_trusted_declaration(declaration)
    return len(data["entries"])


def self_test() -> None:
    """A declaration in opt-in Computational exists on disk but not in Trusted."""
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    data["entries"][0]["formal_declaration"] = "BealUnified.noCounterexampleUpTo_8_8"
    with tempfile.NamedTemporaryFile("w", suffix=".json", dir=ROOT, delete=False) as fixture:
        json.dump(data, fixture)
        fixture_path = pathlib.Path(fixture.name)
    try:
        try:
            validate(fixture_path)
        except ValueError as exc:
            if "not a trusted, allowlisted registry target" not in str(exc):
                raise
        else:
            raise RuntimeError("registry accepted an opt-in computational declaration")
    finally:
        fixture_path.unlink(missing_ok=True)
    print("registry negative fixture rejected an on-disk declaration outside Trusted")


try:
    count = validate(REGISTRY)
    if "--self-test" in sys.argv:
        self_test()
    print(f"registry validation passed ({count} entries)")
except (ValueError, RuntimeError) as exc:
    print(f"registry validation failed: {exc}", file=sys.stderr)
    sys.exit(1)
