# 07. Numerical & Detection Parity Validation

---

## 1. Dual-Path Evaluation Methodology

```text
                           EVALUATION IMAGE
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
       [FP32 ONNX Runtime]                [INT8 QNN HTP NPU]
        Raw Output Tensor                  Raw Output Tensor
                 │                                 │
                 ├────────────────┬────────────────┤
                 ▼                                 ▼
       [1. Raw Tensor Parity]           [2. Detection Parity]
        - MaxAE & MAE                    - Greedy IoU Matching
        - Cosine Similarity              - Class Agreement %
        - Logit Delta                    - Confidence Delta
```

---

## 2. Mathematical Acceptance Criteria

| Metric | Mathematical Definition | Acceptance Threshold |
| :--- | :--- | :---: |
| **Max Absolute Error (MaxAE)** | $\max |Y_{\text{FP32}} - Y_{\text{INT8}}|$ | $\le \mathbf{0.080}$ |
| **Mean Absolute Error (MAE)** | $\frac{1}{N}\sum |Y_{\text{FP32}} - Y_{\text{INT8}}|$ | $\le \mathbf{0.015}$ |
| **Cosine Similarity** | $\frac{Y_{\text{FP32}} \cdot Y_{\text{INT8}}}{\|Y_{\text{FP32}}\| \|Y_{\text{INT8}}\|}$ | $\ge \mathbf{0.990}$ |
| **Mean Bounding Box IoU** | $\frac{\text{Area}(B_{\text{FP32}} \cap B_{\text{INT8}})}{\text{Area}(B_{\text{FP32}} \cup B_{\text{INT8}})}$ | $\ge \mathbf{0.850}$ |
| **Class Label Match Rate** | $\frac{\text{Identical Class Matches}}{\text{Total Matched Detections}} \times 100\%$ | $\mathbf{100.0\%}$ (conf $> 0.50$) |

---

## 3. Tooling Execution
```bash
python scripts/validation/compare_fp32_int8.py \
    --fp32-dir results/fp32_baseline/raw_outputs \
    --int8-dir results/int8_npu/raw_outputs \
    --output results/parity/parity_report.json
```
