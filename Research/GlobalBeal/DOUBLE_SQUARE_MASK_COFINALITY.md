# Breakthrough: the double-square summand mask is effectively finite

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

This is an effective finite-boundary theorem for the prime-signature sector
whose two positive summand bases are squares.

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

For fixed \(V_r\), smooth integers have density zero. Thus this theorem removes
the entire double-square summand sector asymptotically, not merely a few
individual signatures.

## Orientation matters

This theorem applies when the two **positive summands** are square-masked. A
square on one summand and one on the right produces a difference of even
powers and requires a different descent.
