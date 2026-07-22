#!/usr/bin/env python3
"""Fail-closed audit of the opt-in bounded-search certificate's axioms.

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
    if not match:
        raise RuntimeError("could not parse #print axioms output:\n" + result.stdout)
    # Lean prints a comma-separated list of fully qualified Names.  Do not use
    # an ASCII identifier regex here: an adversarial axiom name may be Unicode
    # and must remain visible to the exact-set comparison.
    content = match.group(1).strip()
    names = [] if not content else [name.strip() for name in content.split(",")]
    if any(not name for name in names):
        raise RuntimeError("malformed #print axioms name list:\n" + result.stdout)
    return set(names), result.stdout

def require_exact_axioms(actual, expected, context):
    if actual != expected:
        raise RuntimeError(
            f"{context} has unexpected axiom set: got {sorted(actual)}, "
            f"expected {sorted(expected)}"
        )

def self_test():
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

try:
    build_target()
    for declaration, expected in CERTIFICATES.items():
        actual, _ = printed_axioms("import BealUnified.Computational\n", declaration)
        require_exact_axioms(actual, expected, declaration)
    if "--self-test" in sys.argv:
        self_test()
    print("computational evidence is opt-in and uses exactly the pinned native_decide axiom set")
except Exception as exc:
    print(f"computational evidence audit failed: {exc}", file=sys.stderr)
    raise SystemExit(1)
