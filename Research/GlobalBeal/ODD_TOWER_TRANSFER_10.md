# An unconditional infinite Beal family from exponent \(10\)

## Theorem

For every

\[
a\ge 2,\qquad b,c\ge 1,
\]

there are no pairwise-coprime positive integers satisfying any coefficient-one
generalized Fermat equation whose exponent multiset is

\[
\boxed{\{2a,3b,10c\}}.
\]

This covers all six permutations.

## Proof

There are three cases, according to the exponent on the right-hand side.

### Right-hand exponent \(10c\)

From

\[
A^{2a}+B^{3b}=C^{10c}
\]

set

\[
(x,y,z)=(A^a,B^b,C^c).
\]

Then \(x^2+y^3=z^{10}\), with all three coordinates positive. Brown's complete
classification contains no such row.

### Right-hand exponent \(2a\)

From

\[
A^{3b}+B^{10c}=C^{2a}
\]

set

\[
(x,y,z)=(C^a,-A^b,B^c).
\]

Brown's classification has exactly one row with \(x>0,y<0,z>0\):

\[
(3,-2,1).
\]

It would force \(C^a=3\), impossible for \(a\ge2\).

### Right-hand exponent \(3b\)

From

\[
A^{2a}+B^{10c}=C^{3b}
\]

set

\[
(x,y,z)=(A^a,B^c,C^b).
\]

Then

\[
x^2+y^{10}=z^3.
\]

Dahmen proved that this equation has no solutions in nonzero coprime integers.

Swapping the two positive summands covers the other three exponent orders.

## Sources

- David Brown, *Primitive Integral Solutions to \(x^2+y^3=z^{10}\)*,
  Theorem 1.1.
- Sander R. Dahmen, *A refined modular approach to the Diophantine equation
  \(x^2+y^{2n}=z^3\)*, the \(n=5\) case.

Certificate SHA-256:

```text
1989f42fc74d00d006cba4ad725ef322d911e8f5026fca98b48e63209b98b86c
```

Replay:

```bash
python3 scripts/check_global_beal_odd_tower_transfer_10.py --self-test
python3 scripts/check_global_beal_odd_tower_transfer_10.py
```
