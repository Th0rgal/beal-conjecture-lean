# Global Beal exponent reduction: corrected canonical core

## Status

This note does **not** prove the Beal conjecture. It proves an unconditional
elementary reduction of arbitrary exponents and uses the published
Ratcliffe--Grechuk survey only to identify which low canonical signatures are
already covered in the literature.

A previous version made the stronger claim that every primitive Beal
counterexample has three odd-prime exponents. That was incorrect: the
canonical reduction also leaves signatures containing exponent `4`.

The corrected conclusion is

\[
\boxed{
\begin{array}{l}
\text{every primitive Beal counterexample reduces either to}\\
\text{an all-odd-prime signature, or to }(4,p,q)\text{ with odd primes }p,q.
\end{array}}
\]

After removing the cases with repeated exponents that are already covered by
FLT or surveyed families, the genuinely open canonical cores are:

\[
\boxed{
(4,p,q),\qquad (p,p,q),\qquad (p,q,r),
}
\]

where the displayed primes are distinct whenever appropriate.

## 1. Unconditional elementary reduction

Suppose

\[
A^x+B^y=C^z,
\qquad A,B,C>0,
\qquad \gcd(A,B,C)=1,
\qquad x,y,z\ge3.
\]

For every integer \(n\ge3\), choose a factorization

\[
n=ke
\]

where \(e=4\) or \(e\) is an odd prime:

1. if \(4\mid n\), take \(e=4\);
2. otherwise, if \(n\) is odd, choose an odd prime divisor of \(n\);
3. otherwise write \(n=2m\), where \(m\ge3\) is odd, and choose an odd prime
   divisor of \(m\).

Absorb the complementary factor into the base. For example,

\[
A^x=(A^k)^e.
\]

Raising pairwise-coprime bases to positive powers preserves pairwise
coprimality. Hence it is enough, unconditionally, to solve signatures whose
exponents lie in

\[
\{4\}\cup\{\text{odd primes}\}.
\]

This bridge is formalized in

```text
BealUnified/ExponentReduction.lean
```

and culminates in

```text
bealConjecture_of_canonical_impossibility
```

which proves Beal from the impossibility of every canonical signature.

## 2. Why exponent `4` cannot be discarded

Replacing a composite exponent by a divisor produces a new base with an
additional perfect-power constraint. For example,

\[
A^4+B^p=C^q
\]

becomes

\[
X^2+B^p=C^q,
\qquad X=A^2.
\]

A theorem solving the unrestricted parent signature \((2,p,q)\) certainly
solves this square-restricted subcase. But the converse is not true, and one
cannot infer that all canonical exponent-4 signatures are covered merely from
a classification of minimal prime-or-special signatures.

The one-\(4\) core therefore remains:

\[
\boxed{(4,p,q)}
\]

up to term placement. If \(p=q\), reduction to \((2,p,p)\) places the case in
the solved repeated-prime family. The unresolved one-\(4\) core has
\(p\ne q\).

Cases with two or three exponent-4 entries reduce to surveyed special or
spherical signatures, or directly to FLT at exponent 4.

## 3. Correct finite boundary after the candidate `(3,5,7)` result

Assume only for this subsection that the candidate conditional proof of the
primitive signature \((3,5,7)\) is correct.

Enumerating sorted canonical triples—each entry either `4` or an odd prime—of
sum below \(16\) gives exactly

\[
\begin{aligned}
&(3,3,3),(3,3,4),(3,3,5),(3,4,4),(3,4,5),\\
&(4,4,4),(3,3,7),(3,5,5),(4,4,5),(3,4,7),\\
&(4,5,5),(5,5,5),(3,5,7),(4,4,7).
\end{aligned}
\]

These are covered by FLT, the surveyed small/repeated-exponent families, or the
candidate \((3,5,7)\) theorem.

At total exponent sum \(16\), there is a unique canonical triple:

\[
\boxed{(4,5,7).}
\]

It is the square-restricted subcase

\[
X^2+B^5=C^7,
\qquad X=A^2,
\]

of the parent signature \((2,5,7)\). The Ratcliffe--Grechuk survey identifies
\((2,5,7)\) as the smallest currently open Fermat--Catalan signature. Thus the
correct next canonical Beal target after \((3,5,7)\) is

\[
\boxed{(4,5,7),}
\]

not \((3,5,11)\).

This boundary computation is replayed by

```bash
python3 scripts/check_global_beal_prime_exponent_reduction.py --self-test
python3 scripts/check_global_beal_prime_exponent_reduction.py
```

## 4. Exact global frontier

The canonical reduction leaves three infinite cores.

### Square-constrained even core

\[
(4,p,q),
\qquad p\ne q\text{ odd primes}.
\]

This is a perfect-square-restricted subfamily of \((2,p,q)\), not automatically
settled by prime-only bookkeeping.

### Repeated odd-prime core

\[
(p,p,q),
\qquad p\ne q.
\]

Several infinite subfamilies are known, but no validated theorem in the current
repository covers every pair.

### Three-distinct-prime core

\[
(p,q,r),
\qquad p<q<r.
\]

This is the principal multi-Frey/hypergeometric frontier.

A proof of isolated signatures cannot terminate the conjecture. A complete
proof must cover all three infinite cores, or establish a uniform theorem that
reduces them to a finite, explicitly verified boundary.

## 5. Trust boundary

The elementary factorization and power-absorption bridge are Lean-checked. The
low-signature coverage statements are literature-assisted and use:

- A. Ratcliffe and B. Grechuk,
  *Generalized Fermat equation: a survey of solved cases*,
  [arXiv:2412.11933v2](https://arxiv.org/abs/2412.11933), published in
  *Expositiones Mathematicae* 43 (2025), 125688.

The candidate \((3,5,7)\) theorem is not treated here as a peer-reviewed or
trusted Lean theorem.
