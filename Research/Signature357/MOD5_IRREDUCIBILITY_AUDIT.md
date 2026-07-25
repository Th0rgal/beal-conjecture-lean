# Mod-5 irreducibility audit and prime-2 obstruction for `(3,5,7)`

## Status

This note records two independently replayable arithmetic reductions for the
plus hypergeometric representation of residual characteristic `5` attached to

```text
A^3 + B^5 = C^7.
```

Neither reduction is entered in `BealUnified.Trusted`. Both depend on explicitly
listed representation-theoretic inputs from the hypergeometric-motive and
conductor papers.

The two results are:

1. a repaired `20/21` local irreducibility sieve in the unit branch, using parity
   of the Swan conductor rather than the size of one coefficient field;
2. a new global prime-`2` character obstruction proving irreducibility when
   `C` is odd and `A` is even.

## 1. Correction to the coefficient-field argument

A reducible residual representation is *absolutely* reducible over
`overline(F)_5`. Its diagonal characters need not take values in `F_125^*`.
Therefore the observations

```text
3 does not divide |F_125^*| and 7 does not divide |F_125^*|
```

do not by themselves exclude one-dimensional wild inertia characters after
extending the coefficient field.

The correct replacement is a Swan-parity argument.

Let `r` be `3` or `7`. If a two-dimensional representation in characteristic
`5` is absolutely reducible and its determinant is unramified on wild inertia,
then, after restriction to wild inertia, it is a direct sum

```text
chi + chi^(-1).
```

The finite wild quotient has order prime to `5`, so Maschke semisimplicity
applies. The two characters have equal Swan conductor, hence the
two-dimensional Swan conductor is even.

Consequently, a source computation giving Swan conductor exactly `1` implies
absolute irreducibility.

The printed statement of Proposition 6.10 in arXiv `2503.21568` contains an
internal conflict: its irreducible branch says both `0` when `r` does not divide
`Delta` and `1` when `v_r(Delta)=0`. The preceding curve conductor formula and
the proof give the latter value. The certificate records this discrepancy
explicitly.

## 2. Exact `20/21` unit-branch sieve

Use the ordering

```text
(-C)^7 + B^5 + A^3 = 0
```

and set

```text
t = A^3 * C^(-7).
```

Assume

```text
3 does not divide A*B*C and 7 does not divide A*B*C.
```

At `7`, the local polynomial is

```text
P_7,t(u) = u^7 - 7*u^5 + 14*u^3 - 7*u + 4*t - 2.
```

Among the `35` admissible classes modulo `49`, it has a root modulo `49`
exactly for

```text
t = 3,13,25,37,47 mod 49.
```

At `3`, the local polynomial is

```text
P_3,t(u) = u^3 - 3*u + 2 - 4*t^(-1).
```

Among the admissible classes `2,5,8 mod 9`, it has a root modulo `9` exactly
when

```text
t = 2 mod 9.
```

The simultaneous exceptional classes are therefore

```text
t = 47,74,101,209,380 mod 441.
```

There are `105` admissible unit classes modulo `441`; only five remain. Using
the Swan-parity lemma and the corrected source conductor value gives:

```text
outside those five classes, the mod-5 representation is absolutely irreducible.
```

Run:

```bash
python3 scripts/check_signature_357_mod5_local.py --self-test
python3 scripts/check_signature_357_mod5_local.py
```

The checker enumerates every root modulo `9` and `49`, recomputes the CRT
intersection, and rejects the contradictory printed conductor branch.

## 3. New prime-2 obstruction

Now assume instead

```text
C odd and A even.
```

Primitivity forces `B` odd. For the same plus representation, the usual
parameter is

```text
t_0 = C^7 / A^3.
```

The inversion isomorphism for hypergeometric motives replaces it by

```text
t_0^(-1) = A^3 / C^7
```

and swaps the two parameter pairs. At `2` this inverse parameter has valuation

```text
3*v_2(A)
```

and odd unit part, hence unit reduction `1`.

The trace formula is only proved over the full cyclotomic field

```text
F = Q(zeta_21).
```

The residue field at `2` is `F_64`. With parameters

```text
((1/7,-1/7),(1/3,-1/3))
```

formula (30) uses the two ordinary Jacobi sums with character exponents

```text
(-4,-10) and (-14,10).
```

In the exact model

```text
F_64 = F_2[x]/(x^6+x+1),
```

both sums equal the rational integer `8`.

The Jacobi-motive factor is not optional. Definition 2.3 gives

```text
J_0 = -g(-3)g(3)g(7)g(-7)g(0)/(g(10)g(-10)) = 64,
```

using `g(k)g(-k)=64` and `g(0)=-1` in characteristic `2`. Thus the normalized
trace is

```text
-(8+8)/64 = -1/4.
```

The weight-`2` Tate normalization used in the modular comparison multiplies by
the residue-field norm `64`, giving the integral trace

```text
a_2 = -16 = 4 mod 5.
```

### Global character contradiction

Let

```text
K_7 = Q(zeta_7)^+.
```

The prime `5` is inert in `K_7`. Put

```text
theta = zeta_7 + zeta_7^(-1).
```

Modulo `5`, `theta` has order `31`. The finite-flat signature of a reducible
rank-one constituent is a vector in `{0,1}^3`. Unit reciprocity with the
away-`5` inertia-killing exponent

```text
lcm(12,28)=84
```

allows only the parallel signatures

```text
(0,0,0) and (1,1,1).
```

After exchanging the two diagonal characters, choose a constituent `lambda`
with signature `(0,0,0)`. Then `lambda^84` is unramified everywhere. The
discriminant of `K_7` is `49`, and its Minkowski bound is

```text
(3!/3^3)*sqrt(49) = 42/27 < 2,
```

so `K_7` has class number one and

```text
lambda^84 = 1.
```

The prime over `2` in `K_7` has norm `8`. Its residue degree in `F/K_7` is `2`.
Set

```text
v = lambda(Frob_2)^2.
```

The cyclotomic determinant over `F` is `8^2 = 4 mod 5`; reducibility and the
certified trace give

```text
v + 4*v^(-1) = 4.
```

Hence `(v-2)^2=0` and `v=2`. But `lambda^84=1` requires

```text
v^42=1,
```

whereas

```text
2^42 = 4 mod 5.
```

This is a contradiction.

Therefore, subject only to the explicitly imported finite-flat and local-global
compatibility statements,

```text
C odd and A even
  => the plus mod-5 representation is absolutely irreducible.
```

Run:

```bash
python3 scripts/check_signature_357_mod5_prime2.py --self-test
python3 scripts/check_signature_357_mod5_prime2.py
```

The checker independently reconstructs `F_64`, both Jacobi sums, the
Jacobi-motive factor, the `F_125` unit calculation, the finite-flat signature
enumeration, the Minkowski bound, and the final Frobenius contradiction.

## 4. Consequence for the Dahmen--Siksek odd branch

The odd branch has

```text
C odd and 7 divides A.
```

The direct fixed-`7` character certificate proves the mod-`7` representation
irreducible, conditional on its standard finite-flat constituent lemma.

The new prime-`2` certificate adds:

```text
if A is even, the independent mod-5 representation is also absolutely irreducible.
```

If `A` is odd, then `B` is even. At `2` this is the level-lowering `t_0=1`
case; its four possible reducible Frobenius character values all have orders
dividing `84`, so the same prime-`2` character argument does not close that
parity branch.

The remaining open sub-branch is consequently sharper:

```text
Dahmen--Siksek odd branch, A odd, B even,
with the fixed-7 survivor and mod-5 automorphic spaces still to be cross-filtered.
```

## 5. Two-Frey coupling

The two hypergeometric parameters satisfy

```text
t_5 + t_7 = 1.
```

A proof-grade multi-Frey computation should therefore compare joint trace pairs

```text
(trace rho_5(t), trace rho_7(1-t))
```

rather than intersecting two marginal trace sets. At an auxiliary prime this
uses at most `ell-2` joint parameter values instead of up to `(ell-2)^2`
independent pairs.

The prime-`2` theorem supplies absolute irreducibility on one full parity half
of the odd branch, making such a joint elimination legitimate there.
