# 12. Model and Existing Binary Validation Report

**Assessment:** KawachX On-Device NPU Deployment  
**Phase:** Phase 2A/2B — Model Contract & Prior Binary Forensic Audit  

---

## 1. Step 0: Permission & FastRPC Status

* **Active User:** `work_user2` (`uid=1006`, `gid=1006`)
* **User Groups:** `1006(work_user2)`, `100(users)`, `1005(qairt-users)`
* **`render` Group Status:** ❌ **MISSING** (Present in `/etc/group` for `radxa,rock,devuser,test_user`, but not yet granted to `work_user2`)
* **FastRPC Device Node:** `/dev/fastrpc-cdsp` (`crw-rw----+ 1 root render`)
* **Impact:** FastRPC session creation throws `EACCES (Permission Denied / 14001: ERROR_DEVICE_CREATE)`. NPU hardware execution is blocked until administrator executes `sudo usermod -aG render work_user2`.

---

## 2. FP32 Source Model Specification (`models/source/new_3class_best_FP32.onnx`)

* **Model File:** `kawachx_task/models/new_3class_best_FP32.onnx` ($103,562,434\text{ bytes}$)
* **Architecture:** Ultralytics YOLOv8 (8.4.113) Detect Head (Anchor-Free)
* **Input Tensor:** `images` (`[1, 3, 640, 640]`, `float32`, RGB, $[0.0, 1.0]$)
* **Output Tensor:** `output0` (`[1, 7, 8400]`, `float32`)
  * $4\text{ channels}$: Bounding box centers and dimensions ($c_x, c_y, w, h$)
  * $3\text{ channels}$: Class scores (`0: person`, `1: fire`, `2: smoke`)
* **Ground Truth CPU Latency:** $2185.58\text{ ms}$ ($0.46\text{ FPS}$)

---

## 3. Prior Context Binary Forensics

### Binary #1: `3class_calibrated_final.bin`
* **File Size:** $26,800,128\text{ bytes}$ ($25.56\text{ MB}$)
* **Internal Graph Name:** `graph_en1elpeg`
* **Tensor Signatures:** `images`, `output_0`, `output_1`, `/model.22/cv3.2/cv3.2.2/Conv`, `/model.22/cv2.2/cv2.2.2/Conv`
* **Architecture Mismatch:** Contains **TWO separate output tensors** (`output_0`, `output_1`) rather than the single concatenated `output0` (`[1, 7, 8400]`) present in the reference FP32 ONNX model.
* **Execution Status:** Cannot be directly ingested by single-output `kawach_worker` without head-concatenation or adapter logic.

### Binary #2: `kawachx_aihub_split.bin`
* **File Size:** $26,861,568\text{ bytes}$ ($25.62\text{ MB}$)
* **Internal Graph Name:** `graph_h9q5bh8w`
* **Tensor Signatures:** `images_uint8`, `output_0`, `output_1`, `/model.22/dfl/conv/Conv_output_0_0123`, `/model.22/Concat_output_0_012`
* **Architecture Mismatch:** Input tensor is named `images_uint8` (split Qualcomm AI Hub export) with split outputs `output_0` and `output_1`.

---

## 4. `npu_worker` Implementation Review
* **C++ Engine:** `qnn_inference.cpp` dynamically loads `libQnnHtp.so` and `libQnnSystem.so`, extracts graph metadata via `systemContextGetBinaryInfo()`, and calls `QnnGraph_execute()`.
* **Current Contract:** Expects $1$ input (`[1, 3, 640, 640]` uint8) and $1$ output (`[1, 7, 8400]` float32).

---

## 5. Phase 2 Conclusion & Next Recommended Action
Both existing context binaries represent earlier split-head exports (`output_0` + `output_1`), which do not match the single concatenated tensor contract (`[1, 7, 8400]`) of `new_3class_best_FP32.onnx`.

**Recommended Next Phase:** **Phase 3 — Quantize and Compile Model** (Generate an exact single-output INT8 context binary matching `new_3class_best_FP32.onnx` via local QAIRT 2.47.0 once `render` permission is active).
