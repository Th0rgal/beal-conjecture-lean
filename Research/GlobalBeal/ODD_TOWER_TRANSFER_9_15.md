# Two additional infinite Beal families

A complete primitive-integer classification of

\[
x^2+y^3=z^n
\]

for odd \(n\) can be transferred to a three-parameter Beal family. For

\[
a\ge 2,\qquad b,c\ge 1,
\]

the three choices of right-hand exponent give the substitutions

\[
(A^a,B^b,C^c),\qquad
(C^a,-A^b,B^c),\qquad
(A^a,-C^b,-B^c).
\]

Thus the remaining finite question is whether a sign-compatible classified
\(x\)-coordinate can be a proper \(a\)-th power.

## Exponent \(9\)

Bruin's complete classification gives, in the orientation
\(x^2+y^3=z^9\),

```text
(0,-1,-1),
(±1,0,1), (±1,-1,0),
(±3,-2,1),
(±13,7,2).
```

The only positive \(x\)-coordinates surviving a relevant sign pattern are
\(3\) and \(13\). Each has a prime divisor of valuation exactly one, so neither
is a proper power.

Therefore

\[
\boxed{
\text{no primitive positive equation with exponent multiset }
\{2a,3b,9c\}\text{ exists.}
}
\]

## Exponent \(15\)

Siksek and Stoll's complete classification gives only trivial points and
\((\pm3,-2,1)\). The only sign-compatible positive \(x\)-coordinate is \(3\),
again not a proper power.

Therefore

\[
\boxed{
\text{no primitive positive equation with exponent multiset }
\{2a,3b,15c\}\text{ exists.}
}
\]

Both statements are unconditional.

Certificate SHA-256:

```text
71e991d826e8842c3f9a140fa0d469f758e2b255a55304f523721e80d74ba82a
```

Replay:

```bash
python3 scripts/check_global_beal_odd_tower_transfer.py --self-test
python3 scripts/check_global_beal_odd_tower_transfer.py
```
