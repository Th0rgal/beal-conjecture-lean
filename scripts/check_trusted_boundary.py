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
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}

def module_path(module): return ROOT.joinpath(*module.split(".")).with_suffix(".lean")
if "--self-test" in sys.argv:
    # Controlled negative fixture: this must be rejected before Lean is run.
    if not FORBIDDEN.search("theorem fixture : True := by sorry"):
        raise SystemExit("negative fixture was not detected")
    print("trusted boundary negative fixture rejected")
    raise SystemExit(0)
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

try:
    modules = closure()
    # Representative declarations cover every direct trusted module.  Import
    # closure and placeholder checks above cover all source; this Lean probe
    # asks the kernel for the actual axiom dependencies of the public surface.
    names = [
        "BealUnified.BealConjecture", "BealUnified.pairwise_coprime_of_solution",
        "BealUnified.beal_case_pow_three", "BealUnified.beal_normalize",
        "BealUnified.lteConclusion_of_mathlib_pow_add_pow",
        "BealUnified.rad_base_pow_min_le_max_cube",
        "BealUnified.no_solution_all_bases_odd",
        "BealUnified.nonexceptional_prime_order_and_congruence",
        "BealUnified.B_modEq_seven_of_even_C_even_x_odd_y_of_solution_of_primitive",
        "BealUnified.PrimitivePowSubDivisor.dvd_prime_sub_one",
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=ROOT, delete=False) as probe:
        probe.write("import BealUnified.Trusted\n")
        probe.write("\n".join(f"#print axioms {n}" for n in sorted(set(names))))
        probe_path = pathlib.Path(probe.name)
    run = subprocess.run(["lake", "env", "lean", str(probe_path)], cwd=ROOT, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    probe_path.unlink(missing_ok=True)
    if run.returncode: raise RuntimeError(run.stdout)
    found = set(re.findall(r"(?:propext|Classical\.choice|Quot\.sound|sorryAx|[A-Za-z][\w.]*axiom[\w.]*)", run.stdout))
    bad = found - ALLOWED_AXIOMS
    if bad: raise RuntimeError("unapproved axioms: " + ", ".join(sorted(bad)))
    print(f"trusted boundary passed ({len(modules)} local modules; axioms: {', '.join(sorted(found)) or 'none'})")
except Exception as exc:
    print(f"trusted boundary failed: {exc}", file=sys.stderr)
    sys.exit(1)
