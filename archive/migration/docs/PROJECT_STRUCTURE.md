# Project Structure & Repository Directory Map

```text
KavachX/
│
├── README.md                           # Main repository entrypoint
├── .gitignore                          # Git ignore rules
├── requirements.txt                    # Python runtime dependencies
│
├── docs/                               # Authoritative technical documentation
│   ├── 01_PROJECT_OVERVIEW.md          # Project goals, SoC architecture, vision task
│   ├── 02_SETUP_AND_ACCESS.md          # Cloudflare tunnel, SSH access, permissions
│   ├── 03_MODEL_AND_ONNX.md            # YOLOv8 ONNX metadata & FP32 baseline
│   ├── 04_CALIBRATION.md               # INT8 quantization & calibration strategy
│   ├── 05_QNN_CONVERSION.md            # QNN conversion & HTP compilation workflow
│   ├── 06_NPU_RUNTIME.md               # C++ daemon architecture & IPC protocol
│   ├── 07_VALIDATION_AND_PARITY.md     # Numerical & detection parity metrics
│   ├── 08_BENCHMARK.md                 # 5-stage latency profiling & anti-fallback
│   ├── 09_TROUBLESHOOTING.md           # FastRPC 14001, DFL Softmax, SiLU gotchas
│   ├── 10_FINAL_ASSESSMENT.md          # Senior engineering critique & roadmap
│   ├── PROJECT_STRUCTURE.md            # Complete repository layout map
│   └── archive/                        # Preserved historical audit files
│
├── scripts/                            # Operational & deployment tooling
│   ├── model/
│   │   ├── inspect_onnx.py             # ONNX model inspection & operator analyzer
│   │   ├── extract_onnx_meta.py        # ONNX metadata & class dictionary extractor
│   │   └── run_fp32_baseline.py        # Target FP32 reference execution
│   ├── calibration/
│   │   └── prepare_calibration_data.py # Calibration dataset & input_list.txt generator
│   ├── qnn/
│   │   ├── inspect_qnn_binary.py       # Multi-tier context binary inspector
│   │   └── run_qnn_pipeline.py         # QNN converter & context compiler orchestrator
│   ├── validation/
│   │   └── compare_fp32_int8.py        # Dual-path tensor & detection parity engine
│   ├── benchmark/                      # Latency & throughput benchmarking tools
│   └── tools/
│       ├── check_deployment_readiness.py # Automated prerequisite checker
│       ├── run_remote.py               # Clean SSH command runner
│       └── run_full_assignment.py      # Master pipeline orchestrator
│
├── src/
│   └── npu_worker/                     # Production C++ QNN C API inference daemon
│       ├── main.cpp                    # Daemon entrypoint, signal handling, loop
│       ├── qnn_inference.cpp           # QNN C API wrapper, context & graph lifecycle
│       ├── qnn_inference.hpp           # QNN inference header & tensor dimensions
│       ├── ipc_handler.cpp             # Unix domain socket server implementation
│       ├── ipc_handler.hpp             # IPC handler interface
│       └── Makefile                    # aarch64 build configuration
│
├── config/
│   └── qnn/
│       └── htp_config.json             # Hexagon v68 HTP performance configuration
│
├── models/                             # Model assets
│   ├── source/                         # Original FP32 ONNX models
│   └── qnn/                            # Compiled QNN context binaries (.bin)
│
├── data/                               # Input datasets
│   ├── test_images/                    # Real test images (fire.jpg, person.jpg, etc.)
│   └── calibration/                    # Calibration imagery & raw files
│
└── results/                            # Output evaluation artifacts
    ├── fp32_baseline/                  # FP32 ONNX Runtime ground truth outputs
    │   ├── fp32_baseline_report.json   # Latency & detection metrics report
    │   ├── raw_outputs/                # Ground truth numpy tensors (.npy)
    │   └── visualizations/             # Bounding box visual overlays
    ├── benchmark_schema.json           # Unified latency reporting schema
    └── FINAL_STATUS.md                 # Visual status dashboard
```
