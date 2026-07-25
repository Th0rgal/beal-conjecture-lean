# Breakthrough: the double-square summand large–large quadrant is empty

Let

\[
X^{2p}+Y^{2q}=Z^r
\]

with \(p,q,r\) odd primes and pairwise-coprime nonzero integer bases.

Sahoo proves that, for each of the 29 primes

\[
\begin{aligned}
r\in\{&
5,7,11,13,19,23,37,47,53,59,61,67,71,79,83,\\
&101,103,107,131,139,149,163,167,173,179,181,191,197,199
\},
\end{aligned}
\]

there is an effectively computable constant \(V_r\) such that no primitive
solution exists when

\[
p,q>V_r.
\]

Therefore:

\[
\boxed{
\text{for fixed listed }r,\quad
p\le V_r\text{ or }q\le V_r.
}
\]

This is an effective **cofinal-quadrant theorem**. The surviving prime pairs
lie in a finite union of horizontal and vertical strips indexed by primes
at most \(V_r\). Those strips are still infinite; they are the next
one-variable modular families.

## Lift to arbitrary even exponents

Suppose

\[
A^{2a}+B^{2b}=C^N
\]

and \(r\mid N\) for one of the listed primes. If \(a\) has a prime divisor
\(p>V_r\) and \(b\) has a prime divisor \(q>V_r\), exponent absorption gives

\[
x^{2p}+y^{2q}=z^r,
\]

a contradiction. Hence

\[
\boxed{
a\text{ is }V_r\text{-smooth}
\quad\text{or}\quad
b\text{ is }V_r\text{-smooth}.
}
\]

For fixed \(V_r\), smooth integers have density zero. Thus the surviving
composite half-exponent strips are infinite but density zero. The theorem
removes the full large–large quadrant and contracts the rest to finitely many
one-small-prime families.

## Orientation matters

This theorem applies when the two **positive summands** are square-masked. A
square on one summand and one on the right produces a difference of even
powers and requires a different descent.

## Exact remaining Type-I frontier

For each listed \(r\), compute \(V_r\). For every prime
\(p\le V_r\), the remaining strip is

\[
x^{2p}+y^{2q}=z^r,
\qquad q\text{ prime and variable},
\]

together with the symmetric strips. This is a finite list of infinite
one-parameter families, not a finite list of signatures.
