# Uniform two-base contraction for the repeated-prime Beal core

## Exact status

This note attacks the entire repeated-prime canonical family

\[
x^p+y^p=z^q,\qquad p>3,\quad q>3,\quad p\ne q,
\]

rather than another isolated signature.

It does **not** prove Beal. The multiplicative-order graph and its
zero-density theorem are unconditional. The implication from a
Diophantine solution to membership in that graph remains conditional on
the characteristic-ideal construction through the `D=1` conclusion in
arXiv:2509.18275. The invalid total-splitting inference later in that
preprint is not used.

## 1. Correct relative-splitting consequence

Let

\[
K=\mathbf Q(\zeta_p),\qquad L=K(\zeta_q).
\]

For a rational prime \(r\nmid pq\), put

\[
m=\operatorname{ord}_p(r),\qquad n=\operatorname{ord}_q(r).
\]

A prime of \(K\) above \(r\) has residue field \(\mathbf F_{r^m}\). It
splits completely in \(L/K\) exactly when this residue field already
contains a primitive \(q\)-th root of unity. Hence

\[
q\mid r^m-1,
\]

and therefore

\[
\boxed{\operatorname{ord}_q(r)\mid\operatorname{ord}_p(r).}
\]

This is the correct rational consequence of relative splitting. It is
strictly weaker than the false assertion \(r\equiv1\pmod q\).

## 2. New fourth Stickelberger congruence: the factor \(x-y\)

Take \(t\in J_k\) in the notation of the preprint. Then

\[
\zeta_p^t=1,\qquad t+\bar t=2kN,
\]

where \(N\) is the group-ring norm and the bar denotes complex
conjugation.

Set \(u=1+\zeta_p\). Since

\[
\bar u=1+\zeta_p^{-1}=\zeta_p^{-1}u,
\]

we have

\[
u^{\bar t}=(\bar u)^t=\zeta_p^{-t}u^t=u^t.
\]

Consequently,

\[
(u^t)^2=u^{t+\bar t}=u^{2kN}.
\]

For odd \(p\),

\[
u^N=\prod_{a=1}^{p-1}(1+\zeta_p^a)=\Phi_p(-1)=1.
\]

Therefore

\[
\boxed{(1+\zeta_p)^t=\pm1.}
\]

Now put

\[
\alpha=y+\zeta_p x,\qquad \Psi_t=\alpha^t.
\]

Modulo an odd prime ideal above a divisor of \(x-y\), one has \(x\equiv
y\), and hence

\[
\Psi_t
\equiv
y^{w(t)}(1+\zeta_p)^t
=
\pm y^{k(p-1)}.
\]

The right-hand side is rational. Thus the usual rational-congruence lemma
extends from the factors \(x,y,x+y\) to the odd part of \(x-y\):

\[
\boxed{x-y\mid\Psi_t-\sigma(\Psi_t)}
\]

away from the fixed denominators. This also explains an inconsistency in
the preprint: its later proof already invokes \(x-y\), although the formal
statement lists only \(x,y,x+y\).

## 3. Two guaranteed rational primes

At least one of

\[
x,\qquad y,\qquad x+y
\]

is even. Since \(q\) is odd, removing a \(q\)-power factor does not remove
the prime \(2\). The corrected relative-splitting statement therefore
gives

\[
\boxed{\operatorname{ord}_q(2)\mid\operatorname{ord}_p(2).}
\]

At least one of

\[
x,\qquad y,\qquad x+y,\qquad x-y
\]

is divisible by \(3\). Indeed, if \(3\nmid xy\), then
\(x/y\equiv\pm1\pmod3\).

Because \(q>3\), removing a \(q\)-power factor does not remove \(3\). In
the \(x-y\) case, \(3\nmid z\): otherwise \(x\equiv y\pmod3\) and

\[
0\equiv z^q\equiv x^p+y^p\equiv2x\pmod3,
\]

forcing \(3\mid x,y\), contrary to primitivity. Hence

\[
\boxed{\operatorname{ord}_q(3)\mid\operatorname{ord}_p(3).}
\]

## 4. Finite out-degree for every repeated exponent

Define

\[
a_p=\operatorname{ord}_p(2),\qquad
b_p=\operatorname{ord}_p(3).
\]

The two order divisibilities imply

\[
q\mid2^{a_p}-1,\qquad q\mid3^{b_p}-1.
\]

Thus, for each fixed \(p\), every possible \(q\) belongs to the explicit
finite set of prime divisors of

\[
\boxed{G_p=\gcd(2^{a_p}-1,3^{b_p}-1).}
\]

This contracts the two-dimensional repeated-prime exponent plane into a
computable directed graph of finite out-degree.

There is also a symmetric formulation. Put

\[
g=\gcd(p-1,q-1).
\]

Both \(\operatorname{ord}_q(2)\) and \(\operatorname{ord}_q(3)\) divide
\(g\), so

\[
\boxed{q\mid H_g:=\gcd(2^g-1,3^g-1).}
\]

Whenever \(H_g=1\), all exponent pairs with that value of \(g\) are
eliminated.

## 5. Unconditional zero-density theorem

Let \(\mathcal S(X)\) denote the set of ordered pairs of distinct primes
\(p,q\in(3,X]\) satisfying both order divisibilities.

For \(q>3\), let

\[
H_q=\langle2,3\rangle\subset\mathbf F_q^\times,\qquad h_q=|H_q|.
\]

### Subgroup lemma

\[
\boxed{
h_q>
\left(\frac{\log q}{\log6}\right)^2.
}
\]

Let \(M=\lfloor\sqrt{h_q}\rfloor\). The \((M+1)^2>h_q\) elements
\(2^a3^b\), with \(0\le a,b\le M\), contain a collision modulo \(q\).
Clearing negative exponents gives a nonzero integer divisible by \(q\) and
of absolute value strictly smaller than \(6^M\). Unique factorization
ensures that the integer is nonzero. Thus

\[
q<6^M\le6^{\sqrt{h_q}},
\]

which proves the lemma.

For \((p,q)\in\mathcal S(X)\), the subgroup order \(h_q\), equal to the
least common multiple of the two orders at \(q\), divides \(p-1\). Hence
fixed \(q\) permits at most

\[
\frac{X}{h_q}+1
\]

values of \(p\le X\).

Split the sum at \(q=\sqrt X\). For \(q>\sqrt X\),

\[
h_q>
\frac{(\log X)^2}{4(\log6)^2}.
\]

The prime number theorem then gives

\[
\boxed{
|\mathcal S(X)|
=
O\left(
\frac{X^2}{(\log X)^3}
+
\frac{X^{3/2}}{(\log X)^2}
\right).
}
\]

Since

\[
\pi(X)^2\sim\frac{X^2}{(\log X)^2},
\]

we obtain

\[
\boxed{
\frac{|\mathcal S(X)|}{\pi(X)^2}\longrightarrow0.
}
\]

Thus the simultaneous two-base order graph has relative density zero among
all ordered prime-exponent pairs.

## 6. Exact trust boundary and impact on Beal

The following statements are unconditional:

1. \((1+\zeta_p)^t=\pm1\) for \(t\in J_k\);
2. the resulting \(x-y\) rational congruence;
3. the finite-out-degree order graph;
4. the subgroup lower bound;
5. the zero-density theorem for that graph.

Conditional on the independently isolated characteristic-ideal prefix
through `D=1`, every primitive solution of

\[
x^p+y^p=z^q
\]

must lie on this graph. Therefore the repeated-prime exponent plane is
eliminated outside a zero-density exceptional set.

This does not prove that the exceptional graph is empty. It does,
however, attack the complete infinite \((p,p,q)\) core in one theorem.
A terminating proof can now target the exceptional edges, rather than all
prime pairs.

The other canonical infinite cores remain

\[
(4,p,q)\qquad\text{and}\qquad(p,q,r).
\]
