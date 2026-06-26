# Mission C: Modular Method Feasibility for Beal

Date: 2026-06-26  
Workspace: `e1c1911e-a7da-4ea1-9dd6-dbf7d77801ad`

## Executive Verdict

The modular method is theoretically viable for many generalized Fermat equations, including Beal-relevant mixed signatures, but it is not currently a uniform proof strategy for the full Beal conjecture.

For a fixed signature

```text
A^p + B^q = C^r,     p,q,r >= 3,     gcd(A,B,C)=1,
```

the modern program is clear: attach a Frey elliptic curve, Q-curve, Frey abelian variety, or motive; prove modularity and irreducibility of a residual Galois representation; lower the level; then eliminate the resulting modular forms by local congruences and explicit computation. This is the same high-level pattern as the Wiles-Ribet proof of FLT.

The obstruction is not conceptual for one signature. It is uniformity. There is no known single Frey curve construction and level-lowering argument covering all mixed exponent triples `(p,q,r)`. Darmon's program replaces missing Frey curves by higher-dimensional abelian varieties of `GL_2`-type over totally real fields, but the program still depends on difficult image, modularity, and Hilbert-newform elimination problems. Recent work has expanded this program, but it remains far from a Beal proof.

Formalization is much further behind. Mathlib has foundational algebra, Galois theory, algebraic geometry, about 9.5K local lines under `Mathlib/AlgebraicGeometry/EllipticCurve`, and about 7.4K local lines under `Mathlib/NumberTheory/ModularForms` in the available snapshot. These are valuable foundations, not a formal modular method. The missing bridge includes conductors and minimal models, Tate modules, residual Galois representations of elliptic curves, modular curves, Hecke algebras/newforms, Ribet level lowering, modularity lifting, and verified newform computations.

Honest estimate: a serious Lean 4 modular-method library sufficient for Beal-style papers is a 200K-400K LOC effort, with 10-25 person-years for a useful narrow vertical slice and 30-80+ person-years for Wiles/Ribet-scale reusable machinery. AI assistance in 2026 helps with routine formalization, but it does not remove the mathematical gap for full Beal.

## What the Modular Method Requires

The FLT pipeline is:

1. Start from a primitive counterexample `a^n + b^n = c^n`.
2. Attach the Frey-Hellegouarch curve, usually written in a form such as `E : y^2 = x(x-a^n)(x+b^n)`.
3. Prove the mod `n` Galois representation on `E[n]` is irreducible and has controlled ramification.
4. Use modularity of semistable elliptic curves over `Q` and Ribet's level lowering.
5. Derive a modular form of an impossible low level.

For Beal or generalized Fermat signatures `(p,q,r)`, the analogous pipeline is:

1. Normalize to a primitive solution `gcd(A,B,C)=1`.
2. Choose a Frey object depending on the signature:
   - elliptic curve over `Q` for some signatures;
   - Q-curve over a number field;
   - Frey abelian variety of `GL_2`-type;
   - hyperelliptic/Frey curve or motive in multi-Frey approaches.
3. Compute its discriminant, conductor, local reduction types, and ramification at primes dividing `ABCpqr`.
4. Prove residual irreducibility or a large-image theorem.
5. Prove modularity of the Frey object, often over `Q` or a totally real field.
6. Apply level lowering to the residual representation.
7. Enumerate and eliminate newforms at the lowered level, usually by comparing Frobenius traces, local behavior, congruences, or rational points on auxiliary curves.

The hard pieces are not optional. Without conductor control the level is too large. Without irreducibility, level lowering is unavailable or much weaker. Without a finite newform computation, the contradiction usually does not appear. Without modularity over the relevant number field, the Frey object cannot be compared to modular forms at all.

## Known Mathematics Around Beal and Generalized Fermat

### Finiteness Is Known, Nonexistence Is Not

Darmon and Granville proved finiteness for fixed hyperbolic generalized Fermat equations in "On the equations `z^m = F(x,y)` and `Ax^p + By^q = Cz^r`", Bull. London Math. Soc. 27 (1995), 513-543. Their theorem implies that for fixed exponents with

```text
1/p + 1/q + 1/r < 1,
```

there are only finitely many primitive solutions, under the standard fixed-coefficient setup. This includes fixed Beal signatures such as `(3,4,5)` and `(3,5,7)`. It does not list the solutions and does not prove Beal.

The full Beal conjecture asks for zero primitive positive solutions for all exponent triples `>= 3`. That is much stronger than fixed-signature finiteness.

### The Signature `(3,4,5)`

The Beal-relevant signature `(3,4,5)` is solved, but not by a clean Wiles-style Frey elliptic curve argument. Siksek and Stoll, "Partial descent on hyperelliptic curves and the generalized Fermat equation `x^3 + y^4 + z^5 = 0`", Bull. London Math. Soc. 44 (2012), 151-166, solve the signature using partial descent on hyperelliptic curves. Their abstract says they define a Selmer set for factorizations of `f` over a number field and show that emptiness implies `C(Q)=empty`; they present `(3,4,5)` as an application "unassailable via the previously existing methods."

This is important for the roadmap: `(3,4,5)` is an excellent minimum Beal-relevant formalization target, but it is a descent/explicit-rational-points target more than a pure modular-method target.

### Modular Method Successes Near Beal

The modular method has solved many generalized Fermat families, including Beal-relevant or adjacent families:

- Wiles (1995) and Taylor-Wiles (1995): modularity of semistable elliptic curves over `Q`, plus Ribet level lowering gives FLT.
- Breuil-Conrad-Diamond-Taylor (2001): modularity of all elliptic curves over `Q`.
- Darmon-Merel (1997): variants of Fermat with signatures related to `(n,n,2)` and `(n,n,3)`.
- Bennett-Skinner and Bennett-Vatsal-Yazdani (early 2000s): modular methods for ternary equations and signatures such as `(p,p,3)`.
- Bennett-Chen, "Multi-Frey Q-curves and the Diophantine equation `a^2 + b^6 = c^n`", Algebra & Number Theory 6 (2012), 707-730.
- Poonen-Schaefer-Stoll, "Twists of `X(7)` and primitive solutions to `x^2 + y^3 = z^7`", Duke Math. J. 137 (2007), 103-158.
- Anni-Siksek, "Modular elliptic curves over real abelian fields and the generalized Fermat equation `x^{2l}+y^{2m}=z^p`", Algebra & Number Theory 10 (2016), 1147-1173.
- Freitas-Naskrecki-Stoll, "The generalized Fermat equation with exponents `2,3,n`", Compositio Math. 156 (2020), 77-113.
- Dahmen-Siksek, "Perfect powers expressible as sums of two fifth or seventh powers", which treats cases such as `(5,5,7)`, `(5,5,19)`, and `(7,7,5)` and permutations.
- Billerey-Chen-Dembele-Dieulefait-Freitas, work on extensions of the modular method and signatures such as `(13,13,n)`.

Surveys:

- Bennett, Chen, Dahmen, Yazdani, "Generalized Fermat equations: A miscellany", Int. J. Number Theory 11 (2015), 1-28.
- Bennett, Mihailescu, Siksek, "The Generalized Fermat Equation", in Open Problems in Mathematics, Springer (2016).
- Billerey and Freitas, "The Generalized Fermat Equation", CIM Bulletin article, 2024/2025.
- Ratcliffe and Grechuk, "Generalised Fermat equation: a survey of solved cases", arXiv:2412.11933.

### Darmon's Program and Structural Limits

Darmon proposed a program using Frey abelian varieties of `GL_2`-type over totally real fields for generalized Fermat equations. This is the natural replacement when a rational Frey elliptic curve is unavailable.

Billerey, Chen, Dieulefait, and Freitas, "On Darmon's program for the generalized Fermat equation, I", arXiv:2205.15861, summarize the current state: Darmon's original approach used hard open conjectures; recent work develops many necessary ingredients using Frey abelian varieties, but some steps, especially elimination of Hilbert newforms at Serre level and residual image issues, remain central bottlenecks.

A useful warning from Billerey-Freitas survey material: only a few exponent choices have known rational Frey curves. For many signatures, one must use higher-dimensional varieties or number-field objects. This is the structural reason FLT does not directly generalize to Beal.

## Why It Might Work for Beal Signatures

For fixed signatures, Beal lies inside the generalized Fermat equation literature. The modular method is precisely the most successful method in that literature.

It might work because:

- Primitive Beal triples give high powers, and high powers create strong ramification divisibility in discriminants/conductors.
- Level lowering can erase primes dividing `A`, `B`, and `C`, forcing a representation to arise from a small-level modular form.
- Many fixed signatures leave only a finite and computable newform list.
- Multi-Frey strategies can combine incompatible Frey objects; one object may prove modularity/level constraints while another eliminates remaining newforms.
- For signatures with one large prime exponent, residual representations modulo that exponent can become rigid enough to contradict local conditions.

But the method hits major obstructions:

- No uniform Frey curve exists for all mixed triples `(p,q,r)`.
- Some signatures require Frey abelian varieties over totally real fields, not elliptic curves over `Q`.
- Modularity over totally real fields is known only in many cases, not in a one-line universal theorem matching all required Frey objects.
- Level lowering over number fields is harder than Ribet over `Q`.
- Residual irreducibility/large image can fail or require deep case-specific arguments.
- The newform-elimination step is often computational and signature-specific.
- Some modular-method pipelines reduce to "trivial" or "ghost" congruence classes that do not contradict automatically.

Bottom line: the modular method is a viable proof technology for islands of Beal, not a known path to all of Beal.

## Formalization State in 2026

### Lean and Mathlib

The local Mathlib snapshot contains meaningful foundations:

- `Mathlib/AlgebraicGeometry/EllipticCurve`: about 9,487 LOC locally, including Weierstrass curves, affine/projective/Jacobian points, formulas, variable change, reduction, division polynomials, and an `LFunction` file.
- `Mathlib/NumberTheory/ModularForms`: about 7,425 LOC locally, including arithmetic subgroups, congruence subgroups, slash actions, modular forms/cusp forms, q-expansions, Eisenstein series, Dedekind eta/discriminant, level-one dimension formula and Sturm bound.
- `Mathlib/FieldTheory/AbsoluteGaloisGroup` and broad Galois theory.
- General representation theory and continuous representation files.
- Formalized Mason-Stothers theorem and FLT-3/FLT-4/basic FLT material.

This does not amount to the modular method. The missing Lean content includes:

- elliptic curves over `Q`/number fields as arithmetic objects with minimal integral models;
- discriminants, local minimality, Kodaira/Neron reduction, conductors;
- Mordell-Weil theorem, torsion, isogenies, Tate modules;
- Galois representations attached to elliptic curves and modular forms;
- ramification, inertia, Frobenius traces, residual representations;
- modular curves `X_0(N)`, `X_1(N)`, Jacobians, Hecke correspondences;
- Hecke algebras, newforms, old/new decomposition, coefficient fields;
- Deligne/Eichler-Shimura construction of Galois representations;
- Ribet level lowering;
- modularity lifting theorems;
- verified modular-symbol/newform computations.

The active Lean FLT project is the closest relevant effort. The Lean use-case page says the project is not formalizing Wiles' original proof verbatim; it uses a modern route involving Khare-Wintenberger, Kisin, and the `R = T` paradigm. Kevin Buzzard's 2024 project updates stated that even defining the relevant deformation ring `R` and Hecke algebra `T` was still ongoing. That is a reliable indicator of how early the formal Wiles infrastructure remains.

There is also a partial Lean formalization of the statement of Deligne's theorem on attaching a p-adic Galois representation to a modular eigenform by Karatarakis et al. The point is significant: the statement-level vocabulary can be encoded, but the proof infrastructure is not present.

### Coq and Isabelle

I found no completed Coq or Isabelle formalization of Wiles' theorem, Ribet level lowering, or a full modular-method proof of FLT.

Relevant comparison points:

- Coq has major finite group and algebra achievements, including the Feit-Thompson theorem and the Four Color Theorem, but not Wiles-style arithmetic geometry.
- Isabelle/HOL has substantial analysis, algebra, number theory, and elliptic-curve-adjacent formalizations in various libraries, but no formalized modularity theorem or Ribet theorem.
- The Wiles formalization discussion has existed since at least Jan Bergstra's 2005 problem proposal, but as of 2026 the serious community effort is centered in Lean.

So the answer to "has any of the modular method been formalized?" is:

- Basic prerequisites: yes, partially, especially algebra, Galois theory, early elliptic curves, and classical modular forms.
- End-to-end modular method: no.
- Ribet level lowering: no.
- Wiles/Taylor-Wiles modularity lifting: no completed formal proof.
- A Beal-specific Frey curve proof: no.

## Effort Estimate in Lean 4

The user's proposed numbers are in the right order, but the estimates should be split between "library foundations" and "one proof vertical."

| Component | Current status | New Mathlib LOC estimate | Notes |
|---|---:|---:|---|
| Elliptic curves over `Q` and number fields | foundations present, arithmetic mostly missing | 40K-70K | minimal models, reduction, conductors, torsion, isogenies, Tate modules |
| Local fields/ramification/conductors | partial foundations | 30K-60K | inertia, Artin/Swan conductors, semistability, Neron/Kodaira data |
| Galois representations | generic representation theory present | 60K-100K | continuous 2D reps, residual reps, Frobenius traces, deformation setup |
| Modular forms/newforms/Hecke | analytic basics present | 80K-140K | Hecke operators, modular curves, newforms, Hecke algebras, q-expansion computations |
| Modular curves/Jacobians/Eichler-Shimura/Deligne | mostly absent | 60K-120K | needed to attach reps to forms, depending on route |
| Ribet level lowering | absent | 40K-80K | uses deep arithmetic geometry; can be stated axiomatically much cheaper |
| Modularity lifting / `R = T` | active FLT project, not complete | 60K-120K | deformation rings, Hecke algebras, commutative algebra, patching |
| Verified computations | mostly absent | 20K-60K | modular symbols/newforms or certificate checkers |
| Beal Frey-object applications | absent | 10K-40K per family | conductor arithmetic and final eliminations |

Total realistic reusable effort: **200K-400K new Mathlib LOC** for a useful modular-method stack. A fully general Darmon-program stack over totally real fields could exceed **500K LOC** once Hilbert modular forms, Frey abelian varieties, and computational certificates are included.

Person-year estimate:

- Narrow conditional vertical slice with black-box modularity/level-lowering theorems: 2-5 person-years.
- One honest fixed-signature proof with certified computations after prerequisites: 5-12 person-years.
- Reusable FLT/Ribet/Wiles-style infrastructure: 30-80+ person-years.
- Full Beal: not estimateable as formalization alone, because the mathematical theorem is open.

## Concrete Milestones

### M1: Arithmetic Elliptic Curves over `Q`

Goal: make elliptic curves usable as Frey curves.

Deliverables:

- integral Weierstrass models over `Z` and base change to `Q`;
- discriminant, `c4`, `c6`, `j`;
- rational points and group law connected to existing algebraic-geometry definitions;
- reduction modulo primes;
- local minimality and conductor for semistable cases;
- enough Tate algorithm interface for Frey curves.

Estimated LOC: 40K-70K.  
Feasibility by 2028: high for a focused team.

### M2: Galois Representations `G_Q -> GL_2`

Goal: encode residual representations attached to elliptic curves.

Deliverables:

- Tate modules and torsion subgroups `E[n]`;
- absolute Galois group action on torsion;
- residual mod `p` representation;
- irreducibility predicates;
- inertia/Frobenius traces at good primes;
- ramification bounds from reduction type.

Estimated LOC: 60K-100K.  
Feasibility by 2029-2031: medium, depends on M1 and local fields.

### M3: Modular Forms, Hecke Operators, Newforms

Goal: connect Galois representations to modular forms at level `N`.

Deliverables:

- Hecke operators on spaces of modular forms/cusp forms;
- finite-dimensionality and bases beyond level 1;
- oldform/newform decomposition;
- normalized eigenforms and coefficient fields;
- modular-symbol computation interface or certificate checker;
- Sturm bounds for congruence subgroups.

Estimated LOC: 80K-140K.  
Feasibility by 2030-2032: medium.

### M4: Ribet Level Lowering

Goal: formalize the theorem that allows removing primes from the level for residual representations.

Deliverables:

- theorem statement first, with hypotheses aligned to Frey-curve applications;
- semistable-over-`Q` version before number-field versions;
- local condition lemmas for Frey curves;
- later: proof via modular curves/Jacobians and component groups.

Estimated LOC:

- statement plus application API: 5K-15K;
- proof: 40K-80K, likely more with prerequisites.

Feasibility by 2032-2035 for a theorem statement/API; proof depends on the FLT project.

### M5: Attach Frey Curve to Beal Triples

Goal: prove Beal-style contradiction for selected signatures.

Deliverables:

- formal primitive Beal triple normalization;
- signature-specific Frey object;
- discriminant/conductor calculations;
- residual irreducibility hypothesis or theorem;
- level lowering invocation;
- modular-form elimination with verified finite computation.

Estimated LOC: 10K-40K per signature after M1-M4.

Best first targets:

1. Reprove the FLT Frey-curve contradiction as an integration test once Wiles/Ribet black boxes are available.
2. A fixed generalized Fermat family with a known rational Frey curve and modest newform elimination.
3. Beal-relevant `(3,4,5)`, but likely by formalizing Siksek-Stoll descent rather than modular method.
4. A modular-method Beal-relevant family such as `(5,5,7)`/permutations from Dahmen-Siksek, if the computational elimination can be certified.

## Minimum Subclaims Worth Proving

### Minimum Modular-Method Subclaim

A realistic first modular-method theorem is conditional:

```text
Assume:
  - a primitive solution of a fixed signature gives Frey curve E;
  - rho_E,p is irreducible;
  - E is modular;
  - Ribet level lowering applies;
  - the lowered newform list is empty or locally incompatible.
Then no primitive solution exists for that signature.
```

This can be useful even before Wiles/Ribet are formalized, because it fixes the Beal-side API and forces all discriminant/conductor calculations to be precise.

### Minimum Unconditional Beal-Relevant Subclaim

The best Beal-relevant target is:

```text
No nonzero primitive integer solutions to x^3 + y^4 + z^5 = 0.
```

This is the Siksek-Stoll `(3,4,5)` theorem. It is not the cleanest modular-method target, but it is the most iconic mixed-exponent Beal case and already solved in the literature.

Formalizing it probably requires:

- hyperelliptic curves;
- number-field factorization certificates;
- Selmer-set emptiness certificates;
- local solubility computations;
- descent correctness theorem.

Estimated effort: 3-8 person-years with certificate-driven computation, less if computational steps are trusted as axioms.

### Minimum End-to-End Wiles-Style Subclaim

If the mission insists on Frey + modularity + level lowering, the best minimum is not `(3,4,5)`. It is an FLT-style or near-FLT family where the Frey elliptic curve is classical and the newform elimination is tiny. That proves the pipeline, but it does not add new Beal coverage beyond existing equal-exponent cases.

## Realism Timeline

### 2026

Not realistic to formalize the modular method for Beal end-to-end. Also not realistic to formalize a full Wiles/Ribet proof from scratch inside this mission. AI assistance can accelerate local algebraic calculations, but the missing objects are large mathematical libraries, not just tedious theorem scripts.

Realistic in 2026:

- write theorem statements and APIs;
- formalize primitive triple reductions;
- formalize Frey curve equations and discriminant calculations for selected signatures;
- state modularity/level-lowering as black-box assumptions;
- build certificate formats for modular-form elimination;
- begin an arithmetic elliptic-curve library.

### 2028-2032

Plausible with a funded team:

- robust elliptic curves over `Q`;
- Tate modules and residual representations;
- enough modular forms/Hecke operators for low-level computation;
- conditional modular-method proofs for selected signatures;
- maybe one unconditional fixed-signature proof if black-box Wiles/Ribet theorem statements are accepted from the FLT project.

### 2032-2038

Plausible for serious Wiles/Ribet-level formalization if the Lean FLT project succeeds:

- reusable Ribet level lowering over `Q`;
- modularity theorem for elliptic curves over `Q` or enough semistable cases;
- end-to-end formal FLT modular proof;
- selected generalized Fermat modular-method proofs over `Q`.

### 2040+

Full Beal is still not a formalization forecast because the mathematics is open. If new mathematics produces a uniform Beal proof, formalization may lag by 5-15 years depending on how much arithmetic geometry is already in Mathlib.

## Risk Register

| Risk | Severity | Comment |
|---|---:|---|
| No known uniform Frey object for all Beal signatures | critical | mathematical blocker |
| Need Hilbert modular forms / abelian varieties over totally real fields | high | beyond current Mathlib and beyond simple Wiles over `Q` |
| Level lowering over number fields | high | known in forms, but formalizing is very hard |
| Newform elimination depends on Magma/Sage computations | high | can be handled by certificates, but must design them |
| Irreducibility/large image arguments are case-specific | high | cannot be hidden in one generic lemma |
| `(3,4,5)` solved by descent, not modular method | medium | affects milestone choice |
| Formalizing Wiles does not prove Beal | critical | it gives infrastructure, not the missing generalized theorem |

## Recommended Plan

Do not make "formalize the modular method for Beal" the immediate proof objective. Make it an infrastructure mission with narrow demonstrators.

Recommended sequence:

1. Formalize a generic `PrimitiveBealTriple` and fixed-signature generalized Fermat equation API.
2. Formalize Frey-curve construction and discriminant calculations for FLT and one generalized Fermat family with known rational Frey curve.
3. State modularity, irreducibility, and level-lowering theorems behind typeclasses or named hypotheses.
4. Build a certificate checker for "no compatible newforms at level `N`" rather than formalizing a full modular-symbol algorithm immediately.
5. Prove a conditional modular-method no-solution theorem for one fixed signature.
6. In parallel, pursue `(3,4,5)` via Siksek-Stoll descent as the smallest genuinely mixed Beal success.

## Final Assessment

The modular method is the correct serious machinery to study Beal-like equations, but it is not a ready-made Beal proof. For FLT, the Frey curve is uniform and the contradiction lands at level 2. For Beal, mixed exponents create many signatures, many Frey objects, and many final computations.

As a Lean project, the modular method is worth building because it would unlock large areas of arithmetic geometry and many generalized Fermat results. As a direct 2026 path to Beal, it is not realistic.

Best near-term deliverable: a conditional modular-method framework plus one formal Frey-curve/conductor calculation.  
Best Beal-relevant theorem target: formalize the solved signature `(3,4,5)` using Siksek-Stoll descent.  
Best long-term modular target: reuse the Lean FLT project's Wiles/Ribet infrastructure once it exists, then attack selected generalized Fermat signatures with certified newform eliminations.

## Sources

- Andrew Wiles, "Modular elliptic curves and Fermat's Last Theorem", Annals of Mathematics 141 (1995), 443-551.
- Richard Taylor and Andrew Wiles, "Ring theoretic properties of certain Hecke algebras", Annals of Mathematics 141 (1995), 553-572.
- Kenneth Ribet, "On modular representations of `Gal(Qbar/Q)` arising from modular forms", Inventiones Mathematicae 100 (1990), 431-476.
- Christophe Breuil, Brian Conrad, Fred Diamond, Richard Taylor, "On the modularity of elliptic curves over `Q`: wild 3-adic exercises", JAMS 14 (2001), 843-939.
- Henri Darmon and Andrew Granville, "On the equations `z^m = F(x,y)` and `Ax^p + By^q = Cz^r`", Bull. London Math. Soc. 27 (1995), 513-543.
- Henri Darmon and Loic Merel, "Winding quotients and some variants of Fermat's Last Theorem", J. Reine Angew. Math. 490 (1997), 81-100.
- Michael Bennett, Imin Chen, Sander Dahmen, Soroosh Yazdani, "Generalized Fermat equations: A miscellany", Int. J. Number Theory 11 (2015), 1-28.
- Michael Bennett, Preda Mihailescu, Samir Siksek, "The Generalized Fermat Equation", in Open Problems in Mathematics, Springer (2016).
- Samir Siksek and Michael Stoll, "Partial descent on hyperelliptic curves and the generalized Fermat equation `x^3 + y^4 + z^5 = 0`", Bull. London Math. Soc. 44 (2012), 151-166.
- Bjorn Poonen, Edward Schaefer, Michael Stoll, "Twists of `X(7)` and primitive solutions to `x^2 + y^3 = z^7`", Duke Math. J. 137 (2007), 103-158.
- Michael Bennett and Imin Chen, "Multi-Frey Q-curves and the Diophantine equation `a^2 + b^6 = c^n`", Algebra & Number Theory 6 (2012), 707-730.
- Samuele Anni and Samir Siksek, "Modular elliptic curves over real abelian fields and the generalized Fermat equation `x^{2l}+y^{2m}=z^p`", Algebra & Number Theory 10 (2016), 1147-1173.
- Nuno Freitas, Bartosz Naskrecki, Michael Stoll, "The generalized Fermat equation with exponents `2,3,n`", Compositio Mathematica 156 (2020), 77-113.
- Nicolas Billerey, Imin Chen, Luis Dieulefait, Nuno Freitas, "On Darmon's program for the generalized Fermat equation, I", arXiv:2205.15861.
- Nicolas Billerey and Nuno Freitas, "The Generalized Fermat Equation", CIM Bulletin article, 2024/2025.
- Ashleigh Ratcliffe and Bogdan Grechuk, "Generalised Fermat equation: a survey of solved cases", arXiv:2412.11933.
- David Kurniadi Angdinata and Junyan Xu, "An Elementary Formal Proof of the Group Law on Weierstrass Elliptic Curves in any Characteristic", arXiv:2302.10640.
- Michail Karatarakis et al., "A Formalization of All Notions in the Statement of a Theorem by Deligne", CICM 2024.
- Lean FLT project, ImperialCollegeLondon/FLT, ongoing Lean formalization of Fermat's Last Theorem.
- Lean mathlib documentation for `Mathlib.AlgebraicGeometry.EllipticCurve.Weierstrass` and `Mathlib.NumberTheory.ModularForms`.
