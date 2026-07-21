#!/usr/bin/env python3
"""Audit the local import closure of BealUnified.Trusted, fail closed."""
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
START = "BealUnified.Trusted"
FORBIDDEN = re.compile(r"\b(sorry|admit|axiom)\b|sorryAx")
IMPORT = re.compile(r"^import\s+(BealUnified(?:\.[A-Za-z0-9_]+)*)", re.M)

def module_path(module): return ROOT.joinpath(*module.split(".")).with_suffix(".lean")
def closure():
    todo, seen = [START], set()
    while todo:
        module = todo.pop()
        if module in seen: continue
        path = module_path(module)
        if not path.exists(): raise RuntimeError(f"missing local module {module}")
        seen.add(module)
        source = path.read_text(encoding="utf-8")
        if FORBIDDEN.search(source): raise RuntimeError(f"forbidden trusted token in {path.relative_to(ROOT)}")
        for dep in IMPORT.findall(source):
            if dep.startswith("BealUnified.Challenge") or dep == "BealUnified.BealConjecture":
                raise RuntimeError(f"forbidden trusted import {dep} from {module}")
            todo.append(dep)
    return seen

def run_axiom_audit(extra_source=""):
    """Audit declarations actually loaded by a trusted import."""
    if not extra_source:
        return subprocess.run(["lake", "env", "lean", "scripts/Axioms.lean"], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    auditor = (ROOT / "scripts" / "Axioms.lean").read_text(encoding="utf-8")
    prefix = "import BealUnified.Trusted\n"
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
    # This fixture is temporary and outside the Trusted source tree.  The
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
    print("trusted environment negative fixture rejected (unrecognizable-name axiom and sorryAx)")

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
