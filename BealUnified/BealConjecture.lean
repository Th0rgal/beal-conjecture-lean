import BealUnified.Statement
import BealUnified.FLTReduction
import BealUnified.Parity
import BealUnified.Valuations
import BealUnified.ABC
import BealUnified.Computational

set_option linter.style.header false

/-!
# Beal conjecture: collected main theorem

This module gathers the unified infrastructure and states the full Beal
conjecture theorem.  All imported subcase lemmas are proved without `sorry`.
The only placeholder is `beal_no_coprime_solution`, which is exactly the open
primitive Beal conjecture after the proved pairwise-coprime reduction.
-/

namespace BealUnified

/--
Open core of the Beal conjecture: no pairwise-coprime positive solution exists.

This is the genuine unsolved mathematical content.  The surrounding theorem
uses the proved `pairwise_coprime_of_solution` lemma to reduce the usual
setwise-gcd statement to this primitive case.  No elementary or Mathlib
available theorem currently proves this general statement.
-/
theorem beal_no_coprime_solution
    {A B C x y z : ℕ}
    (_sol : Solution A B C x y z)
    (_hAB : Nat.Coprime A B) (_hBC : Nat.Coprime B C) (_hAC : Nat.Coprime A C) :
    False := by
  sorry

/--
The Beal conjecture in the usual common-factor form.

The proof is complete except for the isolated open primitive core
`beal_no_coprime_solution`.
-/
theorem beal_conjecture
    (A B C x y z : ℕ)
    (hA : 0 < A) (hB : 0 < B) (hC : 0 < C)
    (hx : 3 ≤ x) (hy : 3 ≤ y) (hz : 3 ≤ z)
    (heq : BealEquation A B C x y z) :
    BealConclusion A B C := by
  have sol : Solution A B C x y z := ⟨hA, hB, hC, hx, hy, hz, heq⟩
  have hpos : 0 < Nat.gcd (Nat.gcd A B) C :=
    Nat.gcd_pos_of_pos_left C (Nat.gcd_pos_of_pos_left B hA)
  rcases Nat.lt_or_ge 1 (Nat.gcd (Nat.gcd A B) C) with h | h
  · exact h
  · have hg1 : Nat.gcd (Nat.gcd A B) C = 1 := by omega
    obtain ⟨hAB, hBC, hAC⟩ :=
      pairwise_coprime_of_solution (by omega) (by omega) (by omega) hg1 heq
    exact (beal_no_coprime_solution sol hAB hBC hAC).elim

end BealUnified
