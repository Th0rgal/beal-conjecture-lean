import BealUnified.Parity
import Mathlib.NumberTheory.PrimesCongruentOne

set_option linter.style.header false

/-!
# The prime-order interface for the equal odd-exponent branch

This file isolates the finite-field step behind the cyclotomic quotient
argument.  It deliberately makes no claim that the resulting congruence is a
contradiction: it is a reusable restriction on primes away from `A + B`.
-/

namespace BealUnified

/-- The natural-number cyclotomic quotient occurring for an odd exponent. -/
def oddCyclotomicQuotient (A B p : ℕ) : ℕ :=
  (A ^ p + B ^ p) / (A + B)

/-- The quotient recombines with `A + B` when `p` is odd. -/
theorem oddCyclotomicQuotient_mul_add (A B p : ℕ) (hp : Odd p) :
    oddCyclotomicQuotient A B p * (A + B) = A ^ p + B ^ p := by
  exact Nat.div_mul_cancel (add_dvd_pow_add_pow_of_odd hp)

/-- A divisor of the quotient divides the original sum of odd powers. -/
theorem dvd_pow_add_pow_of_dvd_oddCyclotomicQuotient
    {q A B p : ℕ} (hp : Odd p) (hq : q ∣ oddCyclotomicQuotient A B p) :
    q ∣ A ^ p + B ^ p := by
  rw [← oddCyclotomicQuotient_mul_add A B p hp]
  exact dvd_mul_of_dvd_left hq _

/--
Finite-field order criterion used downstream: if the ratio has `p`-th power
`-1`, but is not itself `-1`, then its order is exactly `2p`.
-/
theorem orderOf_eq_two_mul_of_pow_eq_neg_one
    {q p : ℕ} (hq : q.Prime) (hp : p.Prime) (hqodd : q ≠ 2)
    (x : (ZMod q)ˣ) (hxpow : x ^ p = -1) (hxneg : x ≠ -1) :
    orderOf x = 2 * p := by
  letI : Fact q.Prime := ⟨hq⟩
  have hchar : ringChar (ZMod q) ≠ 2 := by
    simpa [ringChar.eq (ZMod q) q] using hqodd
  have hminus_order : orderOf (-1 : (ZMod q)ˣ) = 2 := by
    rw [← orderOf_units, Units.coe_neg_one, orderOf_neg_one, if_neg hchar]
  have hp0 : p ≠ 0 := hp.ne_zero
  have hdiv : orderOf x / Nat.gcd (orderOf x) p = 2 := by
    rw [← orderOf_pow' x hp0, hxpow, hminus_order]
  have hgcd : Nat.gcd (orderOf x) p = 1 ∨ Nat.gcd (orderOf x) p = p := by
    exact (Nat.dvd_prime hp).mp (Nat.gcd_dvd_right _ _)
  rcases hgcd with hgcd | hgcd
  · have hord : orderOf x = 2 := by simpa [hgcd] using hdiv
    have hsq : x ^ 2 = 1 := by rw [← hord, pow_orderOf_eq_one]
    have hsq' : (x : ZMod q) ^ 2 = 1 := by
      simpa [pow_two] using congrArg Units.val hsq
    have : x = 1 ∨ x = -1 := by
      rcases (sq_eq_one_iff.mp hsq') with hxone | hxminus
      · left
        exact Units.ext (by simpa using hxone)
      · right
        exact Units.ext (by simpa using hxminus)
    rcases this with hxone | hxminus
    · have : orderOf x = 1 := orderOf_eq_one_iff.mpr hxone
      omega
    · exact (hxneg hxminus).elim
  · have hpdvd : p ∣ orderOf x := by
      rwa [Nat.gcd_eq_right_iff_dvd] at hgcd
    rw [hgcd] at hdiv
    exact (Nat.div_eq_iff_eq_mul_left hp.pos hpdvd).mp hdiv

/--
An exact `2p` order in `(ℤ/qℤ)×` forces the standard congruence
restriction `q ≡ 1 (mod 2p)`.
-/
theorem prime_modEq_one_of_orderOf_eq_two_mul
    {q p : ℕ} (hq : q.Prime) (x : (ZMod q)ˣ)
    (horder : orderOf x = 2 * p) :
    q ≡ 1 [MOD 2 * p] := by
  letI : Fact q.Prime := ⟨hq⟩
  letI : NeZero q := ⟨hq.ne_zero⟩
  have hdiv : orderOf x ∣ q - 1 :=
    by simpa only [orderOf_units] using
      ZMod.orderOf_dvd_card_sub_one (Units.ne_zero x)
  rw [horder] at hdiv
  exact (Nat.modEq_iff_dvd' hq.pos).2 hdiv |>.symm

/-- Combined downstream interface for the Card A finite-field step. -/
theorem prime_modEq_one_of_ratio_pow_eq_neg_one
    {q p : ℕ} (hq : q.Prime) (hp : p.Prime) (hqodd : q ≠ 2)
    (x : (ZMod q)ˣ) (hxpow : x ^ p = -1) (hxneg : x ≠ -1) :
    q ≡ 1 [MOD 2 * p] := by
  apply prime_modEq_one_of_orderOf_eq_two_mul hq x
  exact orderOf_eq_two_mul_of_pow_eq_neg_one hq hp hqodd x hxpow hxneg

end BealUnified
