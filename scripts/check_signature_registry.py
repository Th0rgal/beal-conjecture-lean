#!/usr/bin/env python3
"""Fail-closed validator for the checked Beal signature registry.

Solved entries must name declarations in the *imported public trusted
environment*, rather than merely names that happen to occur somewhere in the
working tree.  The Lean command shared with the trusted-boundary gate checks
their transitive axiom dependencies against the same allowlist.
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "signatures" / "registry.json"
AXIOM_AUDITOR = ROOT / "scripts" / "Axioms.lean"
REQUIRED = {"id", "signature", "status", "formal_declaration", "assumptions",
            "literature_source", "certificate_dependency", "last_audit"}
SOLVED_STATUSES = {"solved", "reduction-solved"}
STATUSES = SOLVED_STATUSES | {"open_source_audit_pending"}
STRING_FIELDS = REQUIRED - {"formal_declaration"}
DATE = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")


def fail(message: str) -> None:
    raise ValueError(message)


def require_string(entry: dict, field: str) -> str:
    value = entry[field]
    if not isinstance(value, str) or not value:
        fail(f"{field} must be a non-empty string")
    return value


def require_audit_date(entry: dict) -> None:
    value = require_string(entry, "last_audit")
    if not DATE.fullmatch(value):
        fail("last_audit must use YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError:
        fail("last_audit must be a valid calendar date")


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
    if (not isinstance(data, dict) or set(data) != {"schema_version", "entries"}
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or not isinstance(data["entries"], list)):
        fail("expected schema_version 1 and entries array")
    ids, signatures = set(), set()
    trusted_declarations = []
    for entry in data["entries"]:
        if not isinstance(entry, dict) or set(entry) != REQUIRED:
            fail("every entry must have exactly the required schema fields")
        for field in STRING_FIELDS:
            require_string(entry, field)
        require_audit_date(entry)
        entry_id = entry["id"]
        signature = entry["signature"]
        if entry_id in ids or signature in signatures:
            fail("duplicate id or signature")
        ids.add(entry_id); signatures.add(signature)
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
    """Reject untrusted declarations and malformed values before any Lean probe."""
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

    for field, malformed in {
        "id": 7,
        "signature": ["(3,3,3)"],
        "status": {"solved": True},
        "formal_declaration": 3,
        "assumptions": None,
        "literature_source": False,
        "certificate_dependency": {"kind": "none"},
        "last_audit": 20260721,
    }.items():
        fixture_data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        fixture_data["entries"][0][field] = malformed
        with tempfile.NamedTemporaryFile("w", suffix=".json", dir=ROOT, delete=False) as fixture:
            json.dump(fixture_data, fixture)
            fixture_path = pathlib.Path(fixture.name)
        try:
            try:
                validate(fixture_path)
            except ValueError:
                pass
            else:
                raise RuntimeError(f"registry accepted malformed {field} field")
        finally:
            fixture_path.unlink(missing_ok=True)

    for malformed_date in ("2026-7-21", "2026-02-30", "21-07-2026"):
        fixture_data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        fixture_data["entries"][0]["last_audit"] = malformed_date
        with tempfile.NamedTemporaryFile("w", suffix=".json", dir=ROOT, delete=False) as fixture:
            json.dump(fixture_data, fixture)
            fixture_path = pathlib.Path(fixture.name)
        try:
            try:
                validate(fixture_path)
            except ValueError:
                pass
            else:
                raise RuntimeError(f"registry accepted malformed last_audit {malformed_date!r}")
        finally:
            fixture_path.unlink(missing_ok=True)
    print("registry negative fixtures rejected every malformed field type and audit date")


try:
    count = validate(REGISTRY)
    if "--self-test" in sys.argv:
        self_test()
    print(f"registry validation passed ({count} entries)")
except (ValueError, RuntimeError) as exc:
    print(f"registry validation failed: {exc}", file=sys.stderr)
    sys.exit(1)
