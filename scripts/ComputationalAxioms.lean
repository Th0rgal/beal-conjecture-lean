import BealUnified.Computational

/-!
# Computational-environment axiom audit

This command audits every declaration introduced by `BealUnified.Computational`
against the environment imported by `BealUnified.Statement`.  It accepts the
standard logical axioms and the single generated `native_decide` axiom pinned
by the computational-evidence gate; every other axiom is rejected, including
an unused declaration in any namespace.
-/

open Lean Elab Command

namespace BealComputationalAudit

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

private partial def collectAxioms (env : Environment) (decl : Name) : AuditM (List Name) := do
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
  name == ``propext || name == ``Classical.choice || name == ``Quot.sound ||
    name == ``BealUnified.noCounterexampleUpTo_8_8._native.native_decide.ax_1_1

private def introducedDeclarations (baseline target : Environment) : Array Name :=
  (target.constants.map₁.toList ++ target.constants.map₂.toList).foldl
    (init := #[]) fun declarations entry =>
      if (baseline.find? entry.1).isNone then declarations.push entry.1 else declarations

private def computationalEnvironment : CommandElabM (Environment × Array Name) := do
  let baseline ← liftIO <| Lean.importModules #[{ module := `BealUnified.Statement }] {}
  let computational ← liftIO <| Lean.importModules #[{ module := `BealUnified.Computational }] {}
  return (computational, introducedDeclarations baseline computational)

private def reportRejectedAxioms (env : Environment) (declarations : Array Name) :
    CommandElabM Unit := do
  let (usedAxioms, _) := (declarations.foldlM (init := []) fun used declaration =>
    return used ++ (← collectAxioms env declaration)).run {}
  let axioms := usedAxioms.eraseDups
  let rejected := axioms.filter fun name => !allowedAxiom name
  logInfo m!"computational environment declarations audited: {declarations.size}"
  logInfo m!"computational environment axioms: {axioms}"
  if rejected != [] then
    logError m!"unapproved computational axioms: {rejected}"

/-- Audit exactly the declarations introduced by the computational module. -/
elab "#audit_computational_axioms" : command => do
  let (env, declarations) ← computationalEnvironment
  reportRejectedAxioms env declarations

/-- Test-only command: audit all additions to the loaded computational environment. -/
elab "#audit_current_computational_additions" : command => do
  let baseline ← liftIO <| Lean.importModules #[{ module := `BealUnified.Statement }] {}
  let env ← getEnv
  reportRejectedAxioms env (introducedDeclarations baseline env)

end BealComputationalAudit

#audit_computational_axioms
