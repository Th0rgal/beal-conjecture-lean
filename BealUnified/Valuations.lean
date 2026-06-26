import BealUnified.Statement
import Mathlib.NumberTheory.Padics.PadicVal.Basic

set_option linter.style.header false

/-!
# Beal conjecture: p-adic valuations and LTE infrastructure

This module records the direct valuation identity obtained from a Beal
equation and a small LTE interface.  The full plus-sign LTE theorem needed for
general Beal signatures is represented as the proposition `LTEConclusion`;
the exponent-one case and transfer lemmas are proved without assumptions.
-/

namespace BealUnified

/-- Taking `p`-adic valuation of a Beal equation gives the right-side power rule. -/
theorem beal_padicValNat_eq {p A B C x y z : ℕ} [Fact p.Prime]
    (hEq : BealEquation A B C x y z) :
    padicValNat p (A ^ x + B ^ y) = z * padicValNat p C := by
  rw [BealEquation] at hEq
  rw [hEq, padicValNat.pow]

/-- Positive `p`-adic valuation detects divisibility by `p`. -/
theorem prime_dvd_of_padicValNat_pos {p n : ℕ} [Fact p.Prime] (hn : n ≠ 0)
    (hval : 0 < padicValNat p n) : p ∣ n := by
  exact (dvd_iff_padicValNat_ne_zero (p := p) hn).2 (Nat.ne_of_gt hval)

/-- A common prime divisor of all bases gives Beal's common-factor conclusion. -/
theorem common_prime_divisor_implies_conclusion {p A B C : ℕ}
    (hp : p.Prime) (hC : 0 < C) (hpA : p ∣ A) (hpB : p ∣ B) (hpC : p ∣ C) :
    BealConclusion A B C := by
  let g := Nat.gcd (Nat.gcd A B) C
  have hpg : p ∣ g := Nat.dvd_gcd (Nat.dvd_gcd hpA hpB) hpC
  have hgpos : 0 < g := Nat.gcd_pos_of_pos_right _ hC
  exact lt_of_lt_of_le hp.one_lt (Nat.le_of_dvd hgpos hpg)

/-- If the triple gcd is `1`, no prime divides all three bases. -/
theorem no_common_prime_divisor_of_triple_gcd_eq_one {p A B C : ℕ}
    (hp : p.Prime) (hG : Nat.gcd (Nat.gcd A B) C = 1) :
    ¬ (p ∣ A ∧ p ∣ B ∧ p ∣ C) := by
  intro h
  have hpg : p ∣ Nat.gcd (Nat.gcd A B) C :=
    Nat.dvd_gcd (Nat.dvd_gcd h.1 h.2.1) h.2.2
  have hp1 : p ∣ 1 := by simpa [hG] using hpg
  exact (not_le_of_gt hp.one_lt) (Nat.le_of_dvd Nat.one_pos hp1)

/-- The valuation equality supplied by the odd-prime, plus-sign LTE lemma. -/
def LTEConclusion (p a b n : ℕ) : Prop :=
  padicValNat p (a ^ n + b ^ n) = padicValNat p (a + b) + padicValNat p n

/-- The exponent-one case of the plus-sign LTE conclusion. -/
theorem lteConclusion_one (p a b : ℕ) : LTEConclusion p a b 1 := by
  simp [LTEConclusion]

/--
If an LTE conclusion is available for `A ^ n + B ^ n`, then a Beal equation
with matching left exponents forces the corresponding valuation identity on
`C`.
-/
theorem lte_transfers_to_beal_equal_left_exponents {p A B C n z : ℕ}
    [Fact p.Prime] (hEq : BealEquation A B C n n z)
    (hLTE : LTEConclusion p A B n) :
    z * padicValNat p C = padicValNat p (A + B) + padicValNat p n := by
  rw [← padicValNat.pow (p := p) C z, ← hEq]
  exact hLTE

/--
If the valuation predicted by LTE is not divisible by `z`, no matching-left
Beal equation can hold.
-/
theorem no_beal_equal_left_exponents_of_lte_mod_obstruction {p A B C n z : ℕ}
    [Fact p.Prime] (hLTE : LTEConclusion p A B n)
    (hmod : ¬ z ∣ padicValNat p (A + B) + padicValNat p n) :
    ¬ BealEquation A B C n n z := by
  intro hEq
  apply hmod
  refine ⟨padicValNat p C, ?_⟩
  exact (lte_transfers_to_beal_equal_left_exponents (p := p) hEq hLTE).symm

end BealUnified
