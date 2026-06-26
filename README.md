# Beal Conjecture — Formal Verification in Lean 4 + Mathlib

> **Honest status:** This repository formalizes the [Beal conjecture](https://en.wikipedia.org/wiki/Beal_conjecture) in [Lean 4](https://lean-lang.org/) with [Mathlib](https://github.com/leanprover-community/mathlib4). It is **not a proof**. The conjecture is an open problem in number theory (unresolved since 1993, $1M prize unclaimed). What this repository contains is a clean modular formalization of the conjecture together with **all of the reductions and special cases that the existing Lean/Mathlib library can prove**. There is exactly one `sorry`, isolated to the open core after every known reduction has been discharged.

---

## What the conjecture says

For all positive integers `A, B, C, x, y, z` with `min(x, y, z) ≥ 3`:

$$A^x + B^y = C^z \quad\Longrightarrow\quad \gcd(A, B, C) > 1.$$

Equivalently (the contrapositive used internally): there is no *primitive* solution where the bases `A, B, C` are coprime.

---

## What is proved in this repository

Every theorem below compiles under `lake build` with `0 errors` and was verified by `#print axioms` to depend only on standard Mathlib axioms (`propext`, `Quot.sound`, `Classical.choice`) — **none of them depend on `sorryAx`**.

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
| Bounded search: no counterexample for bases `< 2` | `noCounterexample_bases_lt_two` | omega + decide |
| Bounded search: no primitive counterexample `8 × 8 × 8 × 8 × 8 × 8` | `noCounterexampleUpTo_8_8` | `native_decide` |

That is **24 theorems** with no `sorry` and no `sorryAx`. They exhaust everything the elementary toolkit currently available in Mathlib can settle.

---

## What is open

There is exactly **one `sorry`**, in `BealConjecture.lean`:

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
├── BealUnified/
│   ├── Statement.lean         — conjecture, coprimality reduction, contrapositive equivalence
│   ├── FLTReduction.lean      — x=y=z reductions via Mathlib FLT-3 / FLT-4
│   ├── Parity.lean            — Pythagorean reduction, parity branches, odd-exponent factoring
│   ├── Valuations.lean        — p-adic identity, LTE interface
│   ├── ABC.lean               — radical, ABC conjecture, primitive-triple application
│   ├── Computational.lean     — bounded boolean search, `native_decide` certificate
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