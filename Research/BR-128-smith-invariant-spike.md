# BR-128 — Smith-invariant / Mathlib API falsification spike

## Provenance and scope

- Source repository head: `6440b5f586eb9ef60213263c01e199f928609838` (live `main`, verified 2026-07-24).
- Lean toolchain: `leanprover/lean4:v4.31.0`.
- Mathlib lock/source audited: `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.
- Requested packet locator: `/var/lib/hermes-assistant/workspace/inputs/beal-20260724.txt`.
- Required packet SHA-256: `c20bc824c5c25fd472e2f3df3d8055d6cb81852820895694272d80fecbb075b7`.
- Packet status: the host/controller independently verified the required SHA-256
  on 2026-07-24.  The host path is not mounted in this private worktree, so
  this report records that verification as external provenance.  F1 remains a
  hypothesis, not a theorem or a source claim.

## Claim tested

For the integer presentation matrix

```text
[[x, 0, -z],
 [0, y, -z]],
```

F1 proposes determinantal divisors `d₁ = gcd(x,y,z)` and
`d₁*d₂ = gcd(x*y,x*z,y*z)`. Direct expansion gives the three maximal minors
`x*y`, `-x*z`, and `y*z`; this is compatible with the proposed product.

## Deterministic falsifiers

`experiments/br128/smith_invariant_falsifier.py` exhaustively checks
`1 ≤ x,y,z ≤ 12`, cyclic groups `Z/nZ` for `2 ≤ n ≤ 17`, and fields `F_p` for
`p ∈ {2,3,5,7,11,13,17}`. It enumerates the image in `(Z/nZ)^2`, checks the
cokernel cardinality `gcd(n,d₁) gcd(n,d₂)`, and checks field rank from the
same minors. A successful finite sweep is falsification evidence only.

## Mathlib 4.31 API audit and semantic overlap

- `Mathlib/LinearAlgebra/FreeModule/PID.lean` supplies the noncomputable
  submodule API `Submodule.smithNormalForm` and
  `Submodule.smithNormalFormCoeffs`.
- `Mathlib/LinearAlgebra/FreeModule/Finite/Quotient.lean` supplies
  `Submodule.quotientEquivPiZMod` for a full-rank submodule.
- There is no direct, executable rectangular-integer-matrix Smith invariant
  API found in the locked source. Bridging this matrix to its image submodule,
  proving full rank, and identifying the returned coefficients with these
  explicit determinantal divisors is materially broader than one declaration.

## Bounded kernel artifact

`BealUnified.Research.smithPresentation_maximal_minors` is one declaration
that computes the three `2 × 2` column minors using Mathlib 4.31's
`Matrix.det_fin_two`.  It deliberately stops before any statement about the
Smith coefficients, quotient cardinalities, or Beal counterexamples.

The first immutable validation receipt, `94fb313f-d4a0-43cd-a4d9-bc5a0d3e864d`
on Babylon, failed before loading this declaration: its temporary cache-aware
runner passed `IO.Process.Output.exitCode : UInt32` to
`IO.Process.exit`, which expects `UInt8`.  The direct diagnostic was
`RemoteBuildWithCache.lean:8:20: Application type mismatch`.  The runner now
raises `IO.userError` on a nonzero child exit instead; this is a validation
plumbing correction, not a change to the artifact statement or proof.

## Decision card

| Field | Value |
|---|---|
| ID | BR-128 |
| Claim | F1 determinant-divisor statement for the displayed matrix |
| Falsification test | finite cyclic-group image/cokernel and finite-field rank sweep |
| Dependencies | verified packet, a matrix-to-image bridge, full-rank proof, coefficient-identification lemmas |
| Status | `use` — remote kernel validation succeeded; the one-minor declaration is ready for bounded review |
| Use | kernel-checked maximal-minor calculation and finite-shadow test remain reusable regression evidence |
| Retry condition | a separately scoped image-submodule/SNF coefficient bridge is needed |
| Reject condition | any exact counterexample or a corrected packet invalidates F1 |

The replacement validation is immutable receipt
`e104fc8c-665c-457b-9f55-1ed6d84d59ae`: Nippur, exit status `0`, source
bundle `e5ed129a179f105a63e42771c70a0dffc6853ab67d3f27e64861154246f4e170`,
and Lean `v4.31.0`.  The bundle contained the two preserved source changes and
the temporary cache runner; it is not evidence for any PR #6 gate.

This report makes no Beal-proof claim and contains no `sorry`, `admit`, axiom,
or unsafe declaration.
