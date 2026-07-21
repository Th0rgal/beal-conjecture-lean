# Beal Conjecture — Formal Verification in Lean 4 + Mathlib

> **Honest status:** This repository is **not a proof** of the open Beal conjecture. `import BealUnified` exposes only checked trusted reductions. The open normalized target is opt-in: `import BealUnified.Challenge.NormalizedCore`.

## Trust boundary

The default root has no path to `Challenge` or the legacy placeholder module.
`Challenge.NormalizedPrimitiveCore` is a named proposition for pairwise-coprime
positive solutions with normalized exponents (`4` or an odd prime). It is not
asserted as a theorem. `beal_conjecture_of_normalized_core` conditionally
assembles `BealConjecture` from its emptiness, and
`beal_conjecture_iff_normalized_core_empty` proves the exact equivalence using
`beal_normalize`. `(3,3,3)` is separately excluded with Mathlib FLT-3; the
remaining target is named `non333`, not “hyperbolic”.

Run `python3 scripts/check_trusted_boundary.py` for the trusted import closure,
placeholder scan, and an environment audit of every loaded `BealUnified`
declaration. It permits only `propext`, `Classical.choice`, and `Quot.sound`;
its controlled temporary fixture confirms rejection of both a new axiom and
`sorryAx`. Run `python3 scripts/check_signature_registry.py` for the
machine-readable registry in `signatures/registry.json`. Run
`python3 scripts/check_research_checkpoints.py` for historical research
provenance. Checkpoints validate artifact bytes with `git show <commit>:<path>`;
they are evidence records, never theorem claims.

---

## What the conjecture says

For all positive integers `A, B, C, x, y, z` with `min(x, y, z) ≥ 3`:

$$A^x + B^y = C^z \quad\Longrightarrow\quad \gcd(A, B, C) > 1.$$

Equivalently (the contrapositive used internally): there is no *primitive* solution where the bases `A, B, C` are coprime.

---

## What is proved in this repository

Every trusted theorem below compiles under `lake build` with `0 errors` and is
covered by the environment audit, which permits only standard Mathlib axioms
(`propext`, `Quot.sound`, `Classical.choice`) — **none depend on `sorryAx`**.

| Subcase | Theorem | Method |
|---|---|---|
| Setwise-coprime solution ⇒ pairwise coprime | `pairwise_coprime_of_solution` | `Nat.dvd_sub`, `Nat.gcd_assoc` |
| Common-factor form ↔ no-primitive-solution form | `beal_iff_no_coprime_solution` | contrapositive |
| `x = y = z = 3` (unconditional) | `beal_case_pow_three`, `beal_three_three_three` | Mathlib `fermatLastTheoremThree` |
| `x = y = z = 4` (unconditional) | `beal_case_pow_four`, `four_four_four_case` | Mathlib `fermatLastTheoremFour` |
| `x = y = z = n` (conditional) | `beal_equalExponent_of_fermatLastTheorem` | assuming `FermatLastTheorem` |
| All exponents divisible by `4` | `all_even_halves_case` | descent on FLT-4 |
| All exponents even ⇒ Pythagorean triple | `even_exponents_pythagorean` | classification of Pythagorean triples |
| Pythagorean triple classification applied | `even_exponents_pythagorean_classified` | Mathlib `PythagoreanTriple.classification` |
| All bases odd ⇒ impossible | `no_solution_all_bases_odd` | parity |
| `C` even and one left base even ⇒ conclusion | `bealConclusion_of_evenC_and_even_left_base` | parity + coprimality |
| Mixed-parity sub-branch (same conclusion) | `mixedParity_bealConclusion_of_evenC_and_even_left_base` | above |
| For odd `n`: `A + B ∣ Aⁿ + Bⁿ` | `add_dvd_pow_add_pow_of_odd` | sum-of-odd-powers factoring |
| Odd normalization: `A^(2k+1) = A · (A^k)²` | `pow_two_mul_add_one_eq_mul_square` | algebra |
| `padicValNat p (A^x + B^y) = z · padicValNat p C` | `beal_padicValNat_eq` | rewriting along the equation |
| Common prime divisor of `(A,B,C)` ⇒ conclusion | `common_prime_divisor_implies_conclusion` | divisibility |
| Triple gcd `1` ⇒ no common prime | `no_common_prime_divisor_of_triple_gcd_eq_one` | contrapositive |
| LTE base case `n = 1` | `lteConclusion_one` | `simp` |
| LTE ⇒ valuation identity on `C` (equal left exponents) | `lte_transfers_to_beal_equal_left_exponents` | rewrite |
| LTE modular obstruction ⇒ no matching Beal equation | `no_beal_equal_left_exponents_of_lte_mod_obstruction` | rewrite |
| `rad n = ∏ primeFactors(n)` | `rad`, `rad_dvd`, `rad_pow_of_pos` | Mathlib `Nat.prod_primeFactors_dvd` |
| ABC applies to `(A^x, B^y, C^z)` of any primitive triple | `abc_applies_to_primitive_beal_counterexample` | assuming `ABCConjecture` |
| Opt-in computational evidence: no counterexample for bases `< 2` | `noCounterexample_bases_lt_two` | omega + decide (outside `Trusted`) |
| Radical/minimum-exponent bridge | `rad_base_pow_min_le_max_cube` | elementary inequalities |
| Coprime-sum valuation side condition | `padicValNat_prime_dvd_coprime_sum_pows_eq_zero` | `padicValNat` |
| Primitive-divisor data ⇒ exact order and `n ∣ p - 1` | `orderOf_primitivePowSubRatio_eq`, `PrimitivePowSubDivisor.dvd_prime_sub_one` | finite-group order |
| Odd cyclotomic quotient factorization and order/congruence interfaces | `oddCyclotomicQuotient_mul_add`, `nonexceptional_prime_order_and_congruence` | polynomial identity + `ZMod` units |
| Exponent normalization to `4` or an odd prime divisor | `exists_admissibleExponentDivisor`, `beal_normalize` | elementary divisor decomposition |
| Primitive modulo-eight structure | `exactly_one_even_of_solution_of_primitive`, `odd_C_of_even_left_exponents_of_solution_of_primitive`, `B_modEq_seven_of_even_C_even_x_odd_y_of_solution_of_primitive` | parity + congruences |

The original 24-theorem suite and the consolidated research lemmas above contain no `sorry` and no `sorryAx`. They are structural reductions: in particular, the primitive-divisor module consumes primitive-divisor data but does not prove that such a divisor exists.

`BealUnified.Computational` is an explicit, separately audited opt-in module
for finite-search evidence (`python3 scripts/check_computational_evidence.py`).
It is not imported by `BealUnified` or `BealUnified.Trusted`, because its
`native_decide` certificate uses Lean's generated native-decision axiom, which
is intentionally outside the strict trusted allowlist. The audit records that
dependency as exactly `Lean.ofReduceBool` and rejects every other axiom; it
does not elevate the finite computation to trusted theorem evidence.

---

## What is open

The legacy `BealConjecture.lean` module remains outside the default import
boundary for compatibility with historical work; it is not production API.

```lean
theorem beal_no_coprime_solution
    {A B C x y z : ℕ}
    (_sol : Solution A B C x y z)
    (_hAB : Nat.Coprime A B) (_hBC : Nat.Coprime B C) (_hAC : Nat.Coprime A C) :
    False := by
  sorry
```

The shape of this gap: there is no positive primitive solution when the exponents are *not* all equal (i.e. not pure FLT) **and** not all multiples of `3` or `4`. Concretely, the cases that remain are the genuinely *mixed-exponent* families like `A³ + B⁴ = C⁵`, `A³ + B⁵ = C⁷`, and so on.

The proved lemma `beal_conjecture` then assembles every reduction into a single theorem whose only remaining gap is `beal_no_coprime_solution`:

```lean
theorem beal_conjecture
    (A B C x y z : ℕ) (hA : 0 < A) (hB : 0 < B) (hC : 0 < C)
    (hx : 3 ≤ x) (hy : 3 ≤ y) (hz : 3 ≤ z)
    (heq : BealEquation A B C x y z) : BealConclusion A B C := by
  ...
  exact (beal_no_coprime_solution sol hAB hBC hAC).elim
```

### Why this gap is hard

The settled cases are exactly the cases that can be discharged by the **elementary** number theory that Mathlib already formalizes:
- FLT for `n = 3` and `n = 4` (Sophie Germain descent and the FLT-4 proof);
- Pythagorean triple classification;
- parity arguments;
- elementary `padicValNat` arithmetic.

The mixed-exponent cases need machinery that Mathlib does not currently have:
- The **modular method** (Frey curves, Galois representations, modularity lifting) that underpins Wiles' proof of FLT. None of this is in Mathlib.
- A general Lifting-the-Exponent lemma with all hypothesis discharged from the Beal signature.
- The Darmon–Granville theorem on finiteness of primitive solutions with fixed exponents.

Even an elementary attempt at `A³ + B⁴ = C⁵` quickly runs into needing either deep Diophantine geometry or the full modular method. This is not a Lean limitation — it is a number-theoretic limitation: the open cases of the Beal conjecture are **the same cases that are open in the literature**.

---

## Repository layout

```
.
├── BealUnified.lean           — top-level imports
├── lakefile.toml              — Mathlib project, Lean 4.31.0
├── lean-toolchain             — pinned toolchain
├── Research/checkpoints/      — versioned, historical-source checkpoint manifests
├── scripts/check_research_checkpoints.py — fail-closed provenance validator
├── BealUnified/
│   ├── Statement.lean         — conjecture, coprimality reduction, contrapositive equivalence
│   ├── FLTReduction.lean      — x=y=z reductions via Mathlib FLT-3 / FLT-4
│   ├── Parity.lean            — Pythagorean reduction, parity branches, odd-exponent factoring
│   ├── Valuations.lean        — p-adic identity, LTE interface
│   ├── CyclotomicQuotient.lean — odd cyclotomic quotient identities and order lemmas
│   ├── CyclotomicCofactor.lean — cofactor decomposition interfaces
│   ├── ExponentNormalization.lean — normalize exponents to 4 or odd primes
│   ├── ModEight.lean           — primitive modulo-eight structure
│   ├── PrimitiveDivisors.lean  — consequences of supplied primitive-divisor data
│   ├── Research/BR20.lean      — coprime-sum valuation side condition
│   ├── ABC.lean               — radical, ABC conjecture, primitive-triple application
│   ├── Computational.lean     — opt-in bounded search, `native_decide` certificate
│   └── BealConjecture.lean    — collected main theorem + isolated `sorry` on the open core
└── .github/workflows/         — Mathlib CI, release tagging, dependency updates
```

Each module has a top-of-file docstring explaining what is proved in it and what is left to the open core.

---

## Build

```bash
curl https://raw.githubusercontent.com/leanprover/elan/elan-init/elan-init.sh -sSf | sh -s -- -y --default-toolchain none
source ~/.profile

git clone https://github.com/th0rgal/beal-conjecture-lean.git
cd beal-conjecture-lean
lake update
lake build      # completes with 0 errors, 1 warning (the intentional `sorry` in BealConjecture.lean)
```

Lean 4.31.0 and Mathlib v4.31.0 are pinned by `lean-toolchain` and `lakefile.toml`.

---

## Provenance

This formalization was assembled from six parallel Lean 4 + Mathlib attempts (FLT reduction, ABC reduction, p-adic valuation, all-even case, mixed-parity case, all-odd case, exponent-3 specialization), each of which independently reached the same open frontier. The single `sorry` is the same gap every attempt converged on.

The repository is published as an **honest milestone**: the cleanest currently attainable Lean 4 rendering of Beal's conjecture, the largest reduction that can be proved inside Mathlib, and a precise identification of the number-theoretic gap that remains.

---

## License

Released under the Apache 2.0 license, the same license as Mathlib.
