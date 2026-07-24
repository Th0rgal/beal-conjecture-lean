# Complete low-level Hilbert-newform closure for signature `(3,5,7)`

## Status

This note originally recorded the first database-backed compression of the
independent mod-`5` program. That intermediate frontier has now been completed.

The final result is:

```text
no hypothetical primitive solution A^3+B^5=C^7
lowers on the independent mod-5 side to any Hilbert-newform level
of norm at most 2059 over K7=Q(zeta_7)^+.
```

This is a finite, literature-assisted reduction. It is not a proof of the full
signature `(3,5,7)` and is not imported by `BealUnified.Trusted`.

## Complete LMFDB inventory

The optimized conductor bound is

```text
p3^3*p7^3.
```

LMFDB documents complete cubic Hilbert-newform coverage through level norm
`2059`. Exactly eight candidate norms lie in that range:

```text
1, 7, 27, 49, 189, 343, 729, 1323.
```

The pinned inventory contains fourteen packets of total coefficient-field
dimension `26`. Its digest is

```text
5a5bce8c80ea5d4bfb59dc67b4c10c8827ab7c1f486e27e93691900bf7e91495.
```

## Successive reductions

At the norm-`8` prime, the necessary congruence

```text
a_P=0 mod 5
```

reduces the fourteen packets to

```text
3.3.49.1-49.1-a
3.3.49.1-189.1-a
3.3.49.1-729.1-b
3.3.49.1-1323.1-a.
```

The global CM-support theorem removes the two CM packets `49.1-a` and
`729.1-b`. The even-branch 7-unit local-type obstruction removes `1323.1-a`.
The only packet at the intermediate frontier is therefore

```text
3.3.49.1-189.1-a,
```

in the even branch with `7 | C`.

A complete local trace calculation at the auxiliary prime `41` then forces

```text
u=C^7/A^3=1 mod 41,
```

hence `41 | B`. The coupled fixed-`7` parameter is consequently `t7=0 mod 41`.
The five pinned `t7=0` trace polynomials all evaluate nontrivially at the
reducible target `2 mod 7`, contradicting the even-branch fixed-`7`
reducibility conclusion.

Thus the final count is

```text
14 -> 4 -> 2 -> 1 -> 0.
```

## Replay

The complete inventory/filter checker is:

```bash
python3 scripts/check_signature_357_lmfdb_low_levels.py --self-test
python3 scripts/check_signature_357_lmfdb_low_levels.py
```

The final coupled closure checker is:

```bash
python3 scripts/check_signature_357_low_level_closure.py --self-test
python3 scripts/check_signature_357_low_level_closure.py
```

The final manifest is

```text
Research/Signature357/low_level_complete_closure.json
```

with digest

```text
8c84d73b5fd8c242ffe265a49615794c436ea725d33b1f312a74454af387dde4.
```

A detailed derivation, including every candidate polynomial and imported theorem
boundary, is in

```text
Research/Signature357/COMPLETE_LOW_LEVEL_CLOSURE.md.
```

## Remaining frontier

The eight candidate norms above the documented LMFDB completeness bound are

```text
5103, 9261, 19683, 35721, 137781, 250047, 964467, 6751269.
```

These higher spaces still require explicit computation or sharper local
conductor theorems. No claim here asserts that they are empty.
