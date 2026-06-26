import BealUnified.Statement

set_option linter.style.header false
set_option linter.style.nativeDecide false

/-!
# Beal conjecture: bounded computational checks

This module contains executable boolean searches for primitive Beal
counterexamples.  These checks are finite sanity tests only; they are not a
substitute for a proof of the open conjecture.
-/

namespace BealUnified

/-- Executable Boolean form of a primitive Beal counterexample. -/
def primitiveBealCounterexampleBool (A B C x y z : ℕ) : Bool :=
  decide (0 < A) &&
  decide (0 < B) &&
  decide (0 < C) &&
  decide (3 ≤ x) &&
  decide (3 ≤ y) &&
  decide (3 ≤ z) &&
  decide (A ^ x + B ^ y = C ^ z) &&
  decide (Nat.gcd (Nat.gcd A B) C = 1)

/-- Executable bounded search for primitive Beal counterexamples. -/
def hasCounterexampleUpTo (baseBound expBound : ℕ) : Bool :=
  Id.run do
    for A in [0:baseBound] do
      for B in [0:baseBound] do
        for C in [0:baseBound] do
          for x in [0:expBound] do
            for y in [0:expBound] do
              for z in [0:expBound] do
                if primitiveBealCounterexampleBool A B C x y z then
                  return true
    return false

/-- No positive primitive counterexample exists with all bases `< 2`. -/
theorem noCounterexample_bases_lt_two :
    ∀ A B C x y z : ℕ,
      A < 2 → B < 2 → C < 2 →
      ¬ (Solution A B C x y z ∧ Nat.gcd (Nat.gcd A B) C = 1) := by
  intro A B C x y z hA2 hB2 hC2 h
  have hApos : 0 < A := h.1.posA
  have hBpos : 0 < B := h.1.posB
  have hCpos : 0 < C := h.1.posC
  have hA1 : A = 1 := by omega
  have hB1 : B = 1 := by omega
  have hC1 : C = 1 := by omega
  have hEq : BealEquation A B C x y z := h.1.eqn
  simp [BealEquation, hA1, hB1, hC1] at hEq

/-- Certified finite search: no primitive counterexample for all six variables `< 8`. -/
theorem noCounterexampleUpTo_8_8 : hasCounterexampleUpTo 8 8 = false := by
  native_decide

end BealUnified
