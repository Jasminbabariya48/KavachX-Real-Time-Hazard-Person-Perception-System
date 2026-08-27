#!/usr/bin/env python3
"""
Deployment Readiness & Dependency Checker for Qualcomm QCS6490 HTP
Evaluates the existence of all physical assets, toolchains, and hardware targets.
"""

import os
import shutil
import sys

def check_readiness():
    print("================================================================")
    print(" Qualcomm QCS6490 NPU Deployment Readiness Checker")
    print("================================================================")

    checks = [
        ("Source ONNX Model", "kavachx_testing/models/new_3class_best_FP32.onnx", os.path.exists("kavachx_testing/models/new_3class_best_FP32.onnx")),
        ("Existing Context Binary #1", "kavachx_testing/models/model1.bin", len([f for f in os.listdir("kavachx_testing/models") if f.endswith(".bin")]) > 0 if os.path.exists("kavachx_testing/models") else False),
        ("Calibration Dataset", "test_data/calibration", os.path.exists("test_data/calibration") and len(os.listdir("test_data/calibration")) > 0 if os.path.exists("test_data/calibration") else False),
        ("Test Imagery", "test_data/images", os.path.exists("test_data/images") and len(os.listdir("test_data/images")) > 0 if os.path.exists("test_data/images") else False),
        ("Qualcomm QAIRT/QNN SDK", "QNN_SDK_ROOT / System PATH", os.environ.get("QNN_SDK_ROOT") is not None or shutil.which("qnn-onnx-converter") is not None),
        ("QNN Converter Tool", "qnn-onnx-converter", shutil.which("qnn-onnx-converter") is not None),
        ("QNN Compiler Tool", "qnn-context-binary-generator", shutil.which("qnn-context-binary-generator") is not None),
        ("npu_worker Source Code", "npu_worker/src/npu_worker.cpp", os.path.exists("npu_worker/src/npu_worker.cpp")),
        ("Target QCS6490 Hardware", "Connected ADB/Device", False) # Local host is x86_64 Windows
    ]

    all_passed = True
    missing_items = []

    for name, location, passed in checks:
        status_str = "[PASS]" if passed else "[FAIL - MISSING]"
        print(f" {status_str:<18} | {name:<28} | {location}")
        if not passed:
            all_passed = False
            missing_items.append(name)

    print("================================================================")
    if all_passed:
        print("OVERALL STATUS: READY")
        print("All dependencies and assets are verified.")
        return 0
    else:
        print("OVERALL STATUS: BLOCKED")
        print(f"Missing {len(missing_items)} critical requirement(s):")
        for item in missing_items:
            print(f" - {item}")
        return 1

if __name__ == "__main__":
    sys.exit(check_readiness())
