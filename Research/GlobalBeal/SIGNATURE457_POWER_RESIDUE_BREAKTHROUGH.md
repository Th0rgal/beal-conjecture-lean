# Signature `(4,5,7)`: full-modulus power-residue structure

## Status

This note proves unconditional necessary conditions for a primitive positive
solution of

\[
A^4+B^5=C^7.
\]

It does **not** eliminate the signature and does not prove the Beal conjecture.
The point is that the next corrected canonical boundary is not merely subject
to quadratic residue tests prime by prime: it satisfies exact power identities
modulo the full composite powers \(A^4,B^5,C^7\).

Throughout assume

\[
A,B,C>0,
\qquad \gcd(A,B)=\gcd(B,C)=\gcd(A,C)=1.
\]

## 1. Exact parity classification

Pairwise coprimality permits at most one even base. All three bases cannot be
odd because the left side would be even and the right side odd. Therefore
exactly one of \(A,B,C\) is even.

The equation modulo \(32\) gives three disjoint branches.

### `A` even

Then \(B,C\) are odd. In the unit group modulo \(32\), every odd element has
order dividing \(8\). From

\[
C^7\equiv B^5+A^4\pmod {32}
\]

and \(A^4\in\{0,16\}\), inversion of the seventh-power map gives

\[
\boxed{C\equiv B^3+A^4\pmod {32}.}
\]

Moreover,

\[
A^4\equiv
\begin{cases}
16\pmod {32},&v_2(A)=1,\\
0\pmod {32},&v_2(A)\ge2.
\end{cases}
\]

### `B` even

Here \(B^5\equiv0\pmod {32}\), so

\[
C^7\equiv A^4\pmod {32}.
\]

Raising both sides to the inverse exponent \(7\) in the odd unit group yields

\[
\boxed{C\equiv A^4\pmod {32}},
\qquad
\boxed{C\equiv1\pmod {16}}.
\]

### `C` even

Now \(C^7\equiv0\pmod {32}\), and hence

\[
B^5\equiv-A^4\pmod {32}.
\]

The fifth-power map is its own inverse on the odd unit group modulo \(32\), so

\[
\boxed{B\equiv-A^4\pmod {32}},
\qquad
\boxed{B\equiv-1\pmod {16}}.
\]

## 2. Full-modulus fourth roots

Modulo \(B^5\), the equation gives \(A^4\equiv C^7\). Both \(A\) and \(C\)
are units, so for

\[
u=C^2A^{-1}\pmod {B^5}
\]

we have

\[
u^4=C^8A^{-4}\equiv C.
\]

Thus \(C\) is a fourth power modulo the full modulus \(B^5\).

Modulo \(C^7\), define

\[
v=-AB^{-1}.
\]

Since \(A^4\equiv-B^5\),

\[
v^4=A^4B^{-4}\equiv-B\pmod {C^7}.
\]

Thus \(-B\) is a fourth power modulo the full modulus \(C^7\).

## 3. One common parameter modulo `A^4`

Modulo \(A^4\), \(B^5\equiv C^7\). Put

\[
t=B^3C^{-4}.
\]

Then

\[
\begin{aligned}
t^7&=B\,(B^5)^4(C^7)^{-4}\equiv B,\\
t^5&=C\,(B^5)^3(C^7)^{-3}\equiv C.
\end{aligned}
\]

Therefore

\[
\boxed{B\equiv t^7,
\qquad C\equiv t^5
\pmod {A^4}.}
\]

## 4. Independently checkable replay

```bash
python3 scripts/check_global_beal_signature457_power_residue.py --self-test
python3 scripts/check_global_beal_signature457_power_residue.py
```

The symbolic group identities are formalized in

```text
BealUnified/Research/Signature457.lean
```

The remaining gap is substantive: these are necessary conditions, but no
complete descent or modular contradiction from them is presently proved.
