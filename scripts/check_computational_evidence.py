#!/usr/bin/env python3
"""Record the non-kernel dependency of the opt-in bounded-search certificate.

This is deliberately not a trust gate: native_decide's generated axiom is
outside the trusted allowlist.  The check makes that boundary explicit and
fails if the computational certificate ever gains a placeholder dependency.
"""
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = """import BealUnified.Computational
#print axioms BealUnified.noCounterexampleUpTo_8_8
"""

# This audit runs before the full project build in the trust-gate workflow.
# Build its one opt-in target explicitly so a clean checkout has the olean that
# the temporary import probe requires.  Keeping this here makes direct local
# invocation and CI use the same deterministic dependency order.
build = subprocess.run(["lake", "build", "BealUnified.Computational"], cwd=ROOT,
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       check=False)
if build.returncode:
    print(build.stdout, file=sys.stderr)
    raise SystemExit(build.returncode)

with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=ROOT, delete=False) as probe:
    probe.write(SOURCE)
    probe_path = pathlib.Path(probe.name)
try:
    result = subprocess.run(["lake", "env", "lean", str(probe_path)], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
finally:
    probe_path.unlink(missing_ok=True)

if result.returncode:
    print(result.stdout, file=sys.stderr)
    raise SystemExit(1)
if "native_decide" not in result.stdout or "sorryAx" in result.stdout:
    print("computational evidence audit did not find exactly the expected native-decision boundary", file=sys.stderr)
    print(result.stdout, file=sys.stderr)
    raise SystemExit(1)
print("computational evidence is opt-in and uses the generated native_decide axiom")
