import BealUnified.Statement

set_option linter.style.header false

/-!
# Beal conjecture: exponent-factor reduction

This module formalizes the elementary reduction of every exponent at least `3`
to either exponent `4` or an odd prime, together with the algebraic bridge from
canonical signatures to the full primitive Beal statement.

The literature-assisted step that removes all composite-exponent Beal
signatures is intentionally kept outside the trusted namespace.
-/

namespace BealUnified

/-- An exponent is canonical when it is `4` or an odd prime. -/
def CanonicalExponent (n : ℕ) : Prop :=
  n = 4 ∨ (Nat.Prime n ∧ n % 2 = 1)

/-- Every exponent at least `3` admits a factorization through a canonical exponent. -/
def CanonicalFactorizationProperty : Prop :=
  ∀ n : ℕ, 3 ≤ n →
    ∃ e k : ℕ, 3 ≤ e ∧ CanonicalExponent e ∧ n = k * e

/-- Every natural exponent at least `3` factors through `4` or an odd prime. -/
theorem canonicalFactorizationProperty : CanonicalFactorizationProperty := by
  intro n hn
  by_cases h4 : 4 ∣ n
  · obtain ⟨k, hk⟩ := h4
    refine ⟨4, k, by omega, Or.inl rfl, ?_⟩
    simpa only [Nat.mul_comm] using hk
  · by_cases h2 : 2 ∣ n
    · obtain ⟨m, hm⟩ := h2
      have hm2 : 2 ≤ m := by omega
      obtain ⟨p, hp, hpm⟩ := Nat.exists_prime_and_dvd (by omega : m ≠ 1)
      rcases hp.eq_two_or_odd with hp2 | hpodd
      · subst p
        exfalso
        apply h4
        obtain ⟨t, ht⟩ := hpm
        refine ⟨t, ?_⟩
        omega
      · have hp3 : 3 ≤ p := by
          have hpge := hp.two_le
          omega
        obtain ⟨t, ht⟩ := hpm
        refine ⟨p, 2 * t, hp3, Or.inr ⟨hp, hpodd⟩, ?_⟩
        calc
          n = 2 * m := hm
          _ = 2 * (p * t) := by rw [ht]
          _ = (2 * t) * p := by ac_rfl
    · obtain ⟨p, hp, hpn⟩ :=
        Nat.exists_prime_and_dvd (by omega : n ≠ 1)
      rcases hp.eq_two_or_odd with hp2 | hpodd
      · subst p
        exact False.elim (h2 hpn)
      · have hp3 : 3 ≤ p := by
          have hpge := hp.two_le
          omega
        obtain ⟨k, hk⟩ := hpn
        refine ⟨p, k, hp3, Or.inr ⟨hp, hpodd⟩, ?_⟩
        simpa only [Nat.mul_comm] using hk

/--
The primitive canonical-signature statement, formulated with pairwise coprime
bases so that preservation under taking powers is immediate.
-/
def NoCanonicalPairwiseSolution : Prop :=
  ∀ A B C p q r : ℕ,
    Solution A B C p q r →
    CanonicalExponent p →
    CanonicalExponent q →
    CanonicalExponent r →
    Nat.Coprime A B →
    Nat.Coprime B C →
    Nat.Coprime A C →
    False

/--
Factoring each exponent and absorbing the complementary factor into its base
preserves a positive Beal solution.
-/
theorem reduce_solution_by_exponent_factorizations
    {A B C x y z p q r kx ky kz : ℕ}
    (sol : Solution A B C x y z)
    (hp : 3 ≤ p) (hq : 3 ≤ q) (hr : 3 ≤ r)
    (hx : x = kx * p) (hy : y = ky * q) (hz : z = kz * r) :
    Solution (A ^ kx) (B ^ ky) (C ^ kz) p q r := by
  refine
    { posA := pow_pos sol.posA _
      posB := pow_pos sol.posB _
      posC := pow_pos sol.posC _
      hx := hp
      hy := hq
      hz := hr
      eqn := ?_ }
  change (A ^ kx) ^ p + (B ^ ky) ^ q = (C ^ kz) ^ r
  rw [← pow_mul, ← pow_mul, ← pow_mul]
  simpa only [BealEquation, hx, hy, hz] using sol.eqn

/-- Pairwise coprimality is preserved when the three bases are raised to powers. -/
theorem pairwise_coprime_powers
    {A B C kx ky kz : ℕ}
    (hAB : Nat.Coprime A B)
    (hBC : Nat.Coprime B C)
    (hAC : Nat.Coprime A C) :
    Nat.Coprime (A ^ kx) (B ^ ky) ∧
      Nat.Coprime (B ^ ky) (C ^ kz) ∧
      Nat.Coprime (A ^ kx) (C ^ kz) := by
  exact
    ⟨(hAB.pow_left kx).pow_right ky,
      (hBC.pow_left ky).pow_right kz,
      (hAC.pow_left kx).pow_right kz⟩

/--
If canonical factorizations exist and every canonical pairwise-coprime
signature is impossible, then no primitive Beal solution exists.
-/
theorem noCoprimeSolution_of_canonical
    (hfactor : CanonicalFactorizationProperty)
    (hcanonical : NoCanonicalPairwiseSolution) :
    NoCoprimeSolution := by
  intro A B C x y z sol
  intro hgcd
  obtain ⟨p, kx, hp, hcp, hx⟩ := hfactor x sol.hx
  obtain ⟨q, ky, hq, hcq, hy⟩ := hfactor y sol.hy
  obtain ⟨r, kz, hr, hcr, hz⟩ := hfactor z sol.hz
  have hpair :=
    pairwise_coprime_of_solution
      (le_trans (by decide : 1 ≤ 3) sol.hx)
      (le_trans (by decide : 1 ≤ 3) sol.hy)
      (le_trans (by decide : 1 ≤ 3) sol.hz)
      hgcd sol.eqn
  have reduced :=
    reduce_solution_by_exponent_factorizations sol hp hq hr hx hy hz
  have hpowers :=
    pairwise_coprime_powers (kx := kx) (ky := ky) (kz := kz)
      hpair.1 hpair.2.1 hpair.2.2
  exact
    hcanonical
      (A ^ kx) (B ^ ky) (C ^ kz) p q r
      reduced hcp hcq hcr hpowers.1 hpowers.2.1 hpowers.2.2

/-- The full primitive statement follows from impossibility of canonical signatures. -/
theorem noCoprimeSolution_of_canonical_impossibility
    (hcanonical : NoCanonicalPairwiseSolution) :
    NoCoprimeSolution :=
  noCoprimeSolution_of_canonical canonicalFactorizationProperty hcanonical

/-- Common-factor Beal follows from the canonical primitive statement. -/
theorem bealConjecture_of_canonical
    (hfactor : CanonicalFactorizationProperty)
    (hcanonical : NoCanonicalPairwiseSolution) :
    BealConjecture :=
  beal_iff_no_coprime_solution.mpr
    (noCoprimeSolution_of_canonical hfactor hcanonical)

/-- The Beal conjecture follows once all canonical signatures are excluded. -/
theorem bealConjecture_of_canonical_impossibility
    (hcanonical : NoCanonicalPairwiseSolution) :
    BealConjecture :=
  bealConjecture_of_canonical canonicalFactorizationProperty hcanonical

end BealUnified
