# Odd-branch CM and ghost filtering

## Result

Let `(A,B,C)` lie in the Dahmen--Siksek odd branch for

```text
A^3+B^5=C^7.
```

Thus

```text
A,B,C>0,
3 does not divide A*B*C,
5 does not divide A*C,
7 divides A,
C is odd.
```

For the first plus Frey representation use the Pacetti--Villagra orientation

```text
(a,b,c)=(B,-C,A),  (q,p,r)=(5,7,3).
```

Then:

1. the specialization cannot have complex multiplication;
2. the complete fixed-`7` level `(2,2)` is impossible in the odd branch;
3. the complete level `(3,2)` survivor set drops from nine packets to seven;
4. at levels `(2,3)` and `(3,3)`, the persistent CM/ghost packets are already
   impossible, so only additional residual-prime-`7` packets from the missing
   flagged reruns can survive.

These statements use explicit literature inputs and remain outside
`BealUnified.Trusted`.

## CM support contradiction

Pacetti--Villagra Torcomian Proposition 5.8 proves that if the plus motive
specialized at a nontrivial solution has complex multiplication, every prime
dividing the paper variable `b` belongs to `{q,r}`.

Here

```text
b=-C, q=5, r=3.
```

Therefore CM would force

```text
C=3^alpha*5^beta.
```

The odd branch has `3 ∤ C` and `5 ∤ C`, hence `alpha=beta=0` and `C=1`.
But positivity gives

```text
A^3+B^5 >= 1+1 = 2 > 1 = C^7,
```

which is impossible. Thus no odd-branch specialization is CM.

This is stronger than excluding CM solely through a special local type: it uses
the global support theorem and applies at every Hilbert level.

## Complete level `(2,2)` closure

The public fixed-`7` computation at level `(2,2)` contains 14 packets and leaves
exactly

```text
3,9,12.
```

The proof of Theorem A identifies all three as CM. Since the odd branch cannot
produce a CM specialization, the filtered set is empty:

```text
odd branch at level (2,2): no survivors.
```

Hence any hypothetical odd-branch solution must lower to one of the other three
levels.

## Complete level `(3,2)` compression

The exact flagged transcript gives the fixed-`7` survivor set

```text
21,22,26,33,61,65,78,92,98.
```

The persistent forms at this level are

```text
64,65,69,73,77,78,79,
```

and the source proves that all seven are CM. The intersection is

```text
65,78.
```

Removing them leaves exactly

```text
21,22,26,33,61,92,98.
```

Thus the complete level `(3,2)` search has seven genuine non-CM fixed-`7`
candidates, not nine.

## Incomplete levels

At level `(2,3)`, the persistent forms

```text
1,7,11,12,13,16,21
```

are all CM and therefore impossible in the odd branch. The flagged rerun is
still needed to identify any additional forms surviving specifically at
residual characteristic `7`.

At level `(3,3)`, the persistent forms

```text
22,39
```

are the two ghost forms. Pacetti--Villagra Torcomian Theorem 7.18 excludes them
when `3 ∤ c`; here `c=A`, and the odd branch has `3 ∤ A`. Again, the flagged
rerun is required only to identify additional `p=7`-specific forms.

## Replay

```bash
python3 scripts/check_signature_357_odd_cm_filter.py --self-test
python3 scripts/check_signature_357_odd_cm_filter.py
```

The checker independently verifies the support arithmetic, the set
intersections, and consistency with `fixed7_frontier.json`. It imports the CM
support theorem, fixed-level packet classifications, and ghost theorem as
explicit source dependencies.

Certificate digest:

```text
a6b5ec10af2857f92e183e7c10b3d9e572c90da31522817618df3b5cf411b8f1
```

## Revised odd-branch frontier

The odd branch now has:

- an absolutely irreducible fixed-`7` representation;
- an absolutely irreducible independent mod-`5` representation;
- a superspecial/nonordinary local condition at the prime above `7`;
- no CM specialization;
- no ghost specialization;
- no level-`(2,2)` solution;
- exactly seven known candidates at the complete level `(3,2)`.

The next decisive computation is therefore restricted to:

1. the seven packets `21,22,26,33,61,92,98` at level `(3,2)`;
2. the additional non-CM/non-ghost packets revealed by flagged reruns at levels
   `(2,3)` and `(3,3)`;
3. their joint trace-pair compatibility with the independent mod-`5` system
   under the exact relation `u+t_7=1`.
