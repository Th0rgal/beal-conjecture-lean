# Global Beal exponent reduction and the actual infinite frontier

## Status

This note does **not** prove the Beal conjecture. It proves an unconditional
elementary reduction of arbitrary exponents, imports the complete
prime-or-special classification from Ratcliffe--Grechuk, and identifies the
exact global frontier that remains after the candidate signature `(3,5,7)`
closure.

The main conclusion is:

> Every primitive positive Beal counterexample has an exponent triple consisting
> of three odd primes.

This conclusion is literature-assisted at the final step: it uses the survey's
completeness statement for coefficient-one signatures with at least one
composite exponent.

## 1. Elementary canonical reduction

Suppose

\[
A^x+B^y=C^z,\qquad A,B,C>0,\qquad \gcd(A,B,C)=1,
\qquad x,y,z\ge 3.
\]

For every integer \(n\ge3\), choose a factorization

\[
n=k e
\]

where \(e=4\) or \(e\) is an odd prime.

This is always possible:

1. If \(4\mid n\), take \(e=4\) and \(k=n/4\).
2. If \(4\nmid n\) and \(n\) is odd, choose any prime divisor \(e\mid n\).
   Such a divisor is odd.
3. If \(4\nmid n\) and \(n\) is even, write \(n=2m\). Then \(m\ge3\) is odd.
   Choose an odd prime \(e\mid m\), and put \(k=n/e\).

Apply this independently to \(x,y,z\):

\[
x=k_xp,\qquad y=k_yq,\qquad z=k_rr,
\]

with \(p,q,r\in\{4\}\cup\{\text{odd primes}\}\). Set

\[
A_0=A^{k_x},\qquad B_0=B^{k_y},\qquad C_0=C^{k_z}.
\]

Then

\[
A_0^p+B_0^q=C_0^r.
\]

Primitivity is preserved: a prime dividing two of \(A_0,B_0,C_0\) divides the
corresponding two original bases.

Hence it is enough, without any literature input, to solve signatures whose
exponents are \(4\) or odd primes.

## 2. Prime-or-special reduction

Ratcliffe and Grechuk observe that repeatedly replacing a composite exponent by
a proper divisor reduces every hyperbolic generalized-Fermat signature either
to an all-prime signature or to a **special triple**. They classify all special
triples in Table 1.3 of:

- A. Ratcliffe and B. Grechuk,
  *Generalised Fermat equation: a survey of solved cases*,
  [arXiv:2412.11933v2](https://arxiv.org/abs/2412.11933).

The special triples whose minimum exponent is at least \(3\) are exactly

\[
(3,3,4),\quad
(3,3,6),\quad
(3,3,9),\quad
(3,4,4),\quad
(3,4,5),\quad
(4,4,4),
\]

up to permutation.

The same survey compares its solved-signature table with the special-triple
classification and states that the only coefficient-one, non-all-prime
signatures still unresolved are

\[
(2,5,9)\quad\text{and}\quad(2,3,25).
\]

Both have minimum exponent \(2\), so neither lies in the Beal range.

Therefore:

## Global prime-exponent reduction theorem

Assuming the solved-signature references collected in the survey, every
primitive positive Beal counterexample has

\[
\boxed{x,y,z\text{ all odd primes}.}
\]

This is much sharper than the elementary
\(\{4\}\cup\{\text{odd primes}\}\) reduction: every composite-exponent Beal
signature is already covered by existing work.

## 3. What remains after the candidate `(3,5,7)` proof

Order an odd-prime triple as \(p\le q\le r\), allowing sign changes when
permuting an all-odd generalized-Fermat equation.

The prime-exponent frontier separates into:

1. **Equal primes:** \((p,p,p)\), closed by Fermat's Last Theorem.
2. **Two equal primes:** \((p,p,q)\), only partially solved as an infinite
   family.
3. **Three distinct primes:** \((p,q,r)\), the main multi-Frey frontier.

The survey implies that the smallest open Beal signature was `(3,5,7)`.
Assume the candidate conditional proof in `Research/Signature357` is correct.
Then every sorted odd-prime triple of exponent sum below \(19\) is closed:

\[
\begin{aligned}
&(3,3,3),(3,3,5),(3,3,7),(3,3,11),\\
&(3,5,5),(3,5,7),(3,7,7),\\
&(5,5,5),(5,5,7).
\end{aligned}
\]

At sum \(19\),

\[
(3,3,13)
\]

is covered by the solved \((3,3,n)\) range, and

\[
(5,7,7)
\]

is the solved signature \((7,7,5)\). The remaining triple is

\[
\boxed{(3,5,11).}
\]

Thus, conditional on the candidate `(3,5,7)` closure, `(3,5,11)` becomes the
smallest open Beal signature by exponent sum.

This finite-boundary statement is replayed by

```bash
python3 scripts/check_global_beal_prime_exponent_reduction.py --self-test
python3 scripts/check_global_beal_prime_exponent_reduction.py
```

## 4. Why isolated signatures cannot finish Beal

The prime reduction still leaves infinitely many signatures. In particular,
neither of these sets is finite:

\[
\{(p,p,q):p,q\text{ odd primes}\},
\]

\[
\{(p,q,r):p<q<r\text{ odd primes}\}.
\]

Consequently, proving `(3,5,11)`, then `(3,5,13)`, and so on cannot constitute
a terminating proof strategy.

A genuinely global proof needs a cofinal family theorem. One sufficient form
would be the following contractive criterion.

> There is an explicit function \(B(p,q)\) and a finite exceptional set such
> that every primitive solution with sorted odd primes \(p\le q\le r\) satisfies
> \(r\le B(p,q)\), while \(B(p,q)<q\) outside the exceptional set.

Since \(r\ge q\), such a theorem would contradict the existence of every
solution outside a finite boundary. Current asymptotic modular results generally
give a bound only after fixing the other exponents; they do not provide this
contractive uniformity.

## 5. Exact remaining global tasks

Even granting the candidate `(3,5,7)` proof, a full Beal proof still requires:

1. a uniform theorem for the repeated-prime family \((p,p,q)\);
2. a cofinal theorem for three distinct odd primes;
3. a finite treatment of whatever boundary those theorems leave;
4. a formal coverage proof showing that the union of the family theorems
   contains every odd-prime triple.

The present note closes the exponent-reduction bookkeeping. It does not close
either infinite prime core.
