# Global breakthrough: an explicit positive-density region of the full Beal exponent lattice is empty

Consider the ordered primitive positive Beal equation

\[
A^p+B^q=C^r,\qquad p,q,r>2.
\]

Define two subsets of the ordered exponent lattice.

## 1. The common-divisor cone

If

\[
g=\gcd(p,q,r)>2,
\]

then putting

\[
X=A^{p/g},\qquad Y=B^{q/g},\qquad Z=C^{r/g}
\]

gives

\[
X^g+Y^g=Z^g,
\]

contradicting Fermat's Last Theorem.

The natural density of this cone is

\[
1-\frac1{\zeta(3)}-\frac1{2^3\zeta(3)}
=
1-\frac9{8\zeta(3)}.
\]

## 2. Complete-classification cones

Use the complete primitive integer classifications for exponent multisets

\[
\{2,3,d\},
\qquad d\in\{6,7,8,9,10,15\}.
\]

For \(d=7,8,9,15\), every permutation of the divisibility pattern
\((2,3,d)\) is admitted. For \(d=6,10\), this theorem uses the two orientations
directly supplied by the complete classifications:

- \(d\) on the right;
- exponent \(2\) on the right.

Whenever the exponent-2 coordinate occurs in a sign-compatible classified
exception, it has a prime divisor of valuation exactly one. But in a Beal
equation, an exponent divisible by \(2\) is at least \(4\), so that coordinate
would have to be a proper power. This eliminates every such divisibility cone.

The union of these periodic classification cones has period \(2520\) and exact
density

\[
\frac{2338961}{9261000}
\approx 0.2525603067.
\]

## 3. Exact union density

The periodic cones overlap the common-divisor cone. An exact Möbius calculation,
separating \(\gcd=1\) and \(\gcd=2\), gives

\[
\delta\!\left(
T\cap\{\gcd(p,q,r)\in\{1,2\}\}
\right)
=
\frac{40601}{160797\,\zeta(3)}.
\]

Therefore the explicit excluded union has natural density

\[
\begin{aligned}
\delta
&=
1-\frac9{8\zeta(3)}
+\frac{40601}{160797\,\zeta(3)}\\[1mm]
&=
\boxed{
1-\frac{1122365}{1286376\,\zeta(3)}
}\\[1mm]
&\approx
\boxed{0.2741595628}.
\end{aligned}
\]

Thus:

\[
\boxed{
\text{at least }27.4159\%\text{ of the entire ordered Beal exponent lattice}
\text{ is unconditionally empty.}
}
\]

This percentage concerns a rigorously defined subset of all ordered triples,
not a one-dimensional family and not a bounded search.

## 4. Replay

The retained replay script is:

```bash
python3 scripts/check_global_beal_density.py
```

It reconstructs the period-2520 residue set, verifies every displayed
exceptional equation and valuation-one witness, redoes the complete finite
Möbius calculation, derives the rational coefficient of \(1/\zeta(3)\), and
bounds \(\zeta(3)\) by a finite sum with an integral tail estimate.

An expanded fail-closed certificate and negative-fixture checker were also
produced independently; their certificate SHA-256 is:

```text
6dda4052453b2a8c594946b274617983cb60d3f78edb23be82f7f5b0f00ae5f5
```

The theorem imports Fermat's Last Theorem and the complete published
classifications for the six core exponent multisets. It does not claim that
the complementary \(72.584\%\) contains solutions.
