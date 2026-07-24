# Signature `(3,5,7)`: parity-complete prime-2 irreducibility obstruction

## Status

This note records a research theorem with explicit literature inputs and an
independently replayed finite certificate. It is not imported by
`BealUnified.Trusted` and does not prove the signature `(3,5,7)`.

The result removes a residual-image bottleneck:

```text
B odd  => the independent residual mod-5 plus HGM is absolutely irreducible;
B even => A and C are odd, so the independent fixed-7 odd-C theorem applies.
```

Consequently every hypothetical primitive solution of

```text
A^3 + B^5 = C^7
```

has at least one absolutely irreducible Frey representation available for level
lowering.

## Source and orientation

Use the plus hypergeometric motive

```text
H((1/7,-1/7),(1/3,-1/3) | t)
```

over `K_7=Q(zeta_7)^+`, with residual characteristic `5` and

```text
t = C^7/A^3.
```

This corresponds to the generalized-Fermat orientation

```text
(-C)^7 + B^5 + A^3 = 0.
```

The imported source results are:

1. Golfieri--Pacetti, arXiv `2412.08804v2`, Theorems 4.2 and 4.3:
   residual ramification and finite flatness at the prime above `5`;
2. Definition 2.3 and formulas `(30)`--`(31)` in the same paper:
   exact finite-monodromy traces at `t=0` and `t=infinity`;
3. the rank-one finite-flat character classification over an unramified cubic
   `5`-adic field;
4. the source local inertia bounds `12` at `3` and `28` at `7`;
5. the independent fixed-`7` odd-`C` irreducibility theorem recorded in this
   directory.

The standard-library checker verifies the finite arithmetic following from these
inputs. It does not silently promote the imported representation-theoretic
statements to Python proofs.

## Parity split

If `B` is odd, reduction of the equation modulo `2` gives

```text
A + 1 = C mod 2.
```

Thus exactly one of `A,C` is even:

| parity | behavior of `t=C^7/A^3` at `2` | source formula |
|---|---|---|
| `A` odd, `C` even | `t=0` | `(30)` |
| `A` even, `C` odd | `t=infinity` | `(31)` |

Equation `(15)` in the HGM paper exchanges the two parameter pairs when the
parameter is inverted. The two degenerations must therefore be audited
separately; applying the `t=0` character exponents after inversion without
swapping the parameter pairs is not a valid parity-complete argument.

## Exact traces over `F_64`

The prime `2` has residue degree `3` in `K_7`, hence norm `8`. In the full
cyclotomic field `Q(zeta_21)` it has residue degree `6`, so the finite trace
formulas are evaluated over

```text
F_64 = F_2[x]/(x^6+x+1).
```

The checker constructs the ordinary Jacobi sums directly in `Z[zeta_21]` and
reduces them by

```text
Phi_21(X)=X^12-X^11+X^9-X^8+X^6-X^4+X^3-X+1.
```

### Zero branch

The two character-exponent pairs are

```text
(-4,-10), (-14,10).
```

Their sum is the rational integer `16`. After the Jacobi-motive factor and the
weight-two Tate normalization, the trace is

```text
-16.
```

### Infinity branch

The two pairs are

```text
(-4,10), (6,-10).
```

The individual Jacobi sums are non-rational, but their exact sum reduces to
`-9`; the weight-two trace is therefore

```text
9.
```

Both traces satisfy

```text
-16 = 9 = 4 mod 5.
```

## Global reducible-character contradiction

The real cubic field `K_7` has discriminant `49`. Its Minkowski bound is

```text
(3!/3^3)*sqrt(49)=42/27=14/9<2,
```

so its class number is one.

The prime `5` is inert. In

```text
F_125 = F_5[theta]/(theta^3+theta^2-2*theta-1),
```

the unit `theta` has exact order `31`. For a reducible representation, the
rank-one finite-flat signature has bits `(s_0,s_1,s_2) in {0,1}^3`. Unit
reciprocity gives

```text
84*(s_0+5*s_1+25*s_2)=0 mod 31.
```

The only possibilities are the parallel signatures

```text
(0,0,0), (1,1,1).
```

After exchanging the two diagonal characters, use `(0,0,0)`. The exponent

```text
lcm(12,28)=84
```

kills the remaining inertia. Class number one then gives `lambda^84=1`.

Over `Q(zeta_21)` the prime above `2` has relative residue degree two over
`K_7`. Both parity branches have residual trace `4` and determinant

```text
8^2 = 64 = 4 mod 5.
```

If the representation were absolutely reducible, the corresponding diagonal
Frobenius value `v` would satisfy

```text
v^2-4*v+4=0,
```

so `v=2`. But `v=lambda(Frob_2)^2`, hence `lambda^84=1` requires

```text
v^42=1.
```

Instead,

```text
2^42=4=-1 mod 5.
```

This contradiction proves absolute irreducibility whenever `B` is odd.

## Parity-complete two-Frey consequence

If `B` is even, the primitive equation forces `A` and `C` to be odd. In
particular `C` is odd, and the independently audited fixed-`7` character argument
applies.

Therefore:

```text
Every primitive (3,5,7) solution has at least one absolutely irreducible
residual Frey representation:

  B odd  -> mod 5;
  B even -> mod 7.
```

This does not eliminate the solution. It guarantees that reducibility can no
longer be the reason both modular attacks fail simultaneously. The remaining
work is finite conductor/newform elimination, preferably using the exact
parameter coupling between the two Frey systems.

## Replay

Run:

```bash
python3 scripts/check_signature_357_mod5_prime2.py --self-test
python3 scripts/check_signature_357_mod5_prime2.py
```

The version-2 certificate includes both parity branches and rejects:

- a mutated infinity trace;
- reuse of the zero-branch character exponents at infinity;
- an incomplete finite-flat signature list;
- an overclaimed conclusion;
- duplicate JSON keys.

Current canonical certificate digest:

```text
2db512bc99fb5dce051083146f2e4fc61ac09a5b484c0d6c7343a2b6bd47360c
```
