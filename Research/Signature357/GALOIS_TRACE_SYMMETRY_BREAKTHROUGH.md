# Semilinear Galois trace symmetry for the two `(3,5,7)` Frey systems

## Status

This note records a literature-assisted structural reduction. It does **not**
prove signature `(3,5,7)` and it is not imported by `BealUnified.Trusted`.

The new point is that a rational specialization does not produce arbitrary
Hilbert-newform traces at the conjugate primes of the totally real base field.
The traces are Frobenius conjugates in the residual coefficient field.

This supplies two filters that were absent from the previous marginal newform
computations:

```text
at inert rational primes:
  the residual trace must be scalar;

at split rational primes:
  the traces at conjugate prime ideals satisfy explicit Frobenius-power
  relations.
```

## Motive-theoretic input

For rational `t`, Golfieri--Pacetti's Galois-action formula sends

```text
H((a,b),(c,d)|t)
```

under `zeta_N -> zeta_N^j` to

```text
H((j*a,j*b),(j*c,j*d)|t).
```

The relevant rank-two constituents also occur in the new part of a
hyperelliptic curve defined over `Q`, with real multiplication by the totally
real coefficient field. The resulting action is semilinear: conjugating a
base-field prime also conjugates the real-multiplication coefficient.

The finite calculations below import this semilinear descent statement. They
do not treat it as a Python theorem.

## Independent mod-5 system

Let

```text
K7 = Q(zeta_7)^+.
```

The prime `5` is inert in `K7`, so its residue field is `F_125`. A generator of
`Gal(K7/Q)` acts on this residue field by

```text
x -> x^5.
```

For an unramified prime ideal `l` and a generator `sigma` of the cubic Galois
group, the residual traces therefore satisfy

```text
a_(sigma l)   = a_l^5,
a_(sigma^2 l) = a_l^25.
```

If a rational prime is inert in `K7`, its unique prime ideal is fixed by
`sigma`; hence

```text
a_l^5 = a_l,
```

so

```text
a_l in F_5.
```

For a trace polynomial `P`, compatibility at such a prime requires

```text
gcd(P mod 5, X^5-X) != 1.
```

At a completely split rational prime, a residual Hecke eigensystem must lie in
one of the two cyclic orientations cut out by

```text
T_(sigma l)   - T_l^5,
T_(sigma^2 l) - T_l^25.
```

## Fixed-7 system

Let

```text
K5 = Q(sqrt(5)).
```

The prime `7` is inert in `K5`, with residue field `F_49`; the nontrivial
Galois automorphism acts by

```text
x -> x^7.
```

Thus conjugate-prime traces satisfy

```text
a_(sigma l) = a_l^7.
```

At a rational prime inert in `K5`, the unique prime is fixed, so

```text
a_l in F_7.
```

Equivalently, a candidate trace polynomial `P` must satisfy

```text
gcd(P mod 7, X^7-X) != 1.
```

At split primes the two Hecke operators must satisfy

```text
T_(sigma l) - T_l^7 = 0
```

on the residual eigensystem.

## Immediate application to the odd frontier

The two non-CM superspecial fixed-7 packets at level `(2,3)` are packets `24`
and `28`. The rational primes `13` and `43` are inert in `K5`. Therefore their
base-field trace polynomials for either packet must have a linear factor modulo
`7`. This is an additional necessary test before the full two-Frey parameter
graph is considered.

On the mod-5 side, auxiliary rational primes in residue classes

```text
2,3,4,5 mod 7
```

are inert in `K7`. Their Hecke traces must be scalar modulo `5`. The existing
residual Hecke-module sieve currently uses only split primes `13,29,41,43`;
adding inert primes is therefore genuinely new information, not a restatement
of the current marginal trace filter.

## Replay

Run:

```bash
python3 scripts/check_signature_357_galois_trace_symmetry.py --self-test
python3 scripts/check_signature_357_galois_trace_symmetry.py
```

The manifest is:

```text
Research/Signature357/galois_trace_symmetry.json
```

with digest:

```text
81bb184460ad4af3ab19fbdd1f19c7cc8458c3f5fe8094546628cfffbafce116
```

The checker verifies:

- irreducibility of the defining polynomials modulo `5` and `7`;
- the exact sizes and Frobenius fixed fields of `F_125` and `F_49`;
- the splitting classes of rational primes in the real cubic and real quadratic
  fields;
- the two polynomial filters;
- negative fixtures and duplicate-key rejection.

## Trust boundary

The semilinear motive descent and the modular identification are imported
research inputs. The finite-field and splitting calculations are independently
replayed. No absence of a database record or failed external computation is
interpreted as a theorem.
