import Mathlib.NumberTheory.PrimesCongruentOne

set_option linter.style.header false

/-!
# Primitive divisors of differences of equal powers

This module contains only the elementary order-theoretic consequence of
primitive-divisor data.  It does not assert the existence of such divisors.
-/

namespace BealUnified

/-- A prime divisor of `a ^ n - b ^ n` which is new among the positive lower
exponents and does not divide either base. -/
def PrimitivePowSubDivisor (p a b n : ℕ) : Prop :=
  p.Prime ∧
    b < a ∧
    0 < n ∧
    ¬ p ∣ a * b ∧
    p ∣ a ^ n - b ^ n ∧
    ∀ m : ℕ, 0 < m → m < n → ¬ p ∣ a ^ m - b ^ m

/-- The unit represented by the residue ratio `a / b` modulo `p`. -/
noncomputable def primitivePowSubRatio {p a b n : ℕ}
    (h : PrimitivePowSubDivisor p a b n) : (ZMod p)ˣ :=
  ZMod.unitOfCoprime a
      ((h.1.coprime_iff_not_dvd.mpr
        (fun hpa => h.2.2.2.1 (dvd_mul_of_dvd_left hpa b))).symm) /
    ZMod.unitOfCoprime b
      ((h.1.coprime_iff_not_dvd.mpr
        (fun hpb => h.2.2.2.1 (dvd_mul_of_dvd_right hpb a))).symm)

theorem orderOf_primitivePowSubRatio_eq {p a b n : ℕ}
    (h : PrimitivePowSubDivisor p a b n) :
    orderOf (primitivePowSubRatio h) = n := by
  rcases h with ⟨hp, hba, hn, hcop, hdiv, hmin⟩
  let ha : Nat.Coprime a p :=
    (hp.coprime_iff_not_dvd.mpr
      (fun hpa => hcop (dvd_mul_of_dvd_left hpa b))).symm
  let hb : Nat.Coprime b p :=
    (hp.coprime_iff_not_dvd.mpr
      (fun hpb => hcop (dvd_mul_of_dvd_right hpb a))).symm
  let ua : (ZMod p)ˣ := ZMod.unitOfCoprime a ha
  let ub : (ZMod p)ˣ := ZMod.unitOfCoprime b hb
  change orderOf (ua / ub) = n
  have pow_eq {m : ℕ} (hm : p ∣ a ^ m - b ^ m) : ua ^ m = ub ^ m := by
    apply Units.ext
    simp only [ua, ub, Units.val_pow_eq_pow_val, ZMod.coe_unitOfCoprime]
    rw [← Nat.cast_pow, ← Nat.cast_pow]
    apply (ZMod.natCast_eq_natCast_iff _ _ p).2
    exact ((Nat.modEq_iff_dvd' (Nat.pow_le_pow_left hba.le m)).2 hm).symm
  apply (orderOf_eq_iff hn).2
  constructor
  · rw [div_pow, div_eq_one]
    exact pow_eq hdiv
  · intro m hmn hmpos hpow
    apply hmin m hmpos hmn
    rw [div_pow, div_eq_one] at hpow
    have hcast : (a ^ m : ZMod p) = b ^ m := by
      simpa only [ua, ub, Units.val_pow_eq_pow_val, ZMod.coe_unitOfCoprime] using
        congrArg Units.val hpow
    rw [← Nat.cast_pow, ← Nat.cast_pow] at hcast
    exact (Nat.modEq_iff_dvd' (Nat.pow_le_pow_left hba.le m)).1
      ((ZMod.natCast_eq_natCast_iff _ _ p).1 hcast).symm

theorem PrimitivePowSubDivisor.dvd_prime_sub_one {p a b n : ℕ}
    (h : PrimitivePowSubDivisor p a b n) : n ∣ p - 1 := by
  letI : Fact p.Prime := ⟨h.1⟩
  rw [← orderOf_primitivePowSubRatio_eq h]
  simpa only [Fintype.card_units, ZMod.card] using
    (show orderOf (primitivePowSubRatio h) ∣ Fintype.card ((ZMod p)ˣ) from
      orderOf_dvd_card)

end BealUnified
