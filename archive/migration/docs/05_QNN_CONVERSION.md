# 05. Qualcomm QNN Conversion & HTP Compilation

**SDK Version:** Qualcomm QAIRT 2.47.0.260601  
**Target Backend:** Qualcomm Hexagon v68 HTP (`libQnnHtp.so`)  

---

## 1. Two-Stage Compilation Pipeline

### Stage 1: ONNX to Quantized QNN C++ Model
The `qnn-onnx-converter` tool converts the source ONNX graph into quantized QNN operator definitions:

```bash
${QNN_SDK_ROOT}/bin/aarch64-ubuntu-gcc9.4/qnn-onnx-converter \
    --input_network models/source/new_3class_best_FP32.onnx \
    --output_path results/conversion/model_qnn_int8.cpp \
    --input_list results/calibration/input_list.txt \
    --act_bw 8 \
    --bias_bw 32 \
    --weight_bw 8
```

### Stage 2: Offline HTP Context Binary Generation
The `qnn-context-binary-generator` compiles the intermediate model into an optimized, serialized `.bin` context for the Hexagon v68 DSP:

```bash
${QNN_SDK_ROOT}/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator \
    --backend ${QNN_SDK_ROOT}/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so \
    --model results/conversion/model_qnn_int8.bin \
    --binary_file models/qnn/new_3class_best_INT8_HTP_v68.bin \
    --htp_arch v68 \
    --config_file config/qnn/htp_config.json
```

---

## 2. Multi-Tier Binary Validation Tool
To inspect serialized context binaries without executing them on hardware:
```bash
python scripts/qnn/inspect_qnn_binary.py \
    --binary models/qnn/3class_calibrated_final.bin
```
Validates magic headers, HTP architecture compatibility (v68), input/output tensor descriptors, and quantization parameters.
