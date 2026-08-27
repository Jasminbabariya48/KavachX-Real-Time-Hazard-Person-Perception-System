# 09. Troubleshooting & Edge Gotchas

---

## 1. FastRPC Device Creation Failure (`ERROR_DEVICE_CREATE` / `14001`)

### Symptoms
`kawach_worker` fails on startup with:
```text
DspTransport.openSession qnn_open failed, 0x00000072
Failed to create transport for device, error: 1002
[qnn] deviceCreate failed: 14001
[kawach_worker] QNN init failed: ERROR_DEVICE_CREATE
```

### Cause
The Linux device nodes `/dev/fastrpc-cdsp` and `/dev/dma_heap/system` are restricted to `root:render`. If the active Linux user is not in the `render` group, opening the device node throws `EACCES (Permission Denied)`.

### Solution
Add the user to the `render` group and initiate a new session:
```bash
sudo usermod -aG render work_user2
```

---

## 2. DFL (Distribution Focal Loss) Softmax Jitter

### Symptoms
INT8 bounding boxes exhibit high coordinate variance or collapse around anchor grids compared to FP32 reference.

### Cause
YOLOv8 evaluates 16-bin Softmax distributions per bounding box edge across $8400$ anchors ($537,600$ Softmax ops/frame). On vector fixed-point DSPs, 8-bit quantization creates rounding artifacts in exponential probability tails.

### Solution
Decouple the detection head: strip Softmax from the quantized NPU graph and compute the bounding box integral on the host CPU in FP32 during NMS post-processing.

---

## 3. SiLU (Swish) Negative Saturation Truncation

### Symptoms
Low-confidence detections on small smoke plumes or distant fire flares.

### Cause
SiLU ($x \cdot \sigma(x)$) non-linearity in the negative domain ($-0.278 \le x < 0$) suffers quantization clipping under asymmetric uniform INT8.

### Solution
Use KL-divergence calibration or re-train/reparameterize the backbone using **Hard-Swish** or **LeakyReLU**.
