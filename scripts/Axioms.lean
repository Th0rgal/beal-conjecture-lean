import BealUnified.Trusted

/-!
# Trusted-environment axiom audit

This command examines every declaration actually loaded by
`import BealUnified.Trusted` whose name is in the `BealUnified` namespace. It
recursively follows declaration bodies and types to their axioms, and rejects
anything other than Lean's standard logical axioms. It intentionally does not
use a maintained list of representative theorems.
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

/-- Fail when the imported trusted environment uses an unapproved axiom. -/
elab "#audit_trusted_axioms" : command => do
  let env ← getEnv
  let trustedPrefix : Name := `BealUnified
  let declarations := (env.constants.map₁.toList ++ env.constants.map₂.toList).foldl
    (init := #[]) fun declarations entry =>
      if trustedPrefix.isPrefixOf entry.1 then declarations.push entry.1 else declarations
  let (usedAxioms, _) := (declarations.foldlM (init := []) fun used declaration =>
    return used ++ (← collectAxioms env declaration)).run {}
  let axioms := usedAxioms.eraseDups
  let rejected := axioms.filter fun name => !allowedAxiom name
  logInfo m!"trusted environment declarations audited: {declarations.size}"
  logInfo m!"trusted environment declarations: {declarations}"
  logInfo m!"trusted environment axioms: {axioms}"
  if rejected != [] then
    logError m!"unapproved trusted axioms: {rejected}"

end BealTrustAudit

#audit_trusted_axioms
