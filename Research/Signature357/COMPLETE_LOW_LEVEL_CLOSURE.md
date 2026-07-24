# Complete closure of the LMFDB low-level `(3,5,7)` frontier

## Status

This note records a literature-assisted finite reduction. It does **not** prove
the full signature `(3,5,7)` and is not imported by `BealUnified.Trusted`.

The conclusion is exact:

```text
no hypothetical primitive solution A^3+B^5=C^7
can lower on the independent mod-5 side to a Hilbert-newform level
of norm at most 2059 over K7=Q(zeta_7)^+.
```

Equivalently, the complete cubic-Hilbert-newform range currently covered by
LMFDB is now empty for this modular program.

## 1. Frontier before the final auxiliary-prime argument

The pinned LMFDB inventory contains fourteen packets at the eight candidate
level norms

```text
1, 7, 27, 49, 189, 343, 729, 1323.
```

The residual norm-8 congruence first leaves four packets. The global CM-support
argument removes the two CM packets, and the even-branch 7-unit local-type
argument removes `3.3.49.1-1323.1-a`.

The schema-3 filter therefore has only one preclosure packet:

```text
3.3.49.1-189.1-a.
```

It lies in the Dahmen--Siksek even branch with `7 | C`. The packet is rational
and is the base change of the classical conductor-21 isogeny class over `Q`.

## 2. Complete mod-5 local trace calculation at 41

Let

```text
u=C^7/A^3.
```

At the rational prime `41`, the packet has base trace

```text
a_41=2.
```

The prime has residue degree one in `K7`, while the residue degree doubles in
`F21=Q(zeta_21)`. Hence the trace over the full cyclotomic field is

```text
a_F = a_41^2 - 2*41 = -78 = 2 mod 5.
```

The producer

```bash
python3 scripts/produce_signature_357_mod5_complete_local.py
```

uses the pinned Pacetti--Villagra Torcomian PARI/GP implementation to compute all
four local regimes for the independent mod-5 HGM:

```text
generic u not in {0,1};
u=0;
u=infinity;
u=1, represented by the multiplicative target +/- (N+1).
```

At `41`, evaluation at `-78` modulo `5` gives:

```text
39 generic candidate polynomials: none vanish, product = 4 mod 5;
7 zero candidate polynomials:     none vanish, product = 4 mod 5;
3 infinity candidate polynomials: none vanish, product = 4 mod 5.
```

The multiplicative targets are

```text
+/- (41+1) = {2,3} mod 5,
```

and the packet trace is `2 mod 5`. Therefore the only possible reduction regime
is

```text
u=1 mod 41.
```

Since

```text
u-1=B^5/A^3,
```

primitivity gives

```text
41 | B,
41 does not divide A*C.
```

## 3. Coupled fixed-7 contradiction

For the first Frey representation, use

```text
t7=-B^5/A^3.
```

The preceding conclusion forces

```text
t7=0 mod 41.
```

In the Dahmen--Siksek even branch, the fixed-7 level is `(2,2)`. Its exact
fixed-7 computation leaves only CM packets `3,9,12`, while the specialization
has special local type. Under residual irreducibility this is impossible, so the
source chain forces the fixed-7 residual representation to be reducible.

At the split prime of norm `41` in `Q(sqrt(5))`, reducibility gives the base trace

```text
N+1 = 42 = 0 mod 7.
```

The residue degree doubles in `Q(zeta_15)/Q(sqrt(5))`, so the transformed target
is

```text
(N+1)^2-2*N = N^2+1 = 2 mod 7.
```

The pinned `t7=0` candidate polynomials at `41` are

```text
x^2-4*x-5116
x^2+61*x-1601
x^2-19*x-361
x^2+101*x+2399
x^2-139*x+4679.
```

At `x=2 mod 7`, their evaluations are

```text
4, 2, 4, 1, 2,
```

with product `1 mod 7`. None can supply the reducible trace. This contradicts
the even-branch reducibility conclusion.

Therefore `3.3.49.1-189.1-a` cannot arise.

## 4. Certified conclusion

Combining the schema-3 filter and the prime-41 coupled obstruction gives

```text
14 complete-range packets
  -> 4 after the norm-8 congruence
  -> 2 after global non-CM filtering
  -> 1 after the 7-unit local-type filter
  -> 0 after the coupled prime-41 obstruction.
```

Run:

```bash
python3 scripts/check_signature_357_low_level_closure.py --self-test
python3 scripts/check_signature_357_low_level_closure.py
```

The manifest is

```text
Research/Signature357/low_level_complete_closure.json
```

with digest

```text
8c84d73b5fd8c242ffe265a49615794c436ea725d33b1f312a74454af387dde4.
```

The checker replays all polynomial evaluations with Python's standard library,
binds the result to the pinned schema-3 low-level filter, and rejects mutations
that reintroduce either a mod-5 local regime or the fixed-7 reducible trace.

## 5. Remaining frontier

The optimized global level bound is still

```text
p3^3*p7^3.
```

The eight candidate norms above the documented LMFDB completeness bound are

```text
5103, 9261, 19683, 35721, 137781, 250047, 964467, 6751269.
```

Those spaces remain to be computed or removed by sharper local-conductor
arguments. The present theorem closes the entire publicly complete low-level
range; it does not assert that any of the eight higher spaces is empty.

## Trust boundary

The finite polynomial arithmetic is independently replayed. The following
implications remain explicit literature inputs:

1. the Dahmen--Siksek branch theorem;
2. the level-`(2,2)` CM/special-local-type reduction on the fixed-7 side;
3. the reducible Frobenius trace criterion;
4. the degree-doubling trace transformation.

No part of this certificate is silently promoted into `BealUnified.Trusted`.
