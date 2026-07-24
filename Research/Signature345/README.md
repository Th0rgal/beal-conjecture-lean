# Signature (3,4,5): Edwards and source-index certificates

## Status

This directory contains the first replayable stages of a certified proof pipeline
for the mathematically solved signature `(3,4,5)`.

The source is Siksek--Stoll, *Partial descent on hyperelliptic curves and the
generalized Fermat equation x^3+y^4+z^5=0*, arXiv `1103.1979v1`, DOI
`10.1112/blms/bdr086`.

The paper starts from Edwards' parametrization of primitive solutions of

```text
a^2 + b^3 + c^5 = 0
```

and prints 27 binary dodecics `h_i`. It derives degree-20 and degree-30
covariants `g_i` and `f_i`, then adds 22 sign variants, producing 49 triples.

## Edwards identity certificate

Run:

```bash
python3 scripts/check_signature_345_edwards.py --self-test
python3 scripts/check_signature_345_edwards.py
```

The checker uses only Python's standard library and exact `Fraction` arithmetic.
It:

1. rejects duplicate JSON keys and non-canonical rational coefficients;
2. reconstructs each binary dodecic as
   `sum binom(12,i) alpha_i u^i v^(12-i)`;
3. derives `g = (h_uu*h_vv - h_uv^2) / 132^2`;
4. derives `f = (h_u*g_v - h_v*g_u) / 240`;
5. verifies that `f`, `g`, and `h` have integral coefficients and homogeneous
   degrees `30`, `20`, and `12`;
6. verifies the exact polynomial identity `f^2 + g^3 + h^5 = 0`;
7. expands the exact 22 sign variants printed in the paper;
8. pins a SHA-256 digest for every triple and for the complete 49-form family.

The current family digest is:

```text
ec797c0014e827874da79765196c42209899fd6501109266f4b0c65956bba387
```

This is an independent replay of the algebraic heart of the Edwards table. It
removes Magma from this stage of the certification chain.

## Exact source-index finding for Sections 6.2--6.4

The earlier audit noticed that the later printed factorizations did not align
with the literal same-numbered Table-1 covariants. This has now been converted
from an observation into an exact replayable certificate.

Run:

```bash
python3 scripts/check_signature_345_published_factorizations.py --self-test
python3 scripts/check_signature_345_published_factorizations.py
```

The checker rebuilds, coefficient for coefficient, the three factorizations
printed in Sections 6.2, 6.3, and 6.4 and compares them against all reconstructed
Edwards polynomials. It proves the exact equalities:

```text
printed Section-6 f_2 = reconstructed Edwards form 28
printed Section-6 f_3 = reconstructed Edwards form 2
printed Section-6 f_5 = reconstructed Edwards form 3
```

The literal same-ID equalities are false for all three labels. In particular:

- reconstructed form 28 is the sign variant `-f_1`, and equals the polynomial
  printed later as `f_2`;
- reconstructed form 2 equals the polynomial printed later as `f_3`;
- reconstructed form 3 equals the polynomial printed later as `f_5`.

The full Edwards triple hashes are also checked, not merely the factor degrees.
The mapping digest is:

```text
adf38f8a8011cbc15cd7eba511e5299cb527c585c9451ab88c397281d2464e83
```

This does not by itself determine whether the discrepancy is a table-label
convention, a later-section relabelling, or a source erratum. It does establish
that a formal proof must not attach the published rational-point computation for
`C_2`, `C_3`, or `C_5` to the literal same-numbered reconstructed form without an
explicit correspondence certificate.

The practical gain is that the three low-genus quotient computations now have
unambiguous polynomial targets:

- `Y^2 = X^5 + 20736` attaches to reconstructed form 28;
- `Y^2 = X^3 + 25` attaches to reconstructed form 2;
- the genus-1 quotient built from the seven-factor decomposition attaches to
  reconstructed form 3.

A complete source-index manifest for all 49 labels is still required before the
local and Selmer computations can be assembled into one theorem.

## What remains before `(3,4,5)` can enter `BealUnified.Trusted`

### Stage 1 — completeness of the parametrization

Formalize or source-audit the implication:

```text
primitive a^2+b^3+c^5=0
  => one of the 49 reconstructed triples evaluated at coprime (u,v).
```

The identity checker proves that every listed triple produces a solution. It
does not prove that the list is exhaustive. The paper cites Edwards' original
parametrization for this step.

### Stage 2 — complete curve-index and local certificates

Extend the new three-entry factorization certificate to an explicit
permutation/sign/projective-transform manifest connecting all reconstructed
forms to every later `C_i` label. Then independently replay:

- the 16 curves with no `Q_2` point;
- the two curves with no `Q_3` point;
- the eight modulo-256 primitive-square exclusions;
- square-freeness of every relevant degree-30 binary form.

The paper leaves 23 curve labels after these local checks.

### Stage 3 — factorization and partial-Selmer certificates

For the 13 irreducible degree-30 cases, certify:

- the degree-5 field polynomial;
- factorization type `[6,24]` over that field;
- class-group and unit data;
- every local image used in the partial fake Selmer computation;
- emptiness of the resulting Selmer set.

For the ten remaining cases, certify the rational factorization and the
non-empty Selmer representatives used to construct covers.

### Stage 4 — low-genus quotient certificates

Independently replay the rational-point calculations on the quotient curves,
including:

- `Y^2 = X^5 + 20736`;
- `Y^2 = X^3 + 25`;
- the genus-1 curves whose Jacobians have rank zero in the final five cases.

The certificates must include Mordell--Weil group/rank evidence and the maps back
to the correctly indexed genus-14 curves.

### Stage 5 — Lean assembly

Only after Stages 1--4 should the repository expose a theorem equivalent to:

```lean
theorem no_primitive_signature_3_4_5 :
    ¬ PrimitiveGFESolution 3 4 5
```

No external computation should be trusted directly. The intended architecture
is producer output plus a separately implemented, fail-closed replay checker.
