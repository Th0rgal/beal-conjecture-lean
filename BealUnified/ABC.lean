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

/-- Oesterle-Masser ABC, stated for positive coprime natural triples. -/
def ABCConjecture : Prop :=
  ∀ ε : ℝ, 0 < ε →
    ∃ K : ℝ, 0 < K ∧
      ∀ a b c : ℕ,
        0 < a → 0 < b → 0 < c →
        a.Coprime b → a + b = c →
        ((max (max a b) c : ℕ) : ℝ) ≤
          K * (((rad (a * b * c) : ℕ) : ℝ) ^ (1 + ε))

/-- A primitive Beal counterexample. -/
def PrimitiveBealCounterexample (A B C x y z : ℕ) : Prop :=
  Solution A B C x y z ∧ Nat.gcd (Nat.gcd A B) C = 1

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

end BealUnified
