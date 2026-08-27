# 11. Hardware & QAIRT/QNN SDK Environment Baseline

**Device:** Kavach-EdgeBox  
**Date of Baseline:** August 26, 2026  
**Inspection Type:** Live Hardware & Target Environment Audit (Read-Only)  

---

## 1. Hardware Specification

* **Device Hostname:** `Kavach-EdgeBox`
* **SoC / Machine Name:** Radxa Dragon Q6A (`/sys/devices/soc0/machine`)
* **Qualcomm SoC ID:** `498` (Qualcomm QCS6490 / Snapdragon family)
* **CPU Cores:** 8 Cores (4x ARM Cortex-A78 @ 2.707 GHz + 4x ARM Cortex-A55 @ 1.958 GHz)
* **Architecture:** `aarch64` (ARMv8 64-bit Little Endian)
* **RAM:** 7.4 GiB Total (6.7 GiB Available) / 3.7 GiB Swap
* **Hexagon NPU Presence:** Qualcomm Hexagon v68 / V68 HTP present on SoC
* **HTP v68 Backend Support:** Verified in QAIRT SDK (`libQnnHtp.so`, `libQnnHtpV68Skel.so`, `libQnnHtpV68Stub.so`)

---

## 2. Operating System & Kernel

* **Operating System:** KavachOS 1.0 (Ubuntu 24.04 LTS "noble" derivative)
* **Kernel Version:** `Linux Kavach-EdgeBox 6.18.2-3-qcom #3 SMP PREEMPT_DYNAMIC aarch64 GNU/Linux`
* **Target Architecture:** `aarch64`

---

## 3. User Access & Permissions Audit

* **Active User:** `work_user2` (`uid=1006`, `gid=1006`)
* **Assigned Groups:** `1006(work_user2)`, `100(users)`, `1005(qairt-users)`
* **`render` Group Membership:** ❌ **MISSING**
* **Device Node Permissions:**
  * `/dev/fastrpc-cdsp`: `crw-rw----+ 1 root render` (Access **BLOCKED** without `render` group)
  * `/dev/fastrpc-cdsp-secure`: `crw-rw----+ 1 root render` (Access **BLOCKED**)
  * `/dev/dma_heap/system`: `crw-rw----+ 1 root render` (Access **BLOCKED**)
  * `/dev/dma_heap/reserved`: `crw-rw----+ 1 root render` (Access **BLOCKED**)

---

## 4. Qualcomm QAIRT & QNN SDK Baseline

* **QAIRT Version:** `2.47.0` (Build ID: `260601114230`)
* **QNN Backend API Version:** `2.18.0`
* **SDK Flavor:** `premium`
* **SDK Root Path:** `/home/devuser/qairt/2.47.0.260601`
* **Active SDK Status:** Single authoritative SDK installation found in `/home/devuser/qairt/`

---

## 5. QNN Backends & Libraries Available

* **CPU Backend:** `libQnnCpu.so` (7.65 MB, aarch64 ELF shared object) — **FOUND**
* **GPU Backend:** `libQnnGpu.so` (7.85 MB, aarch64 ELF shared object) — **FOUND**
* **HTP Backend:** `libQnnHtp.so` (4.02 MB, aarch64 ELF shared object) — **FOUND**
* **HTP v68 Host Stub:** `libQnnHtpV68Stub.so` (436 KB, aarch64 ELF shared object) — **FOUND**
* **HTP v68 DSP Skel:** `libQnnHtpV68Skel.so` (10.0 MB, Hexagon DSP shared object) — **FOUND**
* **QNN System Library:** `libQnnSystem.so` (5.22 MB, aarch64 ELF shared object) — **FOUND**
* **QNN Headers:** `/home/devuser/qairt/2.47.0.260601/include/QNN/` — **FOUND**

---

## 6. QNN & QAIRT Tools

Located in `/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/` and `bin/x86_64-linux-clang/`:
* `qnn-onnx-converter`: Available (Host x86_64 & Python API)
* `qnn-context-binary-generator`: Available (aarch64 target & x86_64 host)
* `qnn-net-run`: Available (aarch64 target & x86_64 host)
* `qnn-profile-viewer`: Available
* `qairt-converter` / `qairt-quantizer`: Available

---

## 7. Toolchain & Compilers

* **GCC / G++:** GCC 13.3.0 (`/usr/bin/gcc`, `/usr/bin/g++`)
* **Make:** GNU Make 4.3 (`/usr/bin/make`)
* **Python:** Python 3.12.3 (`/usr/bin/python3`) with `onnxruntime 1.23.2`, `numpy 2.2.6`, `opencv-python-headless 4.13.0.92`
* **Glibc:** Ubuntu GLIBC 2.39

---

## 8. Project & Artifacts Baseline

* **C++ Runtime:** `kawachx_task/npu_worker/` (`main.cpp`, `qnn_inference.cpp`, `ipc_handler.cpp`, `Makefile`). Successfully compiles with `make` to `kawach_worker`.
* **Source ONNX Model:** `kawachx_task/models/new_3class_best_FP32.onnx` ($103.5\text{ MB}$, YOLOv8 Detect, `[1, 3, 640, 640]` $\rightarrow$ `[1, 7, 8400]`).
* **Existing Prior .bin Artifacts:**
  * `3class_calibrated_final.bin` ($26.0\text{ MB}$) — Verified format, unexecuted.
  * `kawachx_aihub_split.bin` ($26.0\text{ MB}$) — Verified format, unexecuted.
* **Test Imagery:** `fire.jpg`, `fire_2.jpg`, `person.jpg` ($678\times452$ JPEG).

---

## 9. Baseline Findings Summary

* **VERIFIED:** Qualcomm QCS6490 hardware, KavachOS kernel, QAIRT 2.47.0 SDK, FP32 ONNX model, `kawach_worker` C++ build.
* **FOUND BUT NOT VERIFIED ON NPU:** Context binaries (`.bin`) loadability on Hexagon DSP.
* **BLOCKED:** Hexagon FastRPC NPU session initialization (`/dev/fastrpc-cdsp` EACCES due to missing `render` group on `work_user2`).
