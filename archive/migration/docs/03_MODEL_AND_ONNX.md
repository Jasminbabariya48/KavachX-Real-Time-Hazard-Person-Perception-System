# 03. Model Architecture & FP32 Reference Baseline

**Model File:** `models/source/new_3class_best_FP32.onnx` (103.5 MB)  
**Architecture:** Ultralytics YOLOv8 (Anchor-Free Decoupled Head)  

---

## 1. ONNX Model Specifications

* **Input Tensor:** `images` $\rightarrow$ Shape: `[1, 3, 640, 640]`, Dtype: `float32`, Color: RGB, Normalization: $[0.0, 1.0]$.
* **Output Tensor:** `output0` $\rightarrow$ Shape: `[1, 7, 8400]`, Dtype: `float32`.
* **Class Mapping:**
  ```json
  {
    0: "person",
    1: "fire",
    2: "smoke"
  }
  ```
* **Output Channel Structure ($7$ channels per anchor):**
  * Channels $0..3$: Bounding box center coordinates and dimensions ($c_x, c_y, w, h$).
  * Channels $4..6$: Class classification scores for `person` (0), `fire` (1), `smoke` (2).

---

## 2. FP32 Reference Baseline Execution Results

Inference executed on **Kavach-EdgeBox** CPU (8-Core Cortex-A78/A55) via ONNX Runtime:

| Test Image | Dimensions | Verified Detections | FP32 CPU Latency |
| :--- | :---: | :--- | :---: |
| **`fire.jpg`** | $678\times452$ | 2x **Smoke** (69.4%, 69.3%) | $2187.05\text{ ms}$ |
| **`fire_2.jpg`** | $679\times452$ | 2x **Fire** (32.5%, 28.4%) | $2178.91\text{ ms}$ |
| **`person.jpg`**| $678\times452$ | 2x **Person** (83.4%, 81.6%) | $2190.78\text{ ms}$ |

* **Mean Latency:** **$2185.58\text{ ms}$ ($0.46\text{ FPS}$)**.
* **Ground Truth Storage:** Output numpy tensors saved to `results/fp32_baseline/raw_outputs/`.

---

## 3. Running FP32 Baseline Tooling
```bash
python scripts/model/run_fp32_baseline.py
```
