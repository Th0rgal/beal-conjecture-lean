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

/-- No Beal solution whose three exponents are divisible by `3`, by FLT-3. -/
theorem beal_case_all_exponents_divisible_by_three
    {A B C x y z : ℕ}
    (sol : Solution A B C x y z)
    (hx3 : 3 ∣ x) (hy3 : 3 ∣ y) (hz3 : 3 ∣ z) :
    False := by
  obtain ⟨k, rfl⟩ := hx3
  obtain ⟨m, rfl⟩ := hy3
  obtain ⟨n, rfl⟩ := hz3
  obtain heq : BealEquation A B C (3 * k) (3 * m) (3 * n) := sol.eqn
  change A ^ (3 * k) + B ^ (3 * m) = C ^ (3 * n) at heq
  apply fermatLastTheoremThree (A ^ k) (B ^ m) (C ^ n)
  · exact pow_ne_zero k (Nat.ne_of_gt sol.posA)
  · exact pow_ne_zero m (Nat.ne_of_gt sol.posB)
  · exact pow_ne_zero n (Nat.ne_of_gt sol.posC)
  · have hcube : (A ^ k) ^ 3 + (B ^ m) ^ 3 = (C ^ n) ^ 3 := by
      rw [← pow_mul, ← pow_mul, ← pow_mul]
      simpa only [Nat.mul_comm] using heq
    exact hcube

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
