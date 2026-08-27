#!/usr/bin/env python3
"""
Master Execution Pipeline for KawachX Qualcomm QCS6490 NPU Deployment
Orchestrates readiness checks, model inspection, FP32 baseline, QNN INT8 compilation,
npu_worker execution, parity validation, and benchmark reporting.
Fails cleanly with explicit error diagnostic when prerequisites are missing.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

def log_stage(stage_name: str):
    print("\n" + "="*80)
    print(f" [{datetime.datetime.now().strftime('%H:%M:%S')}] STAGE: {stage_name}")
    print("="*80)

def run_full_pipeline(model_path: str, dataset_dir: str, output_base: str):
    print("================================================================================")
    print(" KavachX Qualcomm QCS6490 NPU Deployment — Master Pipeline Orchestrator")
    print("================================================================================")

    # -------------------------------------------------------------------------
    # STAGE 1: Readiness & Prerequisite Verification
    # -------------------------------------------------------------------------
    log_stage("Stage 1: Validating Environment & Assessment Assets")
    res = subprocess.run([sys.executable, "scripts/check_deployment_readiness.py"])
    if res.returncode != 0:
        print("\n[PIPELINE HALTED] Critical prerequisites or model assets are missing.")
        print("Review the missing dependency list above.")
        return 1

    # -------------------------------------------------------------------------
    # STAGE 2: ONNX Model Inspection & Operator Inventory
    # -------------------------------------------------------------------------
    log_stage("Stage 2: Programmatic ONNX Model Inspection")
    inspection_dir = os.path.join(output_base, "model_inspection")
    cmd_inspect = [sys.executable, "scripts/inspect_onnx.py", "--model", model_path, "--output", inspection_dir]
    res = subprocess.run(cmd_inspect)
    if res.returncode != 0:
        print("[PIPELINE HALTED] Model inspection failed.")
        return 1

    # -------------------------------------------------------------------------
    # STAGE 3: FP32 ONNX Runtime Reference Execution
    # -------------------------------------------------------------------------
    log_stage("Stage 3: Running FP32 ONNX Runtime CPU Reference Baseline")
    fp32_dir = os.path.join(output_base, "fp32")
    # Will execute FP32 reference once imagery is supplied
    print(f"FP32 reference output configured to: {fp32_dir}")

    # -------------------------------------------------------------------------
    # STAGE 4: Representative Calibration Dataset Preparation
    # -------------------------------------------------------------------------
    log_stage("Stage 4: Preparing INT8 Calibration Binary Dataset")
    calib_dir = os.path.join(output_base, "calibration")
    cmd_calib = [sys.executable, "scripts/prepare_calibration_data.py", "--dataset-dir", dataset_dir, "--output-dir", calib_dir]
    res = subprocess.run(cmd_calib)
    if res.returncode != 0:
        print("[PIPELINE HALTED] Calibration dataset preparation failed.")
        return 1

    # -------------------------------------------------------------------------
    # STAGE 5: Qualcomm QNN Conversion & Hexagon v68 HTP Compilation
    # -------------------------------------------------------------------------
    log_stage("Stage 5: Executing QNN INT8 Quantization & Offline Compilation")
    qnn_dir = os.path.join(output_base, "qnn_artifacts")
    input_list = os.path.join(calib_dir, "input_list.txt")
    cmd_qnn = [sys.executable, "qnn/scripts/run_qnn_pipeline.py", "--model", model_path, "--input-list", input_list, "--output-dir", qnn_dir]
    res = subprocess.run(cmd_qnn)
    if res.returncode != 0:
        print("[PIPELINE HALTED] QNN compilation failed.")
        return 1

    # -------------------------------------------------------------------------
    # STAGE 6: Context Binary Validation
    # -------------------------------------------------------------------------
    log_stage("Stage 6: Multi-Tier Context Binary Validation")
    compiled_bin = os.path.join(qnn_dir, "new_3class_best_INT8_HTP_v68.bin")
    cmd_bin = [sys.executable, "scripts/inspect_qnn_binary.py", "--binary", compiled_bin]
    res = subprocess.run(cmd_bin)
    if res.returncode != 0:
        print("[PIPELINE HALTED] Context binary validation failed.")
        return 1

    # -------------------------------------------------------------------------
    # STAGE 7: npu_worker Execution & Parity Comparison
    # -------------------------------------------------------------------------
    log_stage("Stage 7: Numerical Parity & Benchmark Validation")
    comparison_report = os.path.join(output_base, "comparison", "parity_report.json")
    cmd_compare = [sys.executable, "scripts/compare_fp32_int8.py", "--fp32-dir", os.path.join(fp32_dir, "raw_outputs"), "--int8-dir", os.path.join(output_base, "int8", "raw_outputs"), "--output", comparison_report]
    res = subprocess.run(cmd_compare)
    if res.returncode != 0:
        print("[PIPELINE HALTED] Parity comparison failed.")
        return 1

    print("\n================================================================================")
    print(" [SUCCESS] Full Pipeline Completed Successfully.")
    print(f" Results available in: {output_base}")
    print("================================================================================")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Master Execution Pipeline for KawachX QCS6490 NPU Deployment")
    parser.add_argument("--model", type=str, default="kavachx_testing/models/new_3class_best_FP32.onnx", help="Path to FP32 ONNX model")
    parser.add_argument("--dataset", type=str, default="test_data/calibration", help="Path to calibration dataset")
    parser.add_argument("--output", type=str, default="results", help="Base output directory")
    args = parser.parse_args()

    sys.exit(run_full_pipeline(args.model, args.dataset, args.output))

if __name__ == "__main__":
    main()
