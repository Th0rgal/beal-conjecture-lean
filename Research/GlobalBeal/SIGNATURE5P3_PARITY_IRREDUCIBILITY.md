# Signature `(5,p,3)`: parity-complete residual irreducibility

Let

\[
a^5+b^p+c^3=0
\]

be a non-trivial primitive integer solution, with prime `p>13`, and let
`rho_p^+`, `rho_p^-` be the two rank-two residual representations over
`K=Q(sqrt(5))` used by Pacetti--Villagra Torcomian.

Then

\[
\boxed{\text{at least one of }\bar\rho_p^+,\bar\rho_p^-
       \text{ is absolutely irreducible}.}
\]

If `b` is odd, Corollary 7.7 of the source applies at `ell=2`; its explicit
bound is `C(2)=13`, so both signs are absolutely irreducible.

If `b` is even, primitivity makes `a,c` odd. Modulo `4`,

\[
a^5+c^3\equiv0,
\qquad a^5\equiv3c^3.
\]

Proposition 3.15 therefore gives conductor exponent `5` at the prime above `2`
for the minus motive. Theorem 7.2 of Golfieri--Pacetti identifies this local
type as induction from `Q_2(i)/Q_2` of an order-four character and shows that
its odd residual congruences remain supercuspidal after unramified base change.
The completion of `Q(sqrt(5))` at `2` is unramified quadratic, hence linearly
disjoint from the ramified quadratic `Q_2(i)`. Since `p` is odd, reduction
preserves the order-four character and Mackey's criterion keeps the induced
local representation absolutely irreducible. Global reducibility would imply
local reducibility, so `rho_p^-` is globally absolutely irreducible.

This is a uniform residual-image theorem for the complete parity split of the
`(5,p,3)` family. It is not yet a no-solution theorem: fixed-`5` modularity of
the minus motive in the even-`b` branch, followed by a uniform newform
elimination, remains to be proved.

Replay:

```bash
python3 scripts/check_global_beal_signature5p3_parity_irreducibility.py --self-test
```
