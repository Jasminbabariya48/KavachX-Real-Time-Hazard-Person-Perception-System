# KavachX INT8 Calibration Dataset

## Dataset Summary
* **Total Samples:** 3
* **Input Tensor:** `images`
* **Input Shape:** `[1, 3, 640, 640]` (NCHW)
* **Color Space:** RGB
* **Value Range:** `[0.0, 1.0]` (Normalized Float32) / `[0, 255]` (Quantized UINT8)
* **Padding:** Letterbox 640x640 with border color `(114, 114, 114)`
* **NaN / Inf Errors:** 0 / 0 (PASS)

## Files:
* `calibration_manifest.json`: Full metadata and tensor parameters.
* `input_contract.json`: Input contract specification.
* `input_list.txt`: Input file list for `qnn-onnx-converter`.
* `validation_report.json`: Image integrity and statistical audit.
* `preprocessed/`: Raw continuous binary tensors (`.raw`) and NumPy arrays (`.npy`).
* `visualizations/`: Visual validation overlays.
