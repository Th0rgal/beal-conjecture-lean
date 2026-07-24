# Signature (3,4,5): Edwards identity certificate

## Status

This directory contains the first replayable stage of a certified proof pipeline
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

## What is now independently checked

Run:

```bash
python3 scripts/check_signature_345_edwards.py --self-test
python3 scripts/check_signature_345_edwards.py
```

The checker uses only Python's standard library and exact `Fraction` arithmetic.
It:

1. rejects duplicate JSON keys and non-canonical rational coefficients;
2. reconstructs each binary dodecic as
   `Σ binom(12,i) α_i u^i v^(12-i)`;
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

## Important source-audit finding: case labels are not yet certified

A literal reconstruction of Table 1 and the printed differential formulas
produces factorization fingerprints that do not line up directly with the case
labels used later in Section 6.

For example:

- the covariant derived from printed `h_1` is the negative of the polynomial
  displayed later as `f_2`;
- printed `h_2` gives the factorization displayed later for `f_3`;
- printed `h_3` gives the factorization displayed later for `f_5`.

This may be an indexing, sign, or projective-change convention inherited from
the original Edwards parametrization. It is not treated here as a mathematical
error. It does mean that a **separate, explicit index-map certificate** is
required before later claims such as “curve `C_15` has empty partial Selmer set”
can be attached to one of the reconstructed Table-1 triples.

The present checker therefore certifies the 49 algebraic triples as a family,
but deliberately does not claim that a raw Table-1 ID has already been matched
to every later curve label.

## What remains before `(3,4,5)` can enter `BealUnified.Trusted`

### Stage 1 — completeness of the parametrization

Formalize or source-audit the implication:

```text
primitive a^2+b^3+c^5=0
  ⇒ one of the 49 reconstructed triples evaluated at coprime (u,v).
```

The identity checker proves that every listed triple produces a solution. It
does not prove that the list is exhaustive.

### Stage 2 — curve-index and local certificates

Produce an explicit permutation/projective-transform manifest connecting the
49 reconstructed triples to the paper's `C_i` labels. Then independently replay:

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

These certificates must include the Mordell--Weil group/rank evidence and the
map back to each genus-14 curve.

### Stage 5 — Lean assembly

Only after Stages 1--4 should the repository expose a theorem equivalent to:

```lean
theorem no_primitive_signature_3_4_5 :
    ¬ PrimitiveGFESolution 3 4 5
```

No external computation should be trusted directly. The intended architecture
is producer output plus a separately implemented, fail-closed replay checker.
