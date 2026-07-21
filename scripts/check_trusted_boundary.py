#!/usr/bin/env python3
"""Audit the local import closure of the public BealUnified root, fail closed."""
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
# `BealUnified` is the advertised production import.  Starting here, rather
# than at its current `Trusted` implementation detail, makes a future direct
# root import of Challenge or BealConjecture a boundary-gate failure.
START = "BealUnified"
FORBIDDEN = re.compile(r"\b(sorry|admit|axiom)\b|sorryAx")
IMPORT = re.compile(r"^import\s+(\S+)", re.M)

def module_path(module, root=ROOT): return root.joinpath(*module.split(".")).with_suffix(".lean")

def build_public_root():
    """Make the public root import available to both CI and local probes."""
    build = subprocess.run(["lake", "build", START], cwd=ROOT, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if build.returncode:
        raise RuntimeError("could not build public trusted root:\n" + build.stdout)

def closure(start=START, root=ROOT):
    """Return the full local closure, rejecting local escapes from BealUnified.

    Imports supplied by Lean/Mathlib have no source file in this repository and
    are intentionally left to Lean.  Every import that *does* resolve to a
    local source file must stay under BealUnified; silently ignoring a local
    sibling would make the source-token and boundary audit incomplete.
    """
    todo, seen = [start], set()
    while todo:
        module = todo.pop()
        if module in seen: continue
        path = module_path(module, root)
        if not path.exists(): raise RuntimeError(f"missing local module {module}")
        seen.add(module)
        source = path.read_text(encoding="utf-8")
        if FORBIDDEN.search(source): raise RuntimeError(f"forbidden trusted token in {path.relative_to(root)}")
        for dep in IMPORT.findall(source):
            local_dep = module_path(dep, root)
            if local_dep.exists() and dep != "BealUnified" and not dep.startswith("BealUnified."):
                raise RuntimeError(f"local trusted import escapes BealUnified: {dep} from {module}")
            if dep.startswith("BealUnified.Challenge") or dep == "BealUnified.BealConjecture":
                raise RuntimeError(f"forbidden trusted import {dep} from {module}")
            if local_dep.exists():
                todo.append(dep)
    return seen

def run_axiom_audit(extra_source=""):
    """Audit declarations actually loaded by the public trusted import."""
    # The workflow deliberately runs this gate before the project-wide build.
    # Build precisely the root being audited, so clean checkouts and direct
    # invocations do not depend on a pre-existing olean file.
    build_public_root()
    if not extra_source:
        return subprocess.run(["lake", "env", "lean", "scripts/Axioms.lean"], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    auditor = (ROOT / "scripts" / "Axioms.lean").read_text(encoding="utf-8")
    prefix = "import BealUnified\n"
    suffix = "\n#audit_trusted_axioms\n"
    if not auditor.startswith(prefix) or not auditor.endswith(suffix):
        raise RuntimeError("axiom auditor has an unexpected standalone layout")
    source = prefix + auditor.removeprefix(prefix).removesuffix(suffix) + extra_source + suffix
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=ROOT, delete=False) as probe:
        probe.write(source)
        probe_path = pathlib.Path(probe.name)
    try:
        return subprocess.run(["lake", "env", "lean", str(probe_path)], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    finally:
        probe_path.unlink(missing_ok=True)

def self_test():
    # This fixture is temporary and outside the trusted source tree.  The
    # declaration name is deliberately harmless: a name-based/regex audit
    # cannot recognize ``trustWitness`` as an axiom.  The theorem is a newly
    # loaded BealUnified declaration, so this also proves the audit is not
    # limited to a representative, hard-coded declaration list.
    source = """
namespace BealUnified.TrustAuditNegative
axiom trustWitness : True
theorem newlyLoadedTrustedDeclaration : True := trustWitness
theorem injectedSorry : True := by sorry
end BealUnified.TrustAuditNegative
"""
    run = run_axiom_audit(source)
    if (run.returncode == 0 or "unapproved trusted axioms" not in run.stdout
            or "trustWitness" not in run.stdout or "sorryAx" not in run.stdout):
        raise RuntimeError("environment audit accepted the controlled negative fixture:\n" + run.stdout)
    with tempfile.TemporaryDirectory() as directory:
        fixture_root = pathlib.Path(directory)
        (fixture_root / "BealUnified.lean").write_text("import LocalEscape\n", encoding="utf-8")
        (fixture_root / "LocalEscape.lean").write_text("theorem harmless : True := True.intro\n", encoding="utf-8")
        try:
            closure(root=fixture_root)
        except RuntimeError as exc:
            if "escapes BealUnified" not in str(exc):
                raise
        else:
            raise RuntimeError("trusted closure accepted a local non-BealUnified import")
    print("trusted environment negative fixture rejected (unrecognizable-name axiom and sorryAx); local import escape rejected")

try:
    if "--self-test" in sys.argv:
        self_test()
        raise SystemExit(0)
    modules = closure()
    run = run_axiom_audit()
    if run.returncode: raise RuntimeError(run.stdout)
    print(f"trusted boundary passed ({len(modules)} local modules)\n{run.stdout.strip()}")
except Exception as exc:
    print(f"trusted boundary failed: {exc}", file=sys.stderr)
    sys.exit(1)
