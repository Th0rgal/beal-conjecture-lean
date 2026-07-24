# Signature `(3,5,7)`: reciprocal finite-HGM coordinates

## Status

This note records a source-anchored implementation correction for the exact
two-Frey trace graph. It does not change the already valid marginal candidate
sets, and it does not by itself prove the odd branch or the full signature.

## Mathematical parameters

For a hypothetical primitive solution

```text
A^3 + B^5 = C^7,
```

the two mathematical hypergeometric parameters are

```text
u = C^7/A^3,
v = -B^5/A^3,
u + v = 1.
```

The previous parameter-labelled producer passed `u` and `v` literally to the
pinned PARI/GP function `hgm`. That is not the convention used by this routine.

## Published source anchor

Pacetti--Villagra Torcomian, Lemma 7.3 and Table 7.1, identify the specialization

```text
t0 = 3
```

of the plus `(5,p,3)` motive with the genus-two curve

```text
y^2 = 5*x^6 - 12*x^5 + 30*x^3 + 9.
```

At the prime ideal `(11+sqrt(5))/2` of norm `29`, the published characteristic
polynomial is

```text
T^4 - 2*T^3 + 14*T^2 - 58*T + 841.
```

Writing this as

```text
(T^2-a*T+29)*(T^2-a'*T+29)
```

shows that the real-multiplication trace satisfies

```text
x^2 - 2*x - 44.
```

The pinned legacy GP artifact returns:

```text
hgm argument 3  -> x^2 - 8*x + 11,
hgm argument 10 -> x^2 - 2*x - 44.
```

Since

```text
10 = 3^(-1) mod 29,
```

the exact parameter-labelled convention is

```text
GP argument z = t0^(-1).
```

The standard-library checker replays the factorization anchor, the reciprocal
calculation, the two recorded GP rows and negative fixtures:

```bash
python3 scripts/check_signature_357_gp_parameter_convention.py --self-test
python3 scripts/check_signature_357_gp_parameter_convention.py
```

Certificate digest:

```text
c32eb5bb8c060dc6c3625011aa073a0b7f081ad57d2aa51a58daa1abed4df141
```

## Correct joint graph

The GP inputs must therefore be

```text
z5 = u^(-1),
z7 = v^(-1).
```

The mathematical identity `u+v=1` becomes

```text
z5^(-1) + z7^(-1) = 1,
```

or equivalently

```text
(z5-1)*(z7-1) = 1.
```

The corrected producer retains both the mathematical parameters and the GP
arguments, and rejects any row violating these identities.

## Consequences

1. **Marginal eliminations remain valid.** Inversion is a permutation of the
   nondegenerate parameters, so candidate sets that discarded parameter labels
   are unchanged.
2. **The old parameter-labelled joint graph is withdrawn.** It coupled the GP
   implementation arguments by `z5+z7=1`, which is not the mathematical
   two-Frey relation.
3. **The exact odd-branch pair test must be rerun.** The producer now evaluates
   `hgm(u^(-1))` and `hgm(v^(-1))`, retains both coordinate systems and rejects
   any row violating `(z5-1)*(z7-1)=1`.
4. **Degenerate pairings do not change.** In mathematical coordinates, `u=0`
   pairs with `v=1`, `u=1` with `v=0`, and infinity with infinity.

This correction is a prerequisite for any proof-grade joint trace elimination.
It prevents an incorrectly labelled finite computation from being promoted into
a Diophantine contradiction.
