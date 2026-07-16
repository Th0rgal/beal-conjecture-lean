import BealUnified.Parity

set_option linter.style.header false

/-!
# Modulo-eight consequences for primitive Beal solutions

This file records the elementary residue information for a primitive Beal
solution.  It deliberately uses only the established parity and pairwise
coprimality reductions; it does not use a plus-sign LTE argument.
-/

namespace BealUnified

private lemma modEq_one_of_odd_square {n : ℕ} (hn : Odd n) :
    Nat.ModEq 8 (n ^ 2) 1 := by
  apply Nat.ModEq.symm
  have hn0 : n ≠ 0 := by
    rcases hn with ⟨k, rfl⟩
    omega
  have hsqpos : 1 ≤ n ^ 2 := Nat.one_le_iff_ne_zero.mpr (pow_ne_zero 2 hn0)
  apply (Nat.modEq_iff_dvd' hsqpos).mpr
  simpa using Nat.eight_dvd_sq_sub_one_of_odd hn

private lemma modEq_one_of_odd_even_pow {n e : ℕ} (hn : Odd n) (he : Even e) :
    Nat.ModEq 8 (n ^ e) 1 := by
  rcases he with ⟨k, rfl⟩
  have hsq : Nat.ModEq 8 ((n ^ k) ^ 2) 1 :=
    modEq_one_of_odd_square (hn.pow)
  simpa [pow_two, pow_add] using hsq

private lemma modEq_self_of_odd_odd_pow {n e : ℕ} (hn : Odd n) (he : Odd e) :
    Nat.ModEq 8 (n ^ e) n := by
  rcases he with ⟨k, rfl⟩
  have hsq : Nat.ModEq 8 ((n ^ k) ^ 2) 1 :=
    modEq_one_of_odd_square (hn.pow)
  have hpow : Nat.ModEq 8 (n ^ (k + k)) 1 := by
    simpa [pow_two, pow_add] using hsq
  simpa [pow_add, two_mul] using hpow.mul (Nat.ModEq.rfl : Nat.ModEq 8 n n)

/-- An even base raised to an exponent at least three is divisible by eight. -/
lemma eight_dvd_pow_of_even_of_three_le {n e : ℕ}
    (hn : Even n) (he : 3 ≤ e) : 8 ∣ n ^ e := by
  rcases hn with ⟨k, rfl⟩
  have hcube : 8 ∣ (k + k) ^ 3 := by
    refine ⟨k ^ 3, ?_⟩
    ring
  exact hcube.trans (pow_dvd_pow (k + k) he)

private lemma odd_of_coprime_even_right {m n : ℕ}
    (hcop : Nat.Coprime m n) (hn : Even n) : Odd m := by
  apply Nat.not_even_iff_odd.mp
  intro hm
  rw [Nat.coprime_iff_gcd_eq_one] at hcop
  rw [even_iff_two_dvd] at hm hn
  have htwo : 2 ∣ Nat.gcd m n := Nat.dvd_gcd hm hn
  omega

private lemma primitive_pairwise {A B C x y z : ℕ}
    (sol : Solution A B C x y z)
    (hprimitive : Nat.gcd (Nat.gcd A B) C = 1) :
    Nat.Coprime A B ∧ Nat.Coprime B C ∧ Nat.Coprime A C :=
  pairwise_coprime_of_solution (A := A) (B := B) (C := C)
    (x := x) (y := y) (z := z)
    (le_trans (by decide : 1 ≤ 3) sol.hx)
    (le_trans (by decide : 1 ≤ 3) sol.hy)
    (le_trans (by decide : 1 ≤ 3) sol.hz) hprimitive sol.eqn

/-- In a primitive Beal solution, precisely one base is even. -/
theorem exactly_one_even_of_solution_of_primitive
    {A B C x y z : ℕ}
    (sol : Solution A B C x y z)
    (hprimitive : Nat.gcd (Nat.gcd A B) C = 1) :
    (Even A ∧ Odd B ∧ Odd C) ∨
      (Odd A ∧ Even B ∧ Odd C) ∨ (Odd A ∧ Odd B ∧ Even C) := by
  have hcop := primitive_pairwise sol hprimitive
  by_cases hA : Even A
  · by_cases hB : Even B
    · exfalso
      rw [Nat.coprime_iff_gcd_eq_one] at hcop
      rw [even_iff_two_dvd] at hA hB
      have : 2 ∣ Nat.gcd A B := Nat.dvd_gcd hA hB
      omega
    · by_cases hC : Even C
      · exfalso
        rw [Nat.coprime_iff_gcd_eq_one] at hcop
        rw [even_iff_two_dvd] at hA hC
        have : 2 ∣ Nat.gcd A C := Nat.dvd_gcd hA hC
        omega
      · exact Or.inl ⟨hA, Nat.not_even_iff_odd.mp hB, Nat.not_even_iff_odd.mp hC⟩
  · by_cases hB : Even B
    · by_cases hC : Even C
      · exfalso
        rw [Nat.coprime_iff_gcd_eq_one] at hcop
        rw [even_iff_two_dvd] at hB hC
        have : 2 ∣ Nat.gcd B C := Nat.dvd_gcd hB hC
        omega
      · exact Or.inr (Or.inl ⟨Nat.not_even_iff_odd.mp hA, hB, Nat.not_even_iff_odd.mp hC⟩)
    · by_cases hC : Even C
      · exact Or.inr (Or.inr ⟨Nat.not_even_iff_odd.mp hA, Nat.not_even_iff_odd.mp hB, hC⟩)
      · exact (no_solution_all_bases_odd (Nat.not_even_iff_odd.mp hA)
          (Nat.not_even_iff_odd.mp hB) (Nat.not_even_iff_odd.mp hC) sol.eqn).elim

/-- If both left exponents are even in a primitive solution, then `C` is odd. -/
theorem odd_C_of_even_left_exponents_of_solution_of_primitive
    {A B C x y z : ℕ}
    (sol : Solution A B C x y z)
    (hprimitive : Nat.gcd (Nat.gcd A B) C = 1)
    (hx : Even x) (hy : Even y) : Odd C := by
  by_contra hCodd
  have hC : Even C := Nat.not_odd_iff_even.mp hCodd
  have hcop := primitive_pairwise sol hprimitive
  have hA : Odd A := odd_of_coprime_even_right hcop.2.2 hC
  have hB : Odd B := odd_of_coprime_even_right hcop.2.1 hC
  have hAx : Nat.ModEq 8 (A ^ x) 1 := modEq_one_of_odd_even_pow hA hx
  have hBy : Nat.ModEq 8 (B ^ y) 1 := modEq_one_of_odd_even_pow hB hy
  have hCz_dvd : 8 ∣ C ^ z := eight_dvd_pow_of_even_of_three_le hC sol.hz
  have hCz : Nat.ModEq 8 (C ^ z) 0 := by
    exact hCz_dvd.modEq_zero_nat
  have heq : Nat.ModEq 8 (A ^ x + B ^ y) (C ^ z) := by
    rw [sol.eqn]
  have : Nat.ModEq 8 (1 + 1) 0 := (hAx.add hBy).symm.trans heq |>.trans hCz
  norm_num [Nat.ModEq] at this

/-- In the even-`C`, even-`x`, odd-`y` primitive branch, `B` is `7` modulo `8`. -/
theorem B_modEq_seven_of_even_C_even_x_odd_y_of_solution_of_primitive
    {A B C x y z : ℕ}
    (sol : Solution A B C x y z)
    (hprimitive : Nat.gcd (Nat.gcd A B) C = 1)
    (hC : Even C) (hx : Even x) (hy : Odd y) :
    Nat.ModEq 8 B 7 := by
  have hcop := primitive_pairwise sol hprimitive
  have hA : Odd A := odd_of_coprime_even_right hcop.2.2 hC
  have hB : Odd B := odd_of_coprime_even_right hcop.2.1 hC
  have hAx : Nat.ModEq 8 (A ^ x) 1 := modEq_one_of_odd_even_pow hA hx
  have hByB : Nat.ModEq 8 (B ^ y) B := modEq_self_of_odd_odd_pow hB hy
  have hCz_dvd : 8 ∣ C ^ z := eight_dvd_pow_of_even_of_three_le hC sol.hz
  have hCz : Nat.ModEq 8 (C ^ z) 0 := by
    exact hCz_dvd.modEq_zero_nat
  have heq : Nat.ModEq 8 (A ^ x + B ^ y) (C ^ z) := by
    rw [sol.eqn]
  have hsum : Nat.ModEq 8 (1 + B) 0 := (hAx.add hByB).symm.trans heq |>.trans hCz
  have hB7 : Nat.ModEq 8 B 7 := by
    norm_num [Nat.ModEq] at hsum ⊢
    omega
  exact hB7

/-- The four odd residue classes modulo eight. -/
example : (1 : ℕ) % 8 = 1 := by norm_num
example : (3 : ℕ) % 8 = 3 := by norm_num
example : (5 : ℕ) % 8 = 5 := by norm_num
example : (7 : ℕ) % 8 = 7 := by norm_num

end BealUnified
