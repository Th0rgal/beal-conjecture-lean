# Breakthrough: full Beal reduces to the odd-prime exponent core

## Status

This note proves an **unconditional exponent-graph reduction** and then states a
small, explicit literature-assisted corollary.

It does **not** prove the Beal conjecture. It removes the infinite
composite-exponent part of the problem: after six finite boundary signatures
are dealt with, every primitive counterexample has three odd-prime exponents.

The finite arithmetic is replayed by:

```bash
python3 scripts/check_beal_odd_prime_reduction.py --self-test
python3 scripts/check_beal_odd_prime_reduction.py
```

The three non-diagonal boundary theorems remain literature imports until their
proofs or exact certificates are reconstructed in the repository.

## 1. Divisor shadows

For a signature `(x,y,z)`, a **coordinatewise divisor shadow** is a triple

```text
(d_x,d_y,d_z),  d_x|x, d_y|y, d_z|z.
```

A solution

```text
A^x + B^y = C^z
```

induces a solution at the shadow:

```text
(A^(x/d_x))^d_x + (B^(y/d_y))^d_y = (C^(z/d_z))^d_z.
```

Positivity and pairwise coprimality are preserved. Replacing at least one
exponent by a proper divisor strictly decreases `x+y+z`, so descent through
hyperbolic divisor shadows terminates.

Write

```text
H(p,q,r) : p*q+p*r+q*r < p*q*r,
```

which is the cleared-denominator form of

```text
1/p + 1/q + 1/r < 1.
```

A hyperbolic signature is called **special** when it is not all-prime and every
proper coordinatewise divisor shadow is non-hyperbolic.

For Beal exponents, all coordinates are at least `3`. Hence

```text
1/x+1/y+1/z <= 1,
```

with equality only for `(3,3,3)`. That diagonal case is already excluded by
Fermat's Last Theorem. Every hypothetical primitive Beal counterexample
therefore has a hyperbolic signature, and repeated descent ends either at an
all-prime signature or at a special signature.

## 2. Exact classification in the Beal range

Order the coordinates:

```text
3 <= p <= q <= r.
```

Then the special signatures are exactly

```text
(3,3,4), (3,3,6), (3,3,9),
(3,4,4), (3,4,5),
(4,4,4).
```

### Case `p >= 5`

Because the triple is not all-prime, one coordinate is composite. Every
composite integer at least `6` has a proper divisor at least `3`. Replace that
coordinate by such a divisor. The new reciprocal sum is at most

```text
1/3 + 1/5 + 1/5 = 11/15 < 1.
```

This is a proper hyperbolic divisor shadow, contradicting specialness.

Thus `p <= 4`.

### Case `p = 4`

The proper shadow `(2,q,r)` must be non-hyperbolic:

```text
1/2 + 1/q + 1/r >= 1.
```

As `q,r >= 4`, equality is possible only when

```text
q=r=4.
```

This gives `(4,4,4)`.

### Case `p = 3` and `q >= 5`

If `q` or `r` is composite, replace that coordinate by a proper divisor at
least `3`. The reciprocal sum of the shadow is at most

```text
1/3 + 1/3 + 1/5 = 13/15 < 1.
```

If neither is composite, all three coordinates are prime. Neither possibility
is special. Hence a special triple with `p=3` has `q <= 4`.

### Case `(p,q) = (3,4)`

The shadow `(3,2,r)` must be non-hyperbolic:

```text
1/3 + 1/2 + 1/r >= 1,
```

so `r <= 6`. The original triple is hyperbolic for `r >= 4`.
The value `r=6` is not special because `(3,4,3)` is a proper hyperbolic
shadow. Therefore:

```text
r in {4,5}.
```

This gives `(3,4,4)` and `(3,4,5)`.

### Case `(p,q) = (3,3)`

The coordinate `r` must be composite. Let `d` be its largest proper divisor.
The shadow `(3,3,d)` must be non-hyperbolic:

```text
2/3 + 1/d >= 1,
```

hence `d <= 3`.

If `r` is even, then `r/2 <= d <= 3`, so `r` is `4` or `6`.
If `r` is odd and composite, its smallest prime divisor is at least `3`, so

```text
r/3 <= d <= 3,
```

and `r <= 9`; the only odd composite possibility is `9`.

This gives `(3,3,4)`, `(3,3,6)`, and `(3,3,9)`.

The classification is complete.

## 3. The finite boundary

Three entries reduce immediately to trusted diagonal Fermat cases:

```text
(3,3,6) -> (3,3,3) by C^6=(C^2)^3,
(3,3,9) -> (3,3,3) by C^9=(C^3)^3,
(4,4,4) is FLT at exponent 4.
```

The remaining boundary consists of only:

```text
(3,3,4), (3,4,4), (3,4,5),
```

up to orientation/permutation.

Their current status is **literature solved, formalization pending**:

- `(3,3,4)`: N. Bruin, *On powers as sums of two cubes*, ANTS-IV,
  LNCS 1838 (2000), 169--184.
- `(3,4,4)`: H. Cohen, *Number Theory, Vol. II*, Proposition 14.6.6,
  GTM 240, Springer (2007).
- `(3,4,5)`: S. Siksek and M. Stoll, *Partial descent on hyperelliptic
  curves and the generalized Fermat equation x^3+y^4+z^5=0*,
  Bull. Lond. Math. Soc. 44 (2012), 151--166.

The repository must still reconstruct the exact theorem statements,
orientation conventions, and proof/certificate boundaries before treating
these rows as trusted.

## 4. Global consequence

### Unconditional reduction

Every primitive Beal counterexample has a coordinatewise divisor shadow whose
signature is either:

1. three odd primes; or
2. one of the six special signatures classified above.

### Literature-assisted reduction

After importing the three finite literature boundary theorems, every primitive
Beal counterexample has a signature

```text
(p,q,r)
```

with `p,q,r` all odd primes.

This strictly strengthens the current trusted normalization

```text
each exponent is 4 or an odd prime.
```

The exponent `4` no longer belongs to the infinite open core.

## 5. Exact remaining infinite frontier

The odd-prime core splits into three parts.

1. **Diagonal**: `(p,p,p)`. Closed by Fermat's Last Theorem.
2. **Repeated-prime**: up to permutation, `(p,p,q)` with distinct odd primes.
   This is still an infinite open frontier; the complete cyclotomic
   perfect-power split is the next elementary reduction.
3. **Pairwise distinct**: `(p,q,r)` with three distinct odd primes.
   This is the hypergeometric/multi-Frey frontier.

Assuming the candidate `(3,5,7)` proof is valid removes the first
pairwise-distinct node. It does not close an infinite divisibility cone:
an odd prime exponent has no proper exponent divisor greater than `1`.

## 6. What would now prove Beal

The full conjecture follows once the following two uniform statements are
proved:

```text
no primitive solution for any repeated odd-prime signature (p,p,q), p != q;
no primitive solution for any pairwise-distinct odd-prime signature (p,q,r).
```

Equivalently, it is enough to prove one uniform odd-prime-core theorem covering
both cases.

No currently imported theorem in this repository supplies that uniform step.
The reduction here is therefore a genuine global compression, not a completed
proof claim.
