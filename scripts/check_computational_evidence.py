#!/usr/bin/env python3
"""Fail-closed audit of opt-in bounded-search certificates and their module.

This is deliberately not a trusted-boundary gate: native_decide's generated
axiom is outside the trusted allowlist.  The check makes that boundary
explicit, and accepts exactly that generated axiom -- no placeholders and no
additional arbitrary axioms.
"""
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPUTATIONAL_SOURCE = ROOT / "BealUnified" / "Computational.lean"
COMPUTATIONAL_AUDITOR = ROOT / "scripts" / "ComputationalAxioms.lean"
FORBIDDEN_SOURCE_TOKEN = re.compile(r"\b(sorry|admit|axiom)\b|sorryAx")
# Every theorem advertised in the README as computational evidence is audited.
# Each exact-set comparison rejects both missing and additional axioms.
CERTIFICATES = {
    "BealUnified.noCounterexample_bases_lt_two": {
        "Quot.sound",
        "propext",
    },
    "BealUnified.noCounterexampleUpTo_8_8": {
        "BealUnified.noCounterexampleUpTo_8_8._native.native_decide.ax_1_1",
        "Quot.sound",
        "propext",
    },
}
# A pinned axiom set alone is not evidence of the advertised computation: a
# different (or weakened) declaration can retain an allowed dependency.  Probe
# each declaration against its full intended proposition as well.
EXPECTED_PROPOSITIONS = {
    "BealUnified.noCounterexample_bases_lt_two": (
        "∀ A B C x y z : ℕ, A < 2 → B < 2 → C < 2 → "
        "¬ (BealUnified.Solution A B C x y z ∧ Nat.gcd (Nat.gcd A B) C = 1)"
    ),
    "BealUnified.noCounterexampleUpTo_8_8": (
        "BealUnified.hasCounterexampleUpTo 8 8 = false"
    ),
}
# `#print axioms` has two output shapes.  A nonempty set is bracketed, while
# an axiom-free declaration is reported as a sentence.  Match the latter as a
# complete output line so an unrelated diagnostic cannot be mistaken for the
# probe result.
AXIOM_FREE_OUTPUT = re.compile(
    r"^(?:info:\s*)?'[^'\n]+' does not depend on any axioms\s*$", re.M
)
MODULE_AUDIT_OUTPUT = re.compile(r"computational environment declarations audited:\s*(\d+)")

# This audit runs before the full project build in the trust-gate workflow.
# Build its one opt-in target explicitly so a clean checkout has the olean that
# the temporary import probe requires.  Keeping this here makes direct local
# invocation and CI use the same deterministic dependency order.
def build_target():
    build = subprocess.run(["lake", "build", "BealUnified.Computational"], cwd=ROOT,
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           check=False)
    if build.returncode:
        print(build.stdout, file=sys.stderr)
        raise RuntimeError("could not build BealUnified.Computational")

def require_clean_source(path=COMPUTATIONAL_SOURCE):
    """Reject source placeholders before trusting the environment audit.

    The environment audit below is complete for declarations loaded by the
    module.  This direct source check is deliberately fail-closed too, so an
    explicit placeholder is diagnosed even if it is unused.
    """
    source = path.read_text(encoding="utf-8")
    if FORBIDDEN_SOURCE_TOKEN.search(source):
        display_path = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        raise RuntimeError(f"forbidden computational source token in {display_path}")

def run_environment_audit(extra_source=""):
    """Audit every declaration introduced by the computational module.

    The test-only form audits additions to the loaded environment, proving the
    audit rejects an otherwise unused axiom in any namespace.
    """
    if not extra_source:
        return subprocess.run(["lake", "env", "lean", str(COMPUTATIONAL_AUDITOR)], cwd=ROOT,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              check=False)
    auditor = COMPUTATIONAL_AUDITOR.read_text(encoding="utf-8")
    prefix = "import BealUnified.Computational\n"
    suffix = "\n#audit_computational_axioms\n"
    if not auditor.startswith(prefix) or not auditor.endswith(suffix):
        raise RuntimeError("computational axiom auditor has an unexpected standalone layout")
    source = (prefix + auditor.removeprefix(prefix).removesuffix(suffix) + extra_source
              + "\n#audit_current_computational_additions\n")
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=ROOT, delete=False) as probe:
        probe.write(source)
        probe_path = pathlib.Path(probe.name)
    try:
        return subprocess.run(["lake", "env", "lean", str(probe_path)], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    finally:
        probe_path.unlink(missing_ok=True)

def printed_axioms(source: str, declaration: str):
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=ROOT, delete=False) as probe:
        probe.write(source + f"\n#print axioms {declaration}\n")
        probe_path = pathlib.Path(probe.name)
    try:
        result = subprocess.run(["lake", "env", "lean", str(probe_path)], cwd=ROOT, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    finally:
        probe_path.unlink(missing_ok=True)
    if result.returncode:
        raise RuntimeError("Lean axiom probe failed:\n" + result.stdout)
    match = re.search(r"depends on axioms:\s*\[([^]]*)\]", result.stdout)
    if match is None:
        # Unlike a nonempty set, Lean reports an axiom-free declaration as a
        # standalone sentence rather than a bracketed list.
        if AXIOM_FREE_OUTPUT.search(result.stdout):
            return set(), result.stdout
        raise RuntimeError("could not parse #print axioms output:\n" + result.stdout)
    # Lean prints a comma-separated list of fully qualified Names.  Do not use
    # an ASCII identifier regex here: an adversarial axiom name may be Unicode
    # and must remain visible to the exact-set comparison.
    content = match.group(1).strip()
    names = [] if not content else [name.strip() for name in content.split(",")]
    if any(not name for name in names):
        raise RuntimeError("malformed #print axioms name list:\n" + result.stdout)
    return set(names), result.stdout

def require_expected_proposition(source: str, declaration: str, expected: str) -> None:
    """Require Lean to elaborate the declaration at its complete advertised type."""
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=ROOT, delete=False) as probe:
        probe.write(source + f"\nexample : {expected} := {declaration}\n")
        probe_path = pathlib.Path(probe.name)
    try:
        result = subprocess.run(["lake", "env", "lean", str(probe_path)], cwd=ROOT, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    finally:
        probe_path.unlink(missing_ok=True)
    if result.returncode:
        raise RuntimeError(
            f"{declaration} does not have its expected proposition:\n" + result.stdout
        )

def require_exact_axioms(actual, expected, context):
    if actual != expected:
        raise RuntimeError(
            f"{context} has unexpected axiom set: got {sorted(actual)}, "
            f"expected {sorted(expected)}"
        )

def self_test():
    require_clean_source()
    print("computational source audit accepted the production module")

    run = run_environment_audit()
    if run.returncode:
        raise RuntimeError("computational environment audit rejected the production module:\n"
                           + run.stdout)
    audited = MODULE_AUDIT_OUTPUT.search(run.stdout)
    if audited is None or int(audited.group(1)) == 0:
        raise RuntimeError("computational environment audit did not report module-wide coverage:\n"
                           + run.stdout)
    print("computational environment audit accepted the production module")

    with tempfile.TemporaryDirectory() as directory:
        fixture = pathlib.Path(directory) / "Computational.lean"
        fixture.write_text("theorem hiddenSourceWitness : True := by sorry\n", encoding="utf-8")
        try:
            require_clean_source(fixture)
        except RuntimeError as exc:
            if "forbidden computational source token" not in str(exc):
                raise
        else:
            raise RuntimeError("computational source audit accepted a placeholder fixture")
    print("computational source negative fixture rejected")

    # This axiom is deliberately unused and hidden under a harmless namespace.
    # The environment audit must inspect every newly loaded declaration rather
    # than only the representative certificate list.
    run = run_environment_audit("""
namespace BealUnified.ComputationalAuditNegative
axiom unusedΩ : True
theorem unusedSorry : True := by sorry
end BealUnified.ComputationalAuditNegative
""")
    if (run.returncode == 0 or "unapproved computational axioms" not in run.stdout
            or "unusedΩ" not in run.stdout or "sorryAx" not in run.stdout):
        raise RuntimeError("computational environment audit accepted unused placeholders:\n"
                           + run.stdout)
    print("computational environment negative fixture rejected (unused non-ASCII axiom and sorry)")

    axiom_free, axiom_free_output = printed_axioms("""import BealUnified.Computational
namespace BealUnified.ComputationalAuditNegative
theorem axiomFree : True := True.intro
end BealUnified.ComputationalAuditNegative
""", "BealUnified.ComputationalAuditNegative.axiomFree")
    if axiom_free:
        raise RuntimeError("axiom-free #print axioms output was not parsed as an empty set:\n"
                           + axiom_free_output)
    print("computational axiom-free fixture parsed as an empty axiom set")

    # `harmlessΩ` deliberately does not contain "axiom" and is non-ASCII.
    # The audited declaration depends on both it and the generated
    # native_decide axiom, so this proves that extra axioms fail closed.
    actual, _ = printed_axioms("""import BealUnified.Computational
namespace BealUnified.ComputationalAuditNegative
axiom harmlessΩ : True
theorem certificateWithExtraWitness :
    hasCounterexampleUpTo 8 8 = false ∧ True :=
  ⟨noCounterexampleUpTo_8_8, harmlessΩ⟩
end BealUnified.ComputationalAuditNegative
""", "BealUnified.ComputationalAuditNegative.certificateWithExtraWitness")
    negative_axiom = "BealUnified.ComputationalAuditNegative.harmlessΩ"
    expected = CERTIFICATES["BealUnified.noCounterexampleUpTo_8_8"]
    if actual == expected or negative_axiom not in actual:
        raise RuntimeError("computational negative fixture did not expose its extra axiom")
    try:
        require_exact_axioms(actual, expected, "controlled computational negative fixture")
    except RuntimeError:
        print("computational negative fixture rejected (extra harmlessly named axiom)")
        return
    raise RuntimeError("computational negative fixture was accepted")

def proposition_self_test():
    source = """import BealUnified.Computational
namespace BealUnified.ComputationalAuditNegative
theorem weakenedCertificate : True :=
  (fun _ : hasCounterexampleUpTo 8 8 = false => True.intro) noCounterexampleUpTo_8_8
end BealUnified.ComputationalAuditNegative
"""
    declaration = "BealUnified.ComputationalAuditNegative.weakenedCertificate"
    try:
        require_expected_proposition(
            source, declaration, EXPECTED_PROPOSITIONS["BealUnified.noCounterexampleUpTo_8_8"]
        )
    except RuntimeError:
        print("computational negative fixture rejected a weakened certificate proposition")
        return
    raise RuntimeError("computational negative fixture accepted a weakened certificate proposition")

try:
    build_target()
    require_clean_source()
    environment_audit = run_environment_audit()
    if environment_audit.returncode:
        raise RuntimeError("computational environment audit failed:\n" + environment_audit.stdout)
    for declaration, expected in CERTIFICATES.items():
        source = "import BealUnified.Computational\n"
        require_expected_proposition(source, declaration, EXPECTED_PROPOSITIONS[declaration])
        actual, _ = printed_axioms(source, declaration)
        require_exact_axioms(actual, expected, declaration)
    if "--self-test" in sys.argv:
        self_test()
        proposition_self_test()
    print("computational evidence is opt-in and uses exactly the pinned native_decide axiom set")
except Exception as exc:
    print(f"computational evidence audit failed: {exc}", file=sys.stderr)
    raise SystemExit(1)
