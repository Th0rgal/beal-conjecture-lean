# Signature `(5,p,3)`: parity-complete residual irreducibility

## Statement

Let

\[
a^5+b^p+c^3=0
\]

be a non-trivial primitive integer solution, where `p>13` is prime. Let
`rho_p^+` and `rho_p^-` be the two residual rank-two representations over
`K=Q(sqrt(5))` attached to the plus and minus hypergeometric motives of
Pacetti--Villagra Torcomian.

Then

\[
\boxed{\text{at least one of }\bar\rho_p^+,\bar\rho_p^-
       \text{ is absolutely irreducible}.}
\]

More precisely:

- if `b` is odd, **both** representations are absolutely irreducible;
- if `b` is even, the local restriction of `rho_p^-` at the prime above `2`
  is absolutely irreducible, hence `rho_p^-` is globally absolutely
  irreducible.

This removes the residual-image obstruction for every parity branch of the
whole `(5,p,3)` family. It does **not** by itself eliminate any solution.

## Odd `b`

Corollary 7.7 of Pacetti--Villagra Torcomian states that, for a fixed auxiliary
prime `ell` not dividing `b`, both residual representations are absolutely
irreducible for `p>C(ell)`. Their explicit computation gives

```text
C(2)=13.
```

Thus `b` odd and `p>13` imply absolute irreducibility of both signs.

## Even `b`

Primitivity makes `a` and `c` odd. Reducing the equation modulo `4` gives

\[
a^5+c^3\equiv0\pmod4,
\]

and therefore

\[
a^5\equiv-c^3\equiv3c^3\pmod4.
\]

Proposition 3.15 of Pacetti--Villagra Torcomian consequently gives conductor
exponent `5` at the prime above `2` for the minus motive.

The proof of Theorem 7.2 of Golfieri--Pacetti identifies this conductor-five
local type as

\[
\operatorname{Ind}_{W_{\mathbf Q_2(i)}}^{W_{\mathbf Q_2}}\chi,
\]

where `chi` has order `4`; it also states that the odd residual congruences and
unramified base extensions preserve the supercuspidal residual local type.
The completion of `Q(sqrt(5))` at `2` is unramified quadratic, whereas
`Q_2(i)/Q_2` is ramified quadratic, so the two extensions are linearly
disjoint. Restriction to the completion of `K` is therefore still an induced
representation from a quadratic extension.

Because `p` is odd, reduction modulo a prime above `p` preserves the order-four
part of the inducing character. The character and its conjugate remain
distinct, so Mackey's criterion shows that the induced residual local
representation is absolutely irreducible. A globally reducible
representation would be reducible on every decomposition group, proving the
global claim.

## Exact limitation

For fixed exponent `5`, the source proves unconditional modularity of the plus
motive, but it does not yet prove the required fixed-`5` modularity propagation
for the minus motive in every specialization. Thus the theorem supplies the
missing parity-complete **irreducibility** input, not a complete modular
elimination of the even-`b` branch.

## Replay

```bash
python3 scripts/check_global_beal_signature5p3_parity_irreducibility.py --self-test
```

The checker replays the mod-`4` implication, validates the order-four Mackey
criterion in odd characteristic, pins the source statements and rejects
mutated bounds, conductor exponents, local types and conclusions. The cited
local-type identifications remain imported mathematical theorems.
