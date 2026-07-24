# Strategic roadmap: Beal conjecture in Lean 4

Updated 2026-07-24. The evidence and source audit behind this roadmap is in
[`Research/BEAL_FRONTIER_AUDIT_2026-07-24.md`](../Research/BEAL_FRONTIER_AUDIT_2026-07-24.md).

## Bottom line

The repository does not prove the Beal conjecture. PR #6 establishes an honest
trusted boundary and an exact normalized Challenge proposition; it does not make
the remaining mathematics finite or easier by itself.

The immediate opportunity is to formalize several new elementary reductions
that are already within Mathlib's scope. The global frontier remains deep
fixed-signature arithmetic.

Keep these statuses distinct:

- **trusted:** compiled Lean theorem in the public audited environment;
- **kernel candidate:** elementary theorem ready to formalize;
- **literature solved:** primary source claims a solution, but this repository has
  no checked proof/certificate;
- **open frontier:** no complete accepted mathematical solution;
- **experimental:** bounded evidence or speculative program only.

## Correct mathematical frontier

### `(3,4,5)`

Siksek and Stoll solved the signature `(3,4,5)` in the literature using partial
descent on hyperelliptic curves. The repository still needs an exact source audit,
a certificate model, independent replay, and a Lean theorem. It is
**literature-solved/formalization-pending**, not mathematically open.

### `(3,5,7)`

The current solved-case survey identifies `(3,5,7)` as the first unresolved Beal
signature after known cases are removed. This is the first distinct-prime global
research target.

Pacetti–Villagra Torcomian's 2025 `(5,p,3)` work supplies hypergeometric-motive,
conductor, Hilbert-newform, and ghost-solution infrastructure. Its exceptional
sets explicitly include `p = 7`, and its strongest asymptotic theorem is
conditional on a large-image conjecture. It does not prove `(3,5,7)`.

### Repeated-prime signatures

When two left exponents share an odd prime, the nearest elementary target is an
exact homogeneous cyclotomic perfect-power decomposition. The current repository
contains factorization and order consequences, but still assumes the central
cofactor power data. Constructing that data is the highest-payoff trusted
arithmetic PR.

## Priority stack

### Priority 1 — generalized-Fermat signature graph

Create `BealUnified/GeneralizedFermat.lean`.

Deliverables:

1. `PrimitiveGFESolution` with exponents allowed below Beal's floor;
2. signatures, permutations, and hyperbolicity predicates;
3. coordinatewise divisor shadows;
4. preservation of positivity and pairwise coprimality under exponent absorption;
5. upward closure: a solved divisor signature excludes every multiple signature;
6. theorem types suitable for registry validation.

Why first: the existing `4`-or-odd-prime normalization is exact but chooses only
one divisor per exponent and loses perfect-power provenance. A signature graph
lets every future formal theorem close an infinite divisibility cone.

Risk: low. This is elementary algebra and API design.

### Priority 2 — exact cyclotomic power split

Create `BealUnified/CyclotomicPowerSplit.lean`.

For

```text
X^p + Y^p = C^n,
p odd prime,
n ≥ 3,
gcd(X,Y)=1,
```

formalize:

1. `gcd (X+Y) Φ_p^+(X,Y) ∣ p`;
2. the coprime branch `X+Y = U^n`, `Φ = V^n`, `C = U*V`;
3. the exceptional branch `X+Y = p^(n*k-1)U^n`, `Φ = p*V^n`;
4. `v_p Φ = 1` from Mathlib plus-sign LTE;
5. `V > 1`;
6. a prime `q ∣ V` with `q^n ∣ Φ` and `q ≡ 1 (mod 2p)`;
7. at least two distinct prime divisors of `C`;
8. `rad C ≥ 4p+2`;
9. the Beal corollary: a common odd prime divisor of the two left exponents
   excludes a prime-power right base;
10. the analogous difference theorem, retaining the `X-Y=1` exceptional branch.

Why second: this constructs the mathematical data that
`CofactorPowerData` currently records as an assumption and that
`PrimitivePowSubDivisor` only consumes.

Risk: medium-low. The mathematics is elementary; the main work is Mathlib API
navigation for perfect powers and prime factorizations.

### Priority 3 — frontier bounds and method limitations

Create `BealUnified/FrontierBounds.lean`.

Deliverables:

1. the cleared-denominator inequality
   `12*(yz+xz+xy) ≤ 11*xyz` outside `(3,3,3)`;
2. `rad(A*B*C)^12 < (C^z)^11`;
3. exact all-unit finite-field count `(Q-1)(Q-2)` for pairwise-coprime
   exponents;
4. the exact unit count over odd prime powers;
5. a theorem-level statement that a predetermined finite collection of
   all-unit congruence tests cannot eliminate a pairwise-coprime exponent
   signature.

Why third: these are unconditional, reusable, and they prevent further work from
repeating proof strategies that cannot close the distinct-prime core.

Risk: medium. The radical proof needs careful coercion and strict-power
monotonicity; finite-group counting needs a clean Smith-normal-form or explicit
Bezout implementation.

### Priority 4 — expand registry semantics

The current registry distinguishes only trusted solved rows and a generic open
source-audit state. Introduce explicit statuses such as:

- `solved`;
- `reduction-solved`;
- `literature-solved-formalization-pending`;
- `open-frontier`;
- `conditional`;
- `experimental-evidence`.

Requirements:

- only trusted solved statuses may name formal declarations;
- every trusted declaration must have an exact expected Lean type;
- literature rows must pin a primary source and theorem statement;
- computational rows must name a replay checker and exact artifact hashes;
- no literature or experiment row may be imported into `BealUnified.Trusted`.

Risk: low, but fail-closed validation is mandatory.

### Priority 5 — certify `(3,4,5)`

This is a formalization project, not new mathematics.

Milestones:

1. pin the exact Siksek–Stoll source version and theorem statement;
2. reconstruct the reduction to the finite curve/Selmer-set calculation;
3. define certificates for number-field arithmetic and local solubility;
4. independently reproduce every source computation;
5. retain producer and checker hashes in research checkpoints;
6. formalize the implication from empty checked certificates to no primitive
   `(3,4,5)` solution;
7. only then change the registry row to trusted `solved`.

Why before a large generic modular stack: it closes a real Beal signature and
builds reusable descent/certificate infrastructure.

Risk: high implementation cost, low mathematical uncertainty.

### Priority 6 — attack `(3,5,7)` as a fixed signature

Promising methods:

- fixed-signature descent to explicit curves or étale algebras;
- multi-Frey or hypergeometric-motive modular methods;
- conductor and local-type classification;
- Hilbert-newform enumeration with exact trace certificates;
- explicit tracking and elimination of ghost forms;
- cross-checking through an independent implementation.

The 2025 `(5,p,3)` codebase is useful input, not a theorem for `p=7`. A valid
program must explicitly resolve every exceptional residual case rather than
extrapolating an asymptotic theorem.

Risk: high. This is the first genuinely open mathematical target.

### Priority 7 — repeated-prime global arithmetic

After Priority 2, the repeated branch reduces to equations of the form

```text
Φ_p^±(X,Y) = p^δ * D^q.
```

The remaining global question needs one of:

- a verified cyclotomic-unit/class-group obstruction;
- a theorem forcing a nonexceptional valuation not divisible by `q`;
- a certified fixed-family modular argument.

Primitive-divisor existence alone is insufficient because nonexceptional
valuations greater than one occur in the DGX census.

Risk: mathematically high.

## Work not to prioritize as the main proof path

| Approach | Limitation |
|---|---|
| More fixed-modulus finite-field atlases | Pairwise-coprime exponent maps are locally saturated; use them only for support lemmas |
| Unconditional primitive-divisor valuation one | False without extra hypotheses; observed valuations reach four |
| Generic LTE development | The needed plus-sign theorem already exists and applies mainly to shared-exponent slices |
| Generic CUDA brute force | Bounded evidence only; useful after a certificate schema exists |
| Qualitative ABC as a proof | Gives finiteness, not emptiness or a usable enumeration constant |
| Baker bounds followed by brute force | Constants and number fields are too large and signature-dependent |
| Full generic cyclotomic attack | Does not address pairwise-coprime signatures such as `(3,5,7)` |
| Full Wiles/Ribet formalization | Very high cost and does not imply Beal |
| Additive combinatorics or direct transcendence | No established Beal mechanism |
| Unreviewed universal proof preprints | No registry or trusted status before independent source reconstruction |

## Trust and publication gates

A claim may enter the trusted solved inventory only when all of the following
hold:

1. exact Lean theorem type is registered;
2. public trusted import loads the declaration;
3. axiom audit accepts every transitive dependency;
4. all external computations have a certificate schema;
5. a separately implemented checker replays those certificates;
6. source, producer, checker, and artifact hashes are retained;
7. CI exercises negative fixtures for malformed or weakened claims.

A research checkpoint, a paper citation, a bounded search, or a successful Magma
transcript is not by itself a trusted theorem.

## Near-term execution order

1. merge the trust-boundary PR;
2. merge the frontier semantics/audit update;
3. implement generalized-Fermat divisor shadows;
4. implement exact cyclotomic power splitting;
5. implement radical and local-saturation theorems;
6. expand the registry schema;
7. begin `(3,4,5)` certificate reconstruction;
8. maintain `(3,5,7)` as a separate research project with no proof claim.

## Related documents

- [`Research/BEAL_FRONTIER_AUDIT_2026-07-24.md`](../Research/BEAL_FRONTIER_AUDIT_2026-07-24.md)
- [`Research/DGX_SPARK_EXPERIMENTS_2026-07-17.md`](../Research/DGX_SPARK_EXPERIMENTS_2026-07-17.md)
- [`roadmap/state-of-the-art.md`](state-of-the-art.md)
- [`roadmap/mission-C-modular-method.md`](mission-C-modular-method.md)
- [`roadmap/mission-D-alternative-paths.md`](mission-D-alternative-paths.md)
- [`roadmap/TRUST_BOUNDARY_ROADMAP.md`](TRUST_BOUNDARY_ROADMAP.md)
