# Signature `(3,5,7)`: exact `7`-adic Kummer structure in the odd branch

## Status

This note proves an elementary local theorem for every hypothetical primitive
solution in the Dahmen--Siksek odd branch.  It uses only the structure of
`Z_7^*`, Hensel/LTE on principal units, and unique factorization of powers in an
abelian group.  No modularity or database result is used.

It does not by itself prove nonexistence of the odd branch.

## Theorem

Suppose

```text
A^3 + B^5 = C^7,
7 | A,
7 does not divide B*C.
```

Write

```text
a = v_7(A) >= 1.
```

Then there are unique `z in Z_7^*` and `h in 1+7*Z_7` such that

```text
B = z^7,
C = z^5*h,
h^7 = 1 + A^3/B^5.
```

Moreover

```text
v_7(h-1) = 3*a-1,
v_7(C-z^5) = 3*a-1.
```

The normalized difference is a cube:

```text
(C-z^5)/7^(3*a-1) is in (Z_7^*)^3.
```

In particular,

```text
B is an exact seventh power in Z_7^*,
B^6 = 1 mod 49,
B mod 49 is one of 1,18,19,30,31,48.
```

## Proof

Set

```text
r = C^7/B^5 = 1 + A^3/B^5.
```

Since `B` is a unit and `v_7(A)=a`,

```text
v_7(r-1)=3*a.
```

For `n>=1`, the seventh-power map sends the principal-unit group
`1+7^n Z_7` bijectively onto `1+7^(n+1) Z_7`.  This follows either from the
`7`-adic logarithm or directly from Hensel's lemma.  Consequently there is a
unique

```text
h in 1+7^(3*a-1) Z_7
```

with `h^7=r`.  Plus-sign LTE on principal units gives

```text
v_7(h^7-1)=v_7(h-1)+1,
```

so the valuation is exactly `v_7(h-1)=3*a-1`.

Now

```text
(C/h)^7 = B^5.
```

Use the following elementary common-power lemma.  In an abelian group, if
`x^m=y^n` and `gcd(m,n)=1`, then there is `z` with

```text
x=z^n,
y=z^m.
```

Indeed, choose integers `alpha,beta` with `alpha*m+beta*n=1` and take
`z=x^beta*y^alpha`.

Apply this with `(m,n)=(7,5)`, `x=C/h`, and `y=B`.  It gives

```text
C/h=z^5,
B=z^7.
```

The seventh-power map on `Z_7^*` is injective, so `z` is unique.  Since `z` is a
unit,

```text
v_7(C-z^5)=v_7(z^5*(h-1))=3*a-1.
```

For the cube statement, put `Y=z^5` and factor

```text
A^3 = C^7-Y^7 = (C-Y)*Phi_7(C,Y),
Phi_7(C,Y)=C^6+C^5*Y+...+Y^6.
```

LTE gives

```text
v_7(Phi_7(C,Y))=1.
```

Define the units

```text
D=(C-Y)/7^(3*a-1),
E=Phi_7(C,Y)/7.
```

Because `C=Y mod 49`, all seven terms of `Phi_7(C,Y)` are congruent to
`Y^6 mod 49`; hence

```text
E = Y^6 = 1 mod 7.
```

The cube map is an automorphism of `1+7 Z_7`, so `E` is a cube in `Z_7^*`.
The identity

```text
(A/7^a)^3=D*E
```

then forces `D` to be a cube as well.

Finally, reducing `B=z^7` modulo `49` shows that `B` belongs to the image of the
seventh-power map on `(Z/49Z)^*`.  This image is the unique subgroup of order
`6`, equivalently the roots of `X^6-1`.  They are exactly

```text
1,18,19,30,31,48.
```

## Elementary finite-level corollary

The same residue restriction can be obtained without completing to `Z_7`.
Since `7^3 | A^3`,

```text
C^7 = B^5 mod 343.
```

The unit group modulo `343` has order `294`, and `5` is invertible modulo
`294`, with

```text
5*59 = 1 mod 294.
```

Consequently

```text
B=(B^5)^59=(C^59)^7 mod 343,
```

so `B` is already a seventh power modulo `343`.  Its order therefore divides
`294/gcd(294,7)=42`, giving

```text
B^42=1 mod 343.
```

After reduction modulo `49`, the seventh-power image has order `6`, and hence

```text
B^6=1 mod 49.
```

Equivalently, Euler's theorem and `C^7=B^5` also give `B^294=B^210=1`
modulo `343`; their exponent gcd is `42`, which recovers the first displayed
order bound.

## Why this helps

The odd branch is not merely the branch `7|A`: its fifth-power base is forced
into the seventh-power Kummer image at the residual prime.  This removes six
sevenths of the unit classes modulo `49` and supplies an exact normalized-cube
condition for any future `7`-adic descent, etale-algebra search, or local-type
calculation.

The current modular frontier still consists of the two mod-`5` Hilbert levels
`35721` and `964467`; this theorem is an additional local constraint, not a
replacement for the residual Hecke-module computation.

## Replay

```bash
python3 scripts/check_signature_357_odd_7adic_kummer.py --self-test
python3 scripts/check_signature_357_odd_7adic_kummer.py
```
