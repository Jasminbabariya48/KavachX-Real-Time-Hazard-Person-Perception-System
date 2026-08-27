#!/usr/bin/env python3
"""
Calibration Data Preparation Utility for Qualcomm QNN Quantization
Converts a dataset of representative images to raw binary format (.raw) and generates input_list.txt.
Fails cleanly with CALIBRATION_DATASET_NOT_FOUND if the dataset directory does not exist or contains no images.
"""

import argparse
import glob
import json
import os
import sys

def prepare_calibration_data(dataset_dir: str, output_dir: str, num_samples: int, height: int, width: int, layout: str, dtype: str):
    if not os.path.exists(dataset_dir):
        print(f"ERROR: CALIBRATION_DATASET_NOT_FOUND - Dataset directory does not exist: {dataset_dir}")
        sys.exit(1)

    image_extensions = ('*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp')
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(os.path.join(dataset_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(dataset_dir, "**", ext), recursive=True))

    image_paths = sorted(list(set(image_paths)))
    if not image_paths:
        print(f"ERROR: CALIBRATION_DATASET_NOT_FOUND - No valid image files found in: {dataset_dir}")
        sys.exit(1)

    selected_images = image_paths[:num_samples]
    print(f"Found {len(image_paths)} images. Processing {len(selected_images)} samples for calibration.")

    os.makedirs(output_dir, exist_ok=True)
    raw_dir = os.path.join(output_dir, "raw_samples")
    os.makedirs(raw_dir, exist_ok=True)

    try:
        import numpy as np
        import cv2
    except ImportError:
        print("ERROR: numpy and opencv-python are required to prepare calibration data.")
        sys.exit(1)

    manifest_entries = []
    input_list_lines = []

    for idx, img_path in enumerate(selected_images):
        img = cv2.imread(img_path)
        if img is None:
            print(f"Warning: Failed to read image {img_path}, skipping.")
            continue

        orig_h, orig_w = img.shape[:2]
        
        # Standard Resize & Color Conversion (BGR -> RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (width, height), interpolation=cv2.INTER_LINEAR)

        # Normalization and Dtype Conversion
        if dtype == "float32":
            tensor = resized.astype(np.float32) / 255.0
        elif dtype == "uint8":
            tensor = resized.astype(np.uint8)
        else:
            tensor = resized.astype(np.float32)

        # Layout Handling (NCHW vs NHWC)
        if layout.upper() == "NCHW":
            tensor = np.transpose(tensor, (2, 0, 1))  # HWC -> CHW
            tensor = np.expand_dims(tensor, axis=0)   # 1, C, H, W
        else:
            tensor = np.expand_dims(tensor, axis=0)   # 1, H, W, C

        raw_filename = f"sample_{idx:04d}.raw"
        raw_filepath = os.path.join(raw_dir, raw_filename)
        tensor.tofile(raw_filepath)

        manifest_entries.append({
            "sample_index": idx,
            "original_image": os.path.abspath(img_path),
            "original_dimensions": [orig_w, orig_h],
            "raw_file": os.path.abspath(raw_filepath),
            "tensor_shape": list(tensor.shape),
            "dtype": dtype,
            "layout": layout
        })

        input_list_lines.append(f"{os.path.abspath(raw_filepath)}")

    # Write Manifest
    manifest_path = os.path.join(output_dir, "calibration_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({
            "num_samples": len(manifest_entries),
            "target_resolution": [width, height],
            "layout": layout,
            "dtype": dtype,
            "samples": manifest_entries
        }, f, indent=2)

    # Write input_list.txt for QNN Converter
    input_list_path = os.path.join(output_dir, "input_list.txt")
    with open(input_list_path, "w") as f:
        f.write("\n".join(input_list_lines) + "\n")

    print(f"Calibration data successfully generated:")
    print(f" - Manifest: {manifest_path}")
    print(f" - QNN Input List: {input_list_path}")

def main():
    parser = argparse.ArgumentParser(description="Prepare Raw Calibration Data for Qualcomm QNN Quantization")
    parser.add_argument("--dataset-dir", type=str, default="test_data/calibration", help="Path to input image dataset")
    parser.add_argument("--output-dir", type=str, default="results/calibration", help="Path to output calibration directory")
    parser.add_argument("--num-samples", type=int, default=50, help="Number of calibration samples")
    parser.add_argument("--height", type=int, default=640, help="Model input height")
    parser.add_argument("--width", type=int, default=640, help="Model input width")
    parser.add_argument("--layout", type=str, default="NCHW", choices=["NCHW", "NHWC"], help="Input tensor layout")
    parser.add_argument("--dtype", type=str, default="float32", choices=["float32", "uint8"], help="Input tensor dtype")
    args = parser.parse_args()

    prepare_calibration_data(args.dataset_dir, args.output_dir, args.num_samples, args.height, args.width, args.layout, args.dtype)

if __name__ == "__main__":
    main()
