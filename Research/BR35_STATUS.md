# BR-35 preservation status

This branch preserves the untracked BR-35 `BealUnified/ResidueObstruction.lean` draft exactly as recovered on 2026-07-16.

- Source SHA-256: `37d2b91449b22eac51886993ebaa1e5e7132588edfc81c9fdac3e2e9c0a22964`.
- It is **not kernel-valid** and is intentionally not proposed for merge.
- A standalone Lean 4.31 check failed on unavailable `Nat.coprime_mul_left_iff.mp`, a power-rewrite mismatch, and missing decidability for the two `native_decide` obstruction propositions.
- No statement is accepted as proved by this preservation commit.

Reopen only as a fresh bounded repair with unchanged theorem statements, explicit finite decidability, a focused kernel build, forbidden-token audit, and normal review/CI gates.
