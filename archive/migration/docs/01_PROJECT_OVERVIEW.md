# 01. Project Overview

**Project:** KawachX On-Device NPU Deployment  
**Target Hardware:** Qualcomm QCS6490 SoC (Hexagon v68 / V68 HTP)  
**Vision Task:** 3-Class Industrial Safety Object Detection (**Person**, **Fire**, **Smoke**)  
**Runtime Engine:** Qualcomm QNN Core C API (`libQnnHtp.so`) + `kawach_worker` C++ Daemon  

---

## 1. Executive Mission
The KawachX edge deployment framework deploys an optimized, real-time computer vision object detector directly on the Hexagon Tensor Processor (HTP) of the Qualcomm QCS6490 System-on-Chip. The system operates on-premise without cloud latency or continuous network dependencies, executing within a strict $< 5\text{W}$ edge thermal envelope.

---

## 2. Core Architecture Pipeline

```text
Host Development / Model Artifacts
  └── Source ONNX Model (new_3class_best_FP32.onnx)
        │
        ▼
  Calibration Data Generation (prepare_calibration_data.py -> .raw uint8/float32)
        │
        ▼
  QNN INT8 Quantization (qnn-onnx-converter -> 8-bit weight / 8-bit activation)
        │
        ▼
  Offline Context Compilation (qnn-context-binary-generator -> HTP v68 .bin)
        │
Target Edge Appliance (Qualcomm QCS6490 / Kavach-EdgeBox)
        ▼
  C++ Inference Daemon (kawach_worker via libQnnHtp.so / FastRPC)
        │
        ▼
  Hardware Acceleration (Hexagon v68 HTP Vector & Matrix Units)
        │
        ▼
  Output Streaming & Parity Validation (MaxAE / MAE / IoU Matching vs FP32 Reference)
```

---

## 3. High-Level Specification Summary

| Component | Specification |
| :--- | :--- |
| **SoC / NPU** | Qualcomm QCS6490 (8-Core Kryo: 4x Cortex-A78 @ 2.7 GHz, 4x Cortex-A55 @ 1.95 GHz, Hexagon v68 HTP) |
| **OS / Kernel** | KavachOS 1.0 (Linux 6.18.2-3-qcom aarch64, Ubuntu Noble base) |
| **SDK** | Qualcomm QAIRT 2.47.0.260601 (`/home/devuser/qairt/2.47.0.260601/`) |
| **Model** | Ultralytics YOLOv8 3-Class Detector (`images: [1, 3, 640, 640]` $\rightarrow$ `output0: [1, 7, 8400]`) |
| **Classes** | `0: person`, `1: fire`, `2: smoke` |
| **Runtime IPC** | Unix Domain Socket (`/tmp/kawach_worker.sock`) with binary frame streaming |
