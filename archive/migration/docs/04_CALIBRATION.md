# 04. INT8 Calibration Strategy & Dataset Generation

---

## 1. Mathematical Quantization Formulation

Fixed-point INT8 quantization maps 32-bit floating-point tensors $X \in \mathbb{R}$ to 8-bit integers $q \in [-128, 127]$ (or $[0, 255]$ for asymmetric activations):

$$q = \text{clamp}\left(\left\lfloor \frac{X}{S} \right\rceil + Z, q_{\min}, q_{\max}\right)$$

$$X \approx S \cdot (q - Z)$$

* **Weight Quantization:** Symmetric Per-Channel ($Z_w = 0$). Scale calculated per output channel to preserve subtle filter weight distinctions.
* **Activation Quantization:** Asymmetric Per-Tensor ($Z_a \neq 0$). Scale and zero-point calibrated across dynamic activation ranges using Kullback-Leibler (KL) divergence minimization.

---

## 2. Calibration Dataset Protocol

* **Image Requirements:** 50–100 representative industrial frames containing fire flares, dense smoke plumes, and worker scenes under diverse lighting.
* **Preprocessing:** Standard Letterbox resize to $640\times640$, RGB color conversion, normalization to $[0.0, 1.0]$, stored in continuous `.raw` float32 or uint8 binary format.

---

## 3. Tooling Execution
```bash
python scripts/calibration/prepare_calibration_data.py \
    --dataset-dir data/calibration \
    --output-dir results/calibration \
    --layout NCHW
```
Generates the raw binaries and the QNN-compatible `input_list.txt`.
