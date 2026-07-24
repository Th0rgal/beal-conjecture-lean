# Trust-boundary follow-up roadmap

Version 2 (2026-07-24) records work deliberately not claimed by the trusted
boundary PR. The detailed mathematical and literature audit is in
[`Research/BEAL_FRONTIER_AUDIT_2026-07-24.md`](../Research/BEAL_FRONTIER_AUDIT_2026-07-24.md).

Follow-up PRs, in dependency order:

1. Add a generalized-Fermat signature API with divisor-shadow closure, so solved
   signatures generate formally checked upward divisibility cones instead of
   remaining isolated registry strings.
2. Formalize the exact equal-left-odd-prime cyclotomic power split. Construct
   `CofactorPowerData` from a primitive perfect-power equation, prove existence
   of a nonexceptional prime of multiplicity at least the right exponent, and
   derive two-prime support and prime-power-right-base exclusion.
3. Formalize the unconditional asymmetric radical theorem
   `rad(A*B*C)^12 < (C^z)^11` outside `(3,3,3)`.
4. Formalize exact finite-field/unit counts for pairwise-coprime exponents. Use
   the result as a checked no-go theorem for proof strategies based only on a
   predetermined finite collection of congruence moduli.
5. Extend the registry schema to distinguish trusted/formal results,
   literature-solved results awaiting formalization, open frontier signatures,
   conditional results, and bounded evidence.
6. Audit and certify the Siksek–Stoll `(3,4,5)` descent. A literature locator is
   not a Lean theorem; every finite computation needs an independently replayed
   certificate before the signature can enter the trusted solved registry.
7. Treat `(3,5,7)` as the first open distinct-prime research target. Reproduce
   fixed-signature descent or modular/hypergeometric computations with exact
   source and output hashes. The 2025 `(5,p,3)` paper explicitly leaves `p=7`
   exceptional, so it supplies infrastructure rather than a proof of this case.
8. Integrate an official Lean comparator/challenge module only after its API and
   trust model are independently reviewed.
9. Extend durable checkpoint manifests with independently replayed certificates
   and retained source-audit evidence. A checkpoint remains provenance, never a
   theorem claim.

Do not prioritize generic CUDA searches, fixed-modulus atlases, unconditional
valuation-one heuristics, qualitative ABC as a proof, or a full Wiles-scale
formalization as the immediate Beal path. Their precise limitations are recorded
in the frontier audit.
