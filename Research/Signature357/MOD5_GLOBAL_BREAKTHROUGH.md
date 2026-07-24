# Global mod-5 reduction for signature `(3,5,7)`

## Status

This note records a literature-assisted reduction, not a proof of `(3,5,7)` and
not a theorem in `BealUnified.Trusted`.

The current conclusion is:

```text
every hypothetical primitive positive A^3+B^5=C^7 solution
  carries an absolutely irreducible residual mod-5 plus HGM representation
  over K7 = Q(zeta_7)^+,
```

and the prime-to-`5` level of the lowered Hilbert newform divides

```text
p3^3 * p7^3.
```

The finite arithmetic is replayed by standard-library Python checkers. The
Dahmen--Siksek dichotomy, finite-flat character classification, compatible-system
local type transfer, modularity, conductor bounds, and Hilbert level lowering
remain explicit literature inputs.

## 1. Completing the prime-2 parity argument

Use the plus compatible system for

```text
A^3+B^5+(-C)^7=0
```

with the two inverse parameters

```text
t=A^3/C^7,
u=t^(-1)=C^7/A^3
```

over `K7=Q(zeta_7)^+` and residual characteristic `5`.

For a primitive solution there are exactly three parity patterns:

```text
(A,B,C) mod 2 = (0,1,1), (1,0,1), or (1,1,0).
```

The new certificate treats both patterns with `B` odd.

### `A` even

Invert the parameter. Formula (30) over `Q(zeta_21)` gives two Jacobi sums equal
to `8`; after the Jacobi-motive factor and weight-2 Tate normalization the full
cyclotomic trace is

```text
-16 = 4 mod 5.
```

### `C` even

Use `u` without inversion. The two Jacobi sums are non-rational separately, but
their sum reduces exactly to the rational integer `-9` in `Z[zeta_21]`. After
the same normalization the full cyclotomic trace is

```text
9 = 4 mod 5.
```

Thus both `B`-odd parity branches have the same residual trace at the prime over
`2`.

The finite-flat unit calculation over `F_125` allows only the parallel signatures
`(0,0,0)` and `(1,1,1)`. Class number one and the away-`5` inertia exponent `84`
force a diagonal character to satisfy `lambda^84=1`. At the full cyclotomic
prime over `2`, reducibility and the certified trace/determinant force the
character value to be `2`, while base degree `2` requires

```text
2^42 = 1 mod 5.
```

In fact `2^42=4 mod 5`, a contradiction. Therefore

```text
B odd => the residual mod-5 representation is absolutely irreducible.
```

Run:

```bash
python3 scripts/check_signature_357_mod5_bodd.py --self-test
python3 scripts/check_signature_357_mod5_bodd.py
```

Certificate digest:

```text
bee6d05455bb7b8c04b165d6c80cb5275c6bf6e95da7abfbf7307c4a073ad022
```

## 2. The Dahmen--Siksek dichotomy now covers every solution

Their theorem places every primitive solution in one of two branches:

```text
even: 30 divides C and 7 does not divide A*B;
odd:  C odd, 3 does not divide A*B*C, 5 does not divide A*C, 7 divides A.
```

In the even branch, `C` is even and pairwise primitivity forces `A,B` odd. Hence
`B` is odd and the prime-2 theorem applies.

In the odd branch, `3` does not divide `A*B*C`; the certified supercuspidal local
type at `3` gives absolute irreducibility modulo `5`.

Therefore every hypothetical primitive solution has an absolutely irreducible
mod-`5` HGM representation.

Run:

```bash
python3 scripts/check_signature_357_mod5_global.py --self-test
python3 scripts/check_signature_357_mod5_global.py
```

Updated certificate digest:

```text
7b337264f729be16a31b4561bfdbdc0e2ec16e8511956fad5989cc773b35ece0
```

## 3. New conductor breakthrough: optimize locally by parameter inversion

Golfieri--Pacetti equation (15) gives an isomorphism

```text
H((a,b),(c,d)|t) ~= H((c,d),(a,b)|t^(-1)).
```

The conductor is therefore the same in the `t` and `u=t^(-1)` presentations.
The two presentations may be chosen separately at the primes above `3` and `7`
when applying Theorem 7.4.

The Beal equation gives

```text
u-1 = B^5/A^3,
t-1 = -B^5/C^7.
```

The Dahmen--Siksek branches then give the following exact valuation choices.

| branch/place | chosen parameter | valuation pattern |
|---|---|---|
| even at `3` | `u` | `v3(u)>0`, `v3(u-1)=0` |
| odd at `3` | `u` | `v3(u)=v3(u-1)=0` |
| even at `7` | `u` | `v7(u)>=0`, `v7(u-1)=0` |
| odd at `7` | `t=u^(-1)` | `v7(t)>0`, `v7(t-1)=0` |

In every row the chosen parameter is integral, and the valuation of
`parameter*(parameter-1)` is either zero or greater than one. Neither exceptional
clause of Theorem 7.4 occurs. The `otherwise` bound therefore gives conductor
exponent at most `3` at both wild primes.

Consequently the lowered prime-to-`5` level divides

```text
p3^3 * p7^3,
```

not merely the earlier safe bound `p3^5*p7^3`.

Here `N(p3)=27` and `N(p7)=7`, so

```text
maximum level norm = 27^3 * 7^3 = 6,751,269;
possible exponent pairs = (e3,e7), 0 <= e3,e7 <= 3;
number of level divisors = 16.
```

This reduces the maximum norm by a factor of `729` and the number of candidate
levels from `24` to `16`.

## 4. Residual prime-2 Hecke filter

Let `P` be the unique prime of `K7` above `2`; `N(P)=8`. If `a_P` is the Hecke
eigenvalue over `K7`, then after the degree-2 extension to `Q(zeta_21)^+`,

```text
Tr(Frob_P^2) = a_P^2 - 16.
```

Both `B`-odd full-extension traces are congruent to `4 mod 5`. Level lowering
therefore gives only the residual condition

```text
4 = a_P^2 - 16 mod 5,
```

and hence

```text
a_P = 0 mod 5.
```

It does **not** force an exact characteristic-zero value.

A standard-library point counter checks four explicit rational packets:

| packet | `a_P` | `a_P mod 5` | result |
|---|---:|---:|---|
| `3.3.49.1-27.1-a` | `-4` | `1` | eliminated |
| `3.3.49.1-49.1-a` | `-5` | `0` | survives this filter |
| `3.3.49.1-729.1-b` | `0` | `0` | survives this filter |
| `3.3.49.1-1323.1-b` | `-4` | `1` | eliminated |

Run:

```bash
python3 scripts/check_signature_357_mod5_hecke_filter.py --self-test
python3 scripts/check_signature_357_mod5_hecke_filter.py
```

Certificate digest:

```text
7deb530855d6f604c21561d73ac43db23335eb86ef7770f8b3e8aeba93c4378d
```

These four packets are examples, not a complete enumeration of the 16 levels.

## 5. Exact remaining task

The global problem has been reduced to the following finite program:

1. enumerate the parallel-weight-two Hilbert newforms over `K7` at the 16 levels
   dividing `p3^3*p7^3`;
2. apply the exact residual condition `a_P=0 mod 5`;
3. attach the fixed-`7` form on `Q(sqrt(5))`;
4. use the exact parameter relation

   ```text
   u+t7=1
   ```

   to compare joint trace pairs, not independent marginal trace sets;
5. eliminate every remaining pair with replayable resultant and local-type
   certificates.

The new result removes residual irreducibility as a global obstruction and cuts
the automorphic level frontier from 24 to 16 levels. What remains is finite
Hilbert-newform enumeration and two-Frey cross-elimination.
