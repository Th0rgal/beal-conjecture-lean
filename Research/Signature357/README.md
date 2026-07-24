# Signature (3,5,7): fixed-prime modular frontier

## Status

The signature `(3,5,7)` remains open. This directory turns the public
Pacetti--Villagra Torcomian `(5,p,3)` computation into an explicit fixed-`p=7`
frontier, adds an independently replayed local certificate at the residual prime,
and records an independent mod-`5` Frey system whose residual representation is
absolutely irreducible throughout the unit-at-`3` branch.

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
- Golfieri--Pacetti, arXiv `2412.08804`, for the compatible hypergeometric
  system used by the second Frey representation;
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

This is a substantial compression, but it is not yet an unconditional exclusion
of the even branch. The remaining mathematical target is to prove residual
mod-`7` irreducibility in this valuation branch, or classify and eliminate every
reducible case. The parity-free auxiliary-prime sieve recorded in the frontier
audit reduces this further outside an explicitly large divisor of `C`.

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
residual-prime local condition. The direct next computation is therefore to
filter every fixed-`7` survivor by the corresponding nonordinary local type.
This requires explicit local-global compatibility at the residual prime;
ordinary away-from-`7` trace congruences are not enough.

The odd branch also has a source-backed fixed-`7` irreducibility certificate:

```bash
python3 scripts/check_signature_357_odd_irreducibility.py --self-test
python3 scripts/check_signature_357_odd_irreducibility.py
```

It validates the corrected auxiliary-prime obstruction
`900=2^2*3^2*5^2` with `C(2)=5`, the Beal-to-paper orientation, and `7 ∤ 900`. The source
implication from reducibility to divisibility by that obstruction remains an
explicit literature dependency.

## Second Frey system: complete mod-5 irreducibility at 3

Use the independent plus compatible system for signature `(7,5,3)` over

```text
K_7 = Q(zeta_7)^+,
```

with orientation

```text
(a,b,c)=(-C,B,A)
```

and parameter

```text
u = C^7/A^3.
```

Assume `3 ∤ A*B*C`. Exact enumeration of the primitive unit equation modulo `9`
shows

```text
u mod 9 ∈ {2,5,8}.
```

The local-type table in Pacetti--Villagra assigns:

| `u mod 9` | local type at `3` | inertia order bound |
|---:|---|---:|
| `2` | ramified-quadratic supercuspidal | `12` |
| `5` | unramified-quadratic supercuspidal | `4` |
| `8` | ramified-quadratic supercuspidal | `12` |

The rational prime `3` has order `6` modulo `7`, hence residue degree `3` in the
real cubic field `K_7`. The local base change is therefore unramified cubic. It
cannot contain the unramified quadratic extension used by the order-`4` type,
and the ramified-quadratic type is unaffected by unramified base change.
Consequently all three rows remain supercuspidal over `K_7`.

The finite inertia orders `4` and `12` are prime to both the source congruence
characteristic `7` and the target residual characteristic `5`. The cited
local-type compatibility therefore transfers the type from the Darmon curve to
the compatible system and then to its `5`-adic member; reduction modulo `5`
preserves the distinct inducing characters. Thus:

```text
3 ∤ A*B*C
  => the independent residual mod-5 representation is absolutely irreducible.
```

Run:

```bash
python3 scripts/check_signature_357_mod5_irreducibility.py --self-test
python3 scripts/check_signature_357_mod5_irreducibility.py
```

The checker independently verifies the finite arithmetic, including the exact
modulo-`9` enumeration, residue degree, absence of an unramified quadratic
subfield, prime-to-`5`/`7` inertia orders, metadata, and canonical digest:

```text
df815f6ebf008640c51840f19d1d2110f7ce37fd03185caa5cc3bb5cbdbfe21e
```

It does not reprove the cited compatible-system or local-type theorems. This
certificate remains outside `BealUnified.Trusted`.

This closes the five classes

```text
47,74,101,209,380 mod 441
```

that remained in the earlier polynomial-irreducibility sieve. They are not true
exceptions: at `3` their exact supercuspidal type already forces residual
irreducibility. In particular, the Dahmen--Siksek odd branch now has two
independent absolutely irreducible residual representations, modulo `7` and
modulo `5`.

The two parameters are coupled exactly. For the first representation let

```text
t_7 = -B^5/A^3,
```

while the second uses `u=C^7/A^3`. The Beal equation gives

```text
u + t_7 = 1.
```

Therefore the next two-Frey calculation must use the joint trace graph

```text
{ (tr rho_5(u), tr rho_7(1-u)) : u in F_l \ {0,1} },
```

not the Cartesian product of two marginal trace sets.

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

The exact fixed-`7` survivor sets at the other levels require per-form output:

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

For a proof-grade fixed-prime computation, every form/prime certificate should
store:

```text
level
newform packet ID
auxiliary rational prime and prime ideal data
minimal polynomial of the Hecke eigenvalue
candidate trace polynomials
all integer resultants
their gcd across candidates and auxiliary primes
the prime divisors of that gcd
local type at the residual prime
joint trace pairs under u+t_7=1
```

A standard-library checker can replay polynomial resultants, gcds, point counts,
local-type predicates, and joint trace membership. Magma remains a producer of
newform and trace data, not the trusted verifier.

## Most promising mathematical attack

1. Finish the two flagged mod-`7` reruns and obtain the exact survivor set across
   all four levels.
2. Compute the local type at the prime over `7` for each survivor and apply the
   certified superspecial/nonordinary condition in the odd branch.
3. Separate CM packets, ghost packets and genuinely non-CM survivors; apply the
   ghost incompatibility theorem when `3 ∤ A`.
4. Enumerate the relevant Hilbert newforms over `Q(zeta_7)^+` for the now-proved
   irreducible mod-`5` system.
5. Use `u+t_7=1` to run a simultaneous joint trace-pair elimination rather than
   intersecting two independent marginal survivor lists.
6. Prove mod-`7` irreducibility in the remaining even-branch exceptional support
   case, or classify its reducible ray-class characters directly.
7. Retain exact certificate data for every elimination; never infer `p=7` from
   the paper's asymptotic exceptional-set theorem.

The public papers and transcripts are infrastructure, not a proof of `(3,5,7)`.
The new mod-`5` theorem removes the last local irreducibility exceptions in the
odd branch and turns the remaining task into a finite two-Frey/newform
cross-elimination problem.
