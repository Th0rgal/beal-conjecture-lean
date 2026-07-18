#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(git -C "$ROOT" rev-parse --show-toplevel)
RESULTS="$ROOT/results"
LOGS="$ROOT/logs"
BUILD="$ROOT/build"
mkdir -p "$RESULTS" "$LOGS" "$BUILD"

# Source provenance is derived from the checkout, never accepted from a caller.
export SOURCE_COMMIT
SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD)
export SOURCE_BRANCH
SOURCE_BRANCH=$(git -C "$REPO_ROOT" branch --show-current)
if ! git -C "$REPO_ROOT" diff --quiet -- . \
    ':(exclude)experiments/dgx_spark/results/**' \
    ':(exclude)experiments/dgx_spark/logs/**' \
    ':(exclude)experiments/dgx_spark/build/**' \
    ':(exclude)experiments/dgx_spark/smoke/**'; then
  echo "producer source differs from committed HEAD" >&2
  exit 2
fi
if ! git -C "$REPO_ROOT" diff --cached --quiet; then
  echo "staged source differs from committed HEAD" >&2
  exit 2
fi
if [[ -n "$(git -C "$REPO_ROOT" ls-files --others --exclude-standard -- . \
    ':(exclude)experiments/dgx_spark/results/**' \
    ':(exclude)experiments/dgx_spark/logs/**' \
    ':(exclude)experiments/dgx_spark/build/**' \
    ':(exclude)experiments/dgx_spark/smoke/**')" ]]; then
  echo "untracked source exists; commit it before producing canonical results" >&2
  exit 2
fi
export SOURCE_TREE_CLEAN=true
export RUN_ID="${RUN_ID:-dgx-$(date -u +%Y%m%dT%H%M%SZ)-${SOURCE_COMMIT:0:12}}"
export RUN_STARTED_AT_UTC="${RUN_STARTED_AT_UTC:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
export PYTHONPATH="$ROOT"
export OMP_NUM_THREADS=2
RUN_CPU="${RUN_CPU:-1}"
RUN_CUDA="${RUN_CUDA:-0}"
RUN_SHARED_PROBE="${RUN_SHARED_PROBE:-0}"
RUN_TESTS="${RUN_TESTS:-1}"

if [[ "$RUN_CPU" == "1" ]]; then
  python3 "$ROOT/finite_field_support.py" \
    --kernels 3,4,5,7,11,13 --prime-bound 251 \
    --output "$RESULTS/finite_field_support.json" | tee "$LOGS/finite_field_support.log"
  python3 "$ROOT/lte_assumption_miner.py" \
    --a-bound 200 --prime-bound 97 --n-bound 31 \
    --output "$RESULTS/lte_assumption_miner.json" | tee "$LOGS/lte_assumption_miner.log"
  python3 "$ROOT/cyclotomic_census.py" \
    --ells 3,5,7,11 --bound 100 --workers 2 \
    --output "$RESULTS/cyclotomic_census.json" | tee "$LOGS/cyclotomic_census.log"
  python3 "$ROOT/independent_reproduce.py" --results "$RESULTS" \
    --output "$RESULTS/independent_reproduction.json" | tee "$LOGS/independent_reproduction.log"
fi

if [[ "$RUN_CUDA" == "1" || "$RUN_SHARED_PROBE" == "1" ]]; then
  /usr/local/cuda/bin/nvcc -O3 -arch=sm_121 -Xcompiler=-fopenmp \
    "$ROOT/cuda_modexp_bench.cu" -o "$BUILD/cuda_modexp_bench"
fi
CUDA_SOURCE_SHA=$(sha256sum "$ROOT/cuda_modexp_bench.cu" | cut -d' ' -f1)
if [[ "$RUN_SHARED_PROBE" == "1" ]]; then
  python3 "$ROOT/gpu_residency_probe.py" \
    --benchmark "$BUILD/cuda_modexp_bench" --count 100000 \
    --output "$RESULTS/gpu_shared_residency_probe.json" | tee "$LOGS/gpu_shared_residency_probe.log"
fi
if [[ "$RUN_CUDA" == "1" ]]; then
  "$BUILD/cuda_modexp_bench" --count 4000000 --repeats 5 \
    --run-id "$RUN_ID" --source-commit "$SOURCE_COMMIT" \
    --source-tree-clean "$SOURCE_TREE_CLEAN" --producer-sha256 "$CUDA_SOURCE_SHA" \
    > "$RESULTS/cuda_modexp_calibration.json"
  python3 -m json.tool "$RESULTS/cuda_modexp_calibration.json" >/dev/null
fi

OUTPUT="$RESULTS/environment.json" python3 "$ROOT/environment_probe.py"
if [[ "$RUN_CUDA" == "1" ]]; then CUDA_POLICY=required; else CUDA_POLICY=ignore; fi
if [[ "$RUN_SHARED_PROBE" == "1" ]]; then SHARED_POLICY=required; else SHARED_POLICY=auto; fi
python3 "$ROOT/verify_results.py" --results "$RESULTS" \
  --cuda-policy "$CUDA_POLICY" --shared-policy "$SHARED_POLICY" \
  --output "$RESULTS/verification_report.json" | tee "$LOGS/verification.log"

(
  cd "$REPO_ROOT"
  manifest=(
    experiments/dgx_spark/results/cyclotomic_census.json
    experiments/dgx_spark/results/environment.json
    experiments/dgx_spark/results/finite_field_support.json
    experiments/dgx_spark/results/independent_reproduction.json
    experiments/dgx_spark/results/lte_assumption_miner.json
    experiments/dgx_spark/results/verification_report.json
    experiments/dgx_spark/cuda_modexp_bench.cu
    experiments/dgx_spark/cyclotomic_census.py
    experiments/dgx_spark/environment_probe.py
    experiments/dgx_spark/finite_field_support.py
    experiments/dgx_spark/gpu_residency_probe.py
    experiments/dgx_spark/independent_reproduce.py
    experiments/dgx_spark/lte_assumption_miner.py
    experiments/dgx_spark/provenance.py
    experiments/dgx_spark/run_suite.sh
    experiments/dgx_spark/verify_results.py
  )
  if [[ "$CUDA_POLICY" == "required" ]]; then
    manifest+=(experiments/dgx_spark/results/cuda_modexp_calibration.json)
  fi
  if [[ "$SHARED_POLICY" != "ignore" && -f experiments/dgx_spark/results/gpu_shared_residency_probe.json ]]; then
    manifest+=(experiments/dgx_spark/results/gpu_shared_residency_probe.json)
  fi
  sha256sum "${manifest[@]}" > experiments/dgx_spark/results/SHA256SUMS
  sha256sum -c experiments/dgx_spark/results/SHA256SUMS
)

if [[ "$RUN_TESTS" == "1" ]]; then
  python3 -m pytest -q "$ROOT/tests" | tee "$LOGS/pytest.log"
fi

printf 'RUN_ID=%s\nSOURCE_COMMIT=%s\nRESULTS_DIR=%s\n' "$RUN_ID" "$SOURCE_COMMIT" "$RESULTS"
