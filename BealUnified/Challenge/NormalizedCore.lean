import BealUnified.Trusted

set_option linter.style.header false

/-!
# Opt-in normalized open core

`NormalizedPrimitiveCore` is a proposition, not a claimed theorem.  It is the
remaining primitive normalized Beal target.  The trusted normalization theorem
is consumed below to give an exact reduction from the usual Beal proposition.
-/

namespace BealUnified.Challenge

/-- The exponent shapes retained by the trusted normalization procedure. -/
def NormalizedExponent (n : ℕ) : Prop :=
  n = 4 ∨ n.Prime ∧ Odd n

/-- A pairwise-coprime positive Beal solution whose exponents already have the
normal forms selected by `AdmissibleExponentDivisor`. -/
def NormalizedPrimitiveCore : Prop :=
  ∃ A B C x y z : ℕ,
    NormalizedExponent x ∧ NormalizedExponent y ∧ NormalizedExponent z ∧
    Solution A B C x y z ∧
    Nat.Coprime A B ∧ Nat.Coprime B C ∧ Nat.Coprime A C

/-- The normalized target after the independently solved `(3,3,3)` signature
has been excluded.  This is intentionally named `non333`: no hyperbolicity
inequality is encoded here. -/
def NormalizedPrimitiveCoreNon333 : Prop :=
  ∃ A B C x y z : ℕ,
    NormalizedExponent x ∧ NormalizedExponent y ∧ NormalizedExponent z ∧
    Solution A B C x y z ∧
    Nat.Coprime A B ∧ Nat.Coprime B C ∧ Nat.Coprime A C ∧
    (x, y, z) ≠ (3, 3, 3)

/-- The normalized target after both diagonal signatures already proved by the
trusted FLT-3 and FLT-4 modules have been excluded.  No claim is made about any
other equal- or mixed-exponent signature. -/
def NormalizedPrimitiveCoreNonDiagonal : Prop :=
  ∃ A B C x y z : ℕ,
    NormalizedExponent x ∧ NormalizedExponent y ∧ NormalizedExponent z ∧
    Solution A B C x y z ∧
    Nat.Coprime A B ∧ Nat.Coprime B C ∧ Nat.Coprime A C ∧
    (x, y, z) ≠ (3, 3, 3) ∧
    (x, y, z) ≠ (4, 4, 4)

/-- The open Beal target is explicitly a named proposition, with no proof
claim attached to it. -/
def OpenBealTarget : Prop := ¬ NormalizedPrimitiveCore

theorem normalized_core_iff_non333 :
    NormalizedPrimitiveCore ↔ NormalizedPrimitiveCoreNon333 := by
  constructor
  · rintro ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC⟩
    refine ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC, ?_⟩
    rintro hsig
    rcases Prod.ext_iff.mp hsig with ⟨rfl, rfl, rfl⟩
    exact beal_case_pow_three sol
  · rintro ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC, _⟩
    exact ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC⟩

/-- Exact reduction after removing both diagonal normalized signatures already
settled in the trusted boundary. -/
theorem normalized_core_iff_non_diagonal :
    NormalizedPrimitiveCore ↔ NormalizedPrimitiveCoreNonDiagonal := by
  constructor
  · rintro ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC⟩
    refine ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC, ?_, ?_⟩
    · rintro hsig
      rcases Prod.ext_iff.mp hsig with ⟨rfl, rfl, rfl⟩
      exact beal_case_pow_three sol
    · rintro hsig
      rcases Prod.ext_iff.mp hsig with ⟨rfl, rfl, rfl⟩
      exact beal_case_pow_four sol
  · rintro ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC, _, _⟩
    exact ⟨A, B, C, x, y, z, hx, hy, hz, sol, hAB, hBC, hAC⟩

/-- A normalized primitive core directly contradicts the standard
no-primitive-solution formulation. -/
theorem normalized_core_of_no_coprime_solution
    (h : NoCoprimeSolution) : ¬ NormalizedPrimitiveCore := by
  rintro ⟨A, B, C, x, y, z, _, _, _, sol, hAB, hBC, hAC⟩
  have hgcd : Nat.gcd (Nat.gcd A B) C = 1 := by
    apply Nat.dvd_one.mp
    rw [← hAC]
    exact Nat.dvd_gcd
      ((Nat.gcd_dvd_left (Nat.gcd A B) C).trans (Nat.gcd_dvd_left A B))
      (Nat.gcd_dvd_right (Nat.gcd A B) C)
  exact h A B C x y z sol hgcd

/-- Fully checked assembler: eliminating the normalized primitive core proves
the usual Beal proposition. -/
theorem beal_conjecture_of_normalized_core
    (hcore : ¬ NormalizedPrimitiveCore) : BealConjecture := by
  rw [beal_iff_no_coprime_solution]
  intro A B C x y z sol hprimitive
  obtain ⟨dx, dy, dz, hdx, hdy, hdz, nsol, hAB, hBC, hAC, _⟩ :=
    beal_normalize sol hprimitive
  exact hcore ⟨A ^ (x / dx), B ^ (y / dy), C ^ (z / dz), dx, dy, dz,
    hdx.2, hdy.2, hdz.2, nsol, hAB, hBC, hAC⟩

/-- Exact reduction: the usual Beal proposition is equivalent to emptiness of
the normalized primitive core. -/
theorem beal_conjecture_iff_normalized_core_empty :
    BealConjecture ↔ ¬ NormalizedPrimitiveCore := by
  constructor
  · intro h
    exact normalized_core_of_no_coprime_solution (beal_iff_no_coprime_solution.mp h)
  · exact beal_conjecture_of_normalized_core

end BealUnified.Challenge
