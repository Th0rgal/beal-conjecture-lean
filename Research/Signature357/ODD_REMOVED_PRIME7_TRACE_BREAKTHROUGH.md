# Odd `(3,5,7)` branch: the removed-prime trace at `7`

## Status

This note records a new local condition on the cyclotomically untwisted residual
mod-`5` representation.  It does not by itself eliminate a level and is not
imported by `BealUnified.Trusted`.

## 1. Local Steinberg form before reduction

After twisting by the quadratic character of

```text
Q(zeta_7)/Q(zeta_7)^+,
```

the odd-branch representation is Steinberg at the unique prime `p7` above `7`.
Up to an unramified character `mu`, its Weil--Deligne representation has
semisimplification

```text
mu*chi_5 direct_sum mu
```

and nonzero monodromy in characteristic zero.  The determinant normalization of
the rank-two HGM constituent gives

```text
mu^2=1
```

residually.

The exact monodromy calculation shows that the extension class vanishes modulo
`5` exactly when

```text
v_7(A) = 3 mod 5.
```

This is precisely the conductor-drop case `e7=0`.

## 2. Frobenius trace when the prime is removed

The residue field at `p7` has cardinality

```text
q=7.
```

If the monodromy extension dies modulo `5`, the residual representation becomes
unramified with Frobenius eigenvalues

```text
mu*q, mu.
```

Therefore its trace is

```text
mu*(q+1)=+/-8=2 or 3 mod 5.
```

Consequently every level-lowered Hilbert eigensystem at a level with `e7=0`
must satisfy

```text
a_p7 = +/-(7+1) mod 5.
```

Equivalently it is killed by

```text
(T_p7-8)(T_p7+8)
```

in the residual Hecke module.

This is the standard removed-multiplicative-prime condition, but here it becomes
available only after the cyclotomic untwist and the exact monodromy calculation.

## 3. Immediate target

Among the current odd levels, this applies to

```text
19683 = 27^3
```

and to the already eliminated low level `729=27^2`.  The level `19683` residual
Hecke computation should therefore start with the simultaneous conditions

```text
T_2=0,
(T_p7-8)(T_p7+8)=0,
```

before applying the inert/split semilinear trace sieve.

## Trust boundary

The finite polynomial condition is elementary.  Its use depends on the imported
claims that:

- the cyclotomic untwist has Steinberg local type;
- the monodromy class vanishes modulo `5` exactly in the recorded congruence
  class of `v_7(A)`;
- the determinant has the stated cyclotomic normalization;
- level lowering removes `p7` in the conductor-drop case.
