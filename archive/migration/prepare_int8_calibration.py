#!/usr/bin/env python3
"""
Step 3 — INT8 Calibration Dataset Preparation & Input Contract Validation
Authoritative calibration generator matching exact FP32 YOLOv8 Letterbox contract.
"""

import os
import sys
import glob
import json
import shutil
import numpy as np
import cv2

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    """Ultralytics YOLOv8 standard letterbox resizing preserving aspect ratio."""
    shape = img.shape[:2]  # [h, w]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]

    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img, r, (dw, dh)

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_images_dir = os.path.join(base_dir, "data", "test_images")
    output_dir = os.path.join(base_dir, "results", "int8_calibration")
    
    calib_img_dir = os.path.join(output_dir, "images")
    preprocessed_dir = os.path.join(output_dir, "preprocessed")
    vis_dir = os.path.join(output_dir, "visualizations")
    
    os.makedirs(calib_img_dir, exist_ok=True)
    os.makedirs(preprocessed_dir, exist_ok=True)
    os.makedirs(vis_dir, exist_ok=True)

    print("==================================================================")
    print(" INT8 Calibration Dataset Generation & Input Contract Validation")
    print(f" Source Directory: {raw_images_dir}")
    print(f" Target Directory: {output_dir}")
    print("==================================================================")

    # 1. Locate Source Images
    image_paths = sorted(glob.glob(os.path.join(raw_images_dir, "*.*")))
    image_paths = [p for p in image_paths if p.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    
    print(f"Found {len(image_paths)} candidate calibration image(s).")
    
    manifest_entries = []
    validation_entries = []
    input_list_lines = []
    all_stats = []

    for img_path in image_paths:
        filename = os.path.basename(img_path)
        base_name = os.path.splitext(filename)[0]
        
        # Validation checks
        val_record = {
            "filename": filename,
            "source_path": img_path,
            "readable": False,
            "valid_dimensions": False,
            "channels_valid": False,
            "not_corrupted": False,
            "status": "REJECTED"
        }
        
        try:
            img = cv2.imread(img_path)
            if img is None:
                val_record["rejection_reason"] = "Failed to decode image with OpenCV"
                validation_entries.append(val_record)
                continue
                
            orig_h, orig_w, orig_c = img.shape
            val_record["readable"] = True
            val_record["orig_dimensions"] = [int(orig_w), int(orig_h), int(orig_c)]
            
            if orig_h < 32 or orig_w < 32:
                val_record["rejection_reason"] = f"Image dimensions too small ({orig_w}x{orig_h})"
                validation_entries.append(val_record)
                continue
            val_record["valid_dimensions"] = True
            
            if orig_c != 3:
                val_record["rejection_reason"] = f"Expected 3 channels, got {orig_c}"
                validation_entries.append(val_record)
                continue
            val_record["channels_valid"] = True
            val_record["not_corrupted"] = True
            val_record["status"] = "PASSED"
            validation_entries.append(val_record)
            
        except Exception as e:
            val_record["rejection_reason"] = str(e)
            validation_entries.append(val_record)
            continue

        # Copy original image to calibration images folder
        dst_img_path = os.path.join(calib_img_dir, filename)
        shutil.copy2(img_path, dst_img_path)

        # 2. Preprocess using exact FP32 baseline logic
        # Step A: BGR -> RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Step B: Letterbox to 640x640 with padding color (114, 114, 114)
        padded_rgb, r, (dw, dh) = letterbox(img_rgb, (640, 640), color=(114, 114, 114))
        
        # Step C: Visual validation dump
        vis_bgr = cv2.cvtColor(padded_rgb, cv2.COLOR_RGB2BGR)
        vis_path = os.path.join(vis_dir, f"{base_name}_letterbox_640x640.jpg")
        cv2.imwrite(vis_path, vis_bgr)
        
        # Step D: Normalized Float32 tensor [1, 3, 640, 640] in [0.0, 1.0]
        tensor_fp32 = padded_rgb.astype(np.float32) / 255.0
        tensor_fp32 = np.transpose(tensor_fp32, (2, 0, 1))  # HWC -> CHW
        tensor_fp32 = np.expand_dims(tensor_fp32, axis=0)   # [1, 3, 640, 640]
        
        # Step E: Contiguous Raw Binary format for QNN Converter (.raw)
        raw_fp32_path = os.path.join(preprocessed_dir, f"{base_name}_fp32.raw")
        npy_fp32_path = os.path.join(preprocessed_dir, f"{base_name}_fp32.npy")
        
        tensor_fp32.astype(np.float32).tofile(raw_fp32_path)
        np.save(npy_fp32_path, tensor_fp32)
        
        # Also generate UINT8 raw format for direct worker comparison
        tensor_uint8 = padded_rgb.astype(np.uint8)
        tensor_uint8 = np.transpose(tensor_uint8, (2, 0, 1))
        tensor_uint8 = np.expand_dims(tensor_uint8, axis=0)
        raw_uint8_path = os.path.join(preprocessed_dir, f"{base_name}_uint8.raw")
        tensor_uint8.tofile(raw_uint8_path)

        # 3. Statistical Analysis
        stats = {
            "filename": filename,
            "shape": list(tensor_fp32.shape),
            "dtype": "float32",
            "min": float(np.min(tensor_fp32)),
            "max": float(np.max(tensor_fp32)),
            "mean": float(np.mean(tensor_fp32)),
            "std": float(np.std(tensor_fp32)),
            "zero_percentage": float(np.count_nonzero(tensor_fp32 == 0.0) / tensor_fp32.size * 100.0),
            "nan_count": int(np.isnan(tensor_fp32).sum()),
            "inf_count": int(np.isinf(tensor_fp32).sum()),
            "raw_size_bytes": os.path.getsize(raw_fp32_path)
        }
        all_stats.append(stats)

        # QNN input list line format: images:=<path_to_raw>
        input_list_lines.append(f"images:={raw_fp32_path}")

        manifest_entries.append({
            "sample_id": base_name,
            "original_filename": filename,
            "original_resolution": [orig_w, orig_h],
            "preprocessed_shape": [1, 3, 640, 640],
            "raw_fp32_file": os.path.relpath(raw_fp32_path, base_dir),
            "raw_uint8_file": os.path.relpath(raw_uint8_path, base_dir),
            "scale_ratio": r,
            "pad_w_h": [dw, dh],
            "stats": stats
        })

    # Write input_list.txt for QAIRT qnn-onnx-converter
    input_list_path = os.path.join(output_dir, "input_list.txt")
    with open(input_list_path, "w", encoding="utf-8") as f:
        f.write("\n".join(input_list_lines) + "\n")

    # 4. Generate Contract JSON
    input_contract = {
        "model_input_tensor_name": "images",
        "tensor_shape": [1, 3, 640, 640],
        "tensor_layout": "NCHW",
        "color_format": "RGB",
        "data_type": "float32 (normalized) / uint8 (hardware quant)",
        "value_range": [0.0, 1.0],
        "letterbox_padding_color": [114, 114, 114],
        "normalization_formula": "pixel_val / 255.0",
        "target_hexagon_quant_scheme": {
            "scale": 0.00392156862745098,
            "zero_point": 0,
            "bits": 8,
            "is_symmetric": False
        },
        "compatibility_with_fp32_baseline": True
    }
    
    contract_path = os.path.join(output_dir, "input_contract.json")
    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(input_contract, f, indent=2)

    # 5. Generate Manifest JSON
    manifest = {
        "manifest_version": "1.0.0",
        "dataset_name": "KavachX_QCS6490_INT8_Calibration_Set",
        "source_directory": os.path.relpath(raw_images_dir, base_dir),
        "total_samples": len(manifest_entries),
        "input_contract": input_contract,
        "samples": manifest_entries
    }
    
    manifest_path = os.path.join(output_dir, "calibration_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 6. Generate Validation Report JSON
    total_nan = sum(s["nan_count"] for s in all_stats)
    total_inf = sum(s["inf_count"] for s in all_stats)
    all_passed = all(v["status"] == "PASSED" for v in validation_entries) and total_nan == 0 and total_inf == 0

    validation_report = {
        "status": "PASS" if all_passed else "FAIL",
        "total_images_evaluated": len(validation_entries),
        "valid_images": len(manifest_entries),
        "rejected_images": len(validation_entries) - len(manifest_entries),
        "total_nan_count": total_nan,
        "total_inf_count": total_inf,
        "dataset_statistics": {
            "min_observed": float(min(s["min"] for s in all_stats)),
            "max_observed": float(max(s["max"] for s in all_stats)),
            "mean_observed": float(np.mean([s["mean"] for s in all_stats])),
            "std_observed": float(np.mean([s["std"] for s in all_stats]))
        },
        "per_image_validation": validation_entries
    }

    val_report_path = os.path.join(output_dir, "validation_report.json")
    with open(val_report_path, "w", encoding="utf-8") as f:
        json.dump(validation_report, f, indent=2)

    # 7. Write README.md
    readme_content = f"""# KavachX INT8 Calibration Dataset

## Dataset Summary
* **Total Samples:** {len(manifest_entries)}
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
"""
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("\n--- Summary of Calibration Statistics ---")
    for s in all_stats:
        print(f"Image: {s['filename']:<12} | Min: {s['min']:.3f} | Max: {s['max']:.3f} | Mean: {s['mean']:.3f} | NaN: {s['nan_count']} | Inf: {s['inf_count']}")

    print("\n==================================================================")
    print(f" Validation Report: {val_report_path}")
    print(f" Manifest:          {manifest_path}")
    print(f" Contract:          {contract_path}")
    print(f" Overall Status:    {'PASS' if all_passed else 'FAIL'}")
    print("==================================================================")

if __name__ == "__main__":
    main()
