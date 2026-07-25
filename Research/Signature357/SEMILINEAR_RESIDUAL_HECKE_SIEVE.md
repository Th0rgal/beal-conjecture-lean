# Signature `(3,5,7)`: combined semilinear residual Hecke sieve

## Status

This note records a new finite elimination method for the remaining odd branch.
It does **not** by itself prove that either residual space is zero, and it is not
imported by `BealUnified.Trusted`.

The mathematical improvement is that the remaining computation no longer needs
a characteristic-zero newform decomposition.  It works directly in the residual
Hecke module and imposes, simultaneously:

1. the residual-prime local condition;
2. all allowed HGM trace polynomials;
3. the semilinear Galois descent relations forced by a rational specialization.

A zero intersection is a proof-grade finite elimination once the explicitly
listed modularity, level-lowering, local-trace and semilinear-descent inputs are
accepted.

## 1. General residual-Hecke lemma

Let `M` be a finite-dimensional Hecke module over a finite field `k`, and let
`T_v` be its commuting Hecke operators.  Suppose a residual eigensystem with
values `a_v` must satisfy

```text
P_v(a_v)=0
```

at every auxiliary place `v`.  Then a corresponding simultaneous eigenvector
lies in

```text
intersection_v ker(P_v(T_v)).
```

This remains true even when the residual Hecke algebra is non-semisimple: an
actual eigenvector is killed by every polynomial that vanishes at its
eigenvalue.  Consequently

```text
intersection_v ker(P_v(T_v)) = 0
```

eliminates every residual eigensystem.  A nonzero intersection is only a
necessary survivor space; its dimension is not interpreted as a packet count.

For a union of local regimes, use the product of their trace polynomials.  If an
eigenvalue belongs to any regime, that product vanishes.

## 2. Fixed-`7` level `(3,3)`

The residual coefficient field is `F_49`, and the nontrivial automorphism of
`Q(sqrt(5))/Q` acts on coefficients by

```text
x |-> x^7.
```

Start with the superspecial subspace

```text
S_0 = ker(T_7)
```

inside the level-`(3,3)` new subspace modulo `7`.

At a rational prime inert in `Q(sqrt(5))`, the unique prime ideal is fixed by
Galois, so a rational specialization must satisfy

```text
T_l^7-T_l=0.
```

At a split rational prime with conjugate ideals `l_1,l_2`, impose both

```text
T_(l_2)-T_(l_1)^7=0,
T_(l_1)-T_(l_2)^7=0.
```

These relations are independent of the ordering returned by Magma.  Intersect
them with the HGM local-union kernel.  The producer

```text
scripts/run_signature_357_magma_fixed7_combined_residual.py
```

uses inert primes `13,43` first and then `11,29,41`.

## 3. Independent mod-`5` system over the real cubic field

After the cyclotomic quadratic untwist, the odd branch is reduced to the three
levels

```text
5103, 19683, 137781.
```

The residual coefficient field is `F_125`.  A generator of
`Gal(Q(zeta_7)^+/Q)` acts by

```text
x |-> x^5.
```

At an inert rational prime, impose

```text
T_l^5-T_l=0.
```

At a completely split rational prime with three prime ideals and eigenvalues
`a,b,c`, the ordering of the two nontrivial conjugates is irrelevant.  The
Frobenius-orbit condition

```text
{b,c}={a^5,a^25}
```

is equivalent, on eigenvectors, to

```text
b+c=a^5+a^25,
b*c=a^30,
a^125=a.
```

The corresponding operator relations are therefore

```text
T_2+T_3-T_1^5-T_1^25,
T_2*T_3-T_1^30,
T_1^125-T_1.
```

They avoid choosing a cyclic orientation for Magma's prime-ideal ordering.

Start with the independently certified norm-`8` subspace

```text
ker(T_2) mod 5
```

and intersect the complete local HGM union and semilinear kernels at inert
primes `11,23` and split primes `13,29,41,43`.  The producer is

```text
scripts/run_signature_357_magma_mod5_combined_semilinear.py.
```

## 4. Why this is stronger than the earlier computations

The earlier marginal calculations asked, one prime at a time, whether a Hecke
characteristic polynomial shared a factor with an allowed trace polynomial.
Positive gcds at different primes need not belong to the same residual
 eigensystem.

The combined method instead keeps the actual common residual subspace and
intersects it after each prime.  It also adds Galois-descent equations that are
invisible to a marginal trace set.  Thus it can prove emptiness even when every
individual prime has a positive gcd.

It also avoids the expensive characteristic-zero decomposition of the largest
spaces.  Only Hecke operators on a rational basis and finite-field linear
algebra are required.

## 5. Trust boundary

The finite-field linear algebra and polynomial evaluation are performed by
Magma as an external producer and must be retained as artifacts.  A later
standard-library checker should verify dimensions, candidate-polynomial hashes
and the final zero/nonzero result.

The following remain imported research inputs:

- modularity and level lowering for the two Frey systems;
- the complete local HGM trace-polynomial descriptions;
- the residual-prime superspecial and norm-`8` conditions;
- semilinear Galois descent for rational specializations;
- the cyclotomic untwist and its conductor calculation.

A failed or timed-out producer is unresolved and is never interpreted as a zero
space.
