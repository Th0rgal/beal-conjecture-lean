# Global Beal reduction: odd-prime exponent core and repeated-prime audit

## Status

This note records two global advances beyond an isolated signature calculation.

1. The solved-signature literature reduces every primitive positive Beal counterexample to a signature whose three exponents are **odd primes**.
2. A recent claimed complete proof of the repeated-prime family contains a direct-product decomposition-group error. Its valid group-theoretic consequence is a much weaker, but explicit, Mersenne-divisor sieve.

Neither result proves Beal. The remaining exponent space still contains two infinite cores:

```text
(p,p,q) with distinct odd primes p,q;
(p,q,r) with three distinct odd primes.
```

The first core is the repeated-prime core. The second is the genuinely three-exponent core.

## 1. Elementary canonical reduction

For every integer `n >= 3`, choose a divisor `e` as follows.

- If `4 | n`, take `e=4`.
- If `4` does not divide `n`, take an odd prime divisor `e` of `n`.

The second case is exhaustive. If `n` is odd, any prime divisor is odd. If `n` is even but not divisible by `4`, write `n=2m` with odd `m>=3` and choose an odd prime divisor of `m`.

Writing `n=k e` replaces

```text
X^n
```

by

```text
(X^k)^e.
```

Thus a primitive Beal solution reduces unconditionally to exponents in

```text
{4} union {odd primes}.
```

Primitivity is preserved: a prime dividing two of the new powered bases already divides the corresponding original bases.

## 2. Literature-assisted reduction to three odd primes

Ratcliffe and Grechuk classify the minimal non-all-prime hyperbolic signatures as the special triples. Their survey further states that, for the coefficient-one generalized Fermat equation, the only non-all-prime signatures still not covered are

```text
(2,5,9), (2,3,25).
```

Both contain exponent `2`, so neither is a Beal signature. The special triples whose minimum exponent is at least `3` are

```text
(3,3,4), (3,3,6), (3,3,9),
(3,4,4), (3,4,5), (4,4,4).
```

The corresponding coefficient-one equations are solved and have no primitive positive solution. Consequently, importing the survey's solved-case inventory gives the global implication

```text
primitive Beal counterexample
  => primitive counterexample with three prime exponents
  => primitive counterexample with three odd prime exponents.
```

Source:

- Ashleigh Ratcliffe and Bogdan Grechuk, *Generalised Fermat equation: a survey of solved cases*, arXiv:2412.11933v2, especially Table 1.1, Definition 1.5, Table 1.3, and the discussion immediately following Table 1.3.

This is a global reduction of the conjecture, not a proof of the remaining prime-exponent equations.

## 3. Effect of the candidate `(3,5,7)` closure

Assume the repository's candidate conditional proof of the primitive signature `(3,5,7)` survives expert audit.

The sorted odd-prime triples of exponent sum below `19` are exactly

```text
(3,3,3), (3,3,5), (3,3,7), (3,3,11),
(3,5,5), (3,5,7), (3,7,7),
(5,5,5), (5,5,7).
```

They are covered by FLT, the solved `(3,3,n)` and `(n,n,3)` families, the solved `(5,5,7)` case, and the candidate `(3,5,7)` theorem.

At exponent sum `19`, the sorted odd-prime triples are

```text
(3,3,13), (3,5,11), (5,7,7).
```

The first and third are covered by the same published families. Therefore the next smallest open Beal signature becomes

```text
(3,5,11).
```

This signature lies in the same `(5,p,3)` Frey family as `(3,5,7)` after rewriting

```text
A^3+B^5=C^11
```

as

```text
B^5+(-C)^11+A^3=0.
```

The existing fixed-level Hilbert machinery is therefore reusable, although residual characteristic `11` and the independent `mod 5` field `Q(zeta_11)^+` require new computations.

## 4. Audit of the claimed repeated-prime proof

The preprint

- Preda Mihailescu, *The strong Fermat-Catalan Equation*, arXiv:2509.18275v1

claims to eliminate

```text
x^p+y^p=z^q
```

for distinct odd primes `p>3` and `q`.

In its final decomposition-group step, put

```text
L = Q(zeta_p,zeta_q),
Gal(L/Q) = G' x H'.
```

For a rational prime `r != p,q`, the decomposition group is cyclic:

```text
D_r = <(a,b)>,
m = ord_p(r),
n = ord_q(r).
```

The paper obtains

```text
D_r intersect H' = {1}
```

and then infers that the fixed field `L^(D_r)` contains `Q(zeta_q)`, equivalently that `D_r` is contained in `G'`. That inference is false. A subgroup of a direct product can intersect one factor trivially while having nontrivial projection to that factor.

The exact statement is

```text
D_r intersect H' = {1}
  iff
ord_q(r) divides ord_p(r).
```

Indeed, the powers with trivial `G'` coordinate are the multiples of `m`; the intersection is trivial precisely when `b^m=1`, or `n|m`.

A concrete counterexample to the claimed implication is

```text
p=5, q=3, r=2:
ord_5(2)=4,
ord_3(2)=2.
```

The intersection is trivial because `2|4`, but the projection to `H'` is nontrivial and `2` is not `1 mod 3`.

Thus the claimed complete repeated-prime theorem cannot currently be used in a Beal proof.

## 5. Corrected conditional Mersenne-divisor sieve

Suppose, without importing the invalid fixed-field inference, that the preceding ideal argument in the preprint correctly establishes

```text
D_2 intersect H' = {1}
```

for a hypothetical solution. The corrected group theorem then gives

```text
ord_q(2) | ord_p(2).
```

Let

```text
g = gcd(p-1,q-1).
```

Since `ord_p(2)|(p-1)` and `ord_q(2)|(q-1)`, the divisibility above implies

```text
ord_q(2) | g,
```

and hence

```text
q | 2^g-1.
```

This is an explicit exponent-pair sieve. For example, if

```text
gcd(p-1,q-1)=2
```

and `q>3`, then `q` would have to divide `3`, which is impossible. Conversely, the condition is not universal: `(p,q)=(11,31)` survives because

```text
ord_11(2)=10,
ord_31(2)=5,
gcd(10,30)=10,
31 | 2^10-1.
```

The sieve is therefore useful but noncontractive. It does not close the repeated-prime core, and it remains conditional on independently certifying the preprint's earlier ideal-splitting input.

## 6. Exact remaining global target

After the prime-exponent reduction, a full Beal proof must eliminate:

```text
1. every repeated-prime signature (p,p,q);
2. every three-distinct-prime signature (p,q,r).
```

Isolated proofs cannot terminate this program. A sufficient cofinal theorem for the distinct-prime core would have the following contractive form:

```text
for sorted odd primes p<=q<=r,
any primitive solution satisfies r <= B(p,q),
and B(p,q) < q outside a finite boundary.
```

Then `r>=q` and `r<B(p,q)<q` would be contradictory outside that finite boundary. Existing fixed-pair asymptotic modular results do not currently provide such a contractive bound.

## Replay

```bash
python3 scripts/check_global_beal_prime_exponent_reduction.py --self-test
python3 scripts/check_global_beal_prime_exponent_reduction.py
python3 scripts/check_global_beal_repeated_prime_audit.py --self-test
python3 scripts/check_global_beal_repeated_prime_audit.py
```

The checkers replay the finite exponent inventory, canonical factorization algorithm, direct-product subgroup calculation, multiplicative-order consequences, certificate hashes, and negative fixtures. They do not replace the imported solved-case literature or the unverified ideal-theoretic part of the repeated-prime preprint.
