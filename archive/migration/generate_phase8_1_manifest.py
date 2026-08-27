#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess

def get_remote_sha256(filepath):
    cmd = f"sha256sum {filepath} 2>/dev/null | awk '{{print $1}}'"
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    return res.stdout.strip()

def get_remote_filesize(filepath):
    cmd = f"stat -c %s {filepath} 2>/dev/null"
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    return int(res.stdout.strip()) if res.stdout.strip().isdigit() else 0

def generate_manifest():
    os.makedirs('results/step8_production/reports', exist_ok=True)
    
    files_to_hash = [
        ('/home/work_user2/kawachx_task/models/3class_calibrated_final.bin', 'models/3class_calibrated_final.bin'),
        ('/home/work_user2/kawachx_task/models/kawachx_aihub_split.bin', 'models/kawachx_aihub_split.bin'),
        ('/home/work_user2/kawachx_task/models/new_3class_best_FP32_htp_split.onnx', 'models/new_3class_best_FP32_htp_split.onnx'),
        ('/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx', 'models/new_3class_best_FP32.onnx'),
        ('/home/work_user2/kawachx_task/results/qnn_int8_split_conversion/generated/model_split_qnn_int8.bin', 'results/qnn_int8_split_conversion/generated/model_split_qnn_int8.bin'),
        ('/home/work_user2/kawachx_task/npu_worker/kawach_worker', 'src/npu_worker/kawach_worker')
    ]
    
    checksums = []
    artifacts_manifest = {}
    
    for rpath, lpath in files_to_hash:
        sha = get_remote_sha256(rpath)
        sz = get_remote_filesize(rpath)
        checksums.append(f"{sha}  {lpath}")
        artifacts_manifest[lpath] = {
            "remote_path": rpath,
            "sha256": sha,
            "size_bytes": sz
        }
        print(f"{lpath}: {sha} ({sz} bytes)")
        
    with open('results/step8_production/checksums.sha256', 'w') as f:
        f.write("\n".join(checksums) + "\n")
        
    manifest = {
        "production_release": "KavachX NPU v1.0 Production",
        "target_hardware": {
            "board": "Radxa Dragon Q6490 / Qualcomm QCS6490",
            "arch": "aarch64",
            "npu_dsp": "Qualcomm Hexagon v68 HTP",
            "qairt_sdk_version": "2.47.0.260601",
            "fastrpc_device": "/dev/fastrpc-cdsp (GID 993 render, 0660)"
        },
        "frozen_models": artifacts_manifest,
        "input_contract": {
            "name": "images",
            "shape": [1, 3, 640, 640],
            "layout": "NCHW",
            "dtype": "QNN_DATATYPE_UFIXED_POINT_8 (uint8)",
            "quantization": {
                "scale": 0.003921569,
                "offset": 0
            },
            "preprocessing": "aspect-preserving letterbox to 640x640, RGB, [0, 255] uint8 pixels"
        },
        "output_contracts": [
            {
                "name": "output_0",
                "shape": [1, 64, 8400],
                "dtype": "QNN_DATATYPE_UFIXED_POINT_8 (uint8, 537600 bytes)",
                "quantization": {
                    "scale": 0.1574602,
                    "offset": -191
                },
                "semantics": "16-bin DFL bounding box distribution across 8400 anchor grid locations"
            },
            {
                "name": "output_1",
                "shape": [1, 3, 8400],
                "dtype": "QNN_DATATYPE_UFIXED_POINT_8 (uint8, 25200 bytes)",
                "quantization": {
                    "scale": 0.00390625,
                    "offset": 0
                },
                "semantics": "Sigmoid class probabilities for fire (0), smoke (1), person (2)"
            }
        ],
        "post_processing": {
            "type": "CPU vectorized DFL decode + anchor projection + NMS",
            "latency_budget_ms": "< 1.0 ms",
            "output_tensor": "[1, 7, 8400] float32 (cx, cy, w, h, cls0, cls1, cls2)"
        }
    }
    
    with open('results/step8_production/manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
        
    print("Manifest and checksums successfully generated in results/step8_production/")

if __name__ == "__main__":
    generate_manifest()
