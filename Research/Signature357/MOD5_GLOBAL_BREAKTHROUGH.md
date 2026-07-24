# Global mod-5 reduction for signature `(3,5,7)`

## Status

This note records a literature-assisted reduction, not a proof of `(3,5,7)` and
not a theorem in `BealUnified.Trusted`.

The new conclusion is:

```text
every hypothetical primitive positive A^3+B^5=C^7 solution
  carries an absolutely irreducible residual mod-5 plus HGM representation
  over K7 = Q(zeta_7)^+.
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

with parameter `u=C^7/A^3` over `K7=Q(zeta_7)^+` and residual characteristic
`5`.

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
their sum reduces exactly to the rational integer `-9` in
`Z[zeta_21]`. After the same normalization the full cyclotomic trace is

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
`B` is odd and the new prime-2 theorem applies.

In the odd branch, `3` does not divide `A*B*C`; the previously certified
supercuspidal local type at `3` gives absolute irreducibility modulo `5`.

Therefore every hypothetical primitive solution has an absolutely irreducible
mod-`5` HGM representation.

Run:

```bash
python3 scripts/check_signature_357_mod5_global.py --self-test
python3 scripts/check_signature_357_mod5_global.py
```

Certificate digest:

```text
3ffd34b812498338af63108981cee5aa21d17d3600af2227d4e9bac1403ea29b
```

## 3. Finite automorphic frontier

Golfieri--Pacetti's plus family is modular for the orientation above. Combining
absolute irreducibility, finite flatness at `5`, residual ramification control,
and standard Hilbert level lowering reduces the representation to a
parallel-weight `(2,2,2)` Hilbert newform over `K7`.

The exact wild-prime bounds must use Theorem 7.4, not only the coarser
prime-to-base branch of Corollary 7.5:

- at the prime over `3`, the even Dahmen--Siksek branch can have negative
  parameter valuation not divisible by `3`, so the safe global exponent bound is
  `5`;
- at the prime over `7`, the odd branch has positive valuation divisible by `3`
  and the even branch has either unit valuation or negative valuation divisible
  by `7`; the exceptional `q+2` cases do not occur, so the bound is `3`.

Thus the prime-to-`5` level divides

```text
p3^5 * p7^3.
```

Here `3` is inert in `K7`, so `N(p3)=27`, while `7` is totally ramified and
`N(p7)=7`. Consequently:

```text
maximum level norm = 27^5 * 7^3 = 4,921,675,101;
possible exponent pairs = (e3,e7) with 0 <= e3 <= 5 and 0 <= e7 <= 3;
number of level divisors = 24.
```

This is still a finite modular-form problem. The current certificate does not
enumerate those spaces. The earlier provisional `p3^3*p7^3` bound was too
optimistic and has been removed from the checker.

## 4. Exact prime-2 Hecke filter

Let `P` be the unique prime of `K7` above `2`; `N(P)=8`. If `a_P` is the Hecke
eigenvalue over `K7`, then after the degree-2 extension to `Q(zeta_21)^+`,

```text
Tr(Frob_P^2) = a_P^2 - 16.
```

The two `B`-odd traces therefore impose:

```text
C even: a_P = +/-5;
A even: a_P = 0.
```

A standard-library point counter over `F_8` checks four explicit rational
Hilbert-newform packets:

| packet | `a_P` | result |
|---|---:|---|
| `3.3.49.1-27.1-a` | `-4` | eliminated in both branches |
| `3.3.49.1-49.1-a` | `-5` | compatible only when `C` is even |
| `3.3.49.1-729.1-b` | `0` | compatible only when `A` is even |
| `3.3.49.1-1323.1-b` | `-4` | eliminated in both branches |

Run:

```bash
python3 scripts/check_signature_357_mod5_hecke_filter.py --self-test
python3 scripts/check_signature_357_mod5_hecke_filter.py
```

Certificate digest:

```text
1e293c16e00b5f71419cf5bc05718be58537f67d0acc1e7b207d2b72f9a61475
```

These four packets are examples, not a complete enumeration of the 24 levels.

## 5. Exact remaining task

The global problem has been reduced to the following finite program:

1. enumerate the parallel-weight-two Hilbert newforms over `K7` at the 24 levels
   dividing `p3^5*p7^3`;
2. apply the exact `a_P in {0,+/-5}` prime-2 filter, with the parity branch
   retained;
3. attach the fixed-`7` form on `Q(sqrt(5))`;
4. use the exact parameter relation

   ```text
   u+t7=1
   ```

   to compare joint trace pairs, not independent marginal trace sets;
5. eliminate every remaining pair with replayable resultant and local-type
   certificates.

The new result removes residual irreducibility as a global obstruction on the
mod-`5` side. What remains is finite automorphic enumeration and two-Frey
cross-elimination.
