# Beal frontier addendum — fixed `(3,5,7)` branches and repeated-left target

## Status

This addendum records primary-source checks and exact research certificates added
after the main 2026-07-24 frontier audit. It changes no trusted Lean theorem and
does not claim a proof of `(3,5,7)` or of Beal.

## Dahmen--Siksek branch theorem for `(3,5,7)`

Dahmen and Siksek's July-2024 working paper, *On the generalized Fermat equation
x^5+y^3=z^7*, proves that every nontrivial primitive solution satisfies one of

```text
30 | z and 7 does not divide x*y,
```

or

```text
z odd, 3 does not divide x*y*z, 5 does not divide y*z, and 7 | y.
```

Under `(x,y,z)=(B,A,C)`, every primitive solution of

```text
A^3+B^5=C^7
```

therefore lies in the disjoint branches:

```text
even: 30 | C and 7 does not divide A*B;
odd:  C odd, 3 does not divide A*B*C, 5 does not divide A*C, and 7 | A.
```

This is a literature theorem and should eventually be represented by an exact
source-audited theorem interface, not by an axiom hidden in `Trusted`.

## Even branch: one explicit irreducibility problem

Use the Pacetti--Villagra orientation `(a,b,c)=(B,-C,A)` in
`a^5+b^7+c^3=0`. The even branch has `3 | b` and `5 | b`, forcing conductor
exponents `(2,2)` in their Hilbert-modular lowering.

The public fixed-`7` calculation leaves only packets `3,9,12` at this level. The
paper identifies these as CM packets; its special-local-type argument excludes a
CM congruence when the residual representation is irreducible. Hence the audited
conditional conclusion is:

```text
primitive solution in the even branch
  => the associated mod-7 Frey representation is reducible.
```

This is not yet an exclusion. The remaining target is to prove mod-`7`
irreducibility in this branch, or classify and eliminate all reducible cases.

## Odd branch: exact residual-prime local obstruction

Pacetti--Villagra's Frey model can be written

```text
y^2+y*(x^3+B)=2*B*x^3+3*A*x+B^2.
```

Completing the square with `Y=2*y+x^3+B` gives

```text
Y^2=x^6+10*B*x^3+12*A*x+5*B^2.
```

The odd branch has `7 | A`, so reduction at `7` is

```text
Y^2=x^6+3*B*x^3+5*B^2,
```

with `B != 0 mod 7`. The independent standard-library checker in the stacked
signature-certificate PR verifies for every `B in F_7^*`:

- the sextic is squarefree;
- the Cartier--Manin matrix is zero;
- `#C(F_7)=8`;
- `#C(F_49)=22` for `B=+/-2`, and `64` otherwise;
- the real-multiplication constituent trace at the unique prime over `7` is
  `14` for `B=+/-2`, and `-7` otherwise.

Thus every odd-branch specialization satisfies the residual-prime condition

```text
a_p == 0 mod p.
```

This nonordinary/superspecial local condition was not used by the published
auxiliary-prime resultant elimination. Filtering the finite fixed-`7` survivor
lists by the correct local-global compatibility theorem is now the most direct
computational target.

## Repeated-left frontier

The elementary cyclotomic split under audit shows that

```text
X^p+Y^p=C^n, p odd prime, n>=3, gcd(X,Y)=1
```

forces at least two distinct prime divisors of `C`, and a prime `q | C` with

```text
q^n | Phi_(2p)(X,Y),
q == 1 mod 2*p.
```

Combining this with the unit-coefficient solved-signature inventory in the
current survey leaves `(5,5,11)` as the first unresolved repeated-left prime
signature by exponent sum. The cases `(p,p,2)`, `(p,p,3)`, `(p,p,p)`, the
surveyed `(3,3,r)` range, `(5,5,7)`, `(5,5,19)`, and `(7,7,5)` are already
covered by known results at the literature level.

The current version `v4` of Bartolome--Mihailescu, arXiv `2108.08572`, states the
cofactor theorem only with equal right exponent `p`:

```text
(x^p+y^p)/(x+y)=p^e*z^p.
```

It must not be cited as a theorem for a distinct exponent `q`. A specific audit
of superseded proof text should remain separate from the current theorem-status
record.

## Updated priority

1. Prove residual mod-`7` irreducibility in the even `(3,5,7)` branch.
2. Complete the two flagged Hilbert-newform reruns and apply the exact prime-`7`
   local filter in the odd branch.
3. Continue the certified `(3,4,5)` pipeline, with an explicit source-index map
   before attaching local/Selmer results to reconstructed Edwards forms.
4. Use `(5,5,11)` as the first fixed repeated-left modular/cyclotomic research
   target after the elementary split is formalized.
