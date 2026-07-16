# Research consolidation — 2026-07-16

This integration preserves the bounded Lean artifacts produced by the BR-22/23/25 and BR-32/33/34/40 research waves.

## Provenance

- `BealUnified/ABC.lean`: BR-22 `bdbc9f365288ad52d62a7e5bd4e9e77411a8b3e5`.
- `BealUnified/Research/BR20.lean`: BR-23 `d5cc3355429b986ccb88b1d9113c196da99f02c3`.
- `BealUnified/PrimitiveDivisors.lean`: BR-25 `5d71d016b37dcc104d918224d5250b98cf63c106`.
- `BealUnified/CyclotomicQuotient.lean`: BR-40 repaired source SHA-256 `8d4251245e1635ed2d1403b1fe193335a1c1905130dcc56c48aa11f94357d920`.
- `BealUnified/CyclotomicCofactor.lean`: BR-32 `c01d1aac221f7a37ebfd418ff889ec37b3ff3009`.
- `BealUnified/ExponentNormalization.lean`: BR-33 `47cb998325c06bf4a0414b2f71debc24063e4c4d`.
- `BealUnified/ModEight.lean`: BR-34 `e0a5d1821177dca347ae0a3091b259508930dc45`.

## Trust boundary

These are structural lemmas and interfaces. They do not prove the Beal conjecture, primitive-divisor existence, ABC, or the modular method. The intentional open core remains the single `sorry` in `BealUnified/BealConjecture.lean`.
