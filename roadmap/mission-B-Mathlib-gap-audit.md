# Concrete Mathlib Gap Audit for the Beal Conjecture

Project audited: `/root/work/beal-unified`

Toolchain declared by the project: `leanprover/lean4:v4.31.0`, Mathlib `v4.31.0`.

Verification command used:

```bash
PATH=/workspaces/mission-f5a2013d/.elan/bin:$PATH lake build
```

Result: the project builds successfully, with one warning:

```text
BealUnified/BealConjecture.lean:29:8: declaration uses `sorry`
```

## Current Formal Boundary

The only literal proof hole is:

```lean
theorem beal_no_coprime_solution
    {A B C x y z : Nat}
    (_sol : Solution A B C x y z)
    (_hAB : Nat.Coprime A B) (_hBC : Nat.Coprime B C) (_hAC : Nat.Coprime A C) :
    False := by
  sorry
```

Location: `BealUnified/BealConjecture.lean:29`.

This is not a small missing lemma. It is the primitive Beal conjecture:

```text
A^x + B^y = C^z, x,y,z >= 3, A,B,C pairwise coprime => False.
```

The surrounding theorem `beal_conjecture` reduces the standard common-gcd
statement to this primitive case using the proved lemma
`pairwise_coprime_of_solution`.

## What Mathlib Already Supplies

### 1. Core FLT API

Available in Mathlib:

- `FermatLastTheoremFor n`
- `FermatLastTheorem`
- `FermatLastTheoremFor.mono`
- `FermatLastTheorem.of_odd_primes`
- `fermatLastTheoremThree : FermatLastTheoremFor 3`
- `fermatLastTheoremFour : FermatLastTheoremFor 4`
- `not_fermat_42 : a^4 + b^4 != c^2` over integers

Used by this project in:

- `BealUnified/FLTReduction.lean`
- `BealUnified/Parity.lean`

Status: enough for equal-exponent cases when `FermatLastTheoremFor n` is
assumed, and unconditionally for `n = 3` and `n = 4`. Mathlib does not contain
an unconditional proof of global `FermatLastTheorem`.

### 2. Primitive gcd and divisibility infrastructure

Available and already used:

- `Nat.gcd`
- `Nat.Coprime`
- `Nat.exists_prime_and_dvd`
- `Nat.Prime.dvd_of_dvd_pow`
- `dvd_pow`
- `Nat.prod_primeFactors_dvd`
- `Nat.primeFactors_pow`

Status: sufficient for the current primitive-to-pairwise-coprime reductions and
for the elementary prime-divisibility lemmas in `ABC.lean`.

### 3. Pythagorean triples

Available in Mathlib:

- `PythagoreanTriple`
- `PythagoreanTriple.classification`
- `PythagoreanTriple.coprime_classification`
- `PythagoreanTriple.coprime_classification'`

Used by:

- `even_exponents_pythagorean`
- `even_exponents_pythagorean_classified`

Status: Mathlib classifies Pythagorean triples, but does not provide the much
stronger perfect-power obstruction needed to finish the all-even Beal branch.

### 4. Plus-sign LTE

Available in Mathlib, under `padicValNat`:

```lean
theorem padicValNat.pow_add_pow
    (hxy : p | x + y) (hx : not p | x) {n : Nat} (hn : Odd n) :
    padicValNat p (x^n + y^n) =
      padicValNat p (x + y) + padicValNat p n
```

This is in `Mathlib/NumberTheory/Multiplicity.lean`, not imported by the local
`Valuations.lean` file.

Status: the local proposition

```lean
def LTEConclusion (p a b n : Nat) : Prop := ...
```

is an integration gap, not a missing Mathlib theorem, for the standard
odd-exponent plus-sign LTE case with hypotheses `p | a + b`, `not p | a`, and
`Odd n`.

### 5. Polynomial FLT/Fermat-Catalan

Available in Mathlib:

- `Polynomial.flt_catalan`
- `Polynomial.flt`
- `fermatLastTheoremWith'_polynomial`

Status: these are polynomial-ring theorems and do not close the natural-number
Beal conjecture. They are not a direct replacement for integer FLT,
Fermat-Catalan, or Beal.

## Actual Gaps

### Gap A: Primitive Beal core

Lean target:

```lean
theorem beal_no_coprime_solution
    {A B C x y z : Nat}
    (sol : Solution A B C x y z)
    (hAB : Nat.Coprime A B) (hBC : Nat.Coprime B C) (hAC : Nat.Coprime A C) :
    False
```

Why Mathlib does not close it:

- Mathlib has FLT only for exponent `3`, exponent `4`, and conditional/global
  statements.
- Beal permits unequal exponents.
- No Mathlib theorem proves the generalized primitive equation
  `A^x + B^y = C^z` impossible for all `x,y,z >= 3`.

Classification: genuine open mathematics, not a formal-library omission.

### Gap B: Perfect-power Pythagorean obstruction

Local target:

```lean
def PerfectPowerPythagoreanObstruction : Prop :=
  forall A B C a b c : Nat,
    0 < A -> 0 < B -> 0 < C ->
    2 <= a -> 2 <= b -> 2 <= c ->
    A^(2*a) + B^(2*b) = C^(2*c) ->
    Nat.gcd (Nat.gcd A B) C != 1
```

Location: `BealUnified/Parity.lean:51`.

What Mathlib gives:

- Pythagorean parametrization.
- FLT-4 / `not_fermat_42`.

What is missing:

- A theorem excluding primitive Pythagorean triples whose two legs and
  hypotenuse are all nontrivial perfect powers in the required pattern.

Classification: serious number-theory gap. The current Mathlib
Pythagorean-triplet API is useful setup but not enough.

### Gap C: Full integer Fermat-Catalan / generalized Fermat input

Relevant Beal shape:

```text
A^x + B^y = C^z, 1/x + 1/y + 1/z <= 1
```

Mathlib has a polynomial Fermat-Catalan theorem, but no corresponding
integer/natural theorem strong enough to handle Beal signatures.

Classification: missing deep external theory. Even a strong
Fermat-Catalan-style theorem would need careful matching of hypotheses,
coprimality, positivity, and exceptional signatures.

### Gap D: ABC-to-Beal closure

Local ABC statement:

```lean
def ABCConjecture : Prop := ...
```

Current proved bridge:

```lean
lemma abc_applies_to_primitive_beal_counterexample ...
```

Location: `BealUnified/ABC.lean:34` and `BealUnified/ABC.lean:115`.

What is proved:

- ABC can be applied to the power triple
  `(A^x, B^y, C^z)` of a primitive Beal counterexample.

What is missing:

- Inequalities bounding `rad (A^x * B^y * C^z)` by `rad (A*B*C)`.
- The standard growth contradiction for exponents at least `3`.
- A formal finite-search or bounded-exception cleanup after ABC gives a bound.
- A computable or explicitly parameterized version of the ABC constant if the
  intended endpoint is a certified finite search.

Classification: conditional-theory completion gap. It is not a Mathlib theorem
that ABC implies Beal in the required executable form.

### Gap E: LTE integration and downstream use

Local placeholder-like interface:

```lean
def LTEConclusion (p a b n : Nat) : Prop :=
  padicValNat p (a^n + b^n) =
    padicValNat p (a + b) + padicValNat p n
```

Location: `BealUnified/Valuations.lean:49`.

Mathlib already has the theorem needed for the odd plus-sign case:

```lean
padicValNat.pow_add_pow
```

Missing local work:

- Import `Mathlib.NumberTheory.Multiplicity`.
- Prove a wrapper theorem turning Mathlib's theorem into `LTEConclusion` under
  the required hypotheses:

```lean
theorem lteConclusion_of_odd
    [Fact p.Prime] (hp1 : 1 < p)
    (hxy : p | a + b) (ha : not p | a) (hn : Odd n) :
    LTEConclusion p a b n
```

- Use that wrapper to replace assumptions in later valuation obstruction
  lemmas.

Classification: local integration gap, likely tractable.

## Recommended Work Order

1. Close Gap E first. It is concrete, Mathlib already has the main theorem, and
   it will make `Valuations.lean` less artificial.

2. Strengthen the ABC file only if the project is intentionally pursuing a
   conditional `ABCConjecture -> BealConjecture` theorem. Otherwise leave it as
   an application lemma and document that it is not a proof route yet.

3. For all-even exponents, decide whether the project wants a named conditional
   theorem, as it has now, or a serious formalization of the required
   perfect-power Pythagorean obstruction. The latter is not a small Mathlib
   lookup.

4. Do not present `beal_conjecture` as an unconditional theorem while
   `beal_no_coprime_solution` is proved by `sorry`. The build succeeds because
   Lean permits `sorry`, not because Mathlib proves Beal.

## Bottom Line

The formalization has isolated the main mathematical obstruction correctly.
Mathlib supports the elementary reductions, FLT-3, FLT-4, Pythagorean triples,
and plus-sign LTE. It does not contain a theorem proving primitive Beal, global
FLT, integer Fermat-Catalan, ABC-implies-Beal, or the perfect-power
Pythagorean obstruction. The one immediately actionable Mathlib gap is local:
replace the custom `LTEConclusion` assumption with a wrapper around
`padicValNat.pow_add_pow`.
