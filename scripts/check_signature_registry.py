#!/usr/bin/env python3
"""Fail-closed validator for the checked Beal signature registry."""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "signatures" / "registry.json"
REQUIRED = {"id", "signature", "status", "formal_declaration", "assumptions",
            "literature_source", "certificate_dependency", "last_audit"}
STATUSES = {"solved", "reduction-solved", "open_source_audit_pending"}

def declarations() -> set[str]:
    result = set()
    for path in (ROOT / "BealUnified").rglob("*.lean"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^\s*(?:theorem|lemma|def|structure)\s+([A-Za-z_][\w']*)", text, re.M):
            result.add("BealUnified." + match.group(1))
    return result

def fail(message: str) -> None:
    print(f"registry validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)

try:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    fail(str(exc))
if data.get("schema_version") != 1 or not isinstance(data.get("entries"), list):
    fail("expected schema_version 1 and entries array")
ids, signatures, known = set(), set(), declarations()
for entry in data["entries"]:
    if not isinstance(entry, dict) or set(entry) != REQUIRED:
        fail("every entry must have exactly the required schema fields")
    if entry["id"] in ids or entry["signature"] in signatures:
        fail("duplicate id or signature")
    ids.add(entry["id"]); signatures.add(entry["signature"])
    if entry["status"] not in STATUSES:
        fail(f"unknown status for {entry['id']}")
    decl = entry["formal_declaration"]
    if decl is not None and decl not in known:
        fail(f"Lean declaration does not exist: {decl}")
    if entry["status"] == "solved" and decl is None:
        fail(f"solved entry lacks a formal declaration: {entry['id']}")
print(f"registry validation passed ({len(data['entries'])} entries)")
