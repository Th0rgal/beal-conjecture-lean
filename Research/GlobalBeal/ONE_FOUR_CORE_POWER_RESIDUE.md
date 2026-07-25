# Uniform full-modulus theorem for the one-`4` Beal core

## Theorem

Let

\[
A^4+B^p=C^q,
\]

where \(A,B,C\) are pairwise-coprime positive integers and \(p,q\) are
coprime odd positive integers. In the canonical Beal core, \(p,q\) are distinct
odd primes.

Then:

1. exactly one of \(A,B,C\) is even;
2. \(C\) is a fourth power modulo the full modulus \(B^p\);
3. \(-B\) is a fourth power modulo the full modulus \(C^q\);
4. there is one element \(t\in(\mathbf Z/A^4\mathbf Z)^\times\) satisfying
   \[
   t^q=B,
   \qquad
   t^p=C.
   \]

This theorem is unconditional. It does not assert that the equation has no
solutions.

## Full-modulus fourth roots

Modulo \(B^p\), \(A^4=C^q\). If \(q=4k+1\), the element
\(u=AC^{-k}\) satisfies \(u^4=C\). If \(q=4k+3\), the element
\(u=C^{k+1}A^{-1}\) satisfies \(u^4=C\).

Modulo \(C^q\), put \(D=-B\). Because \(p\) is odd, \(A^4=D^p\), and the
same two cases show that \(-B=D\) is a fourth power modulo \(C^q\).

## Common parameter

Modulo \(A^4\), \(B^p=C^q\). Choose integers \(a,b\) with

\[
aq+bp=1.
\]

For \(t=B^aC^b\),

\[
\begin{aligned}
t^q&=B^{aq}(C^q)^b=B^{aq+pb}=B,\\
t^p&=(B^p)^aC^{bp}=C^{aq+bp}=C.
\end{aligned}
\]

## Uniform parity information

Modulo \(8\), exactly one base is even and

\[
\begin{array}{c|c}
\text{even base}&\text{necessary congruence}\\ \hline
A&B\equiv C\pmod8,\\
B&C\equiv1\pmod8,\\
C&B\equiv-1\pmod8.
\end{array}
\]

## Global significance

The corrected canonical reduction leaves the infinite core

\[
(4,p,q),
\qquad p\ne q\text{ odd primes}.
\]

This theorem applies uniformly to every signature in that core. It replaces
independent prime-by-prime residue-symbol conditions with two compatible
fourth roots over the full composite powers and one common parameter modulo
\(A^4\).

A complete proof of Beal still needs a descent or modular argument turning
these necessary conditions into a contradiction, or reducing them to a finite
verified boundary.

## Replay

```bash
python3 scripts/check_global_beal_one_four_core.py --self-test
python3 scripts/check_global_beal_one_four_core.py
```
