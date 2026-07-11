# BR-21: Zsigmondy / Primitive-Divisor Mathlib Audit

Date: 2026-07-11

Repository audited: `Th0rgal/beal-conjecture-lean`

Pinned Lean/Mathlib revision from `lakefile.toml`: Lean `v4.31.0`, Mathlib `v4.31.0`
(`mathlib4` commit audited locally: `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`).

## Scope

Audit Mathlib for primitive prime divisor / Zsigmondy-style theorems applicable
to expressions of the form `A ^ n - B ^ n` or `A ^ n + B ^ n`, especially under
coprimality assumptions. This audit does not attempt a Beal proof.

## Build status

`lake build` could not be run in this environment because `lake` is not on
`PATH`. The repository itself pins Mathlib `v4.31.0`; the Mathlib audit below
was performed by locally cloning that tag and searching the source.

## Exact searches performed

Targeted source searches in Mathlib `v4.31.0`:

- `Zsigmondy`
- `zsigmondy`
- `Primitive.*divisor`
- `primitive.*divisor`
- `primitive prime`
- `prime divisor`
- `multiplicativeOrder`
- `orderOf`
- `orderOf_dvd`
- `pow.*eq_one`
- `ModEq.*pow`
- `dvd.*sub.*pow`
- `pow.*sub.*pow`
- `pow.*add.*pow`
- `Cyclotomic`
- `cyclotomic`
- `padicValNat.pow_add_pow`
- `Nat.emultiplicity_pow_add_pow`
- `Nat.pow_sub_one_gcd_pow_sub_one`
- `Nat.Prime.dvd_of_dvd_pow`
- `Nat.primeFactors_pow`
- `Nat.exists_prime_and_dvd`

## Found support

Mathlib has useful surrounding infrastructure:

- `Nat.exists_prime_and_dvd`
  Every natural number different from `1` has a prime divisor.

- `Nat.Prime.dvd_of_dvd_pow`
  If a prime divides `m ^ n`, then it divides `m`.

- `Nat.primeFactors_pow`
  Prime factors are unchanged by positive powers.

- `Nat.pow_sub_one_gcd_pow_sub_one`
  `gcd (a ^ b - 1) (a ^ c - 1) = a ^ gcd b c - 1`.
  This is useful for same-base divisibility chains, but not for coprime
  two-base Zsigmondy.

- `Polynomial.coprime_of_root_cyclotomic`
  If `(a : Nat)` is a root of `cyclotomic n (ZMod p)`, then `a.Coprime p`.

- `Polynomial.orderOf_root_cyclotomic_dvd`
  If `(a : Nat)` is a root of `cyclotomic n (ZMod p)`, then the multiplicative
  order of `a` modulo `p` divides `n`.

- `Nat.exists_prime_gt_modEq_one`
  For every nonzero `k` and bound `n`, there exists a prime `p > n` with
  `p ≡ 1 [MOD k]`. This proof uses a prime divisor of a cyclotomic evaluation,
  but it constructs a new auxiliary base `b = k * n!`; it is not a primitive
  divisor theorem for a specified `A ^ n - B ^ n`.

- `padicValNat.pow_add_pow`
  Plus-sign LTE for odd primes:
  `padicValNat p (x ^ n + y ^ n) =
   padicValNat p (x + y) + padicValNat p n`
  under `p.Prime`, `Odd p`, `p ∣ x + y`, `¬ p ∣ x`, and `Odd n`.

- `padicValNat.pow_sub_pow`
  Minus-sign LTE for odd primes in the positive ordered natural-number form.

- `Odd.nat_add_dvd_pow_add_pow`
  If `n` is odd, then `x + y ∣ x ^ n + y ^ n`.

- `IsPrimitiveRoot.pow_sub_pow_eq_prod_sub_mul`
  Root-of-unity factorization of `x ^ n - y ^ n`.

- `IsPrimitiveRoot.pow_add_pow_eq_prod_add_mul`
  Root-of-unity factorization of `x ^ n + y ^ n` for odd `n`.

## Not found

No Mathlib declaration was found that states Zsigmondy's theorem, Bang-Zsigmondy,
or a primitive prime divisor theorem for either:

- `A ^ n - B ^ n`
- `A ^ n + B ^ n`
- Lucas / Lehmer sequences
- "there exists a prime dividing `A ^ n - B ^ n` but not any earlier
  `A ^ m - B ^ m`"
- "there exists a prime `p` with `orderOf (A / B mod p) = n`"

The closest theorem, `Nat.exists_prime_gt_modEq_one`, proves infinitely many
primes in the congruence class `1 mod k`; it does not take a fixed coprime pair
`A, B`, and does not yield a prime divisor of `A ^ n - B ^ n` or `A ^ n + B ^ n`.

## Minimal useful bridge statement

A local bridge for Beal should not try to prove the full primitive divisor
theorem immediately. The smallest useful statement is an axiom-free theorem
shape that converts a primitive divisor of a same-exponent difference into the
order/congruence data that Beal-side arguments would consume.

```lean
namespace BealUnified

/--
Primitive divisor data for `A ^ n - B ^ n`: a prime divisor of the nth
difference that divides no earlier positive difference.
-/
def PrimitivePowSubDivisor (p A B n : Nat) : Prop :=
  p.Prime ∧ p ∣ A ^ n - B ^ n ∧
    ∀ m : Nat, 0 < m → m < n → ¬ p ∣ A ^ m - B ^ m

/--
Minimal Zsigmondy-style bridge needed downstream: primitive divisor data forces
the residue ratio `A / B` to have exact order `n` modulo `p`, hence `n ∣ p - 1`.

This is a bridge theorem, not Zsigmondy's existence theorem.
-/
theorem primitive_pow_sub_divisor_order_bridge
    {p A B n : Nat}
    (hn : 0 < n)
    (hAp : Nat.Coprime A p)
    (hBp : Nat.Coprime B p)
    (hprim : PrimitivePowSubDivisor p A B n) :
    orderOf (ZMod.unitOfCoprime A hAp * (ZMod.unitOfCoprime B hBp)⁻¹) = n ∧
      n ∣ p - 1

end BealUnified
```

Expected proof route:

1. `p ∣ A ^ n - B ^ n` gives `(A / B)^n = 1` in `(ZMod p)ˣ`.
2. `orderOf_dvd_of_pow_eq_one` gives `orderOf (...) ∣ n`.
3. If the order is a proper positive divisor `m < n`, then
   `p ∣ A ^ m - B ^ m`, contradicting primitivity.
4. `ZMod.orderOf_dvd_card_sub_one` gives `n ∣ p - 1`.

This statement is intentionally scoped to the minus-sign same-exponent case.
The plus-sign case can be reduced to a minus-sign order statement by requiring
`n` odd and treating `A ^ n + B ^ n = A ^ n - (-B) ^ n` over `ZMod p`, but that
requires a clean signed or unit-level API. It is not the first bridge to build.

## Feasibility

A small compiling bridge file is plausible once Lean/Lake is available, but it
is not feasible to add safely in this environment without `lake build`.

The bridge above should be provable from existing Mathlib group/order/ZMod
infrastructure, after some unit-coprimality plumbing. However, that bridge only
consumes primitive-divisor data. It does not prove such a divisor exists.

The smallest missing dependency for actual Zsigmondy use is:

```lean
theorem exists_primitive_prime_dvd_pow_sub
    {A B n : Nat}
    (hcop : Nat.Coprime A B)
    (hApos : 0 < A) (hBpos : 0 < B)
    (hn : 2 ≤ n)
    (hexception : ¬ ZsigmondyException A B n) :
    ∃ p : Nat, PrimitivePowSubDivisor p A B n
```

No equivalent theorem appears in Mathlib `v4.31.0`.

## Recommendation

Result: **retry**, narrowly.

Retry BR-21 as an implementation task only after a working Lean toolchain is
available. The next task should prove the local bridge
`primitive_pow_sub_divisor_order_bridge`, without introducing any theorem that
asserts primitive divisors exist. Do not attempt a Beal proof from this axis yet.

The Zsigmondy existence theorem itself should be treated as a missing Mathlib
dependency, not as something already available under another name.
