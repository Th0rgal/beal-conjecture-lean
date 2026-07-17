# DGX Spark computational checkpoint — 2026-07-17

## Status and trust boundary

This checkpoint records bounded exact-arithmetic experiments run on the DGX
Spark. It is **not a proof of the Beal conjecture**, does not remove the single
intentional `sorry` in `BealUnified/BealConjecture.lean`, and does not prove a
primitive-divisor existence theorem.

The producer scripts and machine-readable results are under
`experiments/dgx_spark/`. A separate checker replayed every finite-field support
witness, all recorded high-valuation cyclotomic cases, the LTE
assumption-removal counterexamples, and the CUDA differential metadata.

## Environment

- Host: `spark-de79`, Ubuntu 24.04, `aarch64`
- CPU: 20 cores available; experiments were intentionally limited to two workers
- GPU: NVIDIA GB10, compute capability 12.1
- CUDA: 13.0, native compilation with `-arch=sm_121`
- PARI/GP: 2.15.4, pthread build; Python binding `cypari2` 2.1.4
- Repository baseline: `d83704e0904c504ef314bc9cabe08ffd7f67c8a8`
- Resident model: `gemma-4` through `vllm-backend`

The CPU experiments ran while vLLM remained available. CUDA could not allocate
its small calibration buffers while vLLM was resident, so the benchmark used an
explicitly authorized exclusive GPU window. `vllm-backend` and `spark-arbiter`
were restored afterward, and `/health` returned `{"status":"ok",
"current_model":"gemma-4"}`.

## Experiment 1 — finite-field support atlas

### Scope

- Normalized exponent kernels: `3,4,5,7,11,13`
- All 216 ordered signatures
- Every prime `q <= 251`
- 11,664 exact signature-prime checks
- For each check, enumerate the nonzero power subgroups
  `H_x(q), H_y(q), H_z(q)` and count `X + Y = Z` with all three entries nonzero

### Results

- 254 all-unit branches were empty.
- Every signature had at least the trivial support condition at `q=2`.
- Only 16 signatures had an odd support-forcing prime; ten were genuinely mixed.
- The ten mixed rows were permutations in the tested set with two exponent-4
  positions including the right side, such as `(3,4,4)`, `(4,3,4)`,
  `(5,4,4)`, and `(4,5,4)`. For these rows, `q=3` and `q=5` forced
  `q | A*B*C`.
- The permanent residue branch `A=0, B=C=1 mod q` survived every tested
  signature and prime, as expected.

### Interpretation

An empty all-unit branch is a checkable support lemma, not a contradiction.
These data reinforce the rule that finite-field work should classify which base
contains a prime and how that support couples to cyclotomic or conductor data.
A fixed modulus cannot eliminate a primitive signature on its own.

## Experiment 2 — plus-sign LTE assumption miner

### Scope

- Coprime positive bases `a,b <= 200`
- Odd primes `q <= 97`
- Odd exponents `3 <= n <= 31`
- Required hypotheses: `q | a+b` and `q` divides neither base
- 422,340 exact cases

### Results

No violation was found for

```text
v_q(a^n + b^n) = v_q(a+b) + v_q(n)
```

under the stated hypotheses.

The bounded falsifier immediately found counterexamples when essential
hypotheses were removed:

| Removed hypothesis | First counterexample | Actual / predicted valuation |
|---|---|---|
| `n` odd | `q=3, a=1, b=2, n=2` | `0 / 1` |
| `q | a+b` | `q=3, a=1, b=1, n=3` | `0 / 1` |
| base/unit coprimality (`gcd(a,b)=1`, hence `q ∤ ab`) | `q=3, a=3, b=3, n=3` | `3 / 2` |

No failure was found for `q=2` with odd `n` in this bounded search. That is an
observation only; it is not promoted to a general theorem here.

### Interpretation

The data support the exact hypothesis shape already targeted by
`BealUnified.LTEConclusion`, but do not solve the formalization gap. They do
show why a future Lean theorem must keep parity, divisibility, and unit
hypotheses explicit rather than patching failures ad hoc.

## Experiment 3 — odd plus-cyclotomic census

For each odd prime `ell in {3,5,7,11}` and every ordered coprime pair
`1 <= U,V <= 100`, the script factored

```text
PhiPlus_ell(U,V) = (U^ell + V^ell) / (U+V)
```

completely with PARI.

### Coverage

- 24,348 ordered coprime `(ell,U,V)` cases
- 55,758 prime-factor occurrences
- 3,774 occurrences of the exceptional prime `q=ell`

### Zero-failure checks for every nonexceptional factor `q != ell`

- factorization identity `(U+V) * PhiPlus = U^ell + V^ell`;
- `gcd(U+V, PhiPlus) | ell`;
- `ord_q(U/V) = 2*ell`;
- `ord_q(-U/V) = ell`;
- `q = 1 mod 2*ell`.

No failure was recorded in any of those four failure lists.

### Higher valuations are common enough to matter

There were 860 ordered occurrences with `v_q(PhiPlus) > 1`, or 430 after
identifying the `U,V` swap symmetry:

| `ell` | occurrences |
|---:|---:|
| 3 | 376 |
| 5 | 270 |
| 7 | 84 |
| 11 | 130 |

| valuation | occurrences |
|---:|---:|
| 2 | 788 |
| 3 | 60 |
| 4 | 12 |

The most frequent high-valuation primes were `7`, `11`, `23`, `13`, `29`,
`31`, and `19`. Concrete fourth-power examples include:

```text
ell=3, U=16, V=55: PhiPlus = 2401 = 7^4
ell=5, U=21, V=58: 11^4 divides PhiPlus
```

### Interpretation

The exact-order and congruence interfaces already merged into Lean match every
bounded nonexceptional factor observed. The useful negative result is equally
important: **a primitive/nonexceptional cyclotomic divisor cannot be assumed to
have valuation one**. Any route requiring `v_q=1` must prove an additional
ordinary-divisor theorem or classify higher-Wieferich lifts. Statistical rarity
is not a substitute.

## Experiment 4 — CUDA fixed-width modular exponentiation

A native CUDA 13 kernel computed `base^65537 mod 2147483647` for 4,000,000
inputs, repeated five times, and was differentially compared against a two-thread
CPU implementation.

- GPU: GB10 / `sm_121`
- mismatches: **0**
- two-thread CPU time for one batch: 0.110142 s
- GPU kernel time per repeated batch: 0.000688 s
- GPU kernel throughput: approximately 5.82 billion candidates/s
- CPU throughput: approximately 36.3 million candidates/s

The roughly 160x kernel-only ratio is a calibration for this one common-modulus,
31-bit workload. It is not a general bigint benchmark: inputs were reused across
repetitions, transfers were amortized, and the workload had no divergence.

With `vllm-backend` resident, even the 100,000-input smoke failed at `cudaMalloc`
with `CUDA error: out of memory`. On this host configuration, Beal CUDA work must
therefore use an exclusive, operator-controlled GPU window. CPU exact work can
continue beside the model service under the existing two-thread quota.

## Independent artifact verification

`verify_results.py` reported:

- 254 finite-field support witnesses replayed;
- 860 higher-valuation cyclotomic witnesses replayed;
- primality of every replayed finite-field and cyclotomic witness checked;
- three LTE counterexamples replayed;
- CUDA result checked with zero mismatches;
- shared-residency failure checked;
- overall status: `passed`.

SHA-256 checksums for every JSON artifact are stored in
`experiments/dgx_spark/results/SHA256SUMS`.

## Roadmap consequences

1. **Keep the fixed cyclotomic gcd congruence as the nearest Lean target.** The
   bounded data support the current `gcd(U+V,PhiPlus) | ell` interface and expose
   no counterexample, while the theorem still has a direct symbolic proof route.
2. **Reject unconditional valuation-one heuristics.** Replace them with a precise
   higher-Wieferich classification question, initially for a single `ell` and
   third exponent.
3. **Use finite fields as support/character preprocessors only.** The `(k,4,4)`
   support rows at `3` and `5` are potential inputs to a descent, not standalone
   obstruction theorems.
4. **Do not reopen generic LTE implementation solely because the bounded sweep is
   clean.** The experiment clarifies hypotheses but supplies no Lean artifact.
5. **Use CUDA only after a CPU reference and certificate schema exist.** The first
   candidate is batched power-residue/order filtering; general PARI/FLINT work
   remains on CPU.
6. **Continue to describe Beal as unproved.** The central primitive mixed-exponent
   case and the single intentional `sorry` are unchanged.
