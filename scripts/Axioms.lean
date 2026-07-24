import BealUnified

/-!
# Trusted-environment axiom audit

This command examines every declaration introduced by `import BealUnified`,
regardless of its namespace.  It computes that set by subtracting the
environment imported by `Mathlib` (the only non-local import family permitted
by the trusted source closure) from the environment imported by the public
root.  Thus a trusted source file cannot hide a declaration under `Hidden` or
the root namespace, while Mathlib's own declarations are not spuriously
audited.  It recursively follows declaration bodies and types to their axioms,
and rejects anything other than Lean's standard logical axioms.  It
intentionally does not use a maintained list of representative theorems.
-/

open Lean Elab Command

namespace BealTrustAudit

abbrev AuditM := StateM NameSet

private def directDependencies : ConstantInfo → Array Name
  | .axiomInfo v => v.type.getUsedConstants
  | .defnInfo v => v.type.getUsedConstants ++ v.value.getUsedConstants
  | .thmInfo v => v.type.getUsedConstants ++ v.value.getUsedConstants
  | .opaqueInfo v => v.type.getUsedConstants ++ v.value.getUsedConstants
  | .quotInfo _ => #[]
  | .ctorInfo v => v.type.getUsedConstants
  | .recInfo v => v.type.getUsedConstants
  | .inductInfo v => v.type.getUsedConstants ++ v.ctors

/-- Recursively collect all axioms used by a declaration. -/
partial def collectAxioms (env : Environment) (decl : Name) : AuditM (List Name) := do
  if (← get).contains decl then
    return []
  modify (·.insert decl)
  match env.find? decl with
  | some (.axiomInfo _) => return [decl]
  | some info =>
      (directDependencies info).foldlM (init := []) fun used dependency =>
        return used ++ (← collectAxioms env dependency)
  | none => return []

private def allowedAxiom (name : Name) : Bool :=
  name == ``propext || name == ``Classical.choice || name == ``Quot.sound

private def introducedDeclarations (baseline target : Environment) : Array Name :=
  (target.constants.map₁.toList ++ target.constants.map₂.toList).foldl
    (init := #[]) fun declarations entry =>
      if (baseline.find? entry.1).isNone then declarations.push entry.1 else declarations

private def trustedEnvironment : CommandElabM (Environment × Array Name) := do
  -- `check_trusted_boundary.py` independently verifies that every local import
  -- in this closure is under BealUnified and that all external imports are
  -- Mathlib.  Keep this provenance comparison explicit rather than relying on
  -- declaration names, which Lean does not associate with source modules.
  let baseline ← liftIO <| Lean.importModules #[{ module := `Mathlib }] {}
  let trusted ← liftIO <| Lean.importModules #[{ module := `BealUnified }] {}
  return (trusted, introducedDeclarations baseline trusted)

private def reportRejectedAxioms (env : Environment) (declarations : Array Name) : CommandElabM Unit := do
  let (usedAxioms, _) := (declarations.foldlM (init := []) fun used declaration =>
    return used ++ (← collectAxioms env declaration)).run {}
  let axioms := usedAxioms.eraseDups
  let rejected := axioms.filter fun name => !allowedAxiom name
  logInfo m!"trusted environment declarations audited: {declarations.size}"
  logInfo m!"trusted environment declarations: {declarations}"
  logInfo m!"trusted environment axioms: {axioms}"
  if rejected != [] then
    logError m!"unapproved trusted axioms: {rejected}"

/-- Fail when the imported trusted environment uses an unapproved axiom. -/
elab "#audit_trusted_axioms" : command => do
  let (env, declarations) ← trustedEnvironment
  reportRejectedAxioms env declarations

/-- Audit one registry declaration only when it is loaded by the public trusted root. -/
elab "#audit_trusted_registry_declaration " ident:ident : command => do
  let (env, declarations) ← trustedEnvironment
  let declaration := ident.getId
  if !declarations.contains declaration then
    logError m!"registry declaration is not loaded by the trusted root: {declaration}"
  else
    reportRejectedAxioms env #[declaration]

/-- Test-only command: audit all declarations added to this loaded environment
against Mathlib.  This lets the Python gate prove a temporary `Hidden` escape
is rejected without putting a negative fixture in the trusted source tree. -/
elab "#audit_current_additions_against_mathlib" : command => do
  let baseline ← liftIO <| Lean.importModules #[{ module := `Mathlib }] {}
  let env ← getEnv
  reportRejectedAxioms env (introducedDeclarations baseline env)

end BealTrustAudit

#audit_trusted_axioms
