import BealUnified.Valuations

set_option linter.style.header false

/-!
# BR-20: coprime-sum valuation support

This research file records a narrow p-adic side condition useful for applying
plus-sign LTE to coprime bases.  If a prime divides `A + B` and `A` is coprime
to `B`, then the prime cannot divide either base, hence its valuation on both
bases and their powers is zero.
-/

namespace BealUnified

namespace Research

/--
A prime divisor of a sum of coprime natural numbers has zero valuation on both
bases and on all powers of the bases.

This is not the plus-sign LTE formula itself; it is the exact coprime-sum
valuation side condition that such an LTE formula needs.
-/
theorem padicValNat_prime_dvd_coprime_sum_pows_eq_zero
    {p A B x y : ℕ} [Fact p.Prime]
    (hAB : Nat.Coprime A B) (hpAB : p ∣ A + B) :
    padicValNat p A = 0 ∧ padicValNat p B = 0 ∧
      padicValNat p (A ^ x) = 0 ∧ padicValNat p (B ^ y) = 0 := by
  have hp : p.Prime := Fact.out
  have hpA : ¬ p ∣ A := by
    intro hpA
    have hpB : p ∣ B := (Nat.dvd_add_iff_right hpA).2 hpAB
    have hp1 : p = 1 := Nat.eq_one_of_dvd_coprimes hAB hpA hpB
    exact hp.ne_one hp1
  have hpB : ¬ p ∣ B := by
    intro hpB
    have hpA : p ∣ A := (Nat.dvd_add_iff_left hpB).2 hpAB
    have hp1 : p = 1 := Nat.eq_one_of_dvd_coprimes hAB hpA hpB
    exact hp.ne_one hp1
  have hA : padicValNat p A = 0 := padicValNat.eq_zero_of_not_dvd hpA
  have hB : padicValNat p B = 0 := padicValNat.eq_zero_of_not_dvd hpB
  refine ⟨hA, hB, ?_, ?_⟩
  · rw [padicValNat.pow, hA, mul_zero]
  · rw [padicValNat.pow, hB, mul_zero]

end Research

end BealUnified
