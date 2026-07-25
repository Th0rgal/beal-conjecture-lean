# Mod-2 Stickelberger collapse and the graph-or-ray-class frontier

## Breakthrough

For the complete repeated-prime family

\[
x^p+y^p=z^q,\qquad p\ne q,\quad p\ge5,
\]

the previously isolated target—prove a nontrivial residue directly at the
prime above \(2\)—cannot work from the \(q\)-th-power equation. That power
always collapses to \(1\) modulo \(2\).

The correct replacement is the exact dichotomy

\[
\boxed{
\text{contractive exponent graph}
\quad\text{or}\quad
\text{finite ray-class annihilator}.
}
\]

## 1. Mod-2 collapse

Let \(K=\mathbf Q(\zeta_p)\), \(j\) be complex conjugation and let

\[
\theta=\sum_{c=1}^{p-1}n_c\sigma_c^{-1}
\]

be a positive Stickelberger element of relative weight \(r\):

\[
(1+j)\theta=rN.
\]

Put \(u=\zeta+\zeta^{-1}\). Then

\[
N_{K/\mathbf Q}(u)
=\prod_{a=1}^{p-1}(1+\zeta^a)
=\Phi_p(-1)=1.
\]

Because \(u\) is real,

\[
(u^\theta)^2=u^{(1+j)\theta}=u^{rN}=1.
\]

The prime \(2\) is unramified in \(K\), so \(O_K/2O_K\) is reduced.
Thus \(u^\theta=1\pmod2\).

Moreover,

\[
(1+\zeta)^2=1+\zeta^2
=\zeta(\zeta+\zeta^{-1})=\zeta u\pmod2.
\]

Therefore

\[
\bigl((1+\zeta)^\theta\bigr)^2
=\zeta^{\phi(\theta)}.
\]

The square map is bijective, giving

\[
\boxed{
(1+\zeta)^\theta
=\zeta^{\phi(\theta)/2}\pmod2.
}
\]

Hence

\[
\boxed{
\theta\in I_0=\ker\phi
\Longrightarrow
(1+\zeta)^\theta=1\pmod2.
}
\]

## 2. Collapse of the characteristic number

Use \(\alpha=y+\zeta x\). Pairwise coprimality gives

\[
\alpha\equiv
\begin{cases}
1,&2\mid x,\\
\zeta,&2\mid y,\\
1+\zeta,&x,y\text{ odd}
\end{cases}
\pmod2.
\]

Every \(t\in J_k\) lies in \(I_0\), so

\[
\boxed{\alpha^t\equiv1\pmod2.}
\]

The Jacobi generator consequently satisfies

\[
\boxed{
\beta(t)\bmod\mathfrak P\in\mu_q
\qquad(\mathfrak P\mid2).
}
\]

The equation determines only the \(q\)-th power and cannot distinguish
the residue \(1\) from a nontrivial \(q\)-th root.

## 3. Graph branch

Define

\[
\chi_{\mathfrak P}(t)
=\beta(t)\bmod\mathfrak P.
\]

It is multiplicative and satisfies

\[
\chi_{\mathfrak P}(\sigma_2t)
=\chi_{\mathfrak P}(t)^2.
\]

If it is nontrivial somewhere, the earlier anti-cyclotomic Frobenius
argument gives

\[
\boxed{
\operatorname{ord}_q(2)\mid\operatorname{ord}_p(2),
\qquad
\frac{\operatorname{ord}_p(2)}
     {\operatorname{ord}_q(2)}
\text{ odd}.
}
\]

This is the well-founded exponent graph.

## 4. Ray-class branch

If all residue characters are trivial, then

\[
\beta(t)\equiv1\pmod{2O_K}.
\]

Jacobi normalization also gives

\[
\beta(t)\equiv1\pmod{(1-\zeta)^2}.
\]

Thus

\[
\beta(t)\equiv1
\pmod{\mathfrak m},
\qquad
\mathfrak m=2O_K(1-\zeta)^2.
\]

Since \((\beta(t))=\mathfrak A^t\), the ray class
\(c=[\mathfrak A]_{\mathfrak m}\) satisfies \(c^t=1\) for all \(t\in J\).

Let \(M_p=\langle J\rangle_{\mathbf Z}\). Adding and subtracting a
sufficiently large multiple of the positive norm element gives

\[
\boxed{
M_p=
\{\theta\in I_0:
\varsigma(\theta)\equiv0\pmod2\}.
}
\]

Therefore the zero branch lies in the finite module

\[
\boxed{
\mathscr R_p=
\{c\in\operatorname{Cl}_{\mathfrak m}(K):
c^\theta=1\text{ for all }\theta\in M_p\}.
}
\]

## 5. New direction

Every repeated-prime counterexample is now in one of two uniform branches:

\[
\boxed{
\begin{array}{ll}
\textbf{Graph branch:}&q\mid H_p;\\
\textbf{Ray branch:}&[\mathfrak A]_{2(1-\zeta)^2}\in\mathscr R_p.
\end{array}}
\]

The next theorem should compute or annihilate \(\mathscr R_p\) uniformly
through the ray-class exact sequence, character decomposition,
Stickelberger annihilation and reflection. This replaces an impossible
local target by a finite global class-field target.

## Replay

```bash
python3 scripts/check_global_beal_graph_or_ray.py
```
