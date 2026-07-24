# Audited Beal frontier — 2026-07-24

## Status

This document separates four kinds of statements that had previously been mixed
in research notes and exploratory discussions:

1. **Trusted Lean theorem** — compiled under the public `BealUnified` trusted
   import and covered by the axiom audit.
2. **Kernel-checkable candidate** — an elementary theorem with a complete paper
   proof outline, but not yet implemented and compiled in this repository.
3. **Literature result** — a result stated in a primary source, but not yet
   represented by a checked Lean proof or independently replayed certificate.
4. **Experimental or speculative direction** — bounded evidence, a possible
   research program, or an unreviewed proof claim. It is not a theorem.

Nothing below changes the status of the Beal conjecture: it remains open.

## Current trusted boundary

The trusted project already proves:

- equivalence between the common-factor and no-primitive-solution formulations;
- exponent normalization to `4` or an odd prime divisor;
- exact equivalence between `BealConjecture` and emptiness of the opt-in
  `Challenge.NormalizedPrimitiveCore`;
- the diagonal `(3,3,3)` and `(4,4,4)` cases;
- parity, modulo-eight, valuation, cyclotomic-order, radical, and conditional ABC
  interfaces listed in the README.

The normalization theorem is a canonicalization theorem, not a finite reduction:
there are still infinitely many normalized triples of odd primes.

## Correct literature status

### Signature `(3,4,5)`

The signature `(3,4,5)` is solved in the mathematical literature by Siksek and
Stoll, *Partial descent on hyperelliptic curves and the generalized Fermat
equation x^3+y^4+z^5=0*, Bull. Lond. Math. Soc. 44 (2012), 151–166,
DOI `10.1112/blms/bdr086`.

The correct repository status is therefore:

> solved in the literature; formal source audit and independently replayed
> certificate still pending.

It must not be labelled mathematically open merely because it is not yet
formalized here.

### Signature `(3,5,7)`

The current solved-case survey by Ashleigh Wilcox and Bogdan Grechuk,
*Generalised Fermat equation: a survey of solved cases*, arXiv `2412.11933`,
identifies `(3,5,7)` as the first unresolved Beal signature after known solved
cases are removed. This is a literature-level frontier statement, not a Lean
theorem in this repository.

### The 2025 `(5,p,3)` hypergeometric-motive paper

Pacetti and Villagra Torcomian, *On the generalized Fermat equation of signature
(5,p,3)*, arXiv `2512.17845`, gives asymptotic and conditional modular-method
results. Its explicit exceptional sets contain `p = 7`. In particular, its
Theorems A and B do **not** prove the `(5,7,3)` case, and Theorem C assumes a
large-image conjecture.

Therefore this paper supplies a promising computational and modular framework,
but no unconditional `(3,5,7)` exclusion may be entered in the registry from it.
This corrects an earlier exploratory overclaim.

### Recent universal cyclotomic claims

The preprint *The strong Fermat-Catalan Equation*, arXiv `2509.18275`, claims a
universal theorem for a homogeneous cyclotomic perfect-power equation. It has not
been independently source-audited or formalized here. No theorem or solved
registry row should depend on it until its proof has been checked line by line
and, ideally, reconstructed in Lean.

## Kernel-checkable candidates worth formalizing

The candidates in this section use elementary arithmetic, finite groups, and
existing Mathlib infrastructure. They are the highest-value near-term formal
work because they do not depend on modularity, Faltings, or external computer
algebra.

### 1. Generalized-Fermat divisor shadows

Define a primitive generalized-Fermat solution independently of Beal's exponent
floor:

```lean
def PrimitiveGFESolution
    (a b c X Y Z : ℕ) : Prop :=
  0 < X ∧ 0 < Y ∧ 0 < Z ∧
  Nat.Coprime X Y ∧ Nat.Coprime Y Z ∧ Nat.Coprime X Z ∧
  X ^ a + Y ^ b = Z ^ c
```

The basic closure theorem is:

```text
a ∣ x, b ∣ y, c ∣ z, and a primitive solution of (x,y,z)
  ⇒ a primitive solution of (a,b,c)
```

obtained by moving the exponent quotients into the bases. This theorem turns a
solved signature into an upward-closed cone in the coordinatewise divisibility
poset. The current registry treats signatures as isolated strings and therefore
cannot exploit this closure.

The normalized `4`-or-odd-prime representation should remain available, but
proof search should retain the complete divisor provenance instead of choosing
only one admissible divisor per exponent.

### 2. Exclude both trusted diagonal normalized signatures

`NormalizedPrimitiveCoreNon333` currently excludes only `(3,3,3)`, although the
trusted project also proves `(4,4,4)` impossible. Add a non-diagonal proposition
and exact equivalence excluding both tuples. Keep the old name as a compatibility
alias or deprecated theorem if external users may import it.

### 3. Uniform asymmetric radical gap

For a positive solution

```text
A^x + B^y = C^z,  x,y,z ≥ 3,  (x,y,z) ≠ (3,3,3),
```

let `N = C^z` and `R = rad (A*B*C)`. At least one exponent is at least four, so

```text
1/x + 1/y + 1/z ≤ 11/12.
```

Clearing denominators gives

```text
12 * (y*z + x*z + x*y) ≤ 11 * (x*y*z).
```

Using `A^x < N`, `B^y < N`, `C^z = N`, and `R ≤ A*B*C` yields

```text
R^12 < N^11.
```

This is unconditional and strictly stronger than the current minimum-exponent
radical bridge when the minimum exponent is three. A sharper `71/105` frontier
bound is literature-assisted and must wait for certified audits of every solved
signature and every perfect-power lift in the relevant solution lists.

### 4. Exact cyclotomic perfect-power splitting

Let `p` be an odd prime, `n ≥ 3`, `Nat.Coprime X Y`, and

```text
X^p + Y^p = C^n.
```

Set

```text
S = X + Y
Φ = (X^p + Y^p) / (X + Y).
```

The elementary congruence

```text
Φ ≡ p * Y^(p-1) (mod S)
```

implies `gcd S Φ ∣ p`.

If `p ∤ S`, coprimality and unique factorization give

```text
S = U^n,
Φ = V^n,
C = U*V,
Nat.Coprime U V.
```

If `p ∣ S`, plus-sign LTE gives `v_p Φ = 1`, and there are `k,U,V` with

```text
S = p^(n*k-1) * U^n,
Φ = p * V^n,
C = p^k * U * V,
p ∤ U*V.
```

In both branches `V > 1`. Any prime `q ∣ V` then satisfies

```text
q^n ∣ Φ
q ≡ 1 [MOD 2*p].
```

The exact order conclusion already exists in `CyclotomicQuotient.lean`; the new
work is to derive the factorization and the existence of `q` from an actual
perfect-power equation.

### 5. Two-prime support and prime-power exclusion

The same split proves:

```text
X^p + Y^p = C^n, p odd prime, n ≥ 3, gcd(X,Y)=1
  ⇒ C has at least two distinct prime divisors.
```

More precisely, one prime divisor `q` of `C` satisfies

```text
q^n ∣ Φ_p^+(X,Y)
q ≡ 1 (mod 2p),
```

and a second distinct prime also divides `C`. Consequently,

```text
rad C ≥ 4*p + 2.
```

Applied to a primitive Beal solution:

```text
p ∣ x and p ∣ y for an odd prime p
  ⇒ C is not a prime power.
```

For all distinct odd primes dividing `gcd x y`, one obtains the stronger support
constraint

```text
oddSquarefreeKernel (gcd x y)
  ∣ lcm {q - 1 | q prime, q ∣ C}.
```

This is the clearest immediate advance over the current
`CofactorPowerData`/`PrimitivePowSubDivisor` interfaces: the present code records
or consumes the hard data, while this theorem constructs it in the equal-left-
odd-prime perfect-power branch.

### 6. Exact local saturation for pairwise-coprime exponents

For pairwise-coprime positive exponents `x,y,z` and a finite field `𝔽_Q`, the
exponent map

```text
(A,B,C) ↦ (A^x*C^(-z), B^y*C^(-z))
```

is surjective on `(𝔽_Qˣ)^3 → (𝔽_Qˣ)^2`. Therefore

```text
#{(A,B,C) ∈ (𝔽_Qˣ)^3 | A^x + B^y = C^z}
  = (Q - 1) * (Q - 2).
```

For an odd prime power `ℓ^k`, the corresponding exact unit count is

```text
ℓ^(2*k-2) * (ℓ-1) * (ℓ-2).
```

This theorem explains the permanent all-unit residue branches in the DGX
experiments. It formally rules out any proof of a distinct-prime signature based
only on eliminating unit solutions modulo a predetermined finite collection of
moduli. It does not rule out modular methods, whose conductors and Galois
representations depend globally on the hypothetical solution.

### 7. Minimal hyperbolic divisor shadows

The elementary classification of divisor-minimal hyperbolic signatures can be
formalized independently of the solved-case literature. Up to permutation, a
minimal signature is either all-prime or belongs to a finite exceptional list:

```text
(2,3,n), n ∈ {8,9,10,12,15,25}
(2,4,r), r ≥ 5 prime
(2,4,n), n ∈ {6,8,9}
(2,5,6), (2,5,9), (2,6,6)
(3,3,n), n ∈ {4,6,9}
(3,4,4), (3,4,5), (4,4,4)
```

Turning this into an all-prime Beal frontier additionally requires individually
audited solution sets for the exceptional signatures and checks that no listed
solution has the perfect-power provenance required to lift back to Beal. That
second step is literature/certificate work and must not be hidden inside an
"elementary" theorem.

## Approaches already investigated and not promising as the main proof engine

### Fixed congruences and finite-field atlases

The exact local-saturation theorem above shows that pairwise-coprime exponent
triples have abundant all-unit solutions over every finite field. Fixed moduli
can still prove useful support lemmas, but cannot eliminate a distinct-prime
signature by themselves.

### Unconditional valuation-one heuristics

The DGX cyclotomic census found nonexceptional prime valuations `2`, `3`, and
`4`. Any argument assuming that a primitive or nonexceptional cyclotomic divisor
occurs exactly once is false without an additional theorem. The correct target
is classification or exclusion of high-Wieferich lifts.

### Generic LTE

Mathlib already supplies the relevant plus-sign LTE theorem. LTE transfers exact
valuations once a suitable prime and equal exponent are present; it does not
couple three unrelated exponents such as `(3,5,7)` and does not create the needed
prime in the distinct-exponent core.

### Qualitative ABC as a proof

ABC would imply finiteness of Fermat–Catalan counterexamples. It would not, by
itself, prove that the finite set is empty, and the unknown constant prevents an
independent exhaustive search. The asymmetric radical theorem remains valuable
as a conditional bound and quality invariant.

### Generic brute force or CUDA search

Bounded searches are useful for falsifying lemmas, finding witnesses, and
producing finite certificates. They cannot establish the unbounded conjecture.
GPU work should be used only after an independently replayable certificate
format and CPU reference implementation exist.

### Full generic cyclotomic attack on mixed exponents

Cyclotomic splitting is powerful when two exponents share an odd prime. It does
not directly address a pairwise-coprime signature such as `(3,5,7)`.

### Full Wiles-scale formalization as the immediate Beal plan

The infrastructure cost is very large and full FLT machinery does not imply
Beal. Narrow, source-audited fixed-signature modular arguments have much better
payoff.

### Unreviewed universal proof claims

No preprint or exploratory derivation should change the registry to `solved`
without an independently checked theorem statement, source audit, and either a
Lean proof or a replayable certificate chain.

## Most promising program

### Immediate trusted progress

1. **Generalized-Fermat/divisor-shadow API.** This changes the repository from a
   flat list of signatures into a theorem graph with divisibility closure.
2. **Exact cyclotomic power splitting.** Construct `CofactorPowerData` from an
   equal-left-odd-prime solution and derive two-prime support and prime-power
   exclusion.
3. **Asymmetric radical theorem.** Formalize `R^12 < N^11` and its conditional
   ABC consequences.
4. **Local-saturation theorem.** Record a formal no-go result for fixed-modulus
   elimination in the pairwise-coprime exponent core.

These are realistic Mathlib-scale targets and require no unproved global
arithmetic theorem.

### Literature-to-certificate work

5. **Audit `(3,4,5)` first.** Pin the exact paper version, extract every finite
   computation, define a certificate schema, independently replay the
   computations, and only then add a formal theorem hook.
6. **Expand the signature registry.** Distinguish trusted/formal results,
   literature-solved results awaiting formalization, open frontier signatures,
   conditional results, and experimental evidence.

### Global mathematical frontier

7. **Treat `(3,5,7)` as the first open distinct-prime target.** The plausible
   methods are fixed-signature descent, modular/multi-Frey methods, and
   hypergeometric motives with fully checked conductor and newform-elimination
   certificates. The 2025 `(5,p,3)` paper provides infrastructure and identifies
   ghost-solution obstructions, but explicitly leaves `p=7` in its exceptional
   set.
8. **Treat repeated-prime signatures through homogeneous cyclotomic perfect
   powers.** After the elementary split, the hard question is whether
   `Φ_p^±(X,Y)` can equal `p^δ * D^q`. This needs a correct class-group,
   cyclotomic-unit, or valuation theorem; primitive-divisor existence alone is
   insufficient.

## File-level implementation plan

### PR A — frontier semantics and registry

- add this audit document;
- add registry statuses for literature-solved/formalization-pending and open
  frontier entries;
- relabel `(3,4,5)` accordingly;
- add `(3,5,7)` as the open-frontier locator;
- update README and roadmap wording;
- add the non-diagonal normalized core excluding both `(3,3,3)` and `(4,4,4)`.

### PR B — generalized-Fermat core

Create `BealUnified/GeneralizedFermat.lean` with:

- `PrimitiveGFESolution`;
- exponent signatures and permutation handling;
- `DivisorShadow`;
- preservation of positivity and pairwise coprimality under power absorption;
- upward closure of solved signatures;
- tests for exact theorem types used by the registry.

Acceptance criterion: no literature assumptions and no new axioms.

### PR C — cyclotomic power splitting

Create `BealUnified/CyclotomicPowerSplit.lean` with:

- `gcd (X+Y) Φ_p^+(X,Y) ∣ p`;
- the nonexceptional and exceptional exact power splits;
- `v_p Φ = 1` in the exceptional branch via Mathlib LTE;
- existence of a nonexceptional prime `q`;
- exact order `2p`, `q ≡ 1 (mod 2p)`, and `q^n ∣ Φ`;
- two-prime support and prime-power-right-base exclusion;
- the analogous difference theorem with its `X-Y=1` exceptional branch.

Acceptance criterion: construct the data currently represented by
`CofactorPowerData`; do not assume a primitive-divisor existence theorem.

### PR D — radical and local no-go theorems

Create `BealUnified/FrontierBounds.lean` with:

- the integer `11/12` exponent inequality;
- `rad(A*B*C)^12 < (C^z)^11`;
- exact finite-field and prime-power unit counts for pairwise-coprime exponents;
- a theorem stating the limitation of fixed-modulus unit elimination.

Acceptance criterion: all results are unconditional and kernel checked.

### PR E — `(3,4,5)` certified formalization project

- pin the Siksek–Stoll source and theorem statement;
- retain exact source hashes in a research checkpoint;
- design certificates for number-field arithmetic, local solubility, and Selmer
  set emptiness;
- build a second implementation to replay the certificates;
- expose the final theorem to the trusted registry only after its axiom and type
  audits pass.

### PR F — `(3,5,7)` research program

- define the exact primitive signature target and all permutations;
- record local conditions and conductor cases from primary sources;
- reproduce the hypergeometric-motive/newform computations with retained source
  and output hashes;
- explicitly track exceptional residual primes and ghost forms;
- do not claim a theorem until every residual case, including `p=7`, is removed.

## Explicit nonclaims

This audit does not claim:

- a proof of the Beal conjecture;
- a proof of `(3,5,7)`;
- an unconditional consequence for `p=7` from arXiv `2512.17845`;
- acceptance of arXiv `2509.18275` as a solved theorem;
- that bounded computations or provenance manifests are Lean certificates;
- that the literature-assisted `71/105` bound has been formally source-audited.
