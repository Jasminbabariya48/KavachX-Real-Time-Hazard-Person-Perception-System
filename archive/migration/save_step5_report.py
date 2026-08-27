#!/usr/bin/env python3
import subprocess
import os
import json

def sync_and_save():
    os.makedirs('results/htp_compilation/logs', exist_ok=True)
    os.makedirs('results/htp_compilation/reports', exist_ok=True)
    
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/htp_compilation/logs/*', 'results/htp_compilation/logs/'])

    report = {
        "step": "Step 5 — HTP v68 Compilation",
        "qairt_sdk_version": "2.47.0.260601",
        "converter_path": "/home/devuser/qairt/2.47.0.260601/bin/x86_64-linux-clang/qnn-onnx-converter",
        "context_binary_generator": "/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator",
        "input_qnn_model": "results/qnn_int8_conversion/generated/model_qnn_int8.bin",
        "model_shared_library": "results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so",
        "target_backend": "Qualcomm Hexagon v68 HTP (libQnnHtp.so)",
        "graph_name": "model_qnn_int8",
        "input_tensor": {
            "name": "images",
            "shape": [1, 3, 640, 640],
            "dtype": "QNN_DATATYPE_UFIXED_POINT_8"
        },
        "output_tensor": {
            "name": "output0",
            "shape": [1, 7, 8400],
            "dtype": "QNN_DATATYPE_UFIXED_POINT_8"
        },
        "compilation_status": "BLOCKED",
        "exit_code": 139,
        "stages": {
            "graph_composition": "PASS",
            "graph_preparation_initializing": "PASS",
            "graph_optimizations": "PASS (1086259 us)",
            "post_graph_optimization": "PASS (41224 us)",
            "context_binary_serialization": "FAIL (Segmentation Fault 139)"
        },
        "root_cause_analysis": "The monolithic YOLOv8 decode head in model_qnn_int8 contains dynamic Slice operations (/model.22/Slice, /model.22/Slice_1) whose start/end indices are dynamically computed at runtime. The Qualcomm Hexagon v68 HTP offline compiler requires static tensor slicing or pre-decode split outputs ([1, 64, 8400] and [1, 3, 8400]), causing a segmentation fault in libQnnHtpPrepare.so during machine code emission.",
        "log_files": [
            "results/htp_compilation/logs/direct_gen_stdout.log",
            "results/htp_compilation/logs/direct_gen_stderr.log",
            "results/htp_compilation/logs/context_gen_stdout.log",
            "results/htp_compilation/logs/context_gen_stderr.log"
        ]
    }
    
    with open('results/htp_compilation/reports/compilation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print("Compilation report saved to results/htp_compilation/reports/compilation_report.json")

if __name__ == "__main__":
    sync_and_save()
