# Phase 1 Status: Hardware & Environment Baseline

## 1. PASS (Verified Prerequisites)
* **Target Hardware:** Qualcomm QCS6490 SoC (Radxa Dragon Q6A, SoC ID: 498, 8-core aarch64 CPU, 7.4 GiB RAM) verified.
* **Operating System:** KavachOS 1.0 (Linux kernel 6.18.2-3-qcom, Ubuntu 24.04 noble base) verified.
* **SDK Installation:** Qualcomm QAIRT 2.47.0.260601 (QNN Backend API 2.18.0) verified at `/home/devuser/qairt/2.47.0.260601/`.
* **QNN Headers & Libraries:** `QnnInterface.h`, `libQnnHtp.so`, `libQnnHtpV68Stub.so`, `libQnnHtpV68Skel.so`, `libQnnSystem.so` all present and compatible with aarch64 target.
* **C++ Runtime (`kawach_worker`):** Built cleanly with GCC 13.3.0 and Make 4.3 against QNN 2.47.0 headers and libraries.
* **Source ONNX Model:** `new_3class_best_FP32.onnx` (103.5 MB, YOLOv8 3-class detector) verified.
* **FP32 Ground Truth Baseline:** Executed on target CPU ($2185.58\text{ ms}$ latency), capturing raw output tensors and detections.
* **Test Imagery:** 3 test images (`fire.jpg`, `fire_2.jpg`, `person.jpg`) verified.

---

## 2. WARNING
* **Prior Context Binaries:** `3class_calibrated_final.bin` and `kawachx_aihub_split.bin` exist (26 MB each) but their loadability and internal graph accuracy remain unverified on hardware pending NPU device access.

---

## 3. BLOCKED
* **Hexagon NPU FastRPC Device Access:**
  * User `work_user2` is missing the `render` group.
  * Opening `/dev/fastrpc-cdsp` and `/dev/dma_heap/system` throws `EACCES (Permission Denied)`.
  * `kawach_worker` init fails with `ERROR_DEVICE_CREATE (14001)`.
  * **Required Action:** Administrator must execute `sudo usermod -aG render work_user2`.

---

## 4. UNKNOWN
* None. All target hardware, SDK, model, and runtime characteristics have been programmatically investigated.

---

## 5. Ready for Phase 2?

```text
NO — PENDING PERMISSION RESOLUTION
```

### Explanation
All software assets, compilation toolchains, source models, and runtime scaffolding are completely verified and in an executable state. Phase 2 (NPU Execution & Prior Binary Validation) can proceed immediately the moment the administrator adds `work_user2` to the `render` group on `Kavach-EdgeBox`.
