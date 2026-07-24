# Fixed-`7` ray-character sieve and Hasse--Witt dichotomy

## Scope

Let

```text
A^3+B^5=C^7, gcd(A,B,C)=1,
```

and attach the Pacetti--Villagra genus-`2` representation in the orientation

```text
B^5+(-C)^7+A^3=0
```

over `K5=Q(sqrt(5))`, with residual characteristic `7` and parameter
`t=-B^5/A^3`.

This note separates the replayed finite arithmetic from the imported local and
finite-flat statements. The resulting dichotomy is conditional on the latter
and is not a proof of the signature.

## 1. Reducible-character space

The imported reducibility analysis gives

```text
rho_bar_7^ss = psi*chi_7 direct_sum psi^(-1),
```

where `psi` has conductor dividing

```text
3*(sqrt(5))*infinity_1*infinity_2
```

and lies in a ray class group isomorphic to `C4 x C2`. Write its characters as

```text
psi_(a,b)(u,v)=i^(a*u)*(-1)^(b*v),
```

with `a mod 4`, `b mod 2`, and `i^2=-1` in `F_49`.

The finite checker recomputes the ray coordinates of the selected prime ideals:

```text
11: (3,1),(1,1)
13: (1,0)
17: (3,0)
19: (1,0),(1,0)
71: (1,1),(3,1)
 7: (3,0).
```

## 2. Candidate-polynomial sieve modulo `7`

For a prime ideal of norm `N`, reducibility predicts

```text
z=N*psi+psi^(-1).
```

At the zero and infinity degenerations, the pinned elimination code uses

```text
w=z^2-2*N.
```

The checker evaluates every pinned candidate polynomial at these values. The
selected rows are:

```text
ell=17, psi= i: (4+5i,6,6,4)
ell=17, psi=-i: (4+2i,6,6,4)
ell=19, psi= 1: (5,1,5,0)
ell=19, psi=-1: (1,1,5,0)
ell=11, psi= 1: (5,3,4,0)
ell=71, psi=-1: (1,5,4,0)
ell=13, psi=-1: (2,4,0,0).
```

The four entries correspond to generic, zero, infinity, and multiplicative
cases. A nonzero entry excludes that case.

Prime `17` excludes every order-`4` ray character. Prime `19` then forces the
multiplicative case and the value `psi=-1`.

## 3. Nodal splitting character

At `t=1`, the defining polynomial factors exactly as

```text
5*x^6-12*x^5+10*x^3+1
  =(x^2-x-1)^2*(5*x^2-2*x+1).
```

For `phi=(1+sqrt(5))/2`, the common nodal square class is

```text
d=3*(phi+2)=3*sqrt(5)*phi=6+3*phi,
Norm(d)=45.
```

Its reductions at the two primes over `11` are `7,8`, both nonsquares, and at
the two primes over `19` are `2,13`, both nonsquares. The corresponding ray
character has coordinates

```text
eta=(2,0).
```

The multiplicative signs at `19` and `11` isolate this character uniquely.
Then the rows at `71` and `13` force

```text
71 | C,
13 | A*C.
```

Together with the imported exact prime-`2` obstruction

```text
6084=2^2*3^2*13^2,
```

reducibility forces, before using the residual prime,

```text
2*19*71 | C,
13 | A*C.
```

## 4. Hasse--Witt calculation at `7`

For

```text
f_t(x)=5*x^6-12*x^5+10*t*x^3+t^2
```

in characteristic `7`, the checker expands `f_t(x)^3` and obtains

```text
W(t) = [[0,-t^4],[t,0]],
W(t)^2 = -t^5*I.
```

Since `7` is inert in `Q(sqrt(5))` and `Norm(d)=45=3 mod 7` is a nonsquare,

```text
eta(Frob_7)=-1.
```

Under the imported interpretation of an unramified `eta` factor in the ordinary
finite-flat representation, the generic case would force

```text
-t^5=-1,
```

hence `t^5=1`. The fifth-power map is bijective on `F_7^*`, so `t=1`, which is
the `7|C` degeneration.

For the two scaled non-generic models the checker obtains

```text
t=0 model: y^2=1+2*x^5,
W_0=[[0,-1],[0,0]], W_0^2=0;

infinity model: y^2=5*x^6+3*x^3+1,
W_infinity=0.
```

Both have stable Hasse--Witt rank zero.

## 5. Imported step and conditional conclusion

The finite computation alone does not turn those matrices into a contradiction
with reducibility. The required imported chain is:

1. the residual representation is finite flat at the prime over `7`;
2. because the ramification index is `e=1<7-1`, finite-flat full faithfulness
   promotes the unramified `eta` Jordan--Hölder factor to an etale subquotient;
3. the ordinary Hasse--Witt eigenvalue or the stable-rank-zero special fiber
   detects the impossibility of that subquotient in the three non-`C` branches.

Subject to that chain,

```text
rho_bar_7 reducible => 7 | C.
```

For `7|C`, primitivity gives `7` not dividing `A*B`. The independent mod-`5`
plus HGM has an imported prime-to-`5` dihedral supercuspidal local type of order
`4` or `28` at `7`, so its reduction remains absolutely irreducible. Therefore,
again subject to the cited local-type transfer,

```text
the fixed-7 and independent mod-5 representations cannot both be reducible.
```

## Replay

```bash
python3 scripts/check_signature_357_ray_hasse.py --self-test
python3 scripts/check_signature_357_ray_hasse.py
```

The machine-readable source pins, products, ray coordinates, matrices, imported
lemmas, and conditional conclusions are in
`Research/Signature357/ray_hasse_dichotomy.json`.
