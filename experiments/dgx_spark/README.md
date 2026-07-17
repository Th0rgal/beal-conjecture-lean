# DGX Spark computational experiments

Reproducible, bounded exact-arithmetic experiments supporting the Beal research
roadmap. They are **not** a proof of the unrestricted Beal conjecture.

## Experiments and assurance layers

- `finite_field_support.py`: exhaustive all-unit power-subgroup equations over
  finite prime fields. Empty unit branches imply only the support condition
  `q | A*B*C`; the permanent `A=0, B=C=1` branch is checked explicitly.
- `lte_assumption_miner.py`: bounded falsification of the odd-prime plus-sign LTE
  formula and counterexamples when assumptions are removed.
- `cyclotomic_census.py`: complete PARI factorization of odd plus-cyclotomic
  cofactors, with gcd, exact-order, congruence, and valuation checks. `ell` inputs
  must be distinct odd primes.
- `independent_reproduce.py`: reconstructs all three complete CPU domains with
  SymPy without importing producer or checker implementations, and compares the
  complete counts and witness sets.
- `cuda_modexp_bench.cu`: CPU/GPU differential calibration on GB10. Every timed
  repetition is copied back, digested, and compared against a separately coded
  `unsigned __int128` CPU reference. This is a performance probe, not a search
  certificate.
- `gpu_residency_probe.py`: machine-generated record of the allocation attempt
  while resident vLLM is running.
- `verify_results.py`: explicit artifact-consistency and witness-replay checker.
  It uses exceptions rather than Python `assert`, so `python -O` cannot disable
  verification.
- `provenance.py` and `environment_probe.py`: attach one run ID, exact producer
  commit, clean-source flag, producer hash, timestamps, source-file hashes, and
  measured host/service state.

## DGX prerequisites

Ubuntu 24.04 ARM64 packages:

```bash
sudo apt-get install pari-gp python3-cypari2 python3-pytest python3-sympy
```

CUDA 13 is expected at `/usr/local/cuda`; the benchmark is compiled specifically
for the Spark with `-arch=sm_121`.

## Reproduce

Canonical artifacts must start from a committed checkout whose source files are
clean. Use one run ID and start timestamp across all phases:

```bash
export RUN_ID="dgx-$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short=12 HEAD)"
export RUN_STARTED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
export SOURCE_COMMIT="$(git rev-parse HEAD)"
export SOURCE_BRANCH="$(git branch --show-current)"
export SOURCE_TREE_CLEAN=true
export PYTHONPATH="$(pwd)/experiments/dgx_spark"
test -n "$SOURCE_BRANCH"  # create a named local run branch for a detached checkout
```

### 1. CPU domains, independent reproduction, and resident-vLLM probe

The model service remains available. The probe records whether a small CUDA
allocation can coexist with it:

```bash
GPU_WINDOW=resident-vllm-cpu-and-allocation-probe \
RUN_CPU=1 RUN_CUDA=0 RUN_SHARED_PROBE=1 RUN_TESTS=0 \
  ./experiments/dgx_spark/run_suite.sh
```

### 2. CUDA calibration

This requires an operator-approved exclusive GPU window. Stop the model service
through the host's normal operator/arbiter procedure, retaining the same
`RUN_ID` and `RUN_STARTED_AT_UTC`, then run:

```bash
GPU_WINDOW=exclusive-vllm-stopped \
RUN_CPU=0 RUN_CUDA=1 RUN_SHARED_PROBE=0 RUN_TESTS=1 \
  ./experiments/dgx_spark/run_suite.sh
```

The suite deliberately does not control host services. Restore vLLM and the
arbiter even if the benchmark or tests fail. The exported provenance variables
above remain in the calling shell. After restoration, finalize with:

```bash
RESULTS=experiments/dgx_spark/results
OUTPUT="$RESULTS/environment.json" \
  python3 experiments/dgx_spark/environment_probe.py
python3 experiments/dgx_spark/verify_results.py \
  --results "$RESULTS" --cuda-policy required --shared-policy required \
  --output "$RESULTS/verification_report.json"
mapfile -t MANIFEST_PATHS < <(awk '{print $2}' "$RESULTS/SHA256SUMS")
sha256sum "${MANIFEST_PATHS[@]}" > "$RESULTS/SHA256SUMS.next"
mv "$RESULTS/SHA256SUMS.next" "$RESULTS/SHA256SUMS"
sha256sum -c "$RESULTS/SHA256SUMS"
```

This makes the canonical environment record capture the post-window service
state rather than the stopped state. Run these commands from the repository
root and do not edit producer sources between the first phase and finalization.

CPU work uses two workers/threads. Optional CUDA and shared-residency artifacts
are never silently mixed into a new run: `verify_results.py` requires one run ID,
one exact source commit, clean producer source, and a producer SHA-256 for every
artifact it accepts. `--cuda-policy` and `--shared-policy` support `required`,
`ignore`, and `auto`.

## Assurance boundary

The committed checkpoint has four executable layers:

1. producer enumeration with explicit failure lists;
2. complete-domain reconstruction through a separately implemented SymPy path;
3. artifact consistency, primality, witness, per-repeat CUDA, provenance, and
   policy checks that remain active under `python -O`;
4. SHA-256 over both result artifacts and the producer/checker sources.

This is stronger bounded computational evidence, not Lean certification. Any
promoted theorem still needs a symbolic Lean proof or a small theorem-backed
certificate checker.
