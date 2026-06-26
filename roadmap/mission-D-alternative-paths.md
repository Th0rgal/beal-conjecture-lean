# Mission D: Alternative Paths to the Beal Conjecture

Date: 2026-06-26

Workspace ID: `e1c1911e-a7da-4ea1-9dd6-dbf7d77801ad`

## Executive Conclusion

The alternative, non-full-modular approaches to Beal are valuable for formalizing the boundary of current knowledge, but none is a credible route to the full conjecture by itself. The honest 2026 assessment is:

- Darmon-Granville/Faltings proves finiteness for every fixed hyperbolic signature, including mixed Beal signatures such as `(3,4,5)` and `(3,5,7)`, but does not enumerate the finite set.
- Baker theory and weak quantitative ABC bounds are effective in principle, but the constants are far beyond any direct search for Beal signatures, even for `x,y,z <= 100`.
- Cyclotomic/Kummer methods are formalization-friendly compared with the full modular method, but they mainly cover regular-prime FLT-type symmetry, not arbitrary mixed exponents.
- Descent on curves is the best non-full-modular payoff path. It has already solved the Beal-relevant signature `(3,4,5)` via Siksek-Stoll.
- Mason-Stothers is already near/formalized in Lean 4 and is excellent infrastructure, but it proves the function-field analogue, not integer Beal.
- Vojta/ABC would imply strong finiteness consequences, but relying on them means replacing Beal with a larger open conjectural package.
- Additive combinatorics and transcendence theory do not currently supply a concrete Beal attack.

The smallest concrete subcase with real near-term Lean payoff is not "all `min(x,y,z) <= 10`"; that is too optimistic. The best target is a formalized solved island:

```text
Primitive integer solutions to x^3 + y^4 + z^5 = 0 do not exist
in the Beal-positive form A^3 + B^4 = C^5 with gcd(A,B,C)=1.
```

This is publishable as a formalization result if it verifies the actual Siksek-Stoll descent certificate or a rigorous equivalent. Estimated effort: 40k-90k Lean LOC, 3-8 person-years for a focused team, depending on how much computational algebra is trusted versus verified.

## Reference Baseline

Core references checked for this mission:

- Henri Darmon and Andrew Granville, "On the equations `z^m = F(x,y)` and `Ax^p + By^q = Cz^r`", Bulletin of the London Mathematical Society 27 (1995), 513-543. Source: <https://londmathsoc.onlinelibrary.wiley.com/doi/abs/10.1112/blms/27.6.513>; author PDF: <https://www.math.mcgill.ca/darmon/pub/Articles/Research/12.Granville/paper.pdf>.
- C. L. Stewart and R. Tijdeman, "On the Oesterle-Masser conjecture", Monatshefte fur Mathematik 102 (1986), 251-257.
- C. L. Stewart and Kunrui Yu, "On the abc conjecture", Mathematische Annalen 291 (1991), 225-230; "On the abc conjecture. II", Duke Mathematical Journal 108 (2001), 169-181. Bibliographic anchor: <https://nitaj.users.lmno.cnrs.fr/abc.html>.
- Yann Bugeaud, Maurice Mignotte, Samir Siksek, "Classical and modular approaches to exponential Diophantine equations I. Fibonacci and Lucas perfect powers", Annals of Mathematics 163 (2006), 969-1018; arXiv: <https://arxiv.org/abs/math/0403046>.
- Yann Bugeaud, Maurice Mignotte, Samir Siksek, "Classical and modular approaches to exponential Diophantine equations II. The Lebesgue-Nagell equation", Compositio Mathematica 142 (2006), 31-62.
- Samir Siksek and Michael Stoll, "Partial descent on hyperelliptic curves and the generalized Fermat equation `x^3 + y^4 + z^5 = 0`", Bulletin of the London Mathematical Society 44 (2012), 151-166; arXiv: <https://arxiv.org/abs/1103.1979>.
- Bjorn Poonen, Edward F. Schaefer, Michael Stoll, "Twists of `X(7)` and primitive solutions to `x^2 + y^3 = z^7`", Duke Mathematical Journal 137 (2007), 103-158; arXiv: <https://arxiv.org/abs/math/0508174>.
- Jineon Baek and Seewoo Lee, "Formalizing Mason-Stothers Theorem and its Corollaries in Lean 4", arXiv:2408.15180 (2024/2025); <https://arxiv.org/abs/2408.15180>.
- Paul Vojta, "Diophantine Approximations and Value Distribution Theory", Lecture Notes in Mathematics 1239, Springer, 1987; and "On the abc conjecture and diophantine approximation by rational points", arXiv: <https://arxiv.org/abs/math/9908024>.
- Gerd Faltings, "Endlichkeitssatze fur abelsche Varietaten uber Zahlkorpern", Inventiones Mathematicae 73 (1983), 349-366.
- Michael Bennett, Imin Chen, Sander Dahmen, Soroosh Yazdani, "Generalized Fermat equations: a miscellany", International Journal of Number Theory 11 (2015), 1-28.

## Common Reduction Framework

For a primitive Beal counterexample,

```text
A^x + B^y = C^z,     x,y,z >= 3,     gcd(A,B,C)=1,
```

one may reduce exponents to prime powers or prime divisors in many arguments. If `p | x`, `q | y`, and `r | z`, then setting `X=A^(x/p)`, `Y=B^(y/q)`, `Z=C^(z/r)` gives

```text
X^p + Y^q = Z^r.
```

This makes prime signatures central. Equal signatures reduce to Fermat-type equations; exponent triples where all exponents are multiples of 4 are already controlled by FLT-4-type reductions in the existing project. The hard remaining cases are mixed prime signatures such as `(3,4,5)`, `(3,5,7)`, `(3,7,11)`, and all-even cases not reducible to a full multiple-of-4 obstruction.

## 1. Darmon-Granville Theorem

**Mathematical idea.** Darmon and Granville attach fixed-signature generalized Fermat equations to curves or covers whose rational points control primitive solutions. For hyperbolic signatures, `1/p + 1/q + 1/r < 1`, the relevant geometry has genus greater than 1, and Faltings' theorem gives finiteness of rational points. This converts each fixed signature into a finite problem.

**Strongest known result.** Darmon-Granville (1995) proves finiteness of primitive solutions to `A x^p + B y^q = C z^r` for fixed nonzero coefficients and hyperbolic exponents. This covers every fixed Beal signature with `p,q,r >= 3` except the boundary/equal low cases, which are handled by FLT or special arguments.

**Applied to mixed Beal?** Yes, but only as finiteness. It says fixed signatures such as `(3,4,5)` and `(3,5,7)` have finitely many primitive solutions. It does not prove that the finite set is empty.

**Can we iterate?** No useful iteration is known. One can reduce a Beal counterexample to a prime-divisor signature, but there are infinitely many prime triples. Darmon-Granville gives one finite set per fixed triple, not a uniform finite list over all triples. Iterating over signatures recreates the full Beal problem.

**Lean 4 + Mathlib effort.**

- Statement/interface only: 1k-3k LOC, weeks.
- Formal use for fixed signatures, with Faltings/Darmon-Granville as axioms: 5k-15k LOC, months.
- Full proof: 250k-700k LOC, 20-50 person-years, because it needs serious algebraic geometry, heights, abelian varieties, Faltings, and curve covers.

**Payoff.** Medium as infrastructure, low as a proof route. It cleanly formalizes "fixed signatures are finite", but closes no new Beal subcase without effective point computation.

## 2. Effective Baker Theory

**Mathematical idea.** Baker theory gives explicit lower bounds for nonzero linear forms in logarithms, both archimedean and `p`-adic. Exponential Diophantine equations are attacked by converting a hypothetical solution into a very small nonzero expression such as `alpha_1^{n_1} ... alpha_k^{n_k} - 1`, then contradicting the lower bound unless exponents or variables are bounded. The remaining finite range is searched, often after LLL/Baker-Davenport reductions.

**Strongest known result.** Shorey-Tijdeman's book "Exponential Diophantine Equations" (1986) systematizes Baker-theoretic bounds for perfect powers and related equations. Stewart-Yu's 1991 and 2001 weak-ABC results are Baker-theoretic in spirit and give explicit radical-based bounds for `a+b=c`. Bugeaud-Mignotte-Siksek (2006) show the practical modern pattern: combine improved linear forms in logarithms, Thue equations, and modular information to solve specific families such as perfect powers in Fibonacci/Lucas sequences and Lebesgue-Nagell equations.

**Applied to mixed Beal?** Not in a way that proves Beal or broad mixed signatures. Baker methods solve many special exponential equations, especially when a reduction to an `S`-unit equation, Thue equation, or Mordell equation is available. Beal has three variable bases and three variable exponents, which prevents a direct uniform `S`-unit setup with fixed `S`.

**Can Baker give a computable global bound?** In principle, for fixed auxiliary data or fixed signatures one can often make bounds effective. For unrestricted Beal, no practical theorem is known giving a computable bound `max(A,B,C,x,y,z) <= N` such that every primitive counterexample lies below `N`. Even if one extracts a bound from existing logarithmic-form machinery signature by signature, it depends on data that varies with the bases or number fields and is astronomically large.

**Tractability for `x,y,z <= 100`.** Not tractable in the naive sense. There are about `98^3 = 941,192` exponent triples. Reducing to prime divisors lowers the number of prime signatures to primes `<= 100`, i.e. `25^3 = 15,625`, still huge. A Baker bound for one signature can easily exceed `10^100`, `10^1000`, or much worse after explicit constants. Such a bound does not support exhaustive search over bases.

**Lean 4 + Mathlib effort.**

- Basic logarithm/height statements as axioms: 5k-15k LOC, months.
- Verified Matveev/Baker-Wustholz style explicit bounds: 120k-350k LOC, 8-20 person-years.
- A single solved Baker-style equation with external computation certificates: 20k-60k LOC, 1-4 person-years after infrastructure.

**Payoff.** Medium for selected equations, low for Beal. It can support bounded subcases and formalized examples, but no known route closes broad mixed signatures.

## 3. Quantitative ABC, Proven Weak Forms

**Mathematical idea.** For coprime `a+b=c`, ABC predicts `c <= K_epsilon rad(abc)^(1+epsilon)`. Since `A^x`, `B^y`, and `C^z` have radicals much smaller than their sizes when exponents are large, ABC strongly constrains Beal-type equations. Proven weak ABC substitutes much larger exponential functions of the radical.

**Strongest known result.** Stewart-Tijdeman (1986) proved an exponentially weak Oesterle-Masser/ABC-type upper bound. Stewart-Yu improved the exponent in 1991 and again in 2001; standard summaries quote bounds of the shape

```text
c < exp(K_epsilon * rad(abc)^(1/3 + epsilon))
```

or related forms with logarithmic factors/effective constants. These are major unconditional theorems, but much weaker than ABC's near-linear radical bound.

**Applied to mixed Beal?** Conditional ABC implies finiteness of Fermat-Catalan/Beal-type primitive solutions, but not their absence. Proven weak forms do not rule out Beal counterexamples. They are too weak because `rad(A B C)` is not bounded independently of `A,B,C`.

**Concrete inequality check.** From

```text
C^z <= exp(K * rad(ABC)^(1/3) * log(rad(ABC))^3),
rad(ABC) <= ABC,
```

one gets only a very weak relation between sizes. Since `A,B,C` are themselves unbounded, this cannot force `z < 3` or exclude `x,y,z >= 3`.

**Lean 4 + Mathlib effort.**

- Formal ABC conjecture and implication to finiteness: 5k-20k LOC, 3-9 months if ABC is assumed.
- Proven weak ABC statements as imported theorem interfaces: 2k-8k LOC, weeks.
- Formal proofs of Stewart-Tijdeman/Stewart-Yu: 150k-400k LOC, 8-20 person-years, requiring Baker theory, heights, algebraic numbers, and explicit constants.

**Payoff.** Low for unconditional Beal. Medium as a formal comparison theorem: "ABC would imply finiteness but not a complete proof."

## 4. Cyclotomic Field Methods

**Mathematical idea.** Factor expressions such as `X^p + Y^p` in `Z[zeta_p]`, control ideals, units, class groups, and ramification, then use regularity or class-number hypotheses to force divisibility contradictions. This is Kummer's route to FLT for regular primes.

**Strongest known result.** Classical Kummer theory proves FLT for regular primes. Modern Lean work has made substantial progress on FLT for regular primes, making this one of the more realistic advanced-number-theory formalization tracks.

**Applied to mixed Beal?** Only in limited special congruence forms. Mixed exponents such as `X^3 + Y^5 = Z^7` lack the symmetric factorization `X^p + Y^p`; choosing one cyclotomic field usually leaves the other side as an uncontrolled perfect power. There is no broad cyclotomic theorem closing Beal mixed signatures.

**Possible concrete subcases.** Cyclotomic arguments can help when two exponents coincide, e.g. `(p,p,r)`, or when a signature can be reduced to a regular-prime FLT obstruction. They are unlikely to solve `(3,4,5)` or `(3,5,7)` without descent or modular input.

**Lean 4 + Mathlib effort.**

- Reuse regular-prime FLT infrastructure for Beal equal-exponent reductions: 5k-15k LOC, weeks/months.
- New cyclotomic lemmas for `(p,p,r)`-style reductions: 20k-80k LOC, 1-3 person-years.
- General mixed-exponent cyclotomic attack: not a defined theorem; likely years plus new mathematics.

**Payoff.** Medium for formalizing equal-exponent and regular-prime reductions; low for open mixed Beal.

## 5. Class Field Theory, Brauer Groups, and Descent on Torsors

**Mathematical idea.** A fixed generalized Fermat equation defines a curve or a collection of covering curves. Descent replaces rational points on the original curve by rational points on finitely many torsors/covers, often controlled by Selmer groups, local solubility, and Brauer-Manin obstructions. If every relevant torsor is locally insoluble or has no rational points, the original equation has no primitive solution.

**Strongest known result.** Siksek-Stoll (2012) solved the Beal-relevant signature `(3,4,5)` by partial descent on hyperelliptic curves. Poonen-Schaefer-Stoll (2007) solved `x^2 + y^3 = z^7` using twists of `X(7)`, nonabelian descent, modularity, Chabauty, and Mordell-Weil sieve. These are among the strongest non-uniform fixed-signature methods.

**Applied to mixed Beal?** Yes. `(3,4,5)` is the flagship case: in the positive Beal form, it implies no primitive `A^3 + B^4 = C^5`. This is the most concrete non-full-modular Mission D success.

**Lean 4 + Mathlib effort.**

- Statement-only import of Siksek-Stoll theorem: 1k-3k LOC, days/weeks.
- Formal reduction from Beal `(3,4,5)` to their theorem: 5k-15k LOC, weeks/months.
- Verified partial descent proof with computational certificates: 40k-90k LOC, 3-8 person-years.
- General descent infrastructure for genus > 1 curves: 150k-500k LOC, 8-20 person-years.

**Payoff.** Highest among alternatives. It closes a real mixed Beal signature and builds reusable infrastructure. It still does not scale uniformly to all signatures.

## 6. Polynomial ABC / Mason-Stothers

**Mathematical idea.** Mason-Stothers is the function-field analogue of ABC. For coprime polynomials `a+b=c` over characteristic zero, it bounds the maximum degree by the degree of the radical minus one. It gives clean polynomial Fermat-Catalan nonexistence theorems because derivatives detect repeated factors.

**Strongest known result.** Mason-Stothers is classical. Baek-Lee formalized an elementary Snyder-style proof in Lean 4 and formalized consequences including polynomial Fermat-Cartan/Fermat-Catalan-type non-solvability, non-parametrizability of an elliptic curve, and Davenport's theorem; the 2025 version reports integration into Mathlib.

**Applied to integer Beal?** No direct transfer. Specializing polynomial identities to integers usually destroys the derivative/radical control. Mason-Stothers proves an analogue, not an integer theorem.

**Lean 4 + Mathlib effort.**

- Use existing Mathlib theorem: trivial to weeks.
- Add Beal-shaped polynomial corollaries: 1k-5k LOC, weeks.
- Develop a polished tutorial bridge from polynomial Beal to integer Beal obstruction: 3k-10k LOC, 1-3 months.

**Payoff.** High formalization payoff, low mathematical payoff for integer Beal. Recommended as infrastructure and pedagogy, not as a proof route.

## 7. Gel'fond-Schneider and Transcendence

**Mathematical idea.** Transcendence theory proves that certain values, such as algebraic powers with irrational algebraic exponents, are transcendental. Broader Diophantine applications include lower bounds for linear forms in logarithms and finiteness theorems for integral points, especially through Baker theory.

**Strongest known result.** Gel'fond-Schneider itself is not the tool for Beal because Beal has integer exponents. The relevant descendant is Baker's theory of linear forms in logarithms. Siegel's theorem on integral points and Baker's effective refinements are examples where transcendence/logarithmic methods affect Diophantine equations.

**Applied to mixed Beal?** Not directly. Any useful transcendence input is essentially Baker theory, already covered above.

**Lean 4 + Mathlib effort.**

- State Gel'fond-Schneider as an imported theorem: trivial/weeks.
- Formalize enough complex analysis/transcendence for proof: 100k-300k LOC, 5-15 person-years.
- Beal payoff proof: none known.

**Payoff.** Very low for Beal. Do not prioritize beyond references and theorem interfaces.

## 8. Computer Search up to Effective Bounds

**Mathematical idea.** Combine theoretical bounds with exhaustive search. For a fixed signature, if one can prove `A,B,C <= N`, then search all coprime triples or use modular sieves to eliminate candidates. This has worked for many bounded Diophantine problems when the bound is modest or reducible.

**Strongest known result.** Computational searches have found no Beal counterexample in large practical ranges, but such searches are not close to proof without a theoretical bound. For fixed equations, Magma/Sage computations inside descent and Chabauty pipelines are standard; Siksek-Stoll and Poonen-Schaefer-Stoll use heavy certified mathematics plus computation.

**Has anyone done this for small Beal cases?** The public state is: broad numerical searches exist, and many fixed signatures have been solved by specialized methods, but there is no known Baker-bound-plus-bruteforce proof covering all Beal signatures with `x,y,z <= 100`.

**Explicit bound scenario.** Suppose a theorem gave

```text
For each primitive solution to X^p + Y^q = Z^r with p,q,r <= 100,
max(X,Y,Z) <= 10^30.
```

Even this optimistic bound is too large for direct triple enumeration. It would require modular sieves, lattice reductions, local solubility filters, and probably curve-specific descent. Actual Baker-style bounds are usually far beyond `10^30`.

**Lean 4 + Mathlib effort.**

- Certified bounded search for small `N <= 10^4`: 2k-10k LOC, weeks.
- Verified modular sieve framework: 10k-40k LOC, months/year.
- Verified Magma/Sage-equivalent algebraic number theory computations: 100k-300k LOC, 5-15 person-years.

**Payoff.** Medium only when paired with a strong fixed-signature theorem. Low as a general Beal plan.

## 9. Vojta, Mordell, and Faltings

**Mathematical idea.** Beal fixed signatures are rational/integral point problems on curves or stacks. Faltings/Mordell gives finiteness for genus greater than 1. Vojta's conjectures provide a broad height inequality framework implying ABC and many Diophantine finiteness statements.

**Strongest known result.** Faltings proved Mordell in 1983: a smooth projective curve of genus greater than 1 over a number field has finitely many rational points. Vojta developed a general height-conjecture framework and showed forms of his conjectures imply ABC; expository sources summarize the slogan "Mordell is as easy as ABC" in that framework.

**Applied to mixed Beal?** Yes for finiteness, through Darmon-Granville/Faltings. Vojta/ABC would give stronger conditional finiteness. Neither gives an unconditional zero-solution theorem for all Beal signatures.

**Lean 4 + Mathlib effort.**

- Formal interfaces for Faltings/Vojta: 5k-20k LOC, months.
- Formal proof of Faltings: 250k-700k LOC, 20-50 person-years.
- Formal Vojta conjecture framework: 50k-150k LOC for statements, years for surrounding height machinery.

**Payoff.** Medium for conceptual roadmap, low for closing Beal. It identifies the finiteness boundary.

## 10. Additive Combinatorics and Sum-Product

**Mathematical idea.** Sum-product results say finite sets in rings/fields cannot have both small sumset and small product set unless structurally constrained. One might hope that sets of perfect powers have additive sparsity strong enough to obstruct equations like `A^x + B^y = C^z`.

**Strongest known result.** Sum-product theory is powerful over finite fields, real/complex numbers, and subsets of integers. It underlies incidence geometry, expansion, and additive number theory. However, it controls aggregate set growth, not isolated high-precision exponential identities.

**Applied to mixed Beal?** I found no credible published theorem applying sum-product bounds to prove a Beal mixed signature. The method may show that perfect powers are sparse statistically, but Beal is a universal no-exception statement.

**Lean 4 + Mathlib effort.**

- Basic finite-set combinatorics already partly present: weeks/months for small lemmas.
- Sum-product theorem formalization: 30k-100k LOC, 2-5 person-years.
- Beal payoff theorem: no known target.

**Payoff.** Very low. Not recommended for the Beal roadmap except as background exploration.

## Prioritized Effort/Payoff Ranking for 2026-2028

| Rank | Approach | Effort | Payoff | Recommendation |
|---:|---|---:|---:|---|
| 1 | Formalize `(3,4,5)` via Siksek-Stoll descent interface/certificates | 3-8 PY | High | Best concrete Mission D target |
| 2 | Generalized Fermat/Beal signature library + fixed-signature theorem interfaces | 0.5-2 PY | High infrastructure | Do now |
| 3 | Mason-Stothers polynomial Beal analogue in Mathlib style | weeks-3 months | Medium infrastructure | Quick win |
| 4 | Cyclotomic/equal-exponent reductions using FLT regular-prime infrastructure | 0.5-3 PY | Medium | Good adjacent formalization |
| 5 | Verified bounded-search and modular-sieve framework for small boxes | 0.5-2 PY | Medium | Useful only with certificates |
| 6 | Darmon-Granville/Faltings full proof | 20-50 PY | Conceptual only | Interface, do not prove now |
| 7 | Baker/linear-forms infrastructure | 8-20 PY | Medium for special equations | Too large unless separately funded |
| 8 | Stewart-Yu weak ABC formal proof | 8-20 PY | Low for Beal | Not a direct route |
| 9 | Vojta/ABC formal conjecture consequences | months-years | Low/conditional | State consequences only |
| 10 | Gel'fond-Schneider/transcendence beyond Baker | 5-15 PY | Very low | Do not prioritize |
| 11 | Additive combinatorics/sum-product | 2-5 PY | Very low | No Beal theorem target |

## Concrete Lean Roadmap

### Phase 1: Foundational Beal Library

Target: 5k-15k LOC, 1-3 months.

- Define primitive Beal counterexamples over `Nat` and `Int`.
- Prove reductions from arbitrary exponents to prime-divisor signatures.
- Normalize signs for equations `x^p + y^q + z^r = 0` versus `A^p + B^q = C^r`.
- Prove equal-exponent reductions to FLT theorem interfaces.
- Prove all-multiples-of-4 reductions to FLT-4 where applicable.

### Phase 2: Theorem Interfaces

Target: 5k-20k LOC, 2-6 months.

- State Darmon-Granville as a theorem interface for fixed hyperbolic signatures.
- State Faltings/Mordell interface for genus > 1 curves.
- State Siksek-Stoll `(3,4,5)` theorem precisely.
- State Stewart-Yu weak ABC bounds as imported theorem schemas, without proof.
- State ABC/Vojta consequences separately and mark them conditional.

### Phase 3: Quick Formal Wins

Target: 5k-20k LOC, 1-6 months.

- Add polynomial Beal/Mason-Stothers corollaries.
- Add certified finite search for very small bounds, e.g. `A,B,C <= 100`, not as mathematical progress but as executable infrastructure.
- Add congruence filters modulo small primes for fixed signatures.

### Phase 4: Publishable Subcase

Target: 40k-90k LOC, 3-8 person-years.

- Formalize or certificate-check the Siksek-Stoll partial descent result for `(3,4,5)`.
- Minimal viable publication version may trust Magma computations via explicit certificates:
  - number field arithmetic certificates;
  - local solubility certificates;
  - Selmer-set emptiness certificates;
  - rational point exclusions on finitely many hyperelliptic curves.
- Stronger version verifies the computational algebra inside Lean or through a tiny trusted checker.

## Honest Assessment

No approach in this Mission D list is likely to close the general Beal conjecture with current mathematics. The alternatives either:

- prove only finiteness for fixed signatures;
- are conditional on ABC/Vojta;
- give effective but unusably enormous bounds;
- solve isolated signatures through case-specific descent;
- or are analogies without integer force.

Thus the real bottleneck remains either the full modular method plus extensive new uniformity, or a major new idea not currently present in the literature.

The smallest concrete subcase worth formalizing is `(3,4,5)`, not a blanket claim such as all `min(x,y,z) <= 10`. A theorem covering all signatures with `min(x,y,z) <= 10` would include many hard mixed families and would likely require a patchwork of modular, descent, and computational results. It could be publishable if achieved, but it is not "elementary to dispatch."

## Final Recommendation

For an AI-assisted Lean roadmap in 2026-2028:

1. Build the generalized Fermat/Beal signature library.
2. Formalize Mason-Stothers polynomial analogues as a fast infrastructure win.
3. Import Darmon-Granville/Faltings/Stewart-Yu as carefully named theorem interfaces.
4. Target `(3,4,5)` as the main non-full-modular publishable subcase.
5. Avoid investing heavily in Baker, Vojta, weak ABC, or sum-product as direct Beal proof routes unless the project goal is broader formalized Diophantine infrastructure rather than Beal progress.

