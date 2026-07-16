import BealUnified.ABC

set_option linter.style.header false

/-!
# Exponent normalization for Beal solutions

Every exponent at least three has either `4` or an odd prime as a divisor.
Dividing the exponents by such divisors moves the remaining powers into the
bases, retaining the Beal equation and its primitive data.
-/

namespace BealUnified

/-- An exponent divisor usable for Beal normalization. -/
def AdmissibleExponentDivisor (n d : ℕ) : Prop :=
  d ∣ n ∧ (d = 4 ∨ d.Prime ∧ Odd d)

/-- Every natural exponent at least three has an admissible divisor. -/
theorem exists_admissibleExponentDivisor {n : ℕ} (hn : 3 ≤ n) :
    ∃ d, AdmissibleExponentDivisor n d := by
  by_cases hfour : 4 ∣ n
  · exact ⟨4, hfour, Or.inl rfl⟩
  obtain ⟨p, hp, hpn⟩ := Nat.exists_prime_and_dvd (by omega : n ≠ 1)
  rcases hp.eq_two_or_odd' with hp_two | hp_odd
  · subst p
    have htwo : 2 ∣ n := hpn
    have hfactor : 2 * (n / 2) = n := by
      simpa [Nat.mul_comm] using Nat.div_mul_cancel htwo
    have hm_ne_one : n / 2 ≠ 1 := by
      intro hm
      omega
    obtain ⟨q, hq, hqdiv⟩ := Nat.exists_prime_and_dvd hm_ne_one
    have hq_ne_two : q ≠ 2 := by
      intro hq_two
      subst q
      apply hfour
      rw [← hfactor]
      exact Nat.mul_dvd_mul_left 2 hqdiv
    refine ⟨q, ?_, Or.inr ⟨hq, hq.odd_of_ne_two hq_ne_two⟩⟩
    rw [← hfactor]
    exact dvd_mul_of_dvd_right hqdiv 2
  · exact ⟨p, hpn, Or.inr ⟨hp, hp_odd⟩⟩

private lemma admissibleExponentDivisor_three_le
    {n d : ℕ} (hd : AdmissibleExponentDivisor n d) : 3 ≤ d := by
  rcases hd with ⟨_, rfl | ⟨hp, hpodd⟩⟩
  · omega
  · exact hp.odd_iff.mp hpodd

/--
Normalize a primitive Beal solution by admissible divisors of its exponents.

The resulting exponents are each either `4` or an odd prime, while the
equation, pairwise coprimality, and radical of the base product are retained.
-/
theorem beal_normalize
    {A B C x y z : ℕ}
    (sol : Solution A B C x y z)
    (hprim : Nat.gcd (Nat.gcd A B) C = 1) :
    ∃ dA dB dC,
      AdmissibleExponentDivisor x dA ∧
      AdmissibleExponentDivisor y dB ∧
      AdmissibleExponentDivisor z dC ∧
      Solution (A ^ (x / dA)) (B ^ (y / dB)) (C ^ (z / dC)) dA dB dC ∧
      Nat.Coprime (A ^ (x / dA)) (B ^ (y / dB)) ∧
      Nat.Coprime (B ^ (y / dB)) (C ^ (z / dC)) ∧
      Nat.Coprime (A ^ (x / dA)) (C ^ (z / dC)) ∧
      rad ((A ^ (x / dA)) * (B ^ (y / dB)) * (C ^ (z / dC))) = rad (A * B * C) := by
  obtain ⟨dA, hdA⟩ := exists_admissibleExponentDivisor sol.hx
  obtain ⟨dB, hdB⟩ := exists_admissibleExponentDivisor sol.hy
  obtain ⟨dC, hdC⟩ := exists_admissibleExponentDivisor sol.hz
  have hx_rewrite : x / dA * dA = x := Nat.div_mul_cancel hdA.1
  have hy_rewrite : y / dB * dB = y := Nat.div_mul_cancel hdB.1
  have hz_rewrite : z / dC * dC = z := Nat.div_mul_cancel hdC.1
  have hxdA : x / dA ≠ 0 := by
    intro h
    rw [h, zero_mul] at hx_rewrite
    exact (Nat.ne_of_gt (lt_of_lt_of_le (by decide : 0 < 3) sol.hx)) hx_rewrite.symm
  have hydB : y / dB ≠ 0 := by
    intro h
    rw [h, zero_mul] at hy_rewrite
    exact (Nat.ne_of_gt (lt_of_lt_of_le (by decide : 0 < 3) sol.hy)) hy_rewrite.symm
  have hzdC : z / dC ≠ 0 := by
    intro h
    rw [h, zero_mul] at hz_rewrite
    exact (Nat.ne_of_gt (lt_of_lt_of_le (by decide : 0 < 3) sol.hz)) hz_rewrite.symm
  have hpair : Nat.Coprime A B ∧ Nat.Coprime B C ∧ Nat.Coprime A C :=
    pairwise_coprime_of_solution (A := A) (B := B) (C := C)
      (x := x) (y := y) (z := z)
      (le_trans (by decide : 1 ≤ 3) sol.hx)
      (le_trans (by decide : 1 ≤ 3) sol.hy)
      (le_trans (by decide : 1 ≤ 3) sol.hz) hprim sol.eqn
  refine ⟨dA, dB, dC, hdA, hdB, hdC, ?_, ?_, ?_, ?_, ?_⟩
  · refine ⟨pow_pos sol.posA _, pow_pos sol.posB _, pow_pos sol.posC _,
      admissibleExponentDivisor_three_le hdA,
      admissibleExponentDivisor_three_le hdB,
      admissibleExponentDivisor_three_le hdC, ?_⟩
    simpa only [BealEquation, ← pow_mul, hx_rewrite, hy_rewrite, hz_rewrite] using sol.eqn
  · exact (hpair.1.pow_left _).pow_right _
  · exact (hpair.2.1.pow_left _).pow_right _
  · exact (hpair.2.2.pow_left _).pow_right _
  · exact rad_power_triple_mul sol.posA.ne' sol.posB.ne' sol.posC.ne'
      hxdA hydB hzdC

end BealUnified
