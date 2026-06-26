# State of the Art: Beal Conjecture Beyond Elementary Number Theory

Date: 2026-06-26

## Executive Assessment

The Beal conjecture is best viewed as the assertion that the generalized Fermat equation

```text
A^x + B^y = C^z,     x,y,z >= 3,     gcd(A,B,C)=1
```

has no positive integer solutions.  The modern literature usually writes this as

```text
a X^p + b Y^q = c Z^r
```

with fixed coefficients and fixed signature `(p,q,r)`, and asks for primitive solutions.  The known theory is strong for fixed signatures and special infinite families, but no known unconditional method proves Beal uniformly across all mixed exponents.

The central distinction is:

- **Finiteness is known for each fixed hyperbolic signature** `1/p + 1/q + 1/r < 1`, by Darmon-Granville using Faltings.
- **Effectively listing all primitive solutions is usually not known**, and Beal needs zero primitive positive solutions for every signature with all exponents at least 3.
- **ABC would imply only finiteness of global counterexamples**, not an immediate unconditional proof that there are none.
- **The modular method and descent methods solve many islands**, including the signature `(3,4,5)`, but they do not currently form a uniform proof engine for all mixed signatures.

My honest 2026 conclusion: a proof of Beal is not achievable merely by formalizing current mathematics.  The bottleneck is mathematical, not only formalization.  AI-assisted Lean work can realistically formalize useful solved islands and build infrastructure, but a full proof requires either a new mathematical breakthrough or a widely accepted proof of a conjecture at least as strong as ABC/Fermat-Catalan plus additional exclusion work.

## Reference Baseline

Core sources used for this roadmap:

- Henri Darmon and Andrew Granville, "On the equations `z^m = F(x,y)` and `Ax^p + By^q = Cz^r`", Bull. London Math. Soc. 27 (1995), 513-543.  PDF: <https://www.math.mcgill.ca/darmon/pub/Articles/Research/12.Granville/paper.pdf>
- Michael Bennett, Imin Chen, Sander Dahmen, Soroosh Yazdani, "Generalized Fermat equations: A miscellany", Int. J. Number Theory 11 (2015), 1-28.  PDF: <https://personal.math.ubc.ca/~bennett/BeChDaYa-IJNT-2015.pdf>
- Michael Bennett, Preda Mihailescu, Samir Siksek, "The Generalized Fermat Equation", in Open Problems in Mathematics, Springer (2016).  PDF: <https://personal.math.ubc.ca/~bennett/BeMuSi-Springer-2016.pdf>
- Ashleigh Ratcliffe and Bogdan Grechuk, "Generalised Fermat equation: a survey of solved cases", arXiv:2412.11933v2 (2025).  PDF: <https://arxiv.org/pdf/2412.11933>
- Samir Siksek and Michael Stoll, "Partial descent on hyperelliptic curves and the generalized Fermat equation `x^3 + y^4 + z^5 = 0`", Bull. London Math. Soc. 44 (2012), 151-166.  arXiv: <https://arxiv.org/abs/1103.1979>
- Bjorn Poonen, Edward Schaefer, Michael Stoll, "Twists of `X(7)` and primitive solutions to `x^2 + y^3 = z^7`", Duke Math. J. 137 (2007), 103-158.  PDF: <https://math.mit.edu/~poonen/papers/pss.pdf>
- Nuno Freitas, Bartosz Naskrecki, Michael Stoll, "The generalized Fermat equation with exponents 2, 3, n", Compositio Math. 156 (2020).  PDF: <https://www.mathe2.uni-bayreuth.de/stoll/papers/genfermat-final.pdf>
- Michael Bennett and Imin Chen, "Multi-Frey Q-curves and the Diophantine equation `a^2 + b^6 = c^n`", Algebra & Number Theory 6 (2012), 707-730.  PDF: <https://msp.org/ant/2012/6-4/ant-v6-n4-p04-p.pdf>
- Samuele Anni and Samir Siksek, "Modular elliptic curves over real abelian fields and the generalized Fermat equation `x^{2l}+y^{2m}=z^p`", Algebra & Number Theory 10 (2016), 1147-1173.  arXiv: <https://arxiv.org/abs/1506.02860>
- Jineon Baek and Seewoo Lee, "Formalizing Mason-Stothers Theorem and its Corollaries in Lean 4", arXiv:2408.15180v2 (2025).  PDF: <https://arxiv.org/pdf/2408.15180>
- Lean FLT project: <https://github.com/ImperialCollegeLondon/FLT>
- Lean FLT regular primes blueprint: <https://leanprover-community.github.io/flt-regular/blueprint/>

## Current Mathlib/Lean Baseline

Mathlib already has strong algebra, number fields, ideals, valuations, finite fields, basic algebraic geometry, and substantial polynomial/function-field material.  It has a formalized Mason-Stothers theorem integrated into Mathlib according to Baek-Lee.  There is also a complete Lean 4 formalization of FLT for regular primes, and an active project to formalize full FLT.

The main missing areas for Beal-scale work are:

- elliptic curves over `Q` and number fields at the level needed for conductors, minimal models, reduction types, torsion, isogenies, and modularity;
- modular forms, modular curves, Hecke algebras, newforms, Galois representations, and level lowering;
- Chabauty-Coleman, Mordell-Weil sieve, Selmer groups of Jacobians, and explicit descent algorithms;
- Faltings' theorem, Vojta/Bombieri proof, or any effective rational-points package for genus `> 1`;
- serious computational algebraic number theory verified inside Lean.

## Survey by Approach

### 1. Modular Method

**Idea.**  Starting from a putative primitive solution, build a Frey elliptic curve, Q-curve, abelian variety, or hypergeometric motive whose conductor and residual Galois representation encode the arithmetic of the solution.  Modularity says the representation comes from a modular form; Serre modularity, proved by Khare-Wintenberger, explains why odd irreducible mod `p` representations over `Q` should arise from modular forms.  Level lowering, in the style of Ribet and its generalizations, forces the representation to come from a newform at a much smaller level.  One then eliminates the remaining newforms by local information, image arguments, congruences, or explicit computations.

**Strongest results.**  This is the dominant method for many generalized Fermat families.  Examples include Darmon-Merel on variants `x^n+y^n=z^2,z^3`; Bennett-Skinner and Bennett-Vatsal-Yazdani on signatures `(p,p,3)`; Bennett-Chen on `a^2+b^6=c^n`; Anni-Siksek on `x^{2l}+y^{2m}=z^p`; and many later results over totally real fields and real abelian fields.  The 2025 Ratcliffe-Grechuk survey collects solved fixed signatures and families.  The method is not a proof of Beal; it is a toolkit that solves families.

**Mixed-exponent Beal-specific result?**  Yes, for special mixed signatures and families, but not uniformly.  For example `(3,4,5)` is solved by descent rather than pure modularity; signatures involving one exponent `2` are outside Beal but heavily studied.  Modular methods have solved many equations with distinct exponents, but the universal all-prime/all-mixed Beal range is far beyond current uniform results.

**Obstacles.**  There is no known universal Frey object for all signatures that yields a contradiction.  Some signatures require higher-dimensional Frey abelian varieties or motives.  Level lowering over number fields is conditional or technically restricted in many cases.  "Ghost solutions" and trivial-solution congruences can prevent contradiction.  The final elimination of newforms is often computational and signature-specific.

**Minimum missing Mathlib piece.**  Elliptic curves over number fields with conductor/minimal model theory; mod `p` Galois representations; modular forms/newforms; modular curves; Ribet-style level lowering; modularity lifting or accepted modularity theorems; verified finite computations of newform spaces.

**Formalization effort.**  If treated as black-box theorem statements for one solved paper: 1-3 person-years per narrow case after prerequisites.  If formalizing proof machinery for Wiles/Ribet/Khare-Wintenberger scale results: 30-80+ person-years, plausibly decades for a small team.  Full generalized modular method over number fields: beyond current predictable scope.

### 2. Darmon-Granville Theorem

**Idea.**  Darmon and Granville convert generalized Fermat equations to rational or integral points on covers and use Faltings' theorem to prove finiteness of primitive solutions for fixed hyperbolic signatures.  The theorem says, roughly, that for fixed nonzero coefficients and fixed exponents satisfying `1/p+1/q+1/r < 1`, there are only finitely many primitive solutions, modulo natural equivalences.

**Strongest results.**  For each fixed signature `(p,q,r)` with `1/p+1/q+1/r < 1`, finiteness of primitive solutions is known.  This covers all Beal signatures except elliptic/spherical boundaries, and Beal has `p,q,r >= 3`, so most signatures are hyperbolic, with `(3,3,3)` handled by FLT and other equal-exponent reductions.

**Mixed-exponent Beal-specific result?**  Yes, finiteness for every fixed mixed signature such as `(3,4,5)`, `(3,5,7)`, etc.  No, it does not prove absence of solutions.

**Obstacles.**  Finiteness is non-effective in practical terms.  Even when effective bounds exist in principle via Vojta/Bombieri-type refinements, they are not computationally useful for Beal.  The theorem does not list the finite set, so it cannot prove Beal by itself.

**Minimum missing Mathlib piece.**  Faltings' theorem for curves over number fields; construction of the relevant covers; genus calculations; descent from integral primitive solutions to rational points.

**Formalization effort.**  As theorem statement plus application to fixed signatures: 1-2 person-years.  Full proof of Faltings plus Darmon-Granville: 20-50+ person-years even using a streamlined Vojta/Bombieri route, because Arakelov geometry, heights, abelian varieties, and moduli are not yet in Mathlib at required depth.

### 3. Faltings' Theorem on Generalized Fermat Curves

**Idea.**  A fixed equation `X^p + Y^q = Z^r` can be represented by algebraic curves or covers of `P^1` whose genus is often greater than 1.  Faltings' theorem gives finiteness of rational points on each curve over a number field.  This is the geometric engine behind Darmon-Granville and many finiteness statements.

**Strongest results.**  Faltings proves finite rational points on every smooth projective curve of genus `>1` over a number field.  For fixed generalized Fermat signatures, this usually gives finiteness after constructing the correct curve or cover.

**Mixed-exponent Beal-specific result?**  Yes for fixed signatures as finiteness.  No as a zero-solution theorem.

**Obstacles.**  Faltings is non-constructive for explicit solution determination.  Beal requires a uniform no-solution statement, not a finite list.  Turning Faltings into an effective enumerator generally requires Chabauty, descent, Mordell-Weil computations, or conjectural height bounds.

**Minimum missing Mathlib piece.**  Algebraic curves, genus, Jacobians, abelian varieties, heights, Neron models or an alternate Vojta/Bombieri proof of Mordell.

**Formalization effort.**  Stating and using Faltings axiomatically: months.  Formalizing a proof: 20-50 person-years.  Formalizing enough effective rational-points machinery for examples: 5-15 person-years per robust package.

### 4. ABC Conjecture, Baker-Type Bounds, and Vojta

**Idea.**  ABC says that for coprime `a+b=c`, the size of `c` is essentially bounded by `rad(abc)^{1+epsilon}`.  Applying it to `A^x+B^y=C^z` constrains high powers because the radical loses exponent multiplicity.  ABC implies the Fermat-Catalan finiteness conjecture and would imply only finitely many Beal counterexamples.

**Strongest results.**  ABC remains unproved in the mainstream mathematical consensus.  Mochizuki's IUT papers were published, but the claimed proof has not been broadly accepted; Scholze-Stix and others have raised serious objections.  Quantitatively, ABC predicts that for every `epsilon > 0`, `c <= K_epsilon rad(abc)^(1+epsilon)` for coprime `a+b=c`.  Unconditionally, Stewart-Tijdeman proved an exponentially weak form such as `c < exp(K rad(abc)^15)`.  Stewart-Yu improved this dramatically; a standard quoted form is `c < exp(K rad(abc)^(1/3) log(rad(abc))^3)` for an absolute constant `K`, with related `1/3+epsilon` variants.  These are major theorems but still far too weak to prove Beal.

**Mixed-exponent Beal-specific result?**  Conditional: ABC gives finiteness of Beal/Fermat-Catalan counterexamples, not automatic absence.  Unconditional weak ABC bounds do not solve mixed Beal cases.

**Obstacles.**  ABC is open.  Even if ABC were assumed, proving no Beal counterexamples would still require eliminating finitely many unknown exceptions or sharpening to a very explicit effective form.

**Minimum missing Mathlib piece.**  Radical over integers, heights, asymptotic finite-exception statements are feasible.  To formalize ABC consequences: not hard compared with ABC itself.  To formalize proofs of weak ABC bounds: Baker theory, `p`-adic logs, heights.

**Formalization effort.**  ABC implication to Fermat-Catalan/Beal finiteness if ABC is an axiom: 3-9 months.  Formalizing Stewart-Yu style unconditional bounds: 5-15 person-years.  Formalizing IUT or Vojta-level machinery: not realistically estimable; likely >50 person-years and still mathematically controversial if based on IUT.

### 5. Etale ABC / Szemeredi-Trotter Type Approaches

**Idea.**  Etale approaches to ABC repackage arithmetic information through fundamental groups, anabelian geometry, etale covers, and Belyi-type reductions.  Szemeredi-Trotter/incidence geometry analogies appear in attempts to bound arithmetic configurations by combinatorial geometry; function-field analogues often admit geometric incidence proofs.

**Strongest results.**  There is no accepted etale/Szemeredi-Trotter proof of integer ABC or Beal.  The most serious etale-adjacent work is Mochizuki's IUT framework, but it remains outside mainstream acceptance as a proof of ABC.  Incidence methods are powerful in additive combinatorics and function fields, but no known theorem from Szemeredi-Trotter directly attacks Beal mixed exponents over integers.

**Mixed-exponent Beal-specific result?**  No credible published result resolving Beal mixed signatures by this route.

**Obstacles.**  The analogy is too weak over `Z`: archimedean and `p`-adic height information, ramification, and radical behavior are not captured by elementary incidence bounds.  Etale fundamental group methods are extremely high-level and not currently an effective solution engine for fixed signatures.

**Minimum missing Mathlib piece.**  Etale fundamental groups, schemes, covers, anabelian geometry, stacks, and possibly o-minimal/incidence combinatorics if pursuing ST analogues.

**Formalization effort.**  Incidence theorem alone: 1-3 person-years.  Etale/anabelian machinery: 20-60+ person-years.  A Beal proof path is not mathematically defined, so formalization effort is not the main blocker.

### 6. Belyi Maps, Dessins d'Enfants, and Stacky Curves

**Idea.**  Generalized Fermat equations correspond to covers of `P^1` branched over `{0,1,infinity}` and to orbifold/stacky curves `P^1(p,q,r)`.  Belyi maps and dessins encode the branching data combinatorially.  In spherical cases, this leads to parametrizations; in hyperbolic cases, it explains why Faltings/Darmon-Granville finiteness appears.

**Strongest results.**  Beukers and later stack-theoretic work organize generalized Fermat equations via triangle groups and Belyi maps.  Recent work by Arango-Pineros and related stacky-curve projects studies primitive solutions in spherical regimes and arithmetic statistics.  These are structural and counting results, not a Beal proof.

**Mixed-exponent Beal-specific result?**  Structural yes; solving no.  It gives a clean language for fixed signatures and for known parametrizable low-genus cases.  It does not eliminate hyperbolic Beal signatures.

**Obstacles.**  Hyperbolic triangle curves have high genus or arithmetic complexity.  Computing Belyi maps is difficult and case-specific.  The method organizes the problem; it does not provide a uniform contradiction.

**Minimum missing Mathlib piece.**  Algebraic curves, ramified covers, Riemann-Hurwitz, Belyi theorem, triangle groups, stacks/root stacks if using modern language.

**Formalization effort.**  Riemann-Hurwitz and concrete Belyi maps: 2-6 person-years.  Full Belyi theorem/root-stack formalization: 8-20 person-years.  A useful formal framework for signatures and genus estimates is feasible earlier.

### 7. Explicit Baker Theory

**Idea.**  Linear forms in logarithms give effective lower bounds for expressions like `alpha_1^{n_1} ... alpha_k^{n_k} - 1`, which can bound exponents or variables in exponential Diophantine equations.  In practice, one combines a huge Baker bound with reduction techniques and finite search.

**Strongest results.**  Baker theory proves many exponential Diophantine equations and weak ABC-type inequalities.  It is effective in special families, especially when the equation can be reduced to unit equations, Thue equations, or `S`-unit equations.

**Mixed-exponent Beal-specific result?**  Some generalized Fermat subfamilies can be bounded or solved with Baker/Thue/S-unit methods, but there is no Baker-theory proof of Beal's full mixed-exponent range.

**Obstacles.**  Bounds are enormous; reductions are highly specialized; Beal has three variable bases and three variable exponents.  Even when one bounds exponents, the remaining search can be impossible without additional structure.

**Minimum missing Mathlib piece.**  Algebraic and `p`-adic logarithms, heights, explicit lower bounds such as Baker-Wustholz/Matveev, unit equations, LLL/Baker-Davenport reduction if verified computationally.

**Formalization effort.**  A reusable explicit linear-forms package: 8-20 person-years.  A specific small equation proof: 1-4 person-years after infrastructure.  Full Beal via Baker is not a known mathematical path.

### 8. Mason-Stothers Theorem

**Idea.**  Mason-Stothers is the polynomial/function-field analogue of ABC.  For coprime polynomials `a+b+c=0`, it bounds the maximum degree by the degree of the radical.  It proves polynomial Fermat-Catalan type nonexistence when `1/p+1/q+1/r <= 1`, except for derivative-zero phenomena in positive characteristic.

**Strongest results.**  The theorem is known and, importantly for this mission, has been formalized in Lean 4 and integrated into Mathlib, including polynomial Fermat-Catalan corollaries according to Baek-Lee.

**Mixed-exponent Beal-specific result?**  Only as an analogy.  It proves the function-field analogue, not integer Beal.

**Obstacles.**  The integer radical lacks the derivative/Riemann-Hurwitz mechanism that makes Mason-Stothers easy.  The theorem is a model and a source of formalization patterns, not an attack on integer Beal.

**Minimum missing Mathlib piece.**  Mostly present for polynomial version.  To use it as a roadmap for integer analogues, Mathlib would need ABC or height/radical machinery.

**Formalization effort.**  Already largely done.  Extending consequences: weeks to months.  No direct payoff toward integer Beal beyond analogy and training.

### 9. Cyclotomic Field Methods

**Idea.**  Kummer's proof of FLT for regular primes factors `x^p+y^p` in `Z[zeta_p]`, studies ideals, units, class groups, and Bernoulli-number regularity.  One might try to factor one side of `A^x+B^y=C^z` in cyclotomic fields attached to one exponent and derive divisibility constraints.

**Strongest results.**  Classical FLT for regular primes is mature and has a Lean 4 formalization.  Cyclotomic methods remain important background for FLT and Catalan/Mihailescu style work, but the modular method superseded them for full FLT.

**Mixed-exponent Beal-specific result?**  No broad modern Beal result.  Cyclotomic arguments can handle special congruence cases, but mixed exponents destroy the symmetry that makes `x^p+y^p` factor useful.

**Obstacles.**  Different exponents produce incompatible cyclotomic fields.  Irregular primes and class groups remain hard.  The method is sensitive to one exponent at a time and does not naturally control the other two powers.

**Minimum missing Mathlib piece.**  Much of the cyclotomic/class group machinery exists from the FLT regular primes project, but extensions would need deeper class field theory, explicit class number criteria, and factorization in multiple cyclotomic fields.

**Formalization effort.**  For classical Kummer-style cases: already partly done; 1-3 person-years to reuse for related lemmas.  For a new mixed-exponent Beal family: 2-6 person-years plus mathematical invention.  Full Beal path not known.

### 10. Relative Brauer Groups, Descent on Torsors, Chabauty, and Mordell-Weil Sieve

**Idea.**  Transform a fixed generalized Fermat equation into rational points on curves, often hyperelliptic or modular curves.  Then compute Selmer sets, torsors, covers, Jacobians, Mordell-Weil groups, Chabauty-Coleman constraints, Mordell-Weil sieve obstructions, or Brauer-Manin obstructions.  Relative Brauer groups help compute obstructions for torsors.

**Strongest results.**  This is one of the most successful fixed-signature approaches.  Poonen-Schaefer-Stoll solved `x^2+y^3=z^7` using twists of `X(7)`, nonabelian descent, modularity, Chabauty, and Mordell-Weil sieve.  Siksek-Stoll solved the Beal-relevant mixed signature `x^3+y^4+z^5=0` using partial descent on hyperelliptic curves.  Bruin and others solved several equations involving exponents `2`, `3`, `4`, `6`, `8`, etc.

**Mixed-exponent Beal-specific result?**  Yes.  The signature `(3,4,5)` is a flagship Beal-relevant solved case.  There are also many results near Beal but with one exponent `2`, which are crucial as method prototypes.

**Obstacles.**  The approach is not uniform.  Every signature can lead to different curves, fields, ranks, and local obstructions.  Many computations rely on Magma/Sage and expert choices.  Formal verification of computations is hard but more tractable than formalizing Wiles.

**Minimum missing Mathlib piece.**  Hyperelliptic curves, Jacobians, Selmer groups, torsors/covers, local fields, Chabauty-Coleman integration, Mordell-Weil sieve, verified algebraic number theory computations.

**Formalization effort.**  Formalizing one solved paper like Siksek-Stoll `(3,4,5)` with trusted computational certificates: 3-8 person-years.  Building reusable descent/Chabauty infrastructure: 10-25 person-years.  Full coverage of all signatures: not mathematically available.

### 11. Recent Specific Work on Beal and Generalized Fermat Since 2000

**Credible literature.**

- Bennett-Skinner (2004) and Bennett-Vatsal-Yazdani (2004): modular methods for ternary equations, especially signatures `(p,p,2)` and `(p,p,3)`.
- Bruin (1999-2005): Chabauty and covering methods for generalized Fermat equations, including `x^3+y^9=z^2` and related equations.
- Poonen-Schaefer-Stoll (2007): `x^2+y^3=z^7`, a landmark combination of descent, modular curves, Chabauty, and Mordell-Weil sieve.
- Bennett-Chen (2012): multi-Frey Q-curves and `a^2+b^6=c^n`.
- Siksek-Stoll (2012): Beal-relevant `(3,4,5)` solved by partial descent.
- Bennett-Chen-Dahmen-Yazdani (2015): survey plus new infinite-family work.
- Bennett-Mihailescu-Siksek (2016): high-quality survey/open-problem chapter.
- Anni-Siksek (2016): modular elliptic curves over real abelian fields and `x^{2l}+y^{2m}=z^p`.
- Freitas-Naskrecki-Stoll (2020): `x^2+y^3=z^n`.
- Ratcliffe-Grechuk (2025): survey of solved generalized Fermat cases.
- Recent arXiv work continues on signatures such as `(5,p,3)`, `(13,13,n)`, and related hypergeometric motive/Frey abelian variety approaches.  These are relevant methodologically, but they are not a Beal proof.

**Noncredible or unverified Beal proof claims.**  There are many preprints and informal papers claiming elementary proofs of Beal.  I found no peer-reviewed accepted proof.  They should not be used as a roadmap foundation unless independently refereed by experts.

**Mixed-exponent Beal-specific result?**  Yes, but only isolated signatures/families.  `(3,4,5)` is the cleanest Beal-relevant success story.

**Minimum missing Mathlib piece.**  Depends on paper.  For modular papers, modularity infrastructure.  For descent papers, curves/Jacobians/computational certificates.

**Formalization effort.**  Best near-term target: formalize specific solved papers with bounded computational artifacts.  Estimate 3-8 person-years for `(3,4,5)` if Mathlib gets enough curve/descent infrastructure; 8-20 person-years for modular-method papers.

## Approach Matrix

| Approach | Published mixed-exponent result? | What it gives | Main Mathlib gap | Formalization estimate |
|---|---:|---|---|---:|
| Modular method | Yes, many families | Nonexistence for families | elliptic curves, modular forms, Galois reps, level lowering | 30-80+ PY for core machinery |
| Darmon-Granville | Yes, all fixed hyperbolic signatures | Finiteness | Faltings, covers, heights | 20-50+ PY for proof |
| Faltings | Yes, via fixed curves | Finiteness | curves, Jacobians, abelian varieties, heights | 20-50 PY |
| ABC | Conditional | Finiteness of counterexamples | ABC/height machinery | 3-9 months if axiom; proof unavailable |
| Etale ABC/ST | No direct Beal result | speculative structure | etale/anabelian geometry | not a defined proof path |
| Belyi/dessins | Structural yes | parametrization/finiteness framework | covers, Riemann-Hurwitz, stacks | 2-20 PY depending scope |
| Baker theory | Special families | effective bounds | logs, heights, unit equations | 8-20 PY infrastructure |
| Mason-Stothers | Function-field analogue | polynomial Beal analogue | mostly done | weeks-months extensions |
| Cyclotomic | Mostly equal-exponent/classical | congruence cases | class groups, cyclotomic units | partly done; 1-6 PY per family |
| Descent/torsors/Chabauty | Yes, including `(3,4,5)` | exact solution sets for fixed cases | Jacobians, Selmer, Chabauty, computations | 3-25 PY |

`PY` means person-years.

## Prioritized 3-Path Roadmap

### Path 1: Formalize and Generalize the `(3,4,5)` Descent Island

**Why this is top priority.**  It is Beal-relevant, already solved in the literature, and avoids formalizing the full Wiles machine.  It builds Mathlib content that is broadly reusable: hyperelliptic curves, local solubility, Selmer-set certificates, and verified finite computations.

**Milestones.**

1. Formal statement of primitive generalized Fermat signatures and Beal counterexample reduction.
2. Formalize the reduction of `A^3+B^4=C^5` to the finite set of curves used by Siksek-Stoll.
3. Build certificate format for local solubility/non-solubility over number fields.
4. Formalize enough hyperelliptic curve/descent language to state "empty Selmer set implies no rational point".
5. Verify the specific finite computations using certificates generated by Sage/Magma, with Lean checking algebraic identities and local obstructions.
6. Package the result as a theorem excluding primitive positive solutions of signature `(3,4,5)`.

**Effort.**  3-8 person-years for a focused team.  Payoff is high because this is a real Beal mixed-exponent case and creates reusable descent infrastructure.

**Risk.**  Medium.  The mathematics is known, but formalizing computational descent cleanly is difficult.

### Path 2: Build a Generalized Fermat Signature Library + Darmon-Granville/Faltings Interface

**Why this matters.**  It captures the global state of knowledge: every fixed hyperbolic signature has finitely many primitive solutions.  Even axiomatically importing Faltings/Darmon-Granville is useful because it gives a precise formal boundary between solved finiteness and unsolved enumeration.

**Milestones.**

1. Define primitive solutions, signatures, hyperbolic/spherical/Euclidean regimes, coefficient normalization, and reductions by exponent divisibility.
2. Formalize elementary genus/Riemann-Hurwitz calculations for Fermat-type covers where feasible.
3. State Faltings' theorem and Darmon-Granville as named axioms or theorem interfaces.
4. Prove formally that Beal counterexamples for fixed mixed signatures form finite sets under these interfaces.
5. Add a registry of solved signatures with theorem hooks and references.
6. Use this library to prioritize unformalized signatures and avoid duplicate effort.

**Effort.**  1-2 person-years if Faltings/Darmon-Granville are imported as axioms/interfaces; 20-50+ person-years to prove them.

**Risk.**  Low for the interface version; high for full proof.  The payoff is clarity and reusable infrastructure, not a proof of Beal.

### Path 3: Modular-Method Infrastructure via Narrow Theorem Certificates

**Why not full Wiles first.**  Full modularity and level lowering are too large for a Beal project.  The practical route is to formalize theorem interfaces plus the finite eliminations in selected papers.

**Milestones.**

1. Define Frey curves and basic invariants over `Q` for selected families.
2. Add certificate-checking for discriminants, conductors, and local reduction types in the selected family.
3. State modularity and level-lowering as black-box interfaces with exact hypotheses.
4. Formalize newform-elimination computations as checkable finite certificates.
5. Target one modular-method family such as `(p,p,3)` or `a^2+b^6=c^n` before attempting number-field Frey curves.
6. Later extend to Q-curves or real abelian fields only after `Q` cases are robust.

**Effort.**  5-15 person-years for a narrow certified modular-method family with black-box modularity; 30-80+ person-years for foundational proof machinery.

**Risk.**  High.  The mathematical results are known for specific families, but Lean infrastructure is currently thin.  The payoff is high for long-term arithmetic geometry.

## What a Determined Team Could Realistically Do by 2026-2029

Realistic:

- Create a formal generalized Fermat/Beal signature library.
- Formalize polynomial Mason-Stothers consequences already near Mathlib.
- Formalize selected local obstruction and parity/congruence families.
- Formalize the statement and consequences of Darmon-Granville/Faltings using theorem interfaces.
- Begin a certified formalization of one solved mixed signature, preferably `(3,4,5)`, relying on checkable computational certificates.
- Build reusable data formats for Magma/Sage computations checked by Lean.

Unrealistic as a direct Beal plan:

- Formalize the full Wiles/Ribet/Khare-Wintenberger machinery and then solve Beal.
- Formalize ABC/IUT and use it to prove Beal.
- Expect Baker theory or cyclotomic methods to uniformly eliminate all mixed exponents.
- Turn Faltings finiteness into an effective global search for all Beal signatures.

## Bottom Line

The best roadmap is not "prove Beal in Lean."  It is:

1. Formalize the problem and the modern taxonomy of signatures.
2. Turn known solved islands into Lean theorems, especially `(3,4,5)`.
3. Build interfaces for Faltings/Darmon-Granville and modular-method theorems.
4. Use Lean to make the boundary of current mathematics precise.

The full conjecture remains blocked by mathematics.  Current methods solve many fixed cases and prove finiteness in fixed signatures, but they do not provide a uniform contradiction across all mixed exponents `>= 3`.
