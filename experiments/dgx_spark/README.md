# DGX Spark computational experiments

Reproducible, bounded exact-arithmetic experiments supporting the Beal research
roadmap. They are **not** a proof of the unrestricted Beal conjecture.

## Experiments

- `finite_field_support.py`: exhaustive all-unit power-subgroup equations over
  finite prime fields. Empty unit branches imply only the support condition
  `q | A*B*C`; the permanent `A=0, B=C=1` residue branch is explicitly checked.
- `lte_assumption_miner.py`: bounded falsification of the odd-prime plus-sign LTE
  formula and minimal counterexamples when assumptions are removed.
- `cyclotomic_census.py`: factors odd plus-cyclotomic cofactors with PARI and
  checks the gcd, exact-order, congruence, and valuation patterns.
- `cuda_modexp_bench.cu`: CPU/GPU differential calibration for batched fixed-width
  modular exponentiation on the GB10. It is a performance probe, not a search
  certificate.
- `verify_results.py`: separate witness replay for support-forcing rows, LTE
  counterexamples, higher cyclotomic valuations, and CUDA differential metadata.

## DGX prerequisites

Ubuntu 24.04 ARM64 packages:

```bash
sudo apt-get install pari-gp python3-cypari2 python3-pytest
```

CUDA 13 is expected at `/usr/local/cuda`. The CUDA file is compiled specifically
for the Spark using `-arch=sm_121`.

## Run

CPU experiments, while the resident model service remains available. CPU-only
runs explicitly ignore pre-existing optional GPU JSON during verification and
omit it from the generated `SHA256SUMS`:

```bash
SOURCE_COMMIT=$(git rev-parse HEAD) \
SOURCE_BRANCH=$(git branch --show-current) \
./experiments/dgx_spark/run_suite.sh
```

CUDA calibration requires an operator-approved exclusive GPU window. On the
measured Spark, resident vLLM prevented even a small CUDA allocation. Stop the
model service through the host's normal operator/arbiter procedure, then run:

```bash
RUN_CPU=0 RUN_CUDA=1 GPU_WINDOW=exclusive-vllm-stopped-restored-healthy \
  ./experiments/dgx_spark/run_suite.sh
```

Restore the model service and verify its health immediately afterward. The suite
itself deliberately does not control host services. CPU work uses two workers or
threads and all modes write canonical JSON plus SHA-256 checksums under `results/`.
`verify_results.py` exposes `--cuda-policy` and `--shared-policy` with
`required`, `ignore`, and `auto` modes. The committed checkpoint uses `auto`;
`run_suite.sh` uses `required` only for a CUDA phase it actually executed.

## Assurance boundary

PARI, Python, CUDA, and the GPU are treated as untrusted producers. The scripts
emit exact parameters and explicit failure lists. Any promoted theorem still
needs either a symbolic Lean proof or a small theorem-backed certificate checker.
