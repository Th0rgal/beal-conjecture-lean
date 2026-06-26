import BealUnified.Statement
import BealUnified.FLTReduction
import Mathlib.NumberTheory.FLT.Four
import Mathlib.NumberTheory.PythagoreanTriples
import Mathlib.Algebra.Ring.GeomSum

set_option linter.style.header false

/-!
# Beal conjecture: parity reductions

This module consolidates the elementary all-even, mixed-parity, and odd
exponent infrastructure.  It proves the Pythagorean reduction for all-even
exponents, closes the FLT-4 all-even-halves case, closes simple parity
branches, and records the odd-exponent divisibility lemmas.  The full all-even
and mixed/odd cases remain conditional on deeper number theory.
-/

namespace BealUnified

/-- All-even exponents give a Pythagorean triple after halving exponents. -/
theorem even_exponents_pythagorean
    (A B C a b c : ℕ)
    (h : A ^ (2 * a) + B ^ (2 * b) = C ^ (2 * c)) :
    PythagoreanTriple ((A ^ a : ℕ) : ℤ) ((B ^ b : ℕ) : ℤ) ((C ^ c : ℕ) : ℤ) := by
  dsimp [PythagoreanTriple]
  have hA : (A : ℤ) ^ a * (A : ℤ) ^ a = (A : ℤ) ^ (2 * a) := by
    rw [← pow_add, two_mul]
  have hB : (B : ℤ) ^ b * (B : ℤ) ^ b = (B : ℤ) ^ (2 * b) := by
    rw [← pow_add, two_mul]
  have hC : (C : ℤ) ^ c * (C : ℤ) ^ c = (C : ℤ) ^ (2 * c) := by
    rw [← pow_add, two_mul]
  rw [hA, hB, hC]
  exact_mod_cast h

/-- Mathlib's Pythagorean classification, specialized to the even-exponent reduction. -/
theorem even_exponents_pythagorean_classified
    (A B C a b c : ℕ)
    (h : A ^ (2 * a) + B ^ (2 * b) = C ^ (2 * c)) :
    ∃ k m n : ℤ,
      ((((A ^ a : ℕ) : ℤ) = k * (m ^ 2 - n ^ 2) ∧
          ((B ^ b : ℕ) : ℤ) = k * (2 * m * n)) ∨
        (((A ^ a : ℕ) : ℤ) = k * (2 * m * n) ∧
          ((B ^ b : ℕ) : ℤ) = k * (m ^ 2 - n ^ 2))) ∧
        (((C ^ c : ℕ) : ℤ) = k * (m ^ 2 + n ^ 2) ∨
          ((C ^ c : ℕ) : ℤ) = -k * (m ^ 2 + n ^ 2)) := by
  exact (PythagoreanTriple.classification.mp
    (even_exponents_pythagorean A B C a b c h))

/-- Missing obstruction needed to finish the full all-even case. -/
def PerfectPowerPythagoreanObstruction : Prop :=
  ∀ A B C a b c : ℕ,
    0 < A → 0 < B → 0 < C →
    2 ≤ a → 2 ≤ b → 2 ≤ c →
    A ^ (2 * a) + B ^ (2 * b) = C ^ (2 * c) →
    Nat.gcd (Nat.gcd A B) C ≠ 1

/-- The full all-even case follows from the perfect-power Pythagorean obstruction. -/
theorem all_even_case_from_obstruction
    (hobs : PerfectPowerPythagoreanObstruction)
    {A B C a b c : ℕ}
    (hA : 0 < A) (hB : 0 < B) (hC : 0 < C)
    (ha : 2 ≤ a) (hb : 2 ≤ b) (hc : 2 ≤ c)
    (h : A ^ (2 * a) + B ^ (2 * b) = C ^ (2 * c)) :
    BealConclusion A B C := by
  have hne : Nat.gcd (Nat.gcd A B) C ≠ 1 := hobs A B C a b c hA hB hC ha hb hc h
  have hpos : 0 < Nat.gcd (Nat.gcd A B) C :=
    Nat.gcd_pos_of_pos_left C (Nat.gcd_pos_of_pos_left B hA)
  dsimp [BealConclusion]
  omega

/-- Natural-number version of Mathlib's `not_fermat_42`. -/
theorem not_fermat_42_nat {a b c : ℕ} (ha : a ≠ 0) (hb : b ≠ 0) :
    a ^ 4 + b ^ 4 ≠ c ^ 2 := by
  intro h
  exact not_fermat_42 (a := (a : ℤ)) (b := (b : ℤ)) (c := (c : ℤ))
    (by exact_mod_cast ha) (by exact_mod_cast hb) (by exact_mod_cast h)

/-- The concrete `x = y = z = 4` subcase. -/
theorem four_four_four_case
    {A B C : ℕ}
    (hA : 0 < A) (hB : 0 < B) (hC : 0 < C)
    (h : A ^ 4 + B ^ 4 = C ^ 4) :
    BealConclusion A B C := by
  exfalso
  exact fermatLastTheoremFour A B C
    (Nat.ne_of_gt hA) (Nat.ne_of_gt hB) (Nat.ne_of_gt hC) h

/-- If all exponent halves are even, the all-even case reduces to FLT-4. -/
theorem all_even_halves_case
    {A B C a b c : ℕ}
    (hA : 0 < A) (hB : 0 < B) (hC : 0 < C)
    (ha_even : Even a) (hb_even : Even b) (hc_even : Even c)
    (h : A ^ (2 * a) + B ^ (2 * b) = C ^ (2 * c)) :
    BealConclusion A B C := by
  rcases ha_even with ⟨a', rfl⟩
  rcases hb_even with ⟨b', rfl⟩
  rcases hc_even with ⟨c', rfl⟩
  exfalso
  have h4 : (A ^ a') ^ 4 + (B ^ b') ^ 4 = (C ^ c') ^ 4 := by
    have hAeq : (A ^ a') ^ 4 = A ^ (2 * (a' + a')) := by
      have hexp : a' * 4 = 2 * (a' + a') := by omega
      calc
        (A ^ a') ^ 4 = A ^ (a' * 4) := by rw [pow_mul]
        _ = A ^ (2 * (a' + a')) := by rw [hexp]
    have hBeq : (B ^ b') ^ 4 = B ^ (2 * (b' + b')) := by
      have hexp : b' * 4 = 2 * (b' + b') := by omega
      calc
        (B ^ b') ^ 4 = B ^ (b' * 4) := by rw [pow_mul]
        _ = B ^ (2 * (b' + b')) := by rw [hexp]
    have hCeq : (C ^ c') ^ 4 = C ^ (2 * (c' + c')) := by
      have hexp : c' * 4 = 2 * (c' + c') := by omega
      calc
        (C ^ c') ^ 4 = C ^ (c' * 4) := by rw [pow_mul]
        _ = C ^ (2 * (c' + c')) := by rw [hexp]
    rw [hAeq, hBeq, hCeq]
    exact h
  exact fermatLastTheoremFour (A ^ a') (B ^ b') (C ^ c')
    (ne_of_gt (pow_pos hA _)) (ne_of_gt (pow_pos hB _)) (ne_of_gt (pow_pos hC _)) h4

lemma bealConclusion_of_even_all {A B C : ℕ}
    (hApos : 0 < A) (hA : Even A) (hB : Even B) (hC : Even C) :
    BealConclusion A B C := by
  rw [BealConclusion]
  rw [even_iff_two_dvd] at hA hB hC
  have h₂ : 2 ∣ Nat.gcd (Nat.gcd A B) C := Nat.dvd_gcd (Nat.dvd_gcd hA hB) hC
  have hpos : 0 < Nat.gcd (Nat.gcd A B) C :=
    Nat.gcd_pos_of_pos_left C (Nat.gcd_pos_of_pos_left B hApos)
  rcases h₂ with ⟨k, hk⟩
  have hkpos : 0 < k := by
    by_contra hk0
    have : k = 0 := by omega
    omega
  omega

lemma even_base_of_even_pow {A n : ℕ} (hn : n ≠ 0) (h : Even (A ^ n)) : Even A := by
  simpa [Nat.even_pow', hn] using h

lemma even_pow_of_even_base {A n : ℕ} (hn : n ≠ 0) (h : Even A) : Even (A ^ n) := by
  exact (Nat.even_pow' hn).mpr h

lemma odd_pow_of_odd_base {A n : ℕ} (h : Odd A) : Odd (A ^ n) :=
  h.pow

/-- If the right side is even, the two left summands have the same parity. -/
lemma same_parity_of_even_rhs {A B C x y z : ℕ}
    (hz : z ≠ 0) (hC : Even C)
    (heq : BealEquation A B C x y z) :
    (Even (A ^ x) ↔ Even (B ^ y)) := by
  have hR : Even (C ^ z) := even_pow_of_even_base hz hC
  have hL : Even (A ^ x + B ^ y) := by
    dsimp [BealEquation] at heq
    rwa [heq]
  simpa [Nat.even_add] using hL

/-- If `C` and one left base are even, all bases are even, so Beal's conclusion holds. -/
theorem bealConclusion_of_evenC_and_even_left_base
    {A B C x y z : ℕ}
    (hApos : 0 < A) (hx : x ≠ 0) (hy : y ≠ 0) (hz : z ≠ 0)
    (hC : Even C) (hleft : Even A ∨ Even B)
    (heq : BealEquation A B C x y z) :
    BealConclusion A B C := by
  have hsame := same_parity_of_even_rhs (A := A) (B := B) (C := C)
    (x := x) (y := y) (z := z) hz hC heq
  rcases hleft with hA | hB
  · have hApow : Even (A ^ x) := even_pow_of_even_base hx hA
    have hBpow : Even (B ^ y) := hsame.mp hApow
    have hB : Even B := even_base_of_even_pow hy hBpow
    exact bealConclusion_of_even_all hApos hA hB hC
  · have hBpow : Even (B ^ y) := even_pow_of_even_base hy hB
    have hApow : Even (A ^ x) := hsame.mpr hBpow
    have hA : Even A := even_base_of_even_pow hx hApow
    exact bealConclusion_of_even_all hApos hA hB hC

/-- If all three bases are odd, the equation is impossible. -/
theorem no_solution_all_bases_odd
    {A B C x y z : ℕ}
    (hA : Odd A) (hB : Odd B) (hC : Odd C)
    (heq : BealEquation A B C x y z) :
    False := by
  have hApow : Odd (A ^ x) := odd_pow_of_odd_base hA
  have hBpow : Odd (B ^ y) := odd_pow_of_odd_base hB
  have hL : Even (A ^ x + B ^ y) := by
    rw [Nat.even_add]
    simp [Nat.not_even_iff_odd.mpr hApow, Nat.not_even_iff_odd.mpr hBpow]
  have hRodd : Odd (C ^ z) := odd_pow_of_odd_base hC
  have hRnot : ¬ Even (C ^ z) := Nat.not_even_iff_odd.mpr hRodd
  exact hRnot (by
    dsimp [BealEquation] at heq
    rwa [heq] at hL)

/-- Mixed-parity exponent hypotheses for the branch `x` even, `y` odd, `z` odd. -/
structure MixedParityXYZ (x y z : ℕ) : Prop where
  x_ge_three : 3 ≤ x
  y_ge_three : 3 ≤ y
  z_ge_three : 3 ≤ z
  x_even : Even x
  y_odd : Odd y
  z_odd : Odd z

namespace MixedParityXYZ

lemma x_ne_zero {x y z : ℕ} (h : MixedParityXYZ x y z) : x ≠ 0 := by
  have hx := h.x_ge_three
  omega

lemma y_ne_zero {x y z : ℕ} (h : MixedParityXYZ x y z) : y ≠ 0 := by
  have hy := h.y_ge_three
  omega

lemma z_ne_zero {x y z : ℕ} (h : MixedParityXYZ x y z) : z ≠ 0 := by
  have hz := h.z_ge_three
  omega

end MixedParityXYZ

/-- The normalized mixed-parity branch closes when `C` and one left base are even. -/
theorem mixedParity_bealConclusion_of_evenC_and_even_left_base
    {A B C x y z : ℕ}
    (hApos : 0 < A) (hxyz : MixedParityXYZ x y z)
    (hC : Even C) (hleft : Even A ∨ Even B)
    (heq : BealEquation A B C x y z) :
    BealConclusion A B C := by
  exact bealConclusion_of_evenC_and_even_left_base
    hApos hxyz.x_ne_zero hxyz.y_ne_zero hxyz.z_ne_zero hC hleft heq

/-- Odd exponent bookkeeping for all-odd signatures. -/
structure AllOddExponents (x y z : ℕ) : Prop where
  x_odd : Odd x
  y_odd : Odd y
  z_odd : Odd z

/-- For odd `n`, `A + B` divides `A ^ n + B ^ n`. -/
theorem add_dvd_pow_add_pow_of_odd {A B n : ℕ} (hn : Odd n) :
    A + B ∣ A ^ n + B ^ n := by
  exact hn.nat_add_dvd_pow_add_pow A B

/-- If the left exponents are equal and odd, `A + B` divides the right power. -/
theorem add_dvd_right_power_of_equal_odd_left
    {A B C n z : ℕ} (hn : Odd n) (hEq : BealEquation A B C n n z) :
    A + B ∣ C ^ z := by
  rw [← hEq]
  exact add_dvd_pow_add_pow_of_odd hn

/-- A useful normalization of an odd power: `A ^ (2 * k + 1)` is `A` times a square. -/
theorem pow_two_mul_add_one_eq_mul_square (A k : ℕ) :
    A ^ (2 * k + 1) = A * (A ^ k) ^ 2 := by
  rw [pow_add, pow_mul, pow_one]
  ring

/-- The unconditional `x = y = z = 3` Beal subcase, using FLT-3. -/
theorem beal_three_three_three
    {A B C : ℕ} (hA : 0 < A) (hB : 0 < B) (hC : 0 < C)
    (hEq : A ^ 3 + B ^ 3 = C ^ 3) :
    BealConclusion A B C := by
  exfalso
  exact fermatLastTheoremThree A B C
    (Nat.pos_iff_ne_zero.mp hA)
    (Nat.pos_iff_ne_zero.mp hB)
    (Nat.pos_iff_ne_zero.mp hC)
    hEq

end BealUnified
