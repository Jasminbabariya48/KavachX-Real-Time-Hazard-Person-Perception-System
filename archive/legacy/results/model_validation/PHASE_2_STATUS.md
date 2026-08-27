# Phase 2 Status: Model & Existing Binary Validation

## 1. Render Permission Status
* **Status:** ❌ **FAIL (BLOCKED)**
* **Detail:** `work_user2` is not in the `render` group. FastRPC DSP sessions cannot be initiated.

---

## 2. QNN HTP Device Initialization
* **Status:** ❌ **FAIL (ERROR_DEVICE_CREATE / 14001)**
* **Detail:** Direct consequence of missing `render` permission on `/dev/fastrpc-cdsp`.

---

## 3. FP32 Model Contract
* **Status:** ✅ **PASS (VERIFIED)**
* **Model:** `new_3class_best_FP32.onnx` (YOLOv8 Detect, `[1, 3, 640, 640]` $\rightarrow$ `[1, 7, 8400]`).
* **Classes:** `{0: 'person', 1: 'fire', 2: 'smoke'}`.
* **Golden Baseline:** Captured across `fire.jpg`, `fire_2.jpg`, `person.jpg` ($2185.58\text{ ms}$ CPU latency).

---

## 4. Existing Binary Validation
* **Binary 1 (`3class_calibrated_final.bin`):** ❌ **FAIL (Contract Mismatch)** — Exposes split outputs (`output_0`, `output_1`).
* **Binary 2 (`kawachx_aihub_split.bin`):** ❌ **FAIL (Contract Mismatch)** — Exposes `images_uint8` and split outputs (`output_0`, `output_1`).

---

## 5. Recommended Next Phase
```text
C. Quantize and compile model
```
### Justification
Neither existing context binary matches the single-tensor `[1, 7, 8400]` output contract expected by `npu_worker` and `new_3class_best_FP32.onnx`. A clean, reproducible INT8 context binary must be compiled from the source ONNX model using the installed QAIRT 2.47.0 SDK once `render` permissions are active.
