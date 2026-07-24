# Signature (3,5,7): fixed-7 modular frontier

## Status

The signature `(3,5,7)` remains open. This directory turns the public
Pacetti--Villagra Torcomian `(5,p,3)` computation into an explicit fixed-`p=7`
frontier and adds an independently replayed local certificate at the residual
prime itself.

A hypothetical Beal solution

```text
A^3 + B^5 = C^7
```

is also a solution of Dahmen--Siksek's equation `x^5+y^3=z^7` under
`(x,y,z)=(B,A,C)`, and can be written in the Pacetti--Villagra orientation as

```text
a^5 + b^7 + c^3 = 0
```

with `(a,b,c)=(B,-C,A)`.

The primary sources are:

- Dahmen--Siksek, *On the generalized Fermat equation x^5+y^3=z^7*, working
  paper dated July 2024, Theorem 1;
- Pacetti--Villagra Torcomian, arXiv `2512.17845`;
- the pinned computation `lucasvillagra/GFE-5p3` commit
  `e88f914c577ab6cf9a45e5cdd82c1993477fb423`, file
  `Outputs/TheoremA.txt`, blob
  `890802467458f79b468738a90be4bf8e57f255ff`.

## Audited Dahmen--Siksek dichotomy

Theorem 1 of the working paper implies that every nontrivial primitive solution
belongs to exactly one of the following disjoint branches after the substitution
`(x,y,z)=(B,A,C)`:

| branch | necessary conditions |
|---|---|
| even | `30 ∣ C` and `7 ∤ A*B` |
| odd | `C` odd, `3 ∤ A*B*C`, `5 ∤ A*C`, and `7 ∣ A` |

This dichotomy is a literature theorem, not yet a Lean theorem in this
repository. The exact orientation and branch metadata are pinned in
`prime7_local.json` so downstream computations cannot silently use a different
variable convention.

## Even branch: reduced to residual irreducibility

In the Pacetti--Villagra orientation `(a,b,c)=(B,-C,A)`, the even branch has
`3 ∣ b` and `5 ∣ b`. Their conductor formulas therefore force the Hilbert level
exponents to `(2,2)`, i.e. level `3^2*(sqrt(5))^2`.

The public fixed-`7` computation leaves only newform packets `3,9,12` at this
level. The paper identifies these packets as CM, while the special local types
forced at `3` and `5` exclude a congruent CM representation under the residual
irreducibility hypothesis. Consequently the source chain gives the precise
conditional reduction

```text
primitive solution in the even branch
  => the associated residual mod-7 representation is reducible.
```

This is a substantial compression, but it is not an exclusion of the branch.
The remaining mathematical target is now explicit: prove residual mod-`7`
irreducibility for the Frey representation in this valuation branch, or classify
and eliminate every reducible case.

## Odd branch: exact prime-7 local certificate

For the odd branch, Pacetti--Villagra's Frey model can be written

```text
y^2 + y*(x^3+B) = 2*B*x^3 + 3*A*x + B^2.
```

With `Y=2*y+x^3+B`, exact completion of the square gives

```text
Y^2 = x^6 + 10*B*x^3 + 12*A*x + 5*B^2.
```

Since the odd branch has `7 ∣ A` and primitivity gives `B != 0 mod 7`, reduction
at `7` is

```text
Y^2 = x^6 + 3*B*x^3 + 5*B^2.
```

Run:

```bash
python3 scripts/check_signature_357_prime7_local.py --self-test
python3 scripts/check_signature_357_prime7_local.py
```

The standard-library checker independently verifies:

1. the multivariate completed-square identity over the integers;
2. square-freeness of the reduced sextic for every `B in F_7^*`;
3. vanishing of the Cartier--Manin coefficients at exponents
   `5,6,12,13` in the cube of the sextic;
4. exact point counts over `F_7` and `F_49`, using the explicit field
   `F_7[w]/(w^2+1)`;
5. the resulting genus-2 Weil polynomials and the trace of each
   real-multiplication constituent at the unique prime over `7` in
   `Q(sqrt(5))`.

The result is:

| `B mod 7` | `#C(F_7)` | `#C(F_49)` | genus-2 Weil polynomial | RM trace |
|---:|---:|---:|---|---:|
| `1,3,4,6` | 8 | 64 | `T^4+7*T^2+49` | `-7` |
| `2,5` | 8 | 22 | `T^4-14*T^2+49=(T^2-7)^2` | `14` |

Thus every odd-branch specialization has zero Cartier--Manin matrix and

```text
a_p ≡ 0 mod p
```

at the unique prime `p` above `7`. In standard genus-two terminology the zero
matrix gives the maximal `a`-number, hence the superspecial local case. The
fully replayed numerical family digest is

```text
65f0cc94575f0b048e28e60c328b9bed02938af2ecd0de8e9e73a4105bf716d9
```

The source paper's auxiliary-prime resultant elimination did not impose this
residual-prime local condition. The most direct next computation is therefore to
filter every fixed-`7` survivor by the corresponding nonordinary local type.
This requires an explicit local-global compatibility theorem at the residual
prime; ordinary away-from-`7` trace congruences are not enough.

## Fixed-7 newform extraction

The paper lowers an irreducible residual representation to four Hilbert modular
levels over `Q(sqrt(5))`. The public transcript gives enough information to
complete the exact `p=7` elimination at two of the four levels.

| conductor exponents | newforms | exact fixed-7 survivors |
|---|---:|---|
| `(2,2)` | 14 | `3, 9, 12` |
| `(3,2)` | 111 | `21, 22, 26, 33, 61, 65, 78, 92, 98` |
| `(2,3)` | 35 | exact set requires a flagged rerun |
| `(3,3)` | 112 | exact set requires a flagged rerun |

Thus, in the two complete levels, the public Mazur-resultant calculation reduces

```text
125 newform packets -> 12 fixed-7 survivors.
```

That is 113 eliminated packets, or 90.4% of those two spaces.

The nine survivors at level `(3,2)` split as:

- seven forms whose computed resultant bound is divisible by `7`:
  `21,22,26,33,61,92,98`;
- two forms for which the chosen auxiliary primes did not produce a nonzero
  elimination bound: `65,78`.

Run:

```bash
python3 scripts/check_signature_357_fixed7.py --self-test
python3 scripts/check_signature_357_fixed7.py
```

The checker validates the pinned frontier and rejects unsupported completeness
claims. It can also replay a downloaded transcript:

```bash
python3 scripts/check_signature_357_fixed7.py \
  --transcript /path/to/Outputs/TheoremA.txt
```

## The two missing public reruns

The exact fixed-7 survivor sets at the other levels require per-form output:

```magma
TheoremA(2,3,Data : flag := true);
TheoremA(3,3,Data : flag := true);
```

Until those outputs are retained and replayed, the manifest records only lower
bounds:

- `(2,3)` contains at least forms `1,7,11,12,13,16,21`;
- `(3,3)` contains at least the ghost forms `22,39`.

The published exception sets contain `7`, so no smaller exact set follows from
the unflagged summaries.

## Next certificate format

For a proof-grade fixed-7 computation, every form/prime certificate should store:

```text
level
newform packet ID
auxiliary rational prime and prime ideal data
minimal polynomial of the Hecke eigenvalue
candidate trace polynomials
all integer resultants
their gcd across candidates and auxiliary primes
the prime divisors of that gcd
local type at the prime over 7
```

A standard-library checker can replay the polynomial resultants, gcds, point
counts and local-type predicates. Magma remains a producer of newform and trace
data, not the trusted verifier.

## Most promising mathematical attack

1. Prove residual mod-`7` irreducibility in the even branch. This would eliminate
   that entire half of the Dahmen--Siksek dichotomy.
2. Finish the two flagged reruns and obtain the exact survivor set across all four
   levels.
3. Compute the local type at the prime over `7` for each survivor and apply the
   certified condition `a_p ≡ 0` in the odd branch.
4. Separate CM packets, ghost packets and genuinely non-CM survivors.
5. Apply the ghost incompatibility theorem whenever its valuation hypothesis
   (`3 ∤ A` in Beal orientation) is available.
6. For any non-CM survivors, add an independent Frey or hypergeometric
   representation and intersect the two residual trace constraints.
7. Retain exact certificate data for every elimination; never infer `p=7` from
   the paper's asymptotic exceptional-set theorem.

The public papers and transcripts are infrastructure, not a proof of `(3,5,7)`.
The new local certificate turns the odd branch into a concrete nonordinary
fixed-`7` filtering problem, while the even branch is reduced to one explicit
irreducibility problem.

## Repeated-left frontier

The independently audited cyclotomic reduction shows that a primitive solution
of `X^p+Y^p=C^n` with odd prime `p` forces at least two prime divisors of `C` and
a nonexceptional prime of multiplicity at least `n`. Combined with the current
solved-signature survey, `(5,5,11)` is the first unresolved unit-coefficient
repeated-left prime signature by exponent sum.

The current version of Bartolome--Mihailescu, arXiv `2108.08572v4`, proves only
the equal-exponent cofactor equation with right exponent `p`; it must not be used
as a theorem for a distinct exponent `q`. The specific diagnosis of superseded
proof text remains outside this certificate until independently audited.
