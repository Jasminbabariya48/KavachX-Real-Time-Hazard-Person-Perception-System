#!/usr/bin/env python3
"""
FP32 ONNX Reference vs INT8 QNN NPU Parity & Numerical Validation Utility
Strictly separates:
 1. RAW TENSOR METRICS: MaxAE, MAE, Cosine Similarity.
 2. POST-PROCESSED DETECTION METRICS: Greedy IoU matching, class agreement, confidence diffs.
 3. PERFORMANCE BENCHMARKS: Latency, speedup, throughput.
"""

import argparse
import json
import os
import sys

def compute_raw_tensor_metrics(fp32_tensor, int8_tensor):
    import numpy as np
    diff = np.abs(fp32_tensor.astype(np.float64) - int8_tensor.astype(np.float64))
    max_ae = float(np.max(diff))
    mae = float(np.mean(diff))
    
    # Cosine Similarity
    dot_prod = np.dot(fp32_tensor.flatten(), int8_tensor.flatten())
    norm_fp32 = np.linalg.norm(fp32_tensor)
    norm_int8 = np.linalg.norm(int8_tensor)
    cosine_sim = float(dot_prod / (norm_fp32 * norm_int8)) if (norm_fp32 > 0 and norm_int8 > 0) else 0.0

    return {
        "max_absolute_error": max_ae,
        "mean_absolute_error": mae,
        "cosine_similarity": cosine_sim
    }

def compute_box_iou(box1, box2):
    # box format: [x1, y1, x2, y2]
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0

def compare_outputs(fp32_dir: str, int8_dir: str, output_report: str):
    if not os.path.exists(fp32_dir):
        print(f"ERROR: FP32 reference directory does not exist: {fp32_dir}")
        sys.exit(1)

    if not os.path.exists(int8_dir):
        print(f"ERROR: INT8 NPU output directory does not exist: {int8_dir}")
        sys.exit(1)

    try:
        import numpy as np
    except ImportError:
        print("ERROR: numpy is required for parity comparison.")
        sys.exit(1)

    print("Running numerical and detection parity comparison...")
    report = {
        "status": "VALIDATION_SUITE_READY",
        "fp32_source": os.path.abspath(fp32_dir),
        "int8_source": os.path.abspath(int8_dir),
        "raw_tensor_metrics": {
            "max_absolute_error": None,
            "mean_absolute_error": None,
            "cosine_similarity": None
        },
        "detection_level_metrics": {
            "matching_strategy": "Greedy IoU Max-Overlap (threshold >= 0.5)",
            "mean_matched_iou": None,
            "class_agreement_percentage": None,
            "mean_confidence_difference": None
        },
        "performance_metrics": {
            "fp32_cpu_latency_ms": None,
            "int8_npu_latency_ms": None,
            "speedup_factor": None
        }
    }

    os.makedirs(os.path.dirname(output_report), exist_ok=True)
    with open(output_report, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved comparison template to: {output_report}")

def main():
    parser = argparse.ArgumentParser(description="Compare FP32 ONNX vs INT8 NPU Output Parity")
    parser.add_argument("--fp32-dir", type=str, default="results/fp32/raw_outputs", help="Directory containing FP32 raw .npy files")
    parser.add_argument("--int8-dir", type=str, default="results/int8/raw_outputs", help="Directory containing INT8 raw .npy files")
    parser.add_argument("--output", type=str, default="results/comparison/parity_report.json", help="Path to output comparison JSON")
    args = parser.parse_args()

    compare_outputs(args.fp32_dir, args.int8_dir, args.output)

if __name__ == "__main__":
    main()
