# Signature `(3,5,11)`: absolute mod-`5` irreducibility at `3`

## Statement

Assume that

\[
A^3+B^5=C^{11},\qquad \gcd(A,B,C)=1,
\]

and

\[
3\nmid ABC.
\]

Attach the plus hypergeometric compatible system for the orientation

\[
(-C)^{11}+B^5+A^3=0,
\qquad (q,p,r)=(11,5,3),
\]

over

\[
K_{11}=\mathbf Q(\zeta_{11})^+.
\]

Subject to the source local-type identification, compatible-system construction,
modularity, and local--global compatibility, its residual characteristic-`5`
representation is absolutely irreducible.

This is a research theorem with imported literature inputs, not a trusted Lean
theorem and not a proof of the whole signature or of Beal.

## 1. The only possible parameter classes at `3`

Use the inverse parameter

\[
u=\frac{C^{11}}{A^3}.
\]

Modulo `3`, every nonzero element is its own odd power, so the equation gives

\[
A+B=C.
\]

The only triples in \((\mathbf F_3^\times)^3\) satisfying this are

\[
(A,B,C)=(1,1,-1)
\]

and its simultaneous negative. Therefore

\[
u\equiv -1\equiv2\pmod3,
\]

and hence

\[
\boxed{u\bmod9\in\{2,5,8\}.}
\]

The source local classification at `3`, after orienting the general
`(q,p,r)` construction as `(11,5,3)`, gives the following dihedral
supercuspidal types:

\[
\begin{array}{c|c|c}
u\bmod9&\text{quadratic inducing extension}&\text{finite inertia order}\\ \hline
2&\text{ramified}&12\\
5&\text{unramified}&4\\
8&\text{ramified}&12.
\end{array}
\]

## 2. The completion of `K_11` at `3`

One checks

\[
3^5\equiv1\pmod{11},
\]

while

\[
3^i\not\equiv\pm1\pmod{11}
\qquad(1\le i<5).
\]

Thus the unique completion relevant to the real cyclotomic field is the
unramified quintic extension

\[
L/\mathbf Q_3,
\qquad [L:\mathbf Q_3]=5.
\]

## 3. Odd-degree base change preserves the induced local type

Let

\[
\tau=\operatorname{Ind}_{W_E}^{W_{\mathbf Q_3}}\chi
\]

be one of the source dihedral supercuspidal types, where
\(E/\mathbf Q_3\) is quadratic. Since

\[
[E:\mathbf Q_3]=2,
\qquad [L:\mathbf Q_3]=5,
\]

the two fields are linearly disjoint. Mackey restriction gives

\[
\tau|_{W_L}
\simeq
\operatorname{Ind}_{W_{EL}}^{W_L}
\bigl(\chi|_{W_{EL}}\bigr).
\]

Suppose this restriction were reducible. Then, writing \(\sigma\) for the
nontrivial automorphism of \(E/\mathbf Q_3\), the character

\[
\delta=\frac{\chi}{\chi^\sigma}
\]

would be trivial on \(W_{EL}\). Therefore it would factor through

\[
W_E/W_{EL}\cong\operatorname{Gal}(EL/E)\cong C_5.
\]

The quadratic and quintic automorphisms commute, so this quotient gives

\[
\delta^\sigma=\delta.
\]

But the definition gives

\[
\delta^\sigma=\delta^{-1}.
\]

Thus \(\delta^2=1\). Since \(\delta\) also factors through a group of order
`5`, it is trivial. That contradicts the irreducibility of the original
induced supercuspidal representation. Hence

\[
\boxed{\tau|_{W_L}\text{ remains irreducible}.}
\]

## 4. Reduction modulo `5`

The ratios of the two inducing characters have finite orders `4` or `12`.
Both orders are prime to `5`. Reduction modulo `5` therefore preserves their
order and, in particular, preserves the distinction between the two conjugate
inducing characters.

Consequently the residual local representation over \(L\) is absolutely
irreducible. A globally reducible representation would remain reducible on
every decomposition group. Therefore

\[
\boxed{
3\nmid ABC
\Longrightarrow
\bar\rho_5\text{ is absolutely irreducible over }K_{11}.
}
\]

## 5. Modularity boundary

For the unit-coefficient family `(3,p,r)`, the plus hypergeometric motive is
modular by the cited modularity theorem: the coefficient of the cube is `1`,
so the condition that `r` not divide that coefficient is automatic for
`r=11`.

The finite arithmetic and negative fixtures are replayed by

```bash
python3 scripts/check_signature_3511_mod5_irreducibility_at3.py --self-test
python3 scripts/check_signature_3511_mod5_irreducibility_at3.py
```

The checker does **not** reprove the imported local-type or modularity theorems.
