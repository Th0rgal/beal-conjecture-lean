# Cross-side square masks: synchronized cyclotomic descent

Consider the mask not covered by the square-square summand theorem:

\[
X^{2p}+Y^q=Z^{2r},
\]

with \(p,q,r\) odd primes.

Set

\[
U=Z^r-X^p,\qquad V=Z^r+X^p.
\]

Then

\[
UV=Y^q,\qquad
V-U=2X^p,\qquad
V+U=2Z^r,
\]

and

\[
\gcd(U,V)\in\{1,2\}.
\]

## Odd \(Y\): two synchronized cyclotomic powers

If \(Y\) is odd, then \(X,Z\) have opposite parity, so \(\gcd(U,V)=1\).
There are coprime odd integers \(u<v\) with

\[
U=u^q,\qquad V=v^q.
\]

Hence

\[
v^q-u^q=2X^p,
\qquad
v^q+u^q=2Z^r.
\]

Factor both sides:

\[
v^q-u^q=(v-u)\Phi_q(v,u),
\]

\[
v^q+u^q=(v+u)\Phi_{2q}(v,u).
\]

The relevant gcds are each \(1\) or \(q\). Therefore:

- either
  \[
  v-u=2a^p,\qquad \Phi_q(v,u)=b^p,
  \]
  or
  \[
  v-u=2q^{ph-1}a^p,\qquad \Phi_q(v,u)=qb^p;
  \]
- independently, either
  \[
  v+u=2c^r,\qquad \Phi_{2q}(v,u)=d^r,
  \]
  or
  \[
  v+u=2q^{rk-1}c^r,\qquad \Phi_{2q}(v,u)=qd^r.
  \]

Since \(q\) cannot divide both \(v-u\) and \(v+u\), at least one of these two
cyclotomic decompositions is completely pure.

This is an exact synchronized multi-Frey input.

## Even \(Y\): dyadic normal form

If \(Y\) is even, then \(X,Z\) are both odd and \(\gcd(U,V)=2\). Writing
\(k=v_2(Y)\), there are coprime odd \(u,v\) and positive
\(\alpha,\beta\) such that

\[
U=2^\alpha u^q,\qquad
V=2^\beta v^q,
\]

\[
\min(\alpha,\beta)=1,\qquad
\alpha+\beta=qk.
\]

This branch becomes a coefficient-\(2\) coupled perfect-power problem.

## Strategic consequence

The square-mask program now separates into three modules:

1. **double-square summand masks:** effective finite boundary via Hilbert
   modular forms and \(S\)-units;
2. **cross-side double masks:** synchronized plus/minus cyclotomic multi-Frey
   descent;
3. **one-square masks:** asymmetric Frey/HGM systems, beginning with
   \((4,5,7)\).
