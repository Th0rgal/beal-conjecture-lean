import BealUnified.CyclotomicQuotient
import Mathlib.NumberTheory.Padics.PadicVal.Basic

set_option linter.style.header false

/-!
# Cyclotomic cofactors in the odd-prime diagonal branch

This module records the part of the standard odd-prime cyclotomic-cofactor
argument that is independent of a primitive-divisor theorem.  In particular,
the finite-field conclusion is packaged so that a downstream argument only has
to supply the reduction of a prime divisor of the cofactor to a nontrivial
ratio in `ZMod q`.

No existence of a nonexceptional prime divisor, and no contradiction, is
asserted here.
-/

namespace BealUnified

/-- The cofactor in `A^p + B^p = (A + B) * Φ`. -/
abbrev cyclotomicCofactor (A B p : ℕ) : ℕ :=
  oddCyclotomicQuotient A B p

/-- A positive common divisor which divides a prime is either `1` or that prime. -/
theorem eq_one_or_eq_prime_of_dvd_prime {d p : ℕ} (_hd : 0 < d)
    (hp : p.Prime) (hdp : d ∣ p) : d = 1 ∨ d = p := by
  exact (Nat.dvd_prime hp).mp hdp |>.imp id id

/--
The final elementary reduction for the gcd step.  Thus, once the usual
cyclotomic congruence has supplied `gcd (A+B) Φ ∣ p`, the gcd has precisely
the expected two possibilities.
-/
theorem gcd_eq_one_or_eq_prime_of_dvd_prime
    {A B p : ℕ} (hp : p.Prime)
    (hdiv : Nat.gcd (A + B) (cyclotomicCofactor A B p) ∣ p) :
    Nat.gcd (A + B) (cyclotomicCofactor A B p) = 1 ∨
      Nat.gcd (A + B) (cyclotomicCofactor A B p) = p := by
  apply eq_one_or_eq_prime_of_dvd_prime
  · apply Nat.pos_of_ne_zero
    intro hzero
    rw [hzero, zero_dvd_iff] at hdiv
    exact hp.ne_zero hdiv
  · exact hp
  · exact hdiv

/--
The exceptional factor contributes exactly one to its own valuation, before
any contribution from the remaining cofactor.  This is the valuation form
needed when the exceptional branch is separated as `p * D`.
-/
theorem padicValNat_prime_mul {p D : ℕ} [Fact p.Prime] (hD : D ≠ 0) :
    padicValNat p (p * D) = 1 + padicValNat p D := by
  rw [padicValNat.mul (show p ≠ 0 from (Fact.out : p.Prime).ne_zero) hD,
    padicValNat_self]

/-- A prime factor of the residual factor is a prime factor of the right base. -/
theorem prime_dvd_right_of_dvd_residual
    {q D C : ℕ} (_hq : q.Prime) (hD : D ∣ C) (hqD : q ∣ D) : q ∣ C :=
  dvd_trans hqD hD

/--
The nonexceptional finite-field branch of the cofactor argument.  The two
ratio hypotheses are exactly what reduction modulo `q` must provide; they
give exact order `2p` and hence `q ≡ 1 (mod 2p)`.
-/
theorem nonexceptional_prime_order_and_congruence
    {q p : ℕ} (hq : q.Prime) (hp : p.Prime) (hqne : q ≠ 2)
    (x : (ZMod q)ˣ) (hxpow : x ^ p = -1) (hxneg : x ≠ -1) :
    orderOf x = 2 * p ∧ q ≡ 1 [MOD 2 * p] := by
  constructor
  · exact orderOf_eq_two_mul_of_pow_eq_neg_one hq hp hqne x hxpow hxneg
  · exact prime_modEq_one_of_ratio_pow_eq_neg_one hq hp hqne x hxpow hxneg

/--
Downstream interface for a power decomposition of the cyclotomic cofactor.
It deliberately records, rather than proves, the factorisation step: deriving
it from `A^p + B^p = C^z` requires additional valuation input.
-/
structure CofactorPowerData (A B C p z : ℕ) where
  δ : ℕ
  D : ℕ
  δ_le_one : δ ≤ 1
  factor : cyclotomicCofactor A B p = p ^ δ * D ^ z
  residual_dvd_right : D ∣ C

/-- The residual factor supplied by `CofactorPowerData` divides `C`. -/
theorem CofactorPowerData.residual_dvd_C
    {A B C p z : ℕ} (h : CofactorPowerData A B C p z) : h.D ∣ C :=
  h.residual_dvd_right

end BealUnified
