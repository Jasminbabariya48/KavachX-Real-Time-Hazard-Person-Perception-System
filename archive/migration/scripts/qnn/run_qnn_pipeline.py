#!/usr/bin/env python3
"""
Qualcomm QNN INT8 Compilation Pipeline Manager for QCS6490 Hexagon v68 HTP
Orchestrates ONNX conversion, INT8 quantization, and offline context binary compilation.
Reports QNN_SDK_NOT_FOUND and marks execution as BLOCKED if the Qualcomm toolchain is missing.
"""

import argparse
import os
import shutil
import subprocess
import sys

def check_qnn_sdk():
    qnn_sdk_root = os.environ.get("QNN_SDK_ROOT")
    if not qnn_sdk_root or not os.path.exists(qnn_sdk_root):
        # Check standard path search
        converter = shutil.which("qnn-onnx-converter")
        generator = shutil.which("qnn-context-binary-generator")
        if not converter or not generator:
            return False, None
        return True, "SYSTEM_PATH"
    return True, qnn_sdk_root

def run_pipeline(onnx_model: str, input_list: str, output_dir: str, target_arch: str = "v68"):
    print("=================================================================")
    print(" Qualcomm QNN / QCS6490 HTP v68 INT8 Compilation Manager")
    print("=================================================================")

    sdk_available, sdk_path = check_qnn_sdk()
    if not sdk_available:
        print("STATUS: BLOCKED")
        print("ERROR: QNN_SDK_NOT_FOUND")
        print("Reason: Qualcomm QAIRT/QNN SDK is not installed or QNN_SDK_ROOT is not set.")
        print("Instructions:")
        print(" 1. Download Qualcomm QAIRT / QNN SDK (2.x or later).")
        print(" 2. Set export QNN_SDK_ROOT=/path/to/qualcomm/qnn-sdk")
        print(" 3. Source environment: source ${QNN_SDK_ROOT}/bin/envsetup.sh")
        return False

    print(f"Qualcomm QNN SDK detected at: {sdk_path}")
    print(f"Target Architecture: Hexagon HTP {target_arch} (Qualcomm QCS6490)")

    if not os.path.exists(onnx_model):
        print(f"STATUS: BLOCKED - ONNX model not found at: {onnx_model}")
        return False

    if not os.path.exists(input_list):
        print(f"STATUS: BLOCKED - Calibration input list not found at: {input_list}")
        return False

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Model Conversion & Quantization (qnn-onnx-converter)
    qnn_model_cpp = os.path.join(output_dir, "model_qnn_int8.cpp")
    qnn_model_bin = os.path.join(output_dir, "model_qnn_int8.bin")
    
    cmd_convert = [
        "qnn-onnx-converter",
        "--input_network", onnx_model,
        "--output_path", qnn_model_cpp,
        "--input_list", input_list,
        "--act_bw", "8",
        "--bias_bw", "32",
        "--weight_bw", "8"
    ]
    print(f"\n[Stage 1] Converting ONNX to Quantized QNN Model: {' '.join(cmd_convert)}")
    res = subprocess.run(cmd_convert, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Stage 1 FAILED:\n{res.stderr}")
        return False

    # Step 2: Generate Offline Context Binary (qnn-context-binary-generator)
    final_bin = os.path.join(output_dir, "new_3class_best_INT8_HTP_v68.bin")
    cmd_compile = [
        "qnn-context-binary-generator",
        "--backend", "libQnnHtp.so",
        "--model", qnn_model_bin,
        "--binary_file", final_bin,
        "--htp_arch", target_arch,
        "--config_file", "qnn/config/htp_config.json"
    ]
    print(f"\n[Stage 2] Compiling Hexagon HTP v68 Context Binary: {' '.join(cmd_compile)}")
    res = subprocess.run(cmd_compile, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Stage 2 FAILED:\n{res.stderr}")
        return False

    print(f"\n[SUCCESS] Compiled QNN Context Binary generated at: {final_bin}")
    return True

def main():
    parser = argparse.ArgumentParser(description="QNN INT8 Pipeline Runner for QCS6490 HTP")
    parser.add_argument("--model", type=str, default="kavachx_testing/models/new_3class_best_FP32.onnx", help="Input ONNX model path")
    parser.add_argument("--input-list", type=str, default="results/calibration/input_list.txt", help="Calibration input_list.txt")
    parser.add_argument("--output-dir", type=str, default="qnn/artifacts", help="Output directory for compiled artifacts")
    parser.add_argument("--target-arch", type=str, default="v68", help="Hexagon HTP target architecture version")
    args = parser.parse_args()

    run_pipeline(args.model, args.input_list, args.output_dir, args.target_arch)

if __name__ == "__main__":
    main()
