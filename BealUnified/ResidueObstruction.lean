import BealUnified.Statement

set_option linter.style.header false
set_option linter.style.nativeDecide false

/-!
# Unit residue obstructions for Beal equations

This module records finite obstructions among the units of `ZMod m` and
connects them to Beal equations whose exponents have the prescribed divisors.
-/

namespace BealUnified

/-- No sum of the indicated powers of two units is the indicated power of a third unit. -/
def UnitResidueObstruction (m d₁ d₂ d₃ : ℕ) : Prop :=
  ∀ u v w : (ZMod m)ˣ,
    (u : ZMod m) ^ d₁ + (v : ZMod m) ^ d₂ ≠ (w : ZMod m) ^ d₃

theorem not_coprime_modulus_of_unitResidueObstruction
    {m d₁ d₂ d₃ A B C x y z : ℕ}
    (hm : 1 < m) (hobs : UnitResidueObstruction m d₁ d₂ d₃)
    (hEq : BealEquation A B C x y z)
    (h₁ : d₁ ∣ x) (h₂ : d₂ ∣ y) (h₃ : d₃ ∣ z) :
    ¬ Nat.Coprime (A * B * C) m := by
  intro hcop
  have hA : Nat.Coprime A m := (Nat.coprime_mul_left_iff.mp
    (Nat.coprime_mul_left_iff.mp hcop)).1
  have hB : Nat.Coprime B m := (Nat.coprime_mul_left_iff.mp
    (Nat.coprime_mul_left_iff.mp hcop)).2.1
  have hC : Nat.Coprime C m := (Nat.coprime_mul_left_iff.mp
    (Nat.coprime_mul_left_iff.mp hcop)).2.2
  let u : (ZMod m)ˣ := ZMod.unitOfCoprime A hA
  let v : (ZMod m)ˣ := ZMod.unitOfCoprime B hB
  let w : (ZMod m)ˣ := ZMod.unitOfCoprime C hC
  obtain ⟨a, rfl⟩ := h₁
  obtain ⟨b, rfl⟩ := h₂
  obtain ⟨c, rfl⟩ := h₃
  apply hobs u v w
  change (A : ZMod m) ^ d₁ + (B : ZMod m) ^ d₂ = (C : ZMod m) ^ d₃
  rw [← pow_mul, ← pow_mul, ← pow_mul]
  norm_cast
  simpa [BealEquation, pow_mul] using hEq

/-- Cubes of units modulo `7` have no additive Beal relation. -/
theorem cubic_unit_obstruction_mod7 : UnitResidueObstruction 7 3 3 3 := by
  native_decide

/-- Cubes of units modulo `9` have no additive Beal relation. -/
theorem cubic_unit_obstruction_mod9 : UnitResidueObstruction 9 3 3 3 := by
  native_decide

/-- A Beal equation with all exponents divisible by `3` has a base sharing a factor with `7`. -/
theorem not_coprime_abc_mod7_of_three_dvd_exponents
    {A B C x y z : ℕ} (hEq : BealEquation A B C x y z)
    (hx : 3 ∣ x) (hy : 3 ∣ y) (hz : 3 ∣ z) :
    ¬ Nat.Coprime (A * B * C) 7 :=
  not_coprime_modulus_of_unitResidueObstruction (by decide)
    cubic_unit_obstruction_mod7 hEq hx hy hz

end BealUnified
