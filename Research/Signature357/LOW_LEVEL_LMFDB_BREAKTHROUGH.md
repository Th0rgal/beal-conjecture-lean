# Complete low-level Hilbert-newform reduction for signature `(3,5,7)`

## Status

This note records a finite, database-backed reduction.  It is not a proof of the
signature `(3,5,7)` and is not imported by `BealUnified.Trusted`.

The global mod-`5` program attaches to every hypothetical primitive solution of

```text
A^3 + B^5 = C^7
```

an absolutely irreducible residual plus-HGM representation over

```text
K7 = Q(zeta_7)^+.
```

After parameter inversion at the two wild primes, its prime-to-`5` lowered level
divides

```text
p3^3 * p7^3,
```

so there are sixteen possible conductor-exponent pairs.  The norm of `p3` is
`27`, and the norm of `p7` is `7`.

LMFDB documents complete Hilbert-newform data over cubic fields through level
norm `2059`.  Exactly eight of the sixteen candidate levels lie in this complete
range:

```text
1, 7, 27, 49, 189, 343, 729, 1323.
```

## Canonical LMFDB inventory

The dedicated producer queries the official read-only LMFDB PostgreSQL mirror,
using the three source tables

```text
hmf_fields, hmf_forms, hmf_hecke.
```

It pins:

- the complete packet list at the eight levels;
- the coefficient-field polynomial of every packet;
- the Hecke eigenvalue at the unique prime of `K7` of norm `8`;
- CM and base-change flags;
- a canonical SHA-256 digest.

Run the producer with:

```bash
python3 scripts/fetch_signature_357_lmfdb_sql.py \
  > Research/Signature357/lmfdb_low_levels.json
```

The pinned inventory contains exactly

```text
14 Hilbert-newform packets
```

of total coefficient-field dimension `26`.  Its digest is

```text
5a5bce8c80ea5d4bfb59dc67b4c10c8827ab7c1f486e27e93691900bf7e91495.
```

## Residual norm-8 filter

Let `P` be the unique prime above `2` in `K7`; `N(P)=8`.  The independently
certified prime-`2` calculation gives the necessary residual condition

```text
a_P = 0 mod 5.
```

Applying it to all fourteen packets leaves exactly four:

```text
3.3.49.1-49.1-a
3.3.49.1-189.1-a
3.3.49.1-729.1-b
3.3.49.1-1323.1-a
```

Thus, on the complete LMFDB range,

```text
14 packets -> 4 packets.
```

All four survivors have rational Hecke field and all four are base changes from
`Q`.  The six non-rational packets at level `1323`, including the two quadratic
packets whose norm-8 eigenvalue is the field generator, are eliminated: their
Hecke polynomial has nonzero constant term modulo `5`, so no prime above `5`
can make that generator vanish.

The offline standard-library checker is:

```bash
python3 scripts/check_signature_357_lmfdb_low_levels.py --self-test
python3 scripts/check_signature_357_lmfdb_low_levels.py
```

It verifies the pinned inventory hash, exact packet counts, polynomial arithmetic
modulo `5`, the four-packet survivor set and negative fixtures.

## Branch-local compression

The Dahmen--Siksek dichotomy and the local conductor tables reduce the four
packets further.

### Odd branch

The odd branch has `3`-adic unit variables.  Its local conductor exponent at
`p3` is `2` or `3`.  Among the four low-level survivors, only

```text
3.3.49.1-729.1-b
```

has such an exponent.  Therefore the complete low-level odd frontier is

```text
4 -> 1 packet.
```

This packet is rational, CM by `-3`, and a base change of the classical packet
`441.d2/Q`.  It is not eliminated merely by the norm-8 congruence.

### Even branch

The even branch has `30 | C`, so the local representation at `3` is special and
has conductor exponent `1` or `2`.  Special type has nonzero monodromy and cannot
come from a CM automorphic induction.  The low-level survivors are therefore

```text
3.3.49.1-189.1-a
3.3.49.1-1323.1-a.
```

Thus the complete low-level even frontier is

```text
4 -> 2 packets.
```

If the even branch also satisfies `7 not | C`, the local exponent at `p7` is `2`
or `3`, leaving only

```text
3.3.49.1-1323.1-a.
```

Hence that subbranch has a single low-level packet.

## Structural consequence

Every packet surviving the complete low-level range is a base change from
`Q`.  This replaces the low-level Hilbert-newform comparison by a classical
modular-form comparison over `Q`, with the three conjugate primes of `K7` tied
together.  That is the next useful structure for the joint mod-`5`/mod-`7`
trace-pair eliminator.

## Exact remaining frontier

The optimized conductor range contains sixteen levels.  Eight lie above the
LMFDB completeness bound and are not covered by this result:

```text
2401, 5103, 9261, 19683, 64827, 137781, 964467, 6751269.
```

They still require an explicit Hilbert-newform computation or a theorem that
removes the corresponding local conductor exponents.

Within the complete range, the remaining targets are now:

```text
odd branch:  one packet, 729.1-b;
even branch: two packets, 189.1-a and 1323.1-a;
even branch with 7 not | C: one packet, 1323.1-a.
```

The certificate manifest is

```text
Research/Signature357/lmfdb_low_level_filter.json
```

with digest

```text
332ab369db30d24a2e73d880a6d4bd96b8a6f0e1a7be335da19e8fd834660888.
```

No statement in this note asserts that the eight higher levels are empty or that
the surviving packets actually arise from an integral solution.
