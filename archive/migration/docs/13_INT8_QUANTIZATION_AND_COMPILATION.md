# 13. INT8 Quantization & QNN Compilation Specification

**Assessment:** KawachX On-Device NPU Deployment  
**Phase:** Phase 3 — Quantization Blueprint & Pipeline Specification  
**Target Hardware:** Qualcomm QCS6490 (Hexagon v68 HTP)  

---

## 1. Input Tensor Contract Resolution

* **Source FP32 Model Input:** `images` (`[1, 3, 640, 640]`, `float32`, RGB, normalized to $[0.0, 1.0]$).
* **NPU Input Quantization Strategy:**
  * To maximize throughput and avoid CPU-to-DSP float conversions, the input tensor is quantized as **asymmetric 8-bit unsigned integer (`uint8`)** with:
    $$\text{Scale } S_{\text{in}} = \frac{1.0}{255.0} \approx 0.00392157, \quad \text{Zero Point } Z_{\text{in}} = 0$$
  * Preprocessing on CPU/VPU produces contiguous RGB uint8 frames (`1 * 3 * 640 * 640 = 1,228,800 bytes`).
* **Output Tensor Logical Contract:**
  * Single concatenated tensor `output0` (`[1, 7, 8400]`, `float32` dequantized output) representing $4\text{ bounding box coordinates}$ ($c_x, c_y, w, h$) and $3\text{ class scores}$ (`0: person`, `1: fire`, `2: smoke`).

---

## 2. Representative Calibration Dataset Preparation

* **Source Imagery:** `fire.jpg`, `fire_2.jpg`, `person.jpg` ($678\times452$ JPEG).
* **Preprocessing:** Letterbox resize to $640\times640$, RGB conversion, saved in raw binary format (`.raw`).
* **Input List:** `results/calibration/input_list.txt` formatting `images:=results/calibration/fire.raw`.

---

## 3. Exact QAIRT 2.47.0 Quantization & Compilation Commands

### Environment Initialization
```bash
source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh
export ADSP_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned:/vendor/dsp/cdsp:/vendor/lib/rfsa/adsp
```

### Stage 1: Model Conversion & INT8 Quantization
```bash
qnn-onnx-converter \
    --input_network kawachx_task/models/new_3class_best_FP32.onnx \
    --output_path results/quantization/model_qnn_int8.cpp \
    --input_list results/calibration/input_list.txt \
    --act_bw 8 \
    --bias_bw 32 \
    --weight_bw 8 \
    --quantization_overrides config/qnn/quant_overrides.json
```

### Stage 2: Context Binary Compilation for Hexagon v68 HTP
```bash
qnn-context-binary-generator \
    --backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so \
    --model results/quantization/model_qnn_int8.bin \
    --binary_file models/qnn/kavachx_3class_int8_htp_v68.bin \
    --htp_arch v68 \
    --config_file config/qnn/htp_config.json
```

---

## 4. Phase 3 Current Blocker

* **Status:** **BLOCKED** on `render` group permission on `Kavach-EdgeBox`.
* **Impact:** FastRPC session initialization with Hexagon DSP is restricted by Linux kernel DAC permissions on `/dev/fastrpc-cdsp`.
