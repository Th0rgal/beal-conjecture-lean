# Beal Conjecture — Formal Verification in Lean 4 + Mathlib

> **Honest status:** This repository is **not a proof** of the open Beal
> conjecture. `import BealUnified` exposes only checked trusted reductions. The
> open normalized target is opt-in:
> `import BealUnified.Challenge.NormalizedCore`.

## Trust boundary

The default root has no path to `Challenge` or the legacy placeholder module.
`Challenge.NormalizedPrimitiveCore` is a named proposition for pairwise-coprime
positive solutions with normalized exponents (`4` or an odd prime). It is not
asserted as a theorem. `beal_conjecture_of_normalized_core` conditionally
assembles `BealConjecture` from its emptiness, and
`beal_conjecture_iff_normalized_core_empty` proves the exact equivalence using
`beal_normalize`.

The opt-in Challenge module separately excludes `(3,3,3)` and `(4,4,4)` through
trusted Mathlib FLT-3 and FLT-4 results. These exclusions make the displayed
frontier more accurate; they do not solve another mixed signature.

Run `python3 scripts/check_trusted_boundary.py` for the trusted import closure,
placeholder scan, and environment audit. It permits only `propext`,
`Classical.choice`, and `Quot.sound`. Run
`python3 scripts/check_signature_registry.py` for the machine-readable signature
registry and `python3 scripts/check_research_checkpoints.py` for historical
research provenance. Checkpoints are evidence records, never theorem claims.

The current source and strategy audit is
[`Research/BEAL_FRONTIER_AUDIT_2026-07-24.md`](Research/BEAL_FRONTIER_AUDIT_2026-07-24.md).
It distinguishes trusted Lean theorems, kernel-checkable next targets,
literature results awaiting formalization, and experimental or speculative
work.

---

## What the conjecture says

For all positive integers `A, B, C, x, y, z` with `min(x, y, z) ≥ 3`:

$$A^x + B^y = C^z \quad\Longrightarrow\quad \gcd(A, B, C) > 1.$$

Equivalently, there is no positive primitive solution with pairwise-coprime
bases.

---

## What is proved in this repository

Every table entry except the explicitly marked **Opt-in** row is covered by the
trusted environment audit and has no dependency on `sorryAx`.

| Subcase | Theorem | Method |
|---|---|---|
| Setwise-coprime solution ⇒ pairwise coprime | `pairwise_coprime_of_solution` | gcd and divisibility |
| Common-factor form ↔ no-primitive-solution form | `beal_iff_no_coprime_solution` | contrapositive |
| `x = y = z = 3` | `beal_case_pow_three`, `beal_three_three_three` | Mathlib FLT-3 |
| `x = y = z = 4` | `beal_case_pow_four`, `four_four_four_case` | Mathlib FLT-4 |
| `x = y = z = n` | `beal_equalExponent_of_fermatLastTheorem` | conditional on global FLT |
| All exponents divisible by `3` | `beal_case_all_exponents_divisible_by_three` | FLT-3 descent |
| All exponents divisible by `4` | `all_even_halves_case` | FLT-4 descent |
| All exponents even ⇒ Pythagorean triple | `even_exponents_pythagorean` | rewriting |
| Pythagorean classification applied | `even_exponents_pythagorean_classified` | Mathlib classification |
| All bases odd ⇒ impossible | `no_solution_all_bases_odd` | parity |
| `C` even and one left base even ⇒ conclusion | `bealConclusion_of_evenC_and_even_left_base` | parity + coprimality |
| Mixed-parity sub-branch | `mixedParity_bealConclusion_of_evenC_and_even_left_base` | previous theorem |
| For odd `n`, `A + B ∣ Aⁿ + Bⁿ` | `add_dvd_pow_add_pow_of_odd` | factorization |
| Odd normalization identity | `pow_two_mul_add_one_eq_mul_square` | algebra |
| Direct p-adic valuation identity | `beal_padicValNat_eq` | equation rewriting |
| Common prime divisor ⇒ conclusion | `common_prime_divisor_implies_conclusion` | divisibility |
| Triple gcd `1` ⇒ no common prime | `no_common_prime_divisor_of_triple_gcd_eq_one` | contrapositive |
| Plus-sign LTE wrapper | `lteConclusion_of_mathlib_pow_add_pow` | Mathlib `padicValNat.pow_add_pow` |
| LTE transfer to equal-left exponent equation | `lte_transfers_to_beal_equal_left_exponents` | rewriting |
| LTE modular obstruction | `no_beal_equal_left_exponents_of_lte_mod_obstruction` | divisibility |
| `rad n = ∏ primeFactors(n)` and power support | `rad`, `rad_dvd`, `rad_pow_of_pos` | prime factors |
| ABC applies to a primitive power triple | `abc_applies_to_primitive_beal_counterexample` | conditional on `ABCConjecture` |
| Radical/minimum-exponent bridge | `rad_base_pow_min_le_max_cube` | elementary inequalities |
| Coprime-sum valuation side condition | `padicValNat_prime_dvd_coprime_sum_pows_eq_zero` | p-adic valuations |
| Primitive-divisor data ⇒ exact order | `orderOf_primitivePowSubRatio_eq` | finite-group order |
| Primitive-divisor data ⇒ `n ∣ p - 1` | `PrimitivePowSubDivisor.dvd_prime_sub_one` | finite-group order |
| Odd cyclotomic quotient factorization | `oddCyclotomicQuotient_mul_add` | divisibility |
| Nonexceptional prime order/congruence | `nonexceptional_prime_order_and_congruence` | `ZMod` units |
| Exponent normalization to `4` or an odd prime | `exists_admissibleExponentDivisor`, `beal_normalize` | divisor decomposition |
| Primitive modulo-eight structure | `exactly_one_even_of_solution_of_primitive`, related lemmas | parity + congruences |
| **Opt-in:** no counterexample for bases `< 2` | `noCounterexample_bases_lt_two` | finite decision procedure |

These are structural reductions. In particular, the primitive-divisor module
consumes primitive-divisor data but does not prove its existence, and
`CofactorPowerData` currently records a desired perfect-power factorization
without constructing it from a Beal equation.

`BealUnified.Computational` is an explicit, separately audited opt-in module for
finite-search evidence. Its native-decision dependency is intentionally outside
the strict trusted allowlist and does not elevate a bounded computation to an
unbounded theorem.

---

## What remains open

The kernel-level gap is exactly emptiness of `NormalizedPrimitiveCore`.
Normalization preserves the equation, positivity, pairwise coprimality, and
radical support, but it does not reduce the problem to finitely many exponent
triples.

The mathematical and repository statuses must be kept separate:

- `(3,4,5)` is solved in the mathematical literature by Siksek–Stoll. This
  repository does not yet contain an audited Lean proof or independently
  replayed certificate, so it remains outside the trusted solved registry.
- The current solved-case survey places `(3,5,7)` at the first unresolved Beal
  frontier. No complete theorem for that signature is claimed here.
- The 2025 hypergeometric-motive work on `(5,p,3)` gives important modular
  infrastructure and asymptotic results, but its explicit exceptional sets
  include `p = 7`; it does not settle `(3,5,7)`.

The legacy `BealConjecture.lean` module remains outside the public import boundary
for compatibility with historical work. Its isolated `sorry` represents the
entire open primitive core and is not production API.

### Immediate formal targets

The audited next targets are deliberately elementary and kernel-checkable:

1. a generalized-Fermat signature and divisor-shadow API;
2. exact equal-left-odd-prime cyclotomic perfect-power splitting;
3. construction of the currently assumed `CofactorPowerData`;
4. two-prime support and exclusion of a prime-power right base in that branch;
5. the unconditional asymmetric bound
   `rad(A*B*C)^12 < (C^z)^11` outside `(3,3,3)`;
6. exact finite-field/unit counts showing why fixed-modulus all-unit elimination
   cannot settle pairwise-coprime exponent triples.

The detailed statements, proof outlines, limitations, and file-level plan are in
the frontier audit.

### Why the global frontier is hard

The remaining distinct-prime signatures require machinery such as fixed-signature
descent, Frey objects, modularity and level lowering, Hilbert newforms,
hypergeometric motives, Selmer sets, Chabauty, or other global arithmetic. The
current Mathlib project does not yet provide enough of this stack for a direct
formalization.

Darmon–Granville/Faltings gives finiteness for each fixed hyperbolic signature,
but not an effective list of solutions. Qualitative ABC would imply global
finiteness, not automatic emptiness, and does not supply a usable enumeration
constant.

Fixed congruence atlases, unconditional valuation-one heuristics, generic LTE,
and larger brute-force searches are not the main proof engine. Their precise
limitations are recorded in the audit and in the DGX checkpoint.

---

## Repository layout

```text
.
├── BealUnified.lean
├── BealUnified/
│   ├── Trusted.lean
│   ├── Statement.lean
│   ├── FLTReduction.lean
│   ├── Parity.lean
│   ├── Valuations.lean
│   ├── CyclotomicQuotient.lean
│   ├── CyclotomicCofactor.lean
│   ├── ExponentNormalization.lean
│   ├── ModEight.lean
│   ├── PrimitiveDivisors.lean
│   ├── ABC.lean
│   ├── Computational.lean
│   ├── Challenge/NormalizedCore.lean
│   └── BealConjecture.lean
├── Research/
│   ├── BEAL_FRONTIER_AUDIT_2026-07-24.md
│   ├── DGX_SPARK_EXPERIMENTS_2026-07-17.md
│   └── checkpoints/
├── signatures/registry.json
├── scripts/
├── experiments/dgx_spark/
└── roadmap/
```

---

## Build

```bash
curl https://raw.githubusercontent.com/leanprover/elan/elan-init/elan-init.sh -sSf | sh -s -- -y --default-toolchain none
source ~/.profile

git clone https://github.com/Th0rgal/beal-conjecture-lean.git
cd beal-conjecture-lean
lake update
lake build
```

Lean 4.31.0 and Mathlib v4.31.0 are pinned by `lean-toolchain` and
`lakefile.toml`.

---

## Provenance and nonclaims

Research checkpoints pin historical source commits and artifact hashes. They do
not certify mathematical statements. Literature locators do not become trusted
theorems until their exact theorem types and computational dependencies are
independently audited and replayed.

This repository does not claim a proof of Beal, a proof of `(3,5,7)`, acceptance
of an unreviewed universal proof preprint, or that bounded evidence establishes an
unbounded result.

Released under the Apache 2.0 license, the same license as Mathlib.
