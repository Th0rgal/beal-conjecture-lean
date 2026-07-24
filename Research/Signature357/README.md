# Signature (3,5,7): fixed-7 modular frontier

## Status

The signature `(3,5,7)` remains open. This directory turns the public
Pacetti--Villagra Torcomian `(5,p,3)` computation into an explicit fixed-`p=7`
frontier rather than relying on an asymptotic theorem.

A hypothetical Beal solution

```text
A^3 + B^5 = C^7
```

can be written in the paper's orientation as

```text
a^5 + b^7 + c^3 = 0
```

with `(a,b,c) = (B,-C,A)`.

The primary source is arXiv `2512.17845`. The pinned computation is
`lucasvillagra/GFE-5p3` commit
`e88f914c577ab6cf9a45e5cdd82c1993477fb423`, file
`Outputs/TheoremA.txt`, blob
`890802467458f79b468738a90be4bf8e57f255ff`.

## Fixed-7 breakthrough

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
125 newform packets → 12 fixed-7 survivors.
```

That is 113 eliminated packets, or 90.4% of those two spaces.

The nine survivors at level `(3,2)` split as:

- seven forms whose computed resultant bound is divisible by `7`:
  `21, 22, 26, 33, 61, 92, 98`;
- two forms for which the chosen auxiliary primes did not produce a nonzero
  elimination bound: `65, 78`.

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

The exact fixed-7 survivor sets at the other levels can be obtained by running
the public Magma code with per-form output enabled:

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

The current Magma program eliminates a form by computing integer resultants
between:

- the minimal polynomial of a Hilbert-newform Hecke eigenvalue;
- each possible hypergeometric trace polynomial at an auxiliary prime.

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
```

A standard-library Python checker can replay the polynomial resultants, gcds,
and the conclusion “7 does not divide the bound”. Magma remains a producer of
newform and trace data, not the trusted verifier.

## Most promising mathematical attack after complete extraction

1. Finish the two flagged reruns and obtain the exact fixed-7 survivor set across
   all four levels.
2. Separate CM packets, ghost packets, and genuinely non-CM survivors.
3. Apply the local-type theorem that excludes the two ghost packets when
   `3 ∤ c` (in Beal orientation, `3 ∤ A`).
4. For each CM packet, compare inertial type and Frobenius traces at primes where
   the hypothetical solution has forced multiplicative or potentially good
   reduction.
5. For non-CM survivors, add an independent Frey or hypergeometric
   representation and intersect the two residual trace constraints.
6. Retain exact certificate data for every elimination; never infer the `p=7`
   case from the paper's asymptotic exceptional-set theorem.

The public paper and transcript are infrastructure, not a proof of `(3,5,7)`.
The result here is an executable and sharply smaller fixed-7 search target.
