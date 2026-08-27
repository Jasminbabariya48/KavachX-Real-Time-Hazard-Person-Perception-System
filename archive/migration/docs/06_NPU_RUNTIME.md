# 06. NPU Runtime Architecture & C++ Daemon

**Daemon:** `kawach_worker`  
**Source Directory:** `src/npu_worker/`  
**API:** Qualcomm QNN Core C API (`QnnInterface.h`, `QnnBackend.h`, `QnnContext.h`, `QnnGraph.h`, `QnnTensor.h`)  

---

## 1. Daemon Lifecycle

```text
  [1. Startup] ─────────────► Load libQnnHtp.so & libQnnSystem.so via dlopen()
        │
        ▼
  [2. Backend & Device] ────► QnnBackend_initialize() -> QnnDevice_create()
        │
        ▼
  [3. Context Loading] ─────► QnnContext_createFromBinary() (zero-copy mmap)
        │
        ▼
  [4. Graph Retrieval] ─────► QnnGraph_retrieve() & map tensor descriptors
        │
        ▼
  [5. IPC Socket Setup] ────► Listen on Unix domain socket (/tmp/kawach_worker.sock)
        │
        ▼
  [6. Inference Loop] ──────► Ingest frame (uint8, NCHW) -> QnnGraph_execute() -> Send floats
        │
        ▼
  [7. Clean Teardown] ──────► QnnContext_freeContext() -> QnnBackend_free()
```

---

## 2. IPC Protocol Specification

Communication occurs over Unix domain socket `/tmp/kawach_worker.sock`:

* **Frame Request Format:**
  * Payload: Exactly $1 \times 3 \times 640 \times 640 = 1,228,800\text{ bytes}$ (`uint8`, NCHW layout).
* **Inference Response Format:**
  * Header: $4\text{ bytes}$ status code (`0x00000000` = SUCCESS).
  * Payload: Exactly $1 \times 7 \times 8400 \times 4\text{ bytes} = 235,200\text{ bytes}$ (`float32`, $8400$ anchor boxes $\times 7$ channels).

---

## 3. Building and Running `kawach_worker`

```bash
cd src/npu_worker
make

# Execute daemon on Kavach-EdgeBox
export ADSP_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned:/vendor/dsp/cdsp:/vendor/lib/rfsa/adsp
./kawach_worker \
    --backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so \
    --system  /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so \
    --model   models/qnn/3class_calibrated_final.bin \
    --socket  /tmp/kawach_worker.sock
```
