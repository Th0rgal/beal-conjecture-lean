#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
RESULTS="$ROOT/results"
LOGS="$ROOT/logs"
BUILD="$ROOT/build"
mkdir -p "$RESULTS" "$LOGS" "$BUILD"

export PYTHONPATH="$ROOT"
export OMP_NUM_THREADS=2
export SOURCE_COMMIT="${SOURCE_COMMIT:-unknown}"
export SOURCE_BRANCH="${SOURCE_BRANCH:-research/dgx-computational-experiments-20260717}"
RUN_CPU="${RUN_CPU:-1}"
RUN_CUDA="${RUN_CUDA:-0}"

python3 -m pytest -q "$ROOT/tests" | tee "$LOGS/pytest.log"
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
fi

if [[ "$RUN_CUDA" == "1" ]]; then
  /usr/local/cuda/bin/nvcc -O3 -arch=sm_121 -Xcompiler=-fopenmp \
    "$ROOT/cuda_modexp_bench.cu" -o "$BUILD/cuda_modexp_bench"
  "$BUILD/cuda_modexp_bench" --count 4000000 --repeats 5 \
    > "$RESULTS/cuda_modexp_calibration.json"
  python3 -m json.tool "$RESULTS/cuda_modexp_calibration.json" >/dev/null
fi

OUTPUT="$RESULTS/environment.json" python3 "$ROOT/environment_probe.py"
if [[ "$RUN_CUDA" == "1" ]]; then
  CUDA_POLICY=required
else
  CUDA_POLICY=ignore
fi
python3 "$ROOT/verify_results.py" --results "$RESULTS" \
  --cuda-policy "$CUDA_POLICY" --shared-policy ignore \
  --output "$RESULTS/verification_report.json" | tee "$LOGS/verification.log"
(
  cd "$ROOT"
  manifest=(
    results/cyclotomic_census.json
    results/environment.json
    results/finite_field_support.json
    results/lte_assumption_miner.json
    results/verification_report.json
  )
  if [[ "$RUN_CUDA" == "1" ]]; then
    manifest+=(results/cuda_modexp_calibration.json)
  fi
  sha256sum "${manifest[@]}" > results/SHA256SUMS
  sha256sum -c results/SHA256SUMS
)
printf 'RESULTS_DIR=%s\n' "$RESULTS"
