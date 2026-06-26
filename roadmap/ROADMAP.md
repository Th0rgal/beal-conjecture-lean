# Strategic Roadmap: Proving the Beal Conjecture in Lean 4 + Mathlib

> Generated 2026-06-26 from four parallel research missions (A: state-of-the-art survey, B: Mathlib gap audit, C: modular method feasibility, D: alternative elementary paths). All four reports are in this repository at `roadmap/state-of-the-art.md`, `roadmap/mission-C-modular-method.md`, `roadmap/mission-D-alternative-paths.md`.

## Bottom line first

The Beal conjecture **cannot be proved in Lean 4 + Mathlib with currently available formal mathematics**. The bottleneck is genuinely mathematical, not formalization: every known attack either solves only fixed signature families (not all Beal), gives finiteness without enumeration, or is conditional on conjectures at least as strong as ABC.

What an AI-assisted Lean team **can realistically do** in 2026-2028 is:

1. Build a formal generalized Fermat / Beal signature library
2. Formalize the proven `(3,4,5)` mixed-exponent sub-case (Siksek-Stoll, 2012) via certified descent
3. Import Faltings / Darmon-Granville / Stewart-Yu as precisely named theorem interfaces
4. Convert "known islands" into Lean theorems with Magma/Sage-checkable certificates
5. Build reusable Mathlib infrastructure (elliptic curves, modular forms, Jacobians) that supports future arithmetic-geometry formalization

What it **cannot** do:

- Formalize the entire Wiles / Ribet / Khare-Wintenberger machinery and then derive Beal as a corollary
- Assume ABC and call it a proof (ABC is not proven, IUT is not accepted)
- Baker-style explicit bounds alone (constants are too large to brute force)
- Sum-product, additive combinatorics, or transcendence (no Beal attack exists)

## The mixed-exponent gap that remains

After the existing `beal-unified/` Lean 4 project, the open frontier is exactly the mixed-exponent families:

```
A^x + B^y = C^z,  x,y,z >= 3,  x,y,z not all equal,  gcd(A,B,C) = 1
```

with at least one exponent not divisible by 3 or 4. The cleanest such cases are `(3,4,5)`, `(3,5,7)`, `(4,5,7)`, etc. The flagship solved case in this regime is **`(3,4,5)`** — Siksek-Stoll (2012).

## The 3 prioritized paths

### Path 1 — Formalize the `(3,4,5)` descent (Siksek-Stoll)

**The single most actionable Lean 4 target.** A real Beal mixed-exponent case, solved in the literature, avoids formalizing Wiles.

| Milestone | LOC estimate | Effort |
|---|---|---|
| Reduce Beal `(3,4,5)` to a finite Selmer-set statement | 5k-15k | weeks-months |
| Build certificate format for local solubility over number fields | 5k-10k | weeks |
| Formalize enough hyperelliptic-curve language to state "empty Selmer ⟹ no rational point" | 10k-30k | months |
| Verify the specific finite computations (Sage/Magma outputs as checkable certificates) | 20k-35k | 1-3 PY |
| Package as `theorem beal_no_coprime_signature_3_4_5 : False := by ...` | — | — |
| **Total** | **40k-90k LOC** | **3-8 person-years** |

**Why first.** Closes a real Beal signature. Builds reusable descent infrastructure (Jacobians, Selmer, hyperelliptic curves, certified computations) for future work. No need to formalize Wiles.

**Risk.** Medium. Mathematics is known, but clean formalization of computational descent is non-trivial. Computational trust model needs a careful certificate format.

### Path 2 — Generalized Fermat / Beal signature library + theorem interfaces

**The infrastructure that lets us say precisely what is and is not known for every Beal signature.**

| Milestone | LOC estimate | Effort |
|---|---|---|
| Define primitive solutions, signatures, hyperbolic/spherical regimes, reductions by exponent divisibility | 3k-8k | weeks |
| Formalize the elementary reductions already proved in `beal-unified/` as a clean library API | 2k-5k | weeks |
| Import Darmon-Granville as a named theorem interface for fixed hyperbolic signatures | 1k-3k | weeks |
| Import Faltings / Vojta / Stewart-Yu as theorem interfaces | 2k-5k | weeks |
| Build a registry of solved signatures with theorem hooks and literature references | 1k-3k | weeks |
| **Total** | **10k-25k LOC** | **2-6 months** |

**Why second.** Pinpoints exactly which signatures are open vs. closed under what assumptions. Provides a clean dependency graph that future paths can build on.

**Risk.** Low. This is mostly formalization hygiene.

### Path 3 — Modular-method infrastructure via narrow certified papers

**Long-term path toward closing more Beal signatures, one modularity paper at a time.**

| Milestone | LOC estimate | Effort |
|---|---|---|
| Define Frey curves and basic invariants over ℚ for selected families | 15k-30k | 1-2 PY |
| Certificate checking for discriminants, conductors, local reduction types | 10k-25k | 1 PY |
| State modularity and level-lowering as black-box interfaces with explicit hypotheses | 5k-15k | months |
| Formalize newform-elimination computations as checkable certificates for one family (e.g. Bennett-Chen `a² + b⁶ = cⁿ`) | 20k-50k | 2-4 PY |
| Extend one paper at a time | — | — |
| **Total (for one narrow family)** | **50k-120k LOC** | **3-7 PY** |

**Why third.** Eventually, this is what could close *most* known Beal-relevant mixed-signature cases. But it requires significant infrastructure (elliptic curves over ℚ with conductor/minimal model, Galois representations, modular forms, modularity lifting) that is **not in Mathlib today**.

**Risk.** High. The mathematical results are published, but Mathlib has ~9.5k LOC on elliptic curves and ~7.4k on modular forms — foundations, not enough for a modular-method paper. Lean FLT project is still defining the deformation ring `R` and Hecke algebra `T`.

## What NOT to invest in (for a Beal-specific project)

| Approach | Why not |
|---|---|
| Full Wiles / Ribet / Khare-Wintenberger formalization | 30-80+ person-years, doesn't give Beal as a corollary |
| ABC + IUT approach | IUT not accepted; even ABC wouldn't give a clean proof, only finiteness |
| Baker / linear forms in logarithms → brute force | Constants too large to search; bounds exceed 10³⁰⁰ for relevant signatures |
| Cyclotomic methods for mixed exponents | Only works for symmetric `(p,p,r)` or regular-prime cases, not `(3,4,5)` |
| Additive combinatorics / sum-product | No published Beal attack exists |
| Transcendence (Gel'fond-Schneider directly) | Integer exponents don't trigger transcendence methods |

## The effort/payoff chart

```
Payoff for Beal progress
   ▲
   │                ★ (3,4,5) descent
   │              ★
   │        ★
   │           ★ Modular method (narrow certified)
   │
   │     ★ Signature library
   │        ★ Mason-Stothers extension
   │  ★
   │       Darmon-Granville interface
   │  ★ Weak ABC interface
   │
   │           ★ Sum-product
   │     ★ Baker
   │  ★
   └────────────────────────────────────────────►
       1M   1Y   5Y   10Y   50Y   100Y   Effort
```

## Concrete next-step recommendation for an AI-assisted team in 2026

**Quarter 1-2:** Path 2 (signature library + interfaces). ~25k LOC. Sets the foundation.

**Quarter 3-4:** Path 1, phase 1-2 (reduction + certificate format). Sets up the `(3,4,5)` attack.

**Year 2:** Path 1, phase 3-4 (Selmer-set verification). **First publishable result**: a Lean 4 theorem that no primitive `A³ + B⁴ = C⁵` exists, certified against Siksek-Stoll 2012.

**Year 3+:** Path 3, one modular paper at a time. Closes `(p,p,3)`, `(a²,b⁶,cⁿ)`-style families.

**Year 5+:** Build enough Mathlib content that someone (a research mathematician, not an AI) can attempt the full Beal proof using the formal foundation.

## Where AI assistance changes the calculation

Two things make 2026 different from 2016:

1. **Mathematical infrastructure is being formalized concurrently.** The Lean FLT project, Baek-Lee's Mason-Stothers, FLT-for-regular-primes Lean blueprint. Each of these shrinks the distance to a serious Beal attack.

2. **AI-assisted formalization accelerates routine work.** Routine Mathlib contributions (algebraic structures, polynomial identities, number-field arithmetic) can plausibly be 5-10x faster with AI tooling. This means Path 1 at 3-8 person-years might be 1-2 person-years with AI assistance.

It does **not** change the fundamental bottleneck: the modular method's proof machinery still requires human mathematical insight to formalize, not just typing speed.

## What we will not achieve, even with AI

A formal Lean 4 proof of the general Beal conjecture in 2026-2028. The mathematics doesn't exist. ABC is unproven. Wiles' machinery is decades of formalization away from Beal applicability. No amount of AI assistance substitutes for the missing theorems.

The honest deliverable is: a Beal signature library, a closed `(3,4,5)` case, certified interfaces for the modern finiteness theorems, and a roadmap for future paths. This is publishable and useful work — and it is what AI-assisted formalization can achieve in this window.

---

## Mission reports in this repo

- [`roadmap/state-of-the-art.md`](state-of-the-art.md) — survey of 11 mathematical approaches with mixed-exponent relevance, Mathlib gap estimates, person-year estimates
- [`roadmap/mission-B-Mathlib-gap-audit.md`](../beal-unified/BEAL_MATHLIB_GAP_AUDIT.md) — concrete Mathlib 4.31 audit
- [`roadmap/mission-C-modular-method.md`](mission-C-modular-method.md) — deep dive on modular method: Frey curves, Galois reps, level lowering, Lean FLT project status
- [`roadmap/mission-D-alternative-paths.md`](mission-D-alternative-paths.md) — Darmon-Granville, Baker, weak ABC, cyclotomic, descent, Mason-Stothers, Vojta, sum-product — all 10 ranked by effort/payoff
- [`ROADMAP.md`](../ROADMAP.md) — this file, the executive summary