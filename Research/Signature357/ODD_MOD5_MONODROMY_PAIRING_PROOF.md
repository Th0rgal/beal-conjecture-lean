# Signature `(3,5,7)`: integral monodromy proof for the twisted mod-`5` conductor

## Status

This note fills the integral step between the semistable cluster picture and the
residual conductor of the two-dimensional real-multiplication constituent.  It
does **not** prove the odd branch or the full signature.  It uses the following
external mathematical inputs explicitly:

1. the source cluster classification for the Darmon curve after parameter
   inversion;
2. the DDMM description of the dual graph and its length pairing;
3. Grothendieck's semistable monodromy description of the Tate module;
4. the full real-multiplication action by
   `O_K`, for `K=Q(zeta_7)^+`, on the relevant Jacobian.

The arithmetic specialization and the determinant argument below are internal
and do not require a large-image theorem.

## Setup

In the Dahmen--Siksek odd branch, put

```text
a = v_7(A) >= 1.
```

After inverting the hypergeometric parameter and applying the cyclotomic
quadratic untwist, the associated genus-three Darmon curve is semistable at the
unique prime above `7` of

```text
K = Q(zeta_7)^+.
```

The discriminant parameter in the conductor paper satisfies

```text
v_7(Delta) = 3*a.
```

For `r=7`, Corollary 3.5(6) of Cazorla Garcia--Villagra Torcomian gives three
inertia-stable twins, each with relative depth

```text
n = v_7(Delta)/2 - 7/6 = (9*a-7)/2.
```

The displayed relative depth may be half-integral.  The integral edge length in
the dual graph is

```text
m = 2*n = 9*a-7.
```

## The full Jacobian monodromy pairing

Let `X=H_1(Upsilon,Z)` be the character lattice of the toric part of the
semistable Jacobian.  The three twins give a basis

```text
ell_1, ell_2, ell_3
```

of `X`.  The DDMM length-pairing theorem says that distinct twin loops are
orthogonal and that a twin loop has self-pairing twice its relative depth.
Therefore

```text
<ell_i,ell_j> = 0       for i != j,
<ell_i,ell_i> = 9*a-7.
```

Equivalently, the integral monodromy map

```text
lambda : X -> X^vee
```

has matrix

```text
(9*a-7)*I_3.
```

In particular,

```text
det_Z(lambda) = (9*a-7)^3.
```

## Passage to the real-multiplication constituent

The Jacobian has real multiplication by `O_K`.  The Rosati involution is the
identity on this totally real field, so the monodromy map is `O_K`-linear.  The
lattice `X` has rank `3` over `Z` and is torsion-free; hence it is a rank-one
projective `O_K`-module (a fractional ideal).

The rational prime `5` is inert in `K`.  Consequently

```text
O_K tensor Z_5 = O_{K,5}
```

is the unramified degree-three extension of `Z_5`, and

```text
X_5 = X tensor Z_5
```

is free of rank one over `O_{K,5}`.  Thus `lambda_5` is multiplication by one
local scalar, up to the harmless identification of the dual fractional ideal.
If that scalar is denoted by `alpha`, then

```text
v_5(det_Z5(lambda_5)) = 3*v_{K,5}(alpha).
```

On the other hand, the integral loop basis gives

```text
v_5(det_Z5(lambda_5)) = 3*v_5(9*a-7).
```

Therefore

```text
lambda_5 mod 5 = 0  <=>  5 | (9*a-7).
```

If `5` does not divide `9*a-7`, the monodromy map is an isomorphism modulo `5`;
it cannot disappear on an individual two-dimensional constituent.  This avoids
any unproved choice of an `O_K`-basis for the three twin loops: the determinant
and inert-degree calculation are basis independent.

## Residual conductor

Grothendieck's semistable monodromy theorem identifies tame inertia on the
`5`-adic Tate module with the monodromy map.  On each two-dimensional
`K_5`-constituent:

```text
lambda_5 mod 5 = 0  => residual inertia is trivial,
lambda_5 mod 5 != 0 => residual monodromy has rank one.
```

The residual conductor exponent at `7` is therefore exactly

```text
e_7 = 0  if 5 | (9*a-7),
e_7 = 1  otherwise.
```

Since `9*a-7 = 0 mod 5` is equivalent to `a=3 mod 5`, this becomes

```text
e_7 = 0  <=>  v_7(A)=3 mod 5,
e_7 = 1  <=>  v_7(A)!=3 mod 5.
```

## Exact automorphic split

The prime-`3` conductor exponent is `e_3 in {2,3}`.  Hence the cyclotomically
untwisted mod-`5` representation lowers only to

```text
(e_3,e_7) = (2,0), (2,1), (3,0), (3,1),
```

with level norms

```text
729, 5103, 19683, 137781.
```

The complete low-level certificate already removes norm `729`.  The exact
remaining frontier is therefore

```text
5103, 19683, 137781.
```

The branch is split simultaneously by the valuation class:

```text
v_7(A)=3 mod 5:
  e_7=0, levels 729 or 19683;

v_7(A)!=3 mod 5:
  e_7=1, levels 5103 or 137781.
```

## Replay

The finite arithmetic is replayed by

```bash
python3 scripts/check_signature_357_odd_mod5_exact_monodromy.py --self-test
python3 scripts/check_signature_357_odd_mod5_exact_monodromy.py
```

The checker verifies the specialization `v_7(Delta)=3*a`, the integral length
`2*n=9*a-7`, the residue class `a=3 mod 5`, every level norm, source digests and
negative fixtures.  The external cluster, RM and semistable-monodromy theorems
remain outside `BealUnified.Trusted`.
