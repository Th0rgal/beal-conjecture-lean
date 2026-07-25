# Signature `(3,5,7)`: exact odd-branch conductor at `7`

## Status

This note records a literature-assisted local-conductor reduction. The finite
point counts, trace-polynomial comparison, quadratic-character arithmetic and
level-norm calculation are independently replayed. The motive congruence,
parameter-independent twist theorem, exact local conductor comparison and
Hilbert level lowering remain imported inputs. This note does not by itself
prove the odd branch or the full signature.

## Setup

In the Dahmen--Siksek odd branch,

```text
3 does not divide A*B*C,
7 divides A,
7 does not divide B*C.
```

For the independent residual mod-`5` compatible system over

```text
K7 = Q(zeta_7)^+,
```

use the mathematical parameter

```text
u = C^7/A^3.
```

The hypergeometric inversion identity exchanges the exponent pairs and replaces
`u` by

```text
s = u^(-1) = A^3/C^7.
```

Thus `s` is integral and divisible by `7`, and the mod-`7` congruence compares
the swapped compatible system with the rank-two constituent of the Darmon
curve

```text
C_7^+(s):
  y^2 = (x+2)*(x^7-7*x^5+14*x^3-7*x+2-4*s),
```

up to a parameter-independent quadratic character of
`Gal(Q(zeta_21)/K7)`.

## Identifying the twist at `7`

The extension `Q(zeta_21)/K7` is biquadratic. Its four quadratic characters may
be represented by the radicals

```text
1, -3, -7, 21.
```

Take the specialization `s=3` and the rational prime `13`, which splits
completely in `K7`. The pinned finite-HGM producer gives the degree-three trace
polynomial

```text
x^3 + 2*x^2 - x - 1.
```

For the Darmon curve `C_7^+(3)`, exact point counting gives

```text
#C(F_13)   = 7,
#C(F_13^2) = 227,
#C(F_13^3) = 2401.
```

Newton identities recover the rank-three trace polynomial

```text
x^3 - 7*x^2 + 14*x - 7.
```

Modulo `3`, both polynomials equal

```text
x^3 + 2*x^2 + 2*x + 2.
```

The polynomial obtained by negating all three Frobenius eigenvalues is instead

```text
x^3 + x^2 + 2*x + 1 mod 3,
```

so the twist value at the primes over `13` is `+1`.

At `13`, the character values are

```text
chi_(-3) = +1,
chi_(-7) = -1,
chi_(21) = -1,
trivial   = +1.
```

Therefore the parameter-independent congruence twist is either trivial or
`chi_(-3)`. Both are locally trivial at `7`, because `-3=4 mod 7` is a square.

## Exact conductor consequence

After the parameter exchange, the odd branch lies in the first row of the
source conductor table at `7`: `7` divides the swapped paper variable `a`, while
`7` does not divide the other two variables. The paper's exact-conductor remark
fixes the conductor exponent at `2` when the comparison is defined over the base
field or up to an unramified quadratic twist. The preceding calculation shows
that the only possible congruence twists are locally trivial at `7`.

The quadratic ramification involved in the local type has order `2`, so it also
survives reduction modulo `5`. Consequently

```text
e7(mod 5) = 2
```

throughout the odd branch.

## Automorphic frontier compression

The independent mod-`5` exponent at `3` is already known to satisfy

```text
e3 in {2,3}.
```

Hence the odd branch can lower only to

```text
(e3,e7) = (2,2) or (3,2),
```

with level norms

```text
27^2*7^2 = 35,721,
27^3*7^2 = 964,467.
```

The previous odd frontier

```text
729, 5103, 19683, 35721, 137781, 964467
```

therefore collapses to

```text
35,721 and 964,467.
```

In particular, level `5103` is not part of the odd frontier once this
exact-conductor input is accepted.

## Replay

Run:

```bash
python3 scripts/check_signature_357_odd_p7_twist.py --self-test
python3 scripts/check_signature_357_odd_p7_twist.py
```

Certificate:

```text
Research/Signature357/odd_p7_twist.json
```

Digest:

```text
1ac352af8ce0d9d324112c6741bebef06124734d4708e9737bace6804c5931fc
```

## Remaining odd-branch computation

Only two cubic Hilbert-newform spaces remain on the mod-`5` side:

```text
level norm 35,721  with exponents (2,2),
level norm 964,467 with exponents (3,2).
```

They synchronize with the fixed-`7` spaces according to the common `3`-adic
conductor block. A zero residual Hecke module at either level eliminates the
whole block without requiring characteristic-zero packet decomposition.
