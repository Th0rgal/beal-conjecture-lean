#include <cuda_runtime.h>
#include <omp.h>

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#define CUDA_CHECK(call) do { \
  cudaError_t err = (call); \
  if (err != cudaSuccess) { \
    std::cerr << "CUDA error: " << cudaGetErrorString(err) << " at line " << __LINE__ << "\n"; \
    std::exit(2); \
  } \
} while (0)

__host__ __device__ static inline uint32_t mul_mod31(uint32_t a, uint32_t b, uint32_t mod) {
  return static_cast<uint32_t>((static_cast<uint64_t>(a) * b) % mod);
}

__host__ __device__ static inline uint32_t pow_mod31(uint32_t base, uint32_t exponent, uint32_t mod) {
  uint32_t result = 1;
  while (exponent) {
    if (exponent & 1U) result = mul_mod31(result, base, mod);
    base = mul_mod31(base, base, mod);
    exponent >>= 1U;
  }
  return result;
}

__global__ void pow_kernel(const uint32_t* input, uint32_t* output, size_t count,
                           uint32_t exponent, uint32_t modulus) {
  size_t index = static_cast<size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
  size_t stride = static_cast<size_t>(blockDim.x) * gridDim.x;
  for (size_t i = index; i < count; i += stride) {
    output[i] = pow_mod31(input[i], exponent, modulus);
  }
}

int main(int argc, char** argv) {
  size_t count = 4'000'000;
  int repeats = 5;
  uint32_t exponent = 65537;
  uint32_t modulus = 2'147'483'647U;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--count" && i + 1 < argc) count = std::stoull(argv[++i]);
    else if (arg == "--repeats" && i + 1 < argc) repeats = std::stoi(argv[++i]);
    else if (arg == "--exponent" && i + 1 < argc) exponent = std::stoul(argv[++i]);
    else if (arg == "--modulus" && i + 1 < argc) modulus = std::stoul(argv[++i]);
    else {
      std::cerr << "unknown/incomplete argument: " << arg << "\n";
      return 2;
    }
  }

  int device = 0;
  cudaDeviceProp prop{};
  CUDA_CHECK(cudaGetDeviceProperties(&prop, device));

  std::vector<uint32_t> input(count), cpu_output(count), gpu_output(count);
  for (size_t i = 0; i < count; ++i) input[i] = static_cast<uint32_t>((i + 1) % modulus);

  auto cpu_started = std::chrono::steady_clock::now();
#pragma omp parallel for schedule(static)
  for (size_t i = 0; i < count; ++i) cpu_output[i] = pow_mod31(input[i], exponent, modulus);
  auto cpu_finished = std::chrono::steady_clock::now();
  double cpu_seconds = std::chrono::duration<double>(cpu_finished - cpu_started).count();

  uint32_t *d_input = nullptr, *d_output = nullptr;
  CUDA_CHECK(cudaMalloc(&d_input, count * sizeof(uint32_t)));
  CUDA_CHECK(cudaMalloc(&d_output, count * sizeof(uint32_t)));

  int threads = 256;
  int blocks = static_cast<int>((count + threads - 1) / threads);
  if (blocks > prop.multiProcessorCount * 32) blocks = prop.multiProcessorCount * 32;

  cudaEvent_t start_event, stop_event;
  CUDA_CHECK(cudaEventCreate(&start_event));
  CUDA_CHECK(cudaEventCreate(&stop_event));

  auto total_started = std::chrono::steady_clock::now();
  CUDA_CHECK(cudaMemcpy(d_input, input.data(), count * sizeof(uint32_t), cudaMemcpyHostToDevice));
  CUDA_CHECK(cudaEventRecord(start_event));
  for (int r = 0; r < repeats; ++r) {
    pow_kernel<<<blocks, threads>>>(d_input, d_output, count, exponent, modulus);
  }
  CUDA_CHECK(cudaGetLastError());
  CUDA_CHECK(cudaEventRecord(stop_event));
  CUDA_CHECK(cudaEventSynchronize(stop_event));
  float kernel_ms = 0.0F;
  CUDA_CHECK(cudaEventElapsedTime(&kernel_ms, start_event, stop_event));
  CUDA_CHECK(cudaMemcpy(gpu_output.data(), d_output, count * sizeof(uint32_t), cudaMemcpyDeviceToHost));
  auto total_finished = std::chrono::steady_clock::now();
  double total_seconds = std::chrono::duration<double>(total_finished - total_started).count();

  size_t mismatches = 0;
  for (size_t i = 0; i < count; ++i) {
    if (cpu_output[i] != gpu_output[i]) ++mismatches;
  }

  double kernel_seconds_per_repeat = (kernel_ms / 1000.0) / repeats;
  double gpu_kernel_throughput = count / kernel_seconds_per_repeat;
  double cpu_throughput = count / cpu_seconds;
  double end_to_end_per_repeat = total_seconds / repeats;

  int runtime_version = 0;
  CUDA_CHECK(cudaRuntimeGetVersion(&runtime_version));
  std::cout << std::fixed << std::setprecision(6)
            << "{\n"
            << "  \"schema_version\": 1,\n"
            << "  \"experiment\": \"cuda_modexp_calibration\",\n"
            << "  \"gpu_name\": \"" << prop.name << "\",\n"
            << "  \"compute_capability\": \"" << prop.major << "." << prop.minor << "\",\n"
            << "  \"cuda_runtime_version\": " << runtime_version << ",\n"
            << "  \"count\": " << count << ",\n"
            << "  \"repeats\": " << repeats << ",\n"
            << "  \"exponent\": " << exponent << ",\n"
            << "  \"modulus\": " << modulus << ",\n"
            << "  \"cpu_openmp_threads\": " << omp_get_max_threads() << ",\n"
            << "  \"cpu_seconds\": " << cpu_seconds << ",\n"
            << "  \"cpu_candidates_per_second\": " << cpu_throughput << ",\n"
            << "  \"gpu_kernel_seconds_per_repeat\": " << kernel_seconds_per_repeat << ",\n"
            << "  \"gpu_kernel_candidates_per_second\": " << gpu_kernel_throughput << ",\n"
            << "  \"gpu_total_seconds_all_repeats_including_transfers\": " << total_seconds << ",\n"
            << "  \"gpu_end_to_end_seconds_per_repeat_amortized\": " << end_to_end_per_repeat << ",\n"
            << "  \"mismatches\": " << mismatches << ",\n"
            << "  \"interpretation\": \"Calibration only; shared vLLM was left running, and this is not an exhaustiveness certificate.\"\n"
            << "}\n";

  CUDA_CHECK(cudaEventDestroy(start_event));
  CUDA_CHECK(cudaEventDestroy(stop_event));
  CUDA_CHECK(cudaFree(d_input));
  CUDA_CHECK(cudaFree(d_output));
  return mismatches == 0 ? 0 : 1;
}
