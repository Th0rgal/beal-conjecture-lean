import BealUnified.Statement
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.NumberTheory.Divisors

set_option linter.style.header false

/-!
# Beal conjecture: ABC setup

This module defines the radical of a natural number, states a standard
Oesterle-Masser style ABC conjecture over natural triples, and proves that ABC
applies to the `A ^ x + B ^ y = C ^ z` triple of any primitive Beal
counterexample.  It does not claim an unconditional `ABC -> Beal` theorem,
because the qualitative ABC statement alone leaves a finite bounded search
without a computable bound.
-/

namespace BealUnified

/-- The radical of `n`: product of distinct prime factors. -/
def rad (n : ℕ) : ℕ :=
  n.primeFactors.prod id

lemma rad_def (n : ℕ) : rad n = n.primeFactors.prod id := rfl

lemma rad_dvd (n : ℕ) : rad n ∣ n := by
  simpa [rad] using Nat.prod_primeFactors_dvd n

lemma rad_pow_of_pos (n k : ℕ) (hk : k ≠ 0) : rad (n ^ k) = rad n := by
  simp [rad, Nat.primeFactors_pow n hk]

lemma rad_power_triple_mul
    {A B C x y z : ℕ}
    (hA : A ≠ 0) (hB : B ≠ 0) (hC : C ≠ 0)
    (hx : x ≠ 0) (hy : y ≠ 0) (hz : z ≠ 0) :
    rad ((A ^ x) * (B ^ y) * (C ^ z)) = rad (A * B * C) := by
  unfold rad
  rw [Nat.primeFactors_mul
      (mul_ne_zero (pow_ne_zero x hA) (pow_ne_zero y hB)) (pow_ne_zero z hC),
    Nat.primeFactors_mul (pow_ne_zero x hA) (pow_ne_zero y hB),
    Nat.primeFactors_pow A hx, Nat.primeFactors_pow B hy, Nat.primeFactors_pow C hz,
    Nat.primeFactors_mul (mul_ne_zero hA hB) hC, Nat.primeFactors_mul hA hB]

/-- Oesterle-Masser ABC, stated for positive coprime natural triples. -/
def ABCConjecture : Prop :=
  ∀ ε : ℝ, 0 < ε →
    ∃ K : ℝ, 0 < K ∧
      ∀ a b c : ℕ,
        0 < a → 0 < b → 0 < c →
        a.Coprime b → a + b = c →
        ((max (max a b) c : ℕ) : ℝ) ≤
          K * (((rad (a * b * c) : ℕ) : ℝ) ^ (1 + ε))

/--
The ABC inequality for one fixed exponent `ε` and constant `K`.

This is the local assumption actually consumed by the Beal reduction below;
`ABCConjecture` only supplies such a `K` existentially for each positive `ε`.
-/
def ABCBoundFor (ε K : ℝ) : Prop :=
  0 < K ∧
    ∀ a b c : ℕ,
      0 < a → 0 < b → 0 < c →
      a.Coprime b → a + b = c →
      ((max (max a b) c : ℕ) : ℝ) ≤
        K * (((rad (a * b * c) : ℕ) : ℝ) ^ (1 + ε))

/-- A primitive Beal counterexample. -/
def PrimitiveBealCounterexample (A B C x y z : ℕ) : Prop :=
  Solution A B C x y z ∧ Nat.gcd (Nat.gcd A B) C = 1

/--
For a positive Beal solution, the radical of the base product raised to the
minimum exponent is bounded by the cube of the largest Beal power.

The primitive hypothesis is present for the counterexample-facing API; the
inequality itself only uses positivity and the exponent bounds in `Solution`.
-/
lemma rad_base_pow_min_le_max_cube
    {A B C x y z : ℕ}
    (hCounter : PrimitiveBealCounterexample A B C x y z) :
    (rad (A * B * C)) ^ (min x (min y z)) ≤
      (max (max (A ^ x) (B ^ y)) (C ^ z)) ^ 3 := by
  rcases hCounter with ⟨sol, _hPrim⟩
  let m := min x (min y z)
  let M := max (max (A ^ x) (B ^ y)) (C ^ z)
  have hABCpos : 0 < A * B * C := mul_pos (mul_pos sol.posA sol.posB) sol.posC
  have hRadLe : rad (A * B * C) ≤ A * B * C :=
    Nat.le_of_dvd hABCpos (rad_dvd (A * B * C))
  have hmX : m ≤ x := Nat.min_le_left x (min y z)
  have hmY : m ≤ y :=
    le_trans (Nat.min_le_right x (min y z)) (Nat.min_le_left y z)
  have hmZ : m ≤ z :=
    le_trans (Nat.min_le_right x (min y z)) (Nat.min_le_right y z)
  have hA1 : 1 ≤ A := sol.posA
  have hB1 : 1 ≤ B := sol.posB
  have hC1 : 1 ≤ C := sol.posC
  have hAm : A ^ m ≤ A ^ x := pow_le_pow_right₀ hA1 hmX
  have hBm : B ^ m ≤ B ^ y := pow_le_pow_right₀ hB1 hmY
  have hCm : C ^ m ≤ C ^ z := pow_le_pow_right₀ hC1 hmZ
  have hPowProd :
      (A * B * C) ^ m ≤ A ^ x * B ^ y * C ^ z := by
    calc
      (A * B * C) ^ m = A ^ m * B ^ m * C ^ m := by
        rw [mul_pow, mul_pow]
      _ ≤ A ^ x * B ^ y * C ^ z :=
        Nat.mul_le_mul (Nat.mul_le_mul hAm hBm) hCm
  have hRadPow : (rad (A * B * C)) ^ m ≤ (A * B * C) ^ m :=
    Nat.pow_le_pow_left hRadLe m
  have hAxM : A ^ x ≤ M :=
    le_trans (Nat.le_max_left (A ^ x) (B ^ y))
      (Nat.le_max_left (max (A ^ x) (B ^ y)) (C ^ z))
  have hByM : B ^ y ≤ M :=
    le_trans (Nat.le_max_right (A ^ x) (B ^ y))
      (Nat.le_max_left (max (A ^ x) (B ^ y)) (C ^ z))
  have hCzM : C ^ z ≤ M :=
    Nat.le_max_right (max (A ^ x) (B ^ y)) (C ^ z)
  have hPowerProdMax : A ^ x * B ^ y * C ^ z ≤ M ^ 3 := by
    calc
      A ^ x * B ^ y * C ^ z ≤ M * M * M :=
        Nat.mul_le_mul (Nat.mul_le_mul hAxM hByM) hCzM
      _ = M ^ 3 := by ring
  exact le_trans hRadPow (le_trans hPowProd hPowerProdMax)

lemma common_prime_dvd_C_of_dvd_A_B
    {A B C x y z : ℕ}
    (hx : 0 < x) (hy : 0 < y)
    (hEq : BealEquation A B C x y z)
    {p : ℕ} (hp : p.Prime) (hpa : p ∣ A) (hpb : p ∣ B) :
    p ∣ C := by
  have hpAx : p ∣ A ^ x := dvd_pow hpa hx.ne'
  have hpBy : p ∣ B ^ y := dvd_pow hpb hy.ne'
  have hpSum : p ∣ A ^ x + B ^ y := Nat.dvd_add hpAx hpBy
  have hpCz : p ∣ C ^ z := by
    dsimp [BealEquation] at hEq
    rwa [hEq] at hpSum
  exact hp.dvd_of_dvd_pow hpCz

lemma common_prime_dvd_B_of_dvd_A_C
    {A B C x y z : ℕ}
    (hx : 0 < x) (_hy : 0 < y) (hz : 0 < z)
    (hEq : BealEquation A B C x y z)
    {p : ℕ} (hp : p.Prime) (hpa : p ∣ A) (hpc : p ∣ C) :
    p ∣ B := by
  have hpAx : p ∣ A ^ x := dvd_pow hpa hx.ne'
  have hpCz : p ∣ C ^ z := dvd_pow hpc hz.ne'
  have hpBy : p ∣ B ^ y := by
    have hdiv := Nat.dvd_sub hpCz hpAx
    rw [← hEq, Nat.add_sub_cancel_left] at hdiv
    exact hdiv
  exact hp.dvd_of_dvd_pow hpBy

lemma common_prime_dvd_A_of_dvd_B_C
    {A B C x y z : ℕ}
    (_hx : 0 < x) (hy : 0 < y) (hz : 0 < z)
    (hEq : BealEquation A B C x y z)
    {p : ℕ} (hp : p.Prime) (hpb : p ∣ B) (hpc : p ∣ C) :
    p ∣ A := by
  have hpBy : p ∣ B ^ y := dvd_pow hpb hy.ne'
  have hpCz : p ∣ C ^ z := dvd_pow hpc hz.ne'
  have hpAx : p ∣ A ^ x := by
    have hdiv := Nat.dvd_sub hpCz hpBy
    rw [← hEq, Nat.add_sub_cancel_right] at hdiv
    exact hdiv
  exact hp.dvd_of_dvd_pow hpAx

lemma coprime_A_B_of_primitive
    {A B C x y z : ℕ}
    (hx : 0 < x) (hy : 0 < y)
    (hEq : BealEquation A B C x y z)
    (hPrim : Nat.gcd (Nat.gcd A B) C = 1) :
    A.Coprime B := by
  rw [Nat.coprime_iff_gcd_eq_one]
  by_contra hne
  obtain ⟨p, hpprime, hpd⟩ := Nat.exists_prime_and_dvd hne
  have hpa : p ∣ A := hpd.trans (Nat.gcd_dvd_left A B)
  have hpb : p ∣ B := hpd.trans (Nat.gcd_dvd_right A B)
  have hpc : p ∣ C :=
    common_prime_dvd_C_of_dvd_A_B hx hy hEq hpprime hpa hpb
  have hpd3 : p ∣ Nat.gcd (Nat.gcd A B) C := Nat.dvd_gcd hpd hpc
  rw [hPrim] at hpd3
  exact hpprime.not_dvd_one hpd3

lemma coprime_pow_A_B_of_primitive
    {A B C x y z : ℕ}
    (hx : 0 < x) (hy : 0 < y)
    (hEq : BealEquation A B C x y z)
    (hPrim : Nat.gcd (Nat.gcd A B) C = 1) :
    (A ^ x).Coprime (B ^ y) := by
  exact ((coprime_A_B_of_primitive hx hy hEq hPrim).pow_left x).pow_right y

/-- ABC applies to the power triple attached to any primitive Beal counterexample. -/
lemma abc_applies_to_primitive_beal_counterexample
    (hABC : ABCConjecture)
    {A B C x y z : ℕ}
    (hCounter : PrimitiveBealCounterexample A B C x y z)
    (ε : ℝ) (hε : 0 < ε) :
    ∃ K : ℝ, 0 < K ∧
      ((max (max (A ^ x) (B ^ y)) (C ^ z) : ℕ) : ℝ) ≤
        K * (((rad ((A ^ x) * (B ^ y) * (C ^ z)) : ℕ) : ℝ) ^ (1 + ε)) := by
  rcases hCounter with ⟨sol, hPrim⟩
  obtain ⟨K, hK, hBound⟩ := hABC ε hε
  refine ⟨K, hK, ?_⟩
  exact hBound (A ^ x) (B ^ y) (C ^ z)
    (pow_pos sol.posA x) (pow_pos sol.posB y) (pow_pos sol.posC z)
    (coprime_pow_A_B_of_primitive (lt_of_lt_of_le (by decide) sol.hx)
      (lt_of_lt_of_le (by decide) sol.hy) sol.eqn hPrim)
    sol.eqn

/--
The exact ABC-quality threshold needed by the existing Beal scaffold.

For a fixed ABC exponent `ε` and constant `K`, any primitive Beal
counterexample must satisfy the displayed ABC inequality on the power triple
`(A ^ x, B ^ y, C ^ z)`.  Therefore a strict violation of that inequality
rules out that primitive counterexample.  This theorem is conditional only on
the fixed bound `ABCBoundFor ε K`; it does not assert `ABCConjecture`.
-/
theorem not_primitive_beal_counterexample_of_abc_quality_threshold
    {A B C x y z : ℕ} {ε K : ℝ}
    (hBound : ABCBoundFor ε K)
    (hThreshold :
      K * (((rad ((A ^ x) * (B ^ y) * (C ^ z)) : ℕ) : ℝ) ^ (1 + ε)) <
        ((max (max (A ^ x) (B ^ y)) (C ^ z) : ℕ) : ℝ)) :
    ¬ PrimitiveBealCounterexample A B C x y z := by
  intro hCounter
  rcases hCounter with ⟨sol, hPrim⟩
  rcases hBound with ⟨_hK, hBound'⟩
  have hABCOnPowers :
      ((max (max (A ^ x) (B ^ y)) (C ^ z) : ℕ) : ℝ) ≤
        K * (((rad ((A ^ x) * (B ^ y) * (C ^ z)) : ℕ) : ℝ) ^ (1 + ε)) :=
    hBound' (A ^ x) (B ^ y) (C ^ z)
      (pow_pos sol.posA x) (pow_pos sol.posB y) (pow_pos sol.posC z)
      (coprime_pow_A_B_of_primitive (lt_of_lt_of_le (by decide) sol.hx)
        (lt_of_lt_of_le (by decide) sol.hy) sol.eqn hPrim)
      sol.eqn
  exact (not_lt_of_ge hABCOnPowers) hThreshold

/--
Cleaner ABC-quality threshold using the radical of the base triple.

For positive Beal exponents, the radical of the ABC power triple has the same
prime support as `A * B * C`, so the BR-18 threshold can be stated with
`rad (A * B * C)`.
-/
theorem not_primitive_beal_counterexample_of_abc_quality_threshold_rad_base
    {A B C x y z : ℕ} {ε K : ℝ}
    (hBound : ABCBoundFor ε K)
    (hThreshold :
      K * (((rad (A * B * C) : ℕ) : ℝ) ^ (1 + ε)) <
        ((max (max (A ^ x) (B ^ y)) (C ^ z) : ℕ) : ℝ)) :
    ¬ PrimitiveBealCounterexample A B C x y z := by
  intro hCounter
  rcases hCounter with ⟨sol, hPrim⟩
  rcases hBound with ⟨_hK, hBound'⟩
  have hABCOnPowers :
      ((max (max (A ^ x) (B ^ y)) (C ^ z) : ℕ) : ℝ) ≤
        K * (((rad ((A ^ x) * (B ^ y) * (C ^ z)) : ℕ) : ℝ) ^ (1 + ε)) :=
    hBound' (A ^ x) (B ^ y) (C ^ z)
      (pow_pos sol.posA x) (pow_pos sol.posB y) (pow_pos sol.posC z)
      (coprime_pow_A_B_of_primitive (lt_of_lt_of_le (by decide) sol.hx)
        (lt_of_lt_of_le (by decide) sol.hy) sol.eqn hPrim)
      sol.eqn
  have hRad :
      rad ((A ^ x) * (B ^ y) * (C ^ z)) = rad (A * B * C) :=
    rad_power_triple_mul sol.posA.ne' sol.posB.ne' sol.posC.ne'
      (lt_of_lt_of_le (by decide) sol.hx).ne'
      (lt_of_lt_of_le (by decide) sol.hy).ne'
      (lt_of_lt_of_le (by decide) sol.hz).ne'
  rw [hRad] at hABCOnPowers
  exact (not_lt_of_ge hABCOnPowers) hThreshold

/--
At the fixed ABC exponent `ε = 1`, the radical bridge forces a quantitative
power bound for any primitive Beal counterexample whose minimum exponent is at
least seven.
-/
theorem max_power_sub_six_le_abc_constant_pow_min
    {A B C x y z : ℕ} {K : ℝ}
    (hBound : ABCBoundFor 1 K)
    (hCounter : PrimitiveBealCounterexample A B C x y z)
    (hm : 7 ≤ min x (min y z)) :
    ((max (max (A ^ x) (B ^ y)) (C ^ z) : ℕ) : ℝ) ^
        (min x (min y z) - 6) ≤
      K ^ min x (min y z) := by
  rcases hCounter with ⟨sol, hPrim⟩
  let m := min x (min y z)
  let M : ℕ := max (max (A ^ x) (B ^ y)) (C ^ z)
  let R : ℕ := rad (A * B * C)
  rcases hBound with ⟨hK, hBound'⟩
  have hMpos : 0 < (M : ℝ) := by
    have hAxM : A ^ x ≤ M := by
      dsimp [M]
      exact le_trans (Nat.le_max_left _ _) (Nat.le_max_left _ _)
    exact_mod_cast lt_of_lt_of_le (pow_pos sol.posA x) hAxM
  have hABC : (M : ℝ) ≤ K * (R : ℝ) ^ 2 := by
    have h := hBound' (A ^ x) (B ^ y) (C ^ z)
      (pow_pos sol.posA x) (pow_pos sol.posB y) (pow_pos sol.posC z)
      (coprime_pow_A_B_of_primitive (lt_of_lt_of_le (by decide) sol.hx)
        (lt_of_lt_of_le (by decide) sol.hy) sol.eqn hPrim)
      sol.eqn
    have hRad :
        rad ((A ^ x) * (B ^ y) * (C ^ z)) = R := by
      dsimp [R]
      exact rad_power_triple_mul sol.posA.ne' sol.posB.ne' sol.posC.ne'
        (lt_of_lt_of_le (by decide) sol.hx).ne'
        (lt_of_lt_of_le (by decide) sol.hy).ne'
        (lt_of_lt_of_le (by decide) sol.hz).ne'
    dsimp [M]
    rw [hRad] at h
    norm_num at h ⊢
    exact h
  have hRadBridge : (R : ℝ) ^ m ≤ (M : ℝ) ^ 3 := by
    exact_mod_cast rad_base_pow_min_le_max_cube ⟨sol, hPrim⟩
  have hm6 : 6 ≤ m := le_trans (by omega) hm
  have hMain : (M : ℝ) ^ m ≤ K ^ m * (M : ℝ) ^ 6 := by
    calc
      (M : ℝ) ^ m ≤ (K * (R : ℝ) ^ 2) ^ m :=
        pow_le_pow_left₀ (le_of_lt hMpos) hABC m
      _ = K ^ m * ((R : ℝ) ^ m) ^ 2 := by ring
      _ ≤ K ^ m * ((M : ℝ) ^ 3) ^ 2 := by
        apply mul_le_mul_of_nonneg_left _ (by positivity : 0 ≤ K ^ m)
        rw [pow_two, pow_two]
        exact mul_self_le_mul_self (by positivity) hRadBridge
      _ = K ^ m * (M : ℝ) ^ 6 := by ring
  rw [show m = (m - 6) + 6 by omega, pow_add] at hMain
  simpa only [M, m] using
    le_of_mul_le_mul_right hMain (pow_pos hMpos 6)

end BealUnified
