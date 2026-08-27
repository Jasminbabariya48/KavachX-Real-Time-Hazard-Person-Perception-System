import os
import sys
import json
import subprocess

def inspect_bin(path):
    print("==================================================")
    print("Inspecting Binary:", path)
    print("==================================================")
    if not os.path.exists(path):
        print("ERROR: File not found:", path)
        return {"exists": False}

    size = os.path.getsize(path)
    print(f"File Size: {size} bytes ({size / (1024*1024):.2f} MB)")

    with open(path, "rb") as f:
        data = f.read()

    # Look for QNN strings inside the binary
    qnn_strings = []
    current_str = []
    for byte in data:
        if 32 <= byte <= 126:
            current_str.append(chr(byte))
        else:
            if len(current_str) >= 4:
                s = "".join(current_str)
                if any(k in s.lower() for k in ["qnn", "htp", "v68", "hexagon", "graph", "output", "images", "input", "tensor", "conv", "yolo", "detect", "layer"]):
                    qnn_strings.append(s)
            current_str = []

    print(f"Total relevant strings found: {len(qnn_strings)}")
    unique_sample = list(dict.fromkeys(qnn_strings))[:30]
    for s in unique_sample:
        print(" -", s)

    return {
        "exists": True,
        "size_bytes": size,
        "sample_strings": unique_sample
    }

print("--- Inspecting Model 1: 3class_calibrated_final.bin ---")
res1 = inspect_bin("/home/work_user2/kawachx_task/models/3class_calibrated_final.bin")

print("\n--- Inspecting Model 2: kawachx_aihub_split.bin ---")
res2 = inspect_bin("/home/work_user2/kawachx_task/models/kawachx_aihub_split.bin")
