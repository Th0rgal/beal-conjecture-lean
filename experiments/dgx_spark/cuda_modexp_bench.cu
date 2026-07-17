#include <cuda_runtime.h>
#include <omp.h>

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#define CUDA_CHECK(call) do { \
  cudaError_t err = (call); \
  if (err != cudaSuccess) { \
    std::cerr << "CUDA error: " << cudaGetErrorString(err) << " at line " << __LINE__ << "\n"; \
    std::exit(2); \
  } \
} while (0)

__device__ static inline uint32_t device_mul_mod31(uint32_t a, uint32_t b, uint32_t mod) {
  return static_cast<uint32_t>((static_cast<uint64_t>(a) * b) % mod);
}

__device__ static inline uint32_t device_pow_mod31(uint32_t base, uint32_t exponent,
                                                   uint32_t mod) {
  uint32_t result = 1U % mod;
  while (exponent) {
    if (exponent & 1U) result = device_mul_mod31(result, base, mod);
    base = device_mul_mod31(base, base, mod);
    exponent >>= 1U;
  }
  return result;
}

static uint32_t cpu_pow_reference(uint32_t base, uint32_t exponent, uint32_t mod) {
  uint64_t result = 1U % mod;
  uint64_t value = base % mod;
  while (exponent) {
    if (exponent & 1U) {
      result = static_cast<uint64_t>((static_cast<unsigned __int128>(result) * value) % mod);
    }
    value = static_cast<uint64_t>((static_cast<unsigned __int128>(value) * value) % mod);
    exponent >>= 1U;
  }
  return static_cast<uint32_t>(result);
}

static std::string digest_output(const std::vector<uint32_t>& values) {
  uint64_t hash = 1469598103934665603ULL;
  for (uint32_t value : values) {
    for (int shift = 0; shift < 32; shift += 8) {
      hash ^= static_cast<uint8_t>((value >> shift) & 0xffU);
      hash *= 1099511628211ULL;
    }
  }
  std::ostringstream stream;
  stream << std::hex << std::setfill('0') << std::setw(16) << hash;
  return stream.str();
}

__global__ void pow_kernel(const uint32_t* input, uint32_t* output, size_t count,
                           uint32_t exponent, uint32_t modulus) {
  size_t index = static_cast<size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
  size_t stride = static_cast<size_t>(blockDim.x) * gridDim.x;
  for (size_t i = index; i < count; i += stride) {
    output[i] = device_pow_mod31(input[i], exponent, modulus);
  }
}

int main(int argc, char** argv) {
  size_t count = 4'000'000;
  int repeats = 5;
  uint32_t exponent = 65537;
  uint32_t modulus = 2'147'483'647U;
  std::string run_id, source_commit, producer_sha256;
  bool source_tree_clean = false;
  bool source_tree_clean_set = false;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--count" && i + 1 < argc) count = std::stoull(argv[++i]);
    else if (arg == "--repeats" && i + 1 < argc) repeats = std::stoi(argv[++i]);
    else if (arg == "--exponent" && i + 1 < argc) exponent = std::stoul(argv[++i]);
    else if (arg == "--modulus" && i + 1 < argc) modulus = std::stoul(argv[++i]);
    else if (arg == "--run-id" && i + 1 < argc) run_id = argv[++i];
    else if (arg == "--source-commit" && i + 1 < argc) source_commit = argv[++i];
    else if (arg == "--producer-sha256" && i + 1 < argc) producer_sha256 = argv[++i];
    else if (arg == "--source-tree-clean" && i + 1 < argc) {
      std::string value = argv[++i];
      if (value != "true" && value != "false") {
        std::cerr << "--source-tree-clean must be true or false\n";
        return 2;
      }
      source_tree_clean = value == "true";
      source_tree_clean_set = true;
    } else {
      std::cerr << "unknown/incomplete argument: " << arg << "\n";
      return 2;
    }
  }
  if (count == 0 || repeats <= 0 || modulus < 2 || run_id.empty() ||
      source_commit.size() != 40 || producer_sha256.size() != 64 || !source_tree_clean_set) {
    std::cerr << "invalid benchmark parameters or missing provenance\n";
    return 2;
  }

  int device = 0;
  cudaDeviceProp prop{};
  CUDA_CHECK(cudaGetDeviceProperties(&prop, device));

  std::vector<uint32_t> input(count), cpu_output(count), gpu_output(count);
  for (size_t i = 0; i < count; ++i) input[i] = static_cast<uint32_t>((i + 1) % modulus);

  auto cpu_started = std::chrono::steady_clock::now();
#pragma omp parallel for schedule(static)
  for (size_t i = 0; i < count; ++i) cpu_output[i] = cpu_pow_reference(input[i], exponent, modulus);
  auto cpu_finished = std::chrono::steady_clock::now();
  double cpu_seconds = std::chrono::duration<double>(cpu_finished - cpu_started).count();
  std::string cpu_digest = digest_output(cpu_output);

  uint32_t *d_input = nullptr, *d_output = nullptr;
  CUDA_CHECK(cudaMalloc(&d_input, count * sizeof(uint32_t)));
  CUDA_CHECK(cudaMalloc(&d_output, count * sizeof(uint32_t)));

  int threads = 256;
  int blocks = static_cast<int>((count + threads - 1) / threads);
  if (blocks > prop.multiProcessorCount * 32) blocks = prop.multiProcessorCount * 32;

  cudaEvent_t start_event, stop_event;
  CUDA_CHECK(cudaEventCreate(&start_event));
  CUDA_CHECK(cudaEventCreate(&stop_event));

  std::vector<double> kernel_seconds;
  std::vector<size_t> mismatch_counts;
  std::vector<std::string> output_digests;
  kernel_seconds.reserve(repeats);
  mismatch_counts.reserve(repeats);
  output_digests.reserve(repeats);

  auto total_started = std::chrono::steady_clock::now();
  CUDA_CHECK(cudaMemcpy(d_input, input.data(), count * sizeof(uint32_t), cudaMemcpyHostToDevice));
  for (int repeat = 0; repeat < repeats; ++repeat) {
    CUDA_CHECK(cudaEventRecord(start_event));
    pow_kernel<<<blocks, threads>>>(d_input, d_output, count, exponent, modulus);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaEventRecord(stop_event));
    CUDA_CHECK(cudaEventSynchronize(stop_event));
    float elapsed_ms = 0.0F;
    CUDA_CHECK(cudaEventElapsedTime(&elapsed_ms, start_event, stop_event));
    kernel_seconds.push_back(elapsed_ms / 1000.0);
    CUDA_CHECK(cudaMemcpy(gpu_output.data(), d_output, count * sizeof(uint32_t),
                          cudaMemcpyDeviceToHost));
    size_t mismatches = 0;
    for (size_t i = 0; i < count; ++i) {
      if (cpu_output[i] != gpu_output[i]) ++mismatches;
    }
    mismatch_counts.push_back(mismatches);
    output_digests.push_back(digest_output(gpu_output));
  }
  auto total_finished = std::chrono::steady_clock::now();
  double total_seconds = std::chrono::duration<double>(total_finished - total_started).count();

  size_t mismatch_total = 0;
  double kernel_total = 0.0;
  for (size_t value : mismatch_counts) mismatch_total += value;
  for (double value : kernel_seconds) kernel_total += value;
  double kernel_seconds_per_repeat = kernel_total / repeats;
  double gpu_kernel_throughput = count / kernel_seconds_per_repeat;
  double cpu_throughput = count / cpu_seconds;
  double end_to_end_per_repeat = total_seconds / repeats;

  int runtime_version = 0;
  CUDA_CHECK(cudaRuntimeGetVersion(&runtime_version));
  std::cout << std::fixed << std::setprecision(6)
            << "{\n"
            << "  \"schema_version\": 2,\n"
            << "  \"experiment\": \"cuda_modexp_calibration\",\n"
            << "  \"gpu_name\": \"" << prop.name << "\",\n"
            << "  \"compute_capability\": \"" << prop.major << "." << prop.minor << "\",\n"
            << "  \"cuda_runtime_version\": " << runtime_version << ",\n"
            << "  \"count\": " << count << ",\n"
            << "  \"repeats\": " << repeats << ",\n"
            << "  \"exponent\": " << exponent << ",\n"
            << "  \"modulus\": " << modulus << ",\n"
            << "  \"cpu_reference\": \"independent unsigned-__int128 implementation\",\n"
            << "  \"cpu_openmp_threads\": " << omp_get_max_threads() << ",\n"
            << "  \"cpu_seconds\": " << cpu_seconds << ",\n"
            << "  \"cpu_candidates_per_second\": " << cpu_throughput << ",\n"
            << "  \"cpu_output_digest\": \"" << cpu_digest << "\",\n"
            << "  \"gpu_kernel_seconds_per_repeat\": " << kernel_seconds_per_repeat << ",\n"
            << "  \"gpu_kernel_candidates_per_second\": " << gpu_kernel_throughput << ",\n"
            << "  \"gpu_total_seconds_all_repeats_including_each_verification_transfer\": "
            << total_seconds << ",\n"
            << "  \"gpu_end_to_end_seconds_per_repeat\": " << end_to_end_per_repeat << ",\n"
            << "  \"mismatches_per_repeat\": [";
  for (int i = 0; i < repeats; ++i) {
    if (i) std::cout << ", ";
    std::cout << mismatch_counts[i];
  }
  std::cout << "],\n  \"mismatches_total\": " << mismatch_total
            << ",\n  \"output_digest_per_repeat\": [";
  for (int i = 0; i < repeats; ++i) {
    if (i) std::cout << ", ";
    std::cout << "\"" << output_digests[i] << "\"";
  }
  std::cout << "],\n"
            << "  \"provenance\": {\n"
            << "    \"run_id\": \"" << run_id << "\",\n"
            << "    \"source_commit\": \"" << source_commit << "\",\n"
            << "    \"source_tree_clean\": " << (source_tree_clean ? "true" : "false") << ",\n"
            << "    \"producer\": \"cuda_modexp_bench.cu\",\n"
            << "    \"producer_sha256\": \"" << producer_sha256 << "\"\n"
            << "  },\n"
            << "  \"interpretation\": \"Calibration only; every timed repeat was copied back, digested, and compared with an independent CPU reference.\"\n"
            << "}\n";

  CUDA_CHECK(cudaEventDestroy(start_event));
  CUDA_CHECK(cudaEventDestroy(stop_event));
  CUDA_CHECK(cudaFree(d_input));
  CUDA_CHECK(cudaFree(d_output));
  return mismatch_total == 0 ? 0 : 1;
}
