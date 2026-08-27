# KavachX — Real-Time Hazard & Person Perception System

KavachX is an industrial edge-perception system for real-time detection of **Fire, Smoke, and Persons**, hardware-accelerated on the **Qualcomm Hexagon v68 HTP DSP** on the Qualcomm QCS6490 SoC (Radxa Dragon Q6490 / Kavach-EdgeBox).

---

## 1. Executive Summary & Verified Hardware Baseline

- **Hardware Platform:** Qualcomm QCS6490 SoC (Qualcomm Hexagon v68 HTP DSP).
- **Quantization:** Calibrated INT8 compiled QNN context binary.
- **Model Signature:** [`models/production/3class_calibrated_final.bin`](models/production/3class_calibrated_final.bin) (26.8 MB, SHA256: `b7868a8c436fcf723fea7f95b3dcfd6f131fbe8ddb02ddf103addbe351dafabc`).
- **Hardware Acceleration:** **100% Neural Network on Hexagon DSP** via FastRPC (`/dev/fastrpc-cdsp`) with **0 CPU/GPU fallback**.
- **Performance:**
  - **Raw NPU Inference Latency:** $\sim 30\text{ ms}$ ($\sim 33.2\text{ FPS}$).
  - **End-to-End Live Stream Latency:** $\sim 45\text{--}70\text{ ms}$ ($\sim 13.5\text{--}15\text{ FPS}$) including capture, letterboxing, NPU execution, DFL decoding, NMS, and debounced alert dispatching.
- **Target Classes:** `fire` (CRITICAL), `smoke` (WARNING), `person` (WARNING).

---

## 2. End-to-End Pipeline Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│  Camera Ingestion Layer (src/kavachx/capture/)                         │
│  - V4L2 Physical USB/CSI Camera (/dev/video0)                          │
│  - Network RTSP IP Camera (rtsp://...)                                 │
│  - Continuous Video Stream (test_images/live_test_stream.mp4)          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Bounded Frame Queue (src/kavachx/pipeline/frame_queue.py)             │
│  - Latest-Frame-Wins drop policy (maxsize=2, prevents latency buildup) │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Preprocessing & IPC Client (src/kavachx/inference/)                   │
│  - Letterbox to [1, 3, 640, 640] uint8 NCHW                            │
│  - UNIX domain socket transfer to daemon (/tmp/kawach_worker.sock)     │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼ (FastRPC /dev/fastrpc-cdsp)
┌────────────────────────────────────────────────────────────────────────┐
│  Native C++ Worker on Qualcomm Hexagon v68 HTP DSP (native/worker/)    │
│  - QNN HTP Backend (libQnnHtp.so)                                      │
│  - 100% DSP Execution (Backbone, FPN Neck, Output Convolution Heads)   │
│  - Zero CPU Fallback for neural network layers                         │
│  - Returns INT8 outputs: [1, 64, 8400] & [1, 3, 8400] uint8            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  DFL Box Decoding & NMS (src/kavachx/inference/decoder.py)             │
│  - Unletterboxes coordinates to original camera resolution             │
│  - Extracts bounding boxes [x1, y1, x2, y2] + confidence scores        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Alert & Event Manager (src/kavachx/pipeline/events.py)                │
│  - Debounced event dispatching (prevents alert storms)                 │
│  - HAZARD_DETECTED (Fire: CRITICAL, Smoke: WARNING)                    │
│  - PERSON_DETECTED (Person: WARNING)                                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. How to Run the Application

The system can be controlled directly from your **Windows PowerShell terminal** or natively on the **Linux EdgeBox**.

### Option A: From Windows Desktop (VS Code / PowerShell)

Run commands using the target execution runner:

```powershell
# 1. Run Live Interactive Demo (Worker Health + 50 Live Stream Frames)
python tools/target_runner.py "cd /home/work_user2/kawachx_task && make demo"

# 2. Watch Real-Time Detections & Bounding Boxes Frame-by-Frame
python tools/target_runner.py "cd /home/work_user2/kawachx_task && python3 tools/live_camera_viewer.py 20"

# 3. Run Automated Regression Test Suite
python tools/target_runner.py "cd /home/work_user2/kawachx_task && make test"

# 4. Check Production Daemon Health
python tools/target_runner.py "cat /tmp/kawach_health.json"
```

---

### Option B: Directly on the Qualcomm EdgeBox (SSH)

Log into the EdgeBox:
```bash
ssh work_user2@ssh.kavachx.io
cd /home/work_user2/kawachx_task
```

Execute production commands:
```bash
# Build native C++ worker
make build

# Start the background daemon
python3 tools/service_manager.py start

# Check service health
cat /tmp/kawach_health.json

# Run live stream viewer
python3 tools/live_camera_viewer.py 20

# Run full test suite
make test
```

---

## 4. Camera Ingestion Configuration

Edit [`config/production.json`](config/production.json) to switch between physical cameras, RTSP streams, or test feeds:

### 1. Physical USB or CSI Camera (`/dev/video0`)
```json
{
  "stream": {
    "source_type": "camera",
    "source": "/dev/video0",
    "width": 1280,
    "height": 720,
    "target_fps": 30.0,
    "queue_maxsize": 2
  }
}
```

### 2. Network RTSP Security IP Camera
```json
{
  "stream": {
    "source_type": "rtsp",
    "source": "rtsp://admin:password@192.168.1.100:554/live",
    "reconnect_backoff_sec": 1.0,
    "max_reconnect_attempts": 5,
    "target_fps": 30.0,
    "queue_maxsize": 2
  }
}
```

### 3. Continuous Video Stream Feed
```json
{
  "stream": {
    "source_type": "video",
    "source": "test_data/videos/live_test_stream.mp4",
    "capture_fps": 30.0,
    "loop": true,
    "queue_maxsize": 2
  }
}
```

---

## 5. Repository Structure

```text
KavachX/
├── README.md                          # Production product overview & run guide
├── LICENSE                            # Apache 2.0 License
├── Makefile                           # Target build, test, clean, demo, and health targets
├── pyproject.toml                     # Python packaging configuration
├── requirements.txt                   # Production Python dependencies
├── .gitignore                         # Build and runtime artifact filter
│
├── src/                               # Authoritative Python Production Package
│   └── kavachx/
│       ├── inference/                 # Inference engine, DFL decoder, letterbox postprocessing
│       ├── pipeline/                  # Live stream pipeline, bounded drop queue, alert events
│       ├── capture/                   # Unified camera sources (V4L2, RTSP, Video file)
│       ├── ipc/                       # Framed binary socket protocol & client
│       ├── service/                   # Health inspection & daemon state
│       ├── config/                    # Production configuration loader
│       └── common/                    # Logging and process utilities
│
├── native/                            # Production Native C++ Worker
│   └── worker/                        # Qualcomm Hexagon HTP FastRPC Zero-Copy Daemon
│       ├── main.cpp
│       ├── qnn_inference.cpp
│       ├── qnn_inference.hpp
│       ├── ipc_handler.cpp
│       ├── ipc_handler.hpp
│       └── Makefile
│
├── models/
│   ├── production/
│   │   └── 3class_calibrated_final.bin # Frozen Quantized HTP Context Binary (26.8MB)
│   └── reference/
│       └── new_3class_best_FP32_htp_split.onnx
│
├── config/
│   ├── production.json                # Authoritative production configuration
│   └── kawach_worker.service          # Systemd daemon service descriptor
│
├── deployment/                        # Turnkey Deployment Scripts
│   ├── install.sh
│   ├── uninstall.sh
│   ├── run_demo.sh
│   └── README.md
│
├── tests/                             # Automated Test Suites
│   ├── hardware/                      # test_htp_inference.py (Qualcomm DSP verification)
│   ├── integration/                   # test_pipeline_integration.py
│   ├── streaming/                     # test_live_stream.py
│   ├── unit/                          # Unit tests
│   └── fixtures/                      # Mock feeds & test inputs
│
├── tools/                             # Developer & Diagnostic Utilities
│   ├── benchmark.py                   # Hardware latency & throughput benchmark
│   ├── diagnostics.py                 # FastRPC & runtime environment health checker
│   ├── live_camera_viewer.py          # Real-time frame-by-frame detection stream viewer
│   ├── model_inspect.py               # Inspects model binary parameters & checksum
│   ├── service_manager.py             # Service supervisor (start, stop, restart, status)
│   └── target_runner.py               # Remote execution & validation driver
│
├── docs/                              # Product Technical Documentation
│   ├── README.md                      # Documentation index
│   ├── architecture/                  # SYSTEM_ARCHITECTURE.md
│   ├── deployment/                    # DEPLOYMENT_GUIDE.md, CAMERA_SETUP.md, GO_LIVE_GUIDE.md
│   ├── operations/                    # OPERATIONS_RUNBOOK.md, HEALTH_AND_MONITORING.md, TROUBLESHOOTING.md
│   ├── testing/                       # TEST_STRATEGY.md, ACCEPTANCE_TESTS.md, PERFORMANCE_TESTING.md
│   ├── development/                   # DEVELOPMENT_GUIDE.md, REPOSITORY_ARCHITECTURE.md, CONTRIBUTING.md
│   └── handover/                      # PRODUCTION_HANDOVER.md, PROJECT_STATUS.md, REPOSITORY_CLEANUP_REPORT.md
│
├── reports/                           # Archived Verification Reports
│   ├── acceptance/
│   ├── performance/
│   ├── reliability/
│   └── audit/
│
├── test_data/                         # Verification Media (images/ & videos/)
│
└── archive/                           # Preserved Historical Development Milestones
    ├── experiments/
    ├── migration/
    └── legacy/
```

---

## 6. Real Live Stream Verification Output

```text
==================================================================
  KAVACHX REAL-TIME CAMERA INFERENCE (Qualcomm Hexagon v68 HTP DSP)
==================================================================
Frame #01 | DSP Latency: 48.89 ms | Detections: SMOKE (39.1%) [544,413,616,456], PERSON (60.9%) [660,20,986,412] 🚨 [WARNING: HAZARD_DETECTED - SMOKE]
Frame #02 | DSP Latency: 39.56 ms | Detections: SMOKE (39.1%) [543,412,616,455], PERSON (60.9%) [412,129,689,429]
Frame #03 | DSP Latency: 69.14 ms | Detections: SMOKE (39.1%) [543,412,616,454], PERSON (60.9%) [411,131,689,437]
Frame #04 | DSP Latency: 44.84 ms | Detections: SMOKE (39.1%) [543,412,616,454], PERSON (60.9%) [411,133,687,435]
Frame #05 | DSP Latency: 71.38 ms | Detections: SMOKE (39.1%) [543,412,616,454], PERSON (60.9%) [413,135,685,430]
==================================================================
  Live camera stream finished successfully.
==================================================================
```

---

## 7. License
Apache License 2.0. Copyright (c) 2026 KavachX Team.
