# Complete mod-5 irreducibility at the prime above 3

## Proposition

Let `(A,B,C)` be a primitive positive solution of

```text
A^3 + B^5 = C^7
```

and suppose `3 ∤ A*B*C`. Attach the plus compatible system for signature
`(7,5,3)` over

```text
K_7 = Q(zeta_7)^+
```

using `(a,b,c)=(-C,B,A)` and parameter

```text
u = C^7/A^3.
```

Subject to the local-type compatibility statements cited below, the residual
characteristic-`5` representation is absolutely irreducible.

This proposition is a research theorem with explicit literature dependencies. It
is not imported by `BealUnified.Trusted`.

## 1. Exact unit classes modulo 9

Because `A,B,C` are all units at `3`, the equation can be enumerated modulo `9`.
For every unit solution, the parameter satisfies

```text
u = C^7/A^3 mod 9 ∈ {2,5,8}.
```

The standard-library checker enumerates all 18 unit residue triples and recovers
exactly these three classes.

## 2. Local types before base change

Pacetti--Villagra Torcomian's Table 3.1 and Corollary 3.6 give the following
supercuspidal types at `3` for the corresponding Darmon/Frey realization:

| `u mod 9` | inertial degree/type | inducing quadratic extension |
|---:|---|---|
| `2` | `e=12`, supercuspidal | ramified quadratic |
| `5` | `e=4`, supercuspidal | unramified quadratic |
| `8` | `e=12`, supercuspidal | ramified quadratic |

Proposition 3.2 relates this realization to the plus hypergeometric motive modulo
`7`; Remark 3.8 describes the induced local representations and their behavior
under base extension.

## 3. Base change to `K_7`

The order of `3` modulo `7` is `6`. In the maximal real subfield the residue
degree is the least `f` with

```text
3^f ≡ ±1 mod 7,
```

namely `f=3`. Thus the completion of `K_7` at its prime above `3` is the
unramified cubic extension of `Q_3`.

- A ramified quadratic extension remains quadratic after an unramified cubic
  base change.
- The unramified quadratic extension is not contained in an unramified extension
  of odd degree `3`.

Hence all three induced local representations remain supercuspidal after
restriction to `G_{K_7}`.

## 4. Passage from characteristic 7 to characteristic 5

The finite inertia orders involved are `4` and `12`.

```text
gcd(4,5*7)=gcd(12,5*7)=1.
```

The source paper uses preservation of prime-to-the-congruence-characteristic
local type under the hypergeometric congruence. The hypergeometric motive carries
a compatible system, so the same characteristic-zero Weil--Deligne type occurs
in the `5`-adic member. Reducing modulo `5` preserves the distinct inducing
characters because their orders are prime to `5`.

Therefore the residual mod-`5` representation remains absolutely irreducible in
all three admissible classes.

## 5. Consequence for the previous five-class sieve

An earlier polynomial-irreducibility argument left five simultaneous local
classes

```text
47, 74, 101, 209, 380 mod 441.
```

Every one of them has `u mod 9 ∈ {2,5,8}` and is already covered by the exact
supercuspidal-type argument above. They are therefore not genuine exceptions.
The conclusion is the full unit-at-`3` statement

```text
3 ∤ A*B*C
  => rho_bar_5 is absolutely irreducible.
```

In particular, the Dahmen--Siksek odd branch satisfies the hypothesis.

## 6. Two-Frey coupling

For the original fixed-`7` representation use

```text
t_7 = -B^5/A^3.
```

The second representation uses `u=C^7/A^3`. The Beal equation gives the exact
identity

```text
u + t_7 = 1.
```

A correct multi-Frey elimination must therefore use the joint trace graph

```text
{ (tr rho_5(u), tr rho_7(1-u)) : u in F_l minus {0,1} }
```

rather than a Cartesian product of two marginal trace lists.

## Sources and certificate

Primary sources:

- Pacetti--Villagra Torcomian, arXiv `2512.17845v1`, Proposition 3.2,
  Table 3.1, Corollary 3.6, and Remark 3.8;
- Golfieri--Pacetti, arXiv `2412.08804v1`, compatible-system construction and
  signature `(3,p,r)` hypergeometric realization.

Replay:

```bash
python3 scripts/check_signature_357_mod5_irreducibility.py --self-test
python3 scripts/check_signature_357_mod5_irreducibility.py
```

Manifest digest:

```text
df815f6ebf008640c51840f19d1d2110f7ce37fd03185caa5cc3bb5cbdbfe21e
```

The checker verifies the finite arithmetic and metadata. It deliberately does
not claim to replace the cited representation-theoretic theorems.
