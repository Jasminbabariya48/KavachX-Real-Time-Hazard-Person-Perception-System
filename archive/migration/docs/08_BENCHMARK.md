# 08. Benchmark & Latency Profiling

---

## 1. Latency Breakdown

To isolate hardware compute from software overhead, latency is measured across 5 distinct stages:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Total End-to-End Latency                        │
├──────────────┬───────────────┬──────────────────┬──────────────┬───────┤
│ 1. Frame Read│ 2. Preprocess │ 3. NPU Inference │ 4. IPC Read  │ 5. NMS│
│ (DMA/Buffer) │ (Resize/Norm) │ (Hexagon v68)    │ (Socket/DMA) │ (CPU) │
└──────────────┴───────────────┴──────────────────┴──────────────┴───────┘
```

---

## 2. Statistical Profiling Standard

1. **Warm-Up Phase:** 10 unrecorded inferences to stabilize clock frequencies and warm CPU/DSP caches.
2. **Measurement Phase:** 100 iterations recorded using high-resolution monotonic timers (`std::chrono::steady_clock`).
3. **Reported Metrics:**
   * **Mean, Median ($P_{50}$)**
   * **$95^{\text{th}}$ Percentile ($P_{95}$)**
   * **$99^{\text{th}}$ Percentile ($P_{99}$)**
   * **Throughput (FPS):** $\text{FPS} = \frac{1000.0}{\text{Mean Latency (ms)}}$
   * **Speedup:** $\text{Speedup} = \frac{\text{CPU FP32 Latency (2185.58 ms)}}{\text{NPU INT8 Latency (ms)}}$

---

## 3. Anti-CPU-Fallback Telemetry Proof
To certify genuine Hexagon NPU offload:
* DSP FastRPC transport handles bound in `/dev/fastrpc-cdsp`.
* Non-zero HVX instruction cycles recorded via `qnn-profile-viewer`.
* Host CPU load remains flat ($< 5\%$).
