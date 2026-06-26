import BealUnified.Statement
import Mathlib.NumberTheory.FLT.Three
import Mathlib.NumberTheory.FLT.Four

set_option linter.style.header false

/-!
# Beal conjecture: FLT reductions

This module collects the subcases that reduce directly to Fermat's Last
Theorem.  Mathlib proves the common exponent `3` and `4` cases
unconditionally; the general common-exponent theorem is conditional on an
available `FermatLastTheoremFor n` proof.
-/

namespace BealUnified

/-- A positive equal-exponent Beal equation contradicts FLT for that exponent. -/
theorem equalExponent_counterexample_contradicts_flt {A B C n : ℕ}
    (hflt : FermatLastTheoremFor n) (hA : 0 < A) (hB : 0 < B) (hC : 0 < C)
    (hEq : BealEquation A B C n n n) : False := by
  exact hflt A B C (Nat.pos_iff_ne_zero.mp hA) (Nat.pos_iff_ne_zero.mp hB)
    (Nat.pos_iff_ne_zero.mp hC) hEq

/-- No Beal solution with `x = y = z = 3`, by Mathlib's FLT-3 theorem. -/
theorem beal_case_pow_three {A B C : ℕ} (sol : Solution A B C 3 3 3) : False :=
  equalExponent_counterexample_contradicts_flt fermatLastTheoremThree
    sol.posA sol.posB sol.posC sol.eqn

/-- No Beal solution with `x = y = z = 4`, by Mathlib's FLT-4 theorem. -/
theorem beal_case_pow_four {A B C : ℕ} (sol : Solution A B C 4 4 4) : False :=
  equalExponent_counterexample_contradicts_flt fermatLastTheoremFour
    sol.posA sol.posB sol.posC sol.eqn

/-- Any common-exponent Beal case follows from FLT for that exponent. -/
theorem beal_case_pow_of_flt
    {n : ℕ} (hn : FermatLastTheoremFor n)
    {A B C : ℕ} (sol : Solution A B C n n n) : False :=
  equalExponent_counterexample_contradicts_flt hn sol.posA sol.posB sol.posC sol.eqn

/-- The common-exponent Beal conclusion follows from FLT for that exponent. -/
theorem beal_equalExponent_of_fermatLastTheoremFor {n : ℕ}
    (hflt : FermatLastTheoremFor n) :
    ∀ A B C : ℕ, Solution A B C n n n → BealConclusion A B C := by
  intro A B C sol
  exact False.elim (beal_case_pow_of_flt hflt sol)

/-- Conditional reduction from Mathlib's global FLT proposition. -/
theorem beal_equalExponent_of_fermatLastTheorem
    (hFLT : FermatLastTheorem) {n : ℕ} (hn : 3 ≤ n) :
    ∀ A B C : ℕ, Solution A B C n n n → BealConclusion A B C :=
  beal_equalExponent_of_fermatLastTheoremFor (hFLT n hn)

end BealUnified
