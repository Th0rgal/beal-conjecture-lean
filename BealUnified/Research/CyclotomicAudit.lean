import Mathlib

set_option linter.style.header false

/-!
# Cyclotomic proof-audit lemmas

This module formalizes the finite coefficient-pair lemma used in the audit of a
claimed repeated-exponent cyclotomic proof. It makes no Diophantine
nonexistence claim.
-/

namespace BealUnified.Research

/--
Two nonnegative coefficient pairs each summing to `k`, with disjoint support in
each coordinate, are complementary: their coordinatewise sum is `(k,k)`.
-/
theorem complementary_pair_of_disjoint_support
    {k a₀ a₁ b₀ b₁ : ℕ}
    (hk : 0 < k)
    (ha : a₀ + a₁ = k)
    (hb : b₀ + b₁ = k)
    (h0 : a₀ = 0 ∨ b₀ = 0)
    (h1 : a₁ = 0 ∨ b₁ = 0) :
    a₀ + b₀ = k ∧ a₁ + b₁ = k := by
  rcases h0 with ha0 | hb0 <;> rcases h1 with ha1 | hb1
  · subst a₀
    subst a₁
    omega
  · subst a₀
    subst b₁
    omega
  · subst b₀
    subst a₁
    omega
  · subst b₀
    subst b₁
    omega

/-- Dividing a common element twice does not imply divisibility by the product. -/
theorem individual_dvd_does_not_force_product_dvd :
    (2 : ℕ) ∣ 2 ∧ (2 : ℕ) ∣ 2 ∧ ¬(4 : ℕ) ∣ 2 := by
  norm_num

end BealUnified.Research
