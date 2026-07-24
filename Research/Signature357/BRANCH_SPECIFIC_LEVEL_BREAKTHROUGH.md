# Branch-specific mod-5 level compression for signature `(3,5,7)`

## Status

This note records a literature-assisted conductor reduction. It does not prove
the full signature `(3,5,7)` and is not imported by `BealUnified.Trusted`.

The previous safe global bound allowed every exponent pair

```text
0 <= e3,e7 <= 3,
```

hence sixteen levels dividing

```text
p3^3*p7^3
```

and maximum norm

```text
27^3*7^3 = 6,751,269.
```

The Dahmen--Siksek branches and the exact local conductor tables remove five of
those pairs before any Hilbert-newform computation.

## Orientation

Use

```text
(a,b,c)=(-C,B,A),
(q,p,r)=(7,5,3),
```

so that

```text
a^7+b^5+c^3=0.
```

The independent residual mod-5 plus-HGM representation is defined over

```text
K7=Q(zeta_7)^+.
```

The norms of the relevant primes are

```text
N(p3)=27,
N(p7)=7.
```

## Even branch

The even branch has

```text
30 | C.
```

Therefore `3 | a`. Corollary 3.6 and Table 3.2 of Pacetti--Villagra Torcomian
give

```text
e3 in {1,2}.
```

For this certificate the prime-7 exponent is deliberately left in the safe
range

```text
e7 in {0,1,2,3}.
```

Thus no even-branch solution can have `e3=0` or `e3=3`.

## Odd branch

The odd branch has

```text
3 does not divide A*B*C,
7 | A.
```

Therefore all three paper variables are 3-adic units, giving

```text
e3 in {2,3}.
```

Moreover

```text
7 | c,
7 does not divide b.
```

Proposition 3.14 and Table 3.5 give

```text
e7 in {0,1,2}.
```

Thus no odd-branch solution can have `e7=3`.

## Global branch-specific frontier

Taking the union of the two branches leaves exactly eleven exponent pairs:

```text
(1,0), (1,1), (1,2), (1,3),
(2,0), (2,1), (2,2), (2,3),
(3,0), (3,1), (3,2).
```

The removed pairs are

```text
(0,0), (0,1), (0,2), (0,3), (3,3).
```

The corresponding level norms are

```text
27, 189, 729, 1323, 5103, 9261,
19683, 35721, 137781, 250047, 964467.
```

Consequently

```text
16 levels -> 11 levels,
maximum norm 6,751,269 -> 964,467.
```

The maximum norm is reduced by the exact factor `7`.

## Combination with the complete low-level closure

The four branch-admissible norms at most `2059` are

```text
27, 189, 729, 1323.
```

They are all eliminated by the complete low-level closure certificate. Therefore
only seven higher levels remain:

```text
5103, 9261, 19683, 35721, 137781, 250047, 964467.
```

This is the current exact mod-5 automorphic frontier.

## Replay

Run:

```bash
python3 scripts/check_signature_357_branch_levels.py --self-test
python3 scripts/check_signature_357_branch_levels.py
```

The manifest is

```text
Research/Signature357/branch_specific_level_frontier.json
```

with digest

```text
449902ab1189b7f0e12c6bcf9d55928e40425552736da2c642c074c280fec8ec.
```

The checker reconstructs both branch pair sets, their union, all level norms,
the maximum norm reduction and the intersection with the complete low-level
closure. It rejects any mutation that restores the forbidden `(3,3)` pair or
the old maximum norm.

## Remaining task

The seven remaining Hilbert-newform spaces still require explicit computation
or further local restrictions. This result does not claim that any of them is
empty.
