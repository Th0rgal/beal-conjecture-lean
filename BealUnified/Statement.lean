import Mathlib

set_option linter.style.header false

/-!
# Beal conjecture: core statement

This module defines the Beal equation, the common-factor conclusion, the
positive solution predicate, and the two standard formulations of the
conjecture.  It also proves the basic reduction from a setwise-coprime
solution to pairwise coprime bases, plus the equivalence with the
contrapositive "no primitive solution" formulation.
-/

namespace BealUnified

/-- The Beal equation `A ^ x + B ^ y = C ^ z`. -/
def BealEquation (A B C x y z : ℕ) : Prop :=
  A ^ x + B ^ y = C ^ z

/-- The common-divisor conclusion appearing in the Beal conjecture. -/
def BealConclusion (A B C : ℕ) : Prop :=
  1 < Nat.gcd (Nat.gcd A B) C

/-- A positive Beal solution with all exponents at least `3`. -/
structure Solution (A B C x y z : ℕ) : Prop where
  posA : 0 < A
  posB : 0 < B
  posC : 0 < C
  hx : 3 ≤ x
  hy : 3 ≤ y
  hz : 3 ≤ z
  eqn : BealEquation A B C x y z

/-- The Beal conjecture in its common-factor form. -/
def BealConjecture : Prop :=
  ∀ A B C x y z : ℕ, Solution A B C x y z → BealConclusion A B C

/-- The Beal conjecture in primitive-counterexample-free form. -/
def NoCoprimeSolution : Prop :=
  ∀ A B C x y z : ℕ, Solution A B C x y z →
    Nat.gcd (Nat.gcd A B) C ≠ 1

private lemma dvd_add_pows {g A B x y : ℕ} (hA : g ∣ A ^ x) (hB : g ∣ B ^ y) :
    g ∣ A ^ x + B ^ y :=
  Nat.dvd_add hA hB

/--
If the bases of a Beal equation are setwise coprime, then they are pairwise
coprime.  The proof only needs positive exponents.
-/
theorem pairwise_coprime_of_solution
    {A B C x y z : ℕ}
    (hx : 1 ≤ x) (hy : 1 ≤ y) (hz : 1 ≤ z)
    (hgcd : Nat.gcd (Nat.gcd A B) C = 1)
    (heq : BealEquation A B C x y z) :
    Nat.Coprime A B ∧ Nat.Coprime B C ∧ Nat.Coprime A C := by
  have hA_BC : Nat.Coprime A (Nat.gcd B C) := by
    have h := hgcd
    rwa [Nat.gcd_assoc] at h
  have hB_AC : Nat.Coprime B (Nat.gcd A C) := by
    have h := hgcd
    rw [Nat.gcd_comm A B, Nat.gcd_assoc] at h
    exact h
  refine ⟨?_, ?_, ?_⟩
  · have hgA : Nat.gcd A B ∣ A := Nat.gcd_dvd_left A B
    have hgB : Nat.gcd A B ∣ B := Nat.gcd_dvd_right A B
    have hdvd : Nat.gcd A B ∣ C ^ z := by
      have hsum : Nat.gcd A B ∣ A ^ x + B ^ y :=
        dvd_add_pows (dvd_pow hgA (by omega)) (dvd_pow hgB (by omega))
      dsimp [BealEquation] at heq
      rwa [heq] at hsum
    have hcop : Nat.Coprime (Nat.gcd A B) C := hgcd
    have hcop2 : Nat.gcd (Nat.gcd A B) (C ^ z) = 1 := hcop.pow_right z
    exact (Nat.gcd_eq_left hdvd).symm.trans hcop2
  · have hgB : Nat.gcd B C ∣ B := Nat.gcd_dvd_left B C
    have hgC : Nat.gcd B C ∣ C := Nat.gcd_dvd_right B C
    have hAx : A ^ x = C ^ z - B ^ y := by
      dsimp [BealEquation] at heq
      omega
    have hdvd : Nat.gcd B C ∣ A ^ x := by
      rw [hAx]
      exact Nat.dvd_sub (dvd_pow hgC (by omega)) (dvd_pow hgB (by omega))
    have hcop : Nat.Coprime (Nat.gcd B C) A := hA_BC.symm
    have hcop2 : Nat.gcd (Nat.gcd B C) (A ^ x) = 1 := hcop.pow_right x
    exact (Nat.gcd_eq_left hdvd).symm.trans hcop2
  · have hgA : Nat.gcd A C ∣ A := Nat.gcd_dvd_left A C
    have hgC : Nat.gcd A C ∣ C := Nat.gcd_dvd_right A C
    have hBy : B ^ y = C ^ z - A ^ x := by
      dsimp [BealEquation] at heq
      omega
    have hdvd : Nat.gcd A C ∣ B ^ y := by
      rw [hBy]
      exact Nat.dvd_sub (dvd_pow hgC (by omega)) (dvd_pow hgA (by omega))
    have hcop : Nat.Coprime (Nat.gcd A C) B := hB_AC.symm
    have hcop2 : Nat.gcd (Nat.gcd A C) (B ^ y) = 1 := hcop.pow_right y
    exact (Nat.gcd_eq_left hdvd).symm.trans hcop2

/-- Equivalence between the common-factor and no-primitive-solution forms. -/
theorem beal_iff_no_coprime_solution : BealConjecture ↔ NoCoprimeSolution := by
  constructor
  · intro h A B C x y z sol
    have hc := h A B C x y z sol
    dsimp [BealConclusion] at hc
    omega
  · intro h A B C x y z sol
    have hne := h A B C x y z sol
    have hpos : 0 < Nat.gcd (Nat.gcd A B) C :=
      Nat.gcd_pos_of_pos_left C (Nat.gcd_pos_of_pos_left B sol.posA)
    dsimp [BealConclusion]
    omega

end BealUnified
