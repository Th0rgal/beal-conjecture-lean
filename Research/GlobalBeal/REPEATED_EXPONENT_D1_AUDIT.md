# Audit of the `D=1` step in the claimed repeated-exponent proof

## Conclusion

The statement `D=1` may or may not be true, but the displayed proof of
Lemma 5 in arXiv:2509.18275 does not establish it.

The gap occurs before the already-known decomposition-group error.

## 1. The unsupported product-divisibility inference

The proof writes

\[
t=t_1+t_2
\]

and obtains

\[
\beta(t_1)\mid\chi,
\qquad
\beta(t_2)\mid\chi.
\]

It then immediately concludes that

\[
\chi=\beta(t_1)\beta(t_2)\chi'.
\]

This requires

\[
(\beta(t_1),\beta(t_2))=1
\]

or another valuation argument proving that the two divisibilities add.
Neither is supplied.

In ideal terms,

\[
(\beta(t_i))=\mathfrak A^{t_i}.
\]

The conjugates of \(\mathfrak A\) are pairwise coprime, but the supports of
\(t_1\) and \(t_2\) need not be disjoint. Overlapping supports make the
two beta ideals share prime factors.

## 2. Exact failure of the construction at \(p=5\)

Enumerating every conjugate Fueter element for \(p=5\) gives the
coefficient vectors

\[
(0,0,1,1),\quad
(0,1,0,1),\quad
(1,0,1,0),\quad
(1,1,0,0),
\]

with Fermat quotients

\[
1,\quad2,\quad3,\quad4\pmod5.
\]

Every sum of two conjugate Fueter elements lying in the Fermat ideal is

\[
\boxed{N=(1,1,1,1).}
\]

Thus the weight-two construction in Fact 2 gives only the group-ring norm.

For \(t=N\),

\[
\alpha^{2tp}
=
\alpha^{2pN}
=
N_{K/\mathbf Q}(\alpha)^{2p}
\in\mathbf Z.
\]

The proof's final assertion that this quantity is not rational is therefore
false for the only element produced at \(p=5\).

## 3. Exact overlap at \(p=7\)

At \(p=7\), there are Fueter elements \(\psi\) with Fermat quotient zero.
Then

\[
t=2\psi\in J_1
\]

is non-norm, but its decomposition into two positive relative-weight-one
elements is uniquely

\[
t=\psi+\psi.
\]

Consequently,

\[
\beta(t_1)=\beta(t_2).
\]

The proof's inference is then precisely the invalid implication

\[
\beta(\psi)\mid\chi
\quad\Longrightarrow\quad
\beta(\psi)^2\mid\chi.
\]

## 4. Impact

The later total-splitting claim was already invalid because relative
splitting in a compositum gives an order-divisibility condition, not
rational total splitting.

This audit shows that the earlier `D=1` input also remains unproved.
Therefore the new two-base multiplicative-order contraction has the
following exact trust boundary:

* its graph, finite-out-degree, subgroup bound, and zero-density theorem
  are unconditional;
* the claim that a repeated-prime Diophantine solution lies on that graph
  requires a new proof of `D=1` or another route to the relative-splitting
  conclusion.

The next decisive repeated-core theorem is no longer vague: replace Lemma 5
with a valid argument controlling the common rational congruence ideal
without multiplying non-coprime beta divisors.
