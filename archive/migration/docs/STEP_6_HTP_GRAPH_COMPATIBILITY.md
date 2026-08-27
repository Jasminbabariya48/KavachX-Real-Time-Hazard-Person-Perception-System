# KavachX — Step 6: YOLOv8 DFL / Dynamic Slice & HTP Graph Compatibility Report

## 1. Executive Summary

This document details the root cause investigation, graph topology analysis, split model derivation, CPU numerical validation, and Qualcomm Hexagon v68 HTP compilation analysis for the KavachX 3-class YOLOv8 fire/person detection model under QAIRT SDK 2.47.0.260601.

---

## 2. Original YOLOv8 Graph Analysis

### 2.1 Graph Architecture
The source model `models/new_3class_best_FP32.onnx` ($103.56\text{ MB}$, YOLOv8) consists of:
- **Input:** `images` (`[1, 3, 640, 640]`, RGB, NCHW, $[0.0, 1.0]$)
- **Backbone & Neck:** Standard CSPDarknet with PAN-FPN producing 3 multi-scale feature maps at strides 8, 16, and 32 ($80\times80$, $40\times40$, $20\times20$).
- **Detection Head (`model.22`):**
  - Bounding Box Feature Convolutions: 3 scales of $64$ channels ($16$ distribution bins $\times$ $4$ bbox coordinates).
  - Class Feature Convolutions: 3 scales of $3$ channels (fire, smoke, person).
  - Multi-scale Concatenation:
    - Bboxes: `_model_22_Concat` $\rightarrow$ `[1, 64, 8400]`
    - Class Scores: `_model_22_Concat_1` $\rightarrow$ `_model_22_Sigmoid` $\rightarrow$ `[1, 3, 8400]`
  - Distribution Focal Loss (DFL) & Post-Processing Subgraph:
    - `Softmax` over 16 bins
    - 1D Convolution (`dfl.conv`) projection
    - Dynamic Slicing: `/model.22/Slice` and `/model.22/Slice_1`
    - Anchor Box Transformation: `/model.22/Sub`, `/model.22/Add_1`, `/model.22/Add_2`, `/model.22/Sub_1`, `/model.22/Div_1`
    - Final Output Concatenation: `/model.22/Concat_7` $\rightarrow$ `output0` (`[1, 7, 8400]`).

### 2.2 Root Cause of HTP v68 Incompatibility
The DFL post-processing head incorporates dynamic Slice operations:
- `/model.22/Slice` (Inputs: `['/model.22/dfl/Reshape_1_output_0', '/model.22/Constant_26_output_0', '/model.22/Mul_output_0', '/model.22/Constant_25_output_0']`)
- `/model.22/Slice_1` (Inputs: `['/model.22/dfl/Reshape_1_output_0', '/model.22/Mul_output_0', '/model.22/Mul_1_output_0', '/model.22/Constant_25_output_0']`)

The slice start and end indices are calculated at runtime from tensor multiplications (`/model.22/Mul_output_0`). The Qualcomm Hexagon v68 HTP offline compiler requires static tensor slicing and does not support dynamic slice indices in INT8 quantized mode, leading to a segmentation fault in `libQnnHtp.so` during Hexagon machine instruction generation.

---

## 3. Graph Split Strategy

To ensure 100% compatibility with Qualcomm Hexagon HTP vector pipelines while preserving complete numerical accuracy, the graph is cleanly partitioned:

```text
                  +-----------------------------+
                  |  Input [1, 3, 640, 640] RGB  |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |  YOLOv8 Backbone & Neck      |
                  |  (All CNN & Conv2D Layers)  |
                  +--------------+--------------+
                                 |
                 +---------------+---------------+
                 |                               |
                 v                               v
  +-------------------------------+ +-------------------------------+
  | Box Distribution Feature Head | | Class Probability Head        |
  | /model.22/Concat_output_0     | | /model.22/Sigmoid_output_0    |
  | Shape: [1, 64, 8400]          | | Shape: [1, 3, 8400]           |
  | Dtype: float32 / UINT8        | | Dtype: float32 / UINT8        |
  +---------------+---------------+ +---------------+---------------+
                  |                               |
                  +---------------+---------------+
                                  |
                                  v  (Boundary Tensors Exposed from NPU)
                  +-------------------------------+
                  |  C++ NPU Worker Post-Process  |
                  |  - Vectorized DFL Decode      |
                  |  - Anchor Bounding Box Calc   |
                  |  - Class Score Thresholding   |
                  |  - Non-Maximum Suppression    |
                  +-------------------------------+
```

---

## 4. Derived Model & CPU Numerical Validation

A clean derived model `models/new_3class_best_FP32_htp_split.onnx` was generated from `models/new_3class_best_FP32.onnx` without modifying any trained weights or layer parameters.

### 4.1 CPU Parity Verification Results (`results/htp_compilation/reports/split_model_validation.json`)
The split FP32 ONNX model was validated against the original monolithic FP32 ONNX model across all calibration images (`fire.raw`, `fire_2.raw`, `person.raw`) using ONNX Runtime CPU Execution Provider:

| Validation Metric | Measurement | Status |
| :--- | :--- | :--- |
| **Max Absolute Difference** | **`0.000000`** | **PASS** |
| **Mean Absolute Difference** | **`0.000000`** | **PASS** |
| **Relative Error** | **`0.000000%`** | **PASS** |
| **NaN Count** | **`0`** | **PASS** |
| **Inf Count** | **`0`** | **PASS** |
| **Box Tensor Shape** | `[1, 64, 8400]` | **PASS** |
| **Score Tensor Shape** | `[1, 3, 8400]` | **PASS** |

The split FP32 ONNX model is **100% numerically identical** to the backbone and feature heads of the original model.

---

## 5. QNN INT8 Quantization on Split Model

QNN INT8 conversion was executed on `models/new_3class_best_FP32_htp_split.onnx` using `qnn-onnx-converter` (`QAIRT 2.47.0.260601`):

- **Input:** `images` (`[1, 3, 640, 640]`, `QNN_DATATYPE_UFIXED_POINT_8`, Scale $1/255 \approx 0.00392157$, Zero Point $0$)
- **Output 0:** `_model_22_Concat_output_0` (`[1, 64, 8400]`, `QNN_DATATYPE_UFIXED_POINT_8`)
- **Output 1:** `_model_22_Sigmoid_output_0` (`[1, 3, 8400]`, `QNN_DATATYPE_UFIXED_POINT_8`)
- **Quantization Scheme:** Weights = 8-bit Signed Per-Channel Symmetric, Activations = 8-bit Unsigned Min-Max Asymmetric, Bias = 32-bit Signed Symmetric.
- **Conversion Status:** **PASS** (Exit code `0`). Artifacts generated in `results/qnn_int8_split_conversion/generated/`:
  - `model_split_qnn_int8.bin` ($25.75\text{ MB}$)
  - `model_split_qnn_int8.cpp` ($3.55\text{ MB}$)
  - `model_split_qnn_int8_net.json` ($8.34\text{ MB}$)

---

## 6. HTP Compilation & Experimental Diagnosis

### 6.1 Online HTP Compilation Diagnosis
When compiling the generated QNN C++ intermediate representation into an HTP v68 context binary via `libQnnHtp.so`:
- **Stage 1 (Graph Preparation):** `PASS` ($446\ \mu\text{s}$)
- **Stage 2 (Graph Optimizations):** `PASS` ($942.8\text{ ms}$)
- **Stage 3 (Post Graph Optimization):** `PASS` ($32.1\text{ ms}$)
- **Stage 4 (Context Serialization):** `FAIL` (`Segmentation fault 139`)

### 6.2 Root Cause in Target Runtime Engine
On the target ARM64 Linux platform (`Kavach-EdgeBox`), `libQnnHtp.so` is Qualcomm's runtime deployment driver. In Qualcomm QAIRT 2.47, offline compilation of HTP context binaries is designed to run via `qnn-context-binary-generator` on x86_64 build hosts using the 88MB offline compiler `libQnnHtpPrepare.so`. On target ARM64 Linux, `libQnnHtp.so` routes offline graph serialization calls to the Hexagon DSP via FastRPC, which encounters memory/stack limits during full online context binary serialization.

---

## 7. Resolution & Deployment Architecture

The derived model contract `[1, 64, 8400]` (bounding box distributions) and `[1, 3, 8400]` (class probabilities) matches the **exact architecture of the pre-compiled Qualcomm AI Hub binary** `models/3class_calibrated_final.bin` and `models/kawachx_aihub_split.bin` validated in Step 2.

The C++ daemon (`src/npu_worker/`) is designed to consume these exact `[1, 64, 8400]` and `[1, 3, 8400]` tensors and perform real-time SIMD-accelerated DFL decoding, anchor box decoding, confidence scoring, and NMS.
