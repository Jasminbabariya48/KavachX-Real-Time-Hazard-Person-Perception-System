#!/usr/bin/env python3
"""
Qualcomm QNN Context Binary Inspector
Implements a 6-Level Multi-Tier Verification Model:
 - Level 0: File existence and access check.
 - Level 1: Basic file integrity and minimum byte size (>= 64 bytes).
 - Level 2: Header sanity and signature verification (e.g. QNN context markers).
 - Level 3: QNN Tooling / Runtime recognition (Requires QNN SDK / qnn-context-binary-generator).
 - Level 4: Graph deserialization and instantiation.
 - Level 5: Physical Hexagon HTP v68 NPU execution.
"""

import argparse
import os
import sys

def inspect_binary(bin_path: str):
    print("================================================================")
    print(" Qualcomm QNN Context Binary Multi-Tier Inspector")
    print("================================================================")

    # LEVEL 0: File Exists
    if not os.path.exists(bin_path):
        print(f"[LEVEL 0 - FAIL] ERROR: QNN_BINARY_NOT_FOUND - File not found: {bin_path}")
        sys.exit(1)
    print(f"[LEVEL 0 - PASS] File exists: {os.path.abspath(bin_path)}")

    # LEVEL 1: File Integrity
    file_size = os.path.getsize(bin_path)
    print(f"File Size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
    if file_size < 64:
        print("[LEVEL 1 - FAIL] File size too small to contain valid QNN context headers.")
        sys.exit(1)
    print("[LEVEL 1 - PASS] File size exceeds minimum header threshold.")

    # LEVEL 2: Header Sanity & Signatures
    with open(bin_path, "rb") as f:
        header = f.read(128)
    print(f"Header Preview (hex): {header[:32].hex()}")

    detected_markers = []
    with open(bin_path, "rb") as f:
        sample_chunk = f.read(min(file_size, 2 * 1024 * 1024))
        for marker in [b"QnnContext", b"QnnGraph", b"HTP", b"v68", b"QNN", b"libQnnHtp"]:
            if marker in sample_chunk:
                detected_markers.append(marker.decode('latin1', errors='ignore'))

    if detected_markers:
        print(f"[LEVEL 2 - PASS] Recognized QNN signature markers: {', '.join(detected_markers)}")
    else:
        print("[LEVEL 2 - WARNING] No plaintext QNN markers detected in initial 2MB (Binary may be encrypted or pure bytecode).")

    # LEVEL 3: QNN SDK Tooling Validation
    qnn_sdk_root = os.environ.get("QNN_SDK_ROOT")
    if not qnn_sdk_root:
        print("[LEVEL 3 - BLOCKED] QNN SDK not found in environment. Binary recognition by libQnnHtp is unverified.")
    else:
        print(f"[LEVEL 3 - READY] QNN SDK detected at {qnn_sdk_root}. Ready for runtime verification.")

    # LEVEL 4 & 5: Deserialization & NPU Execution
    print("[LEVEL 4 - BLOCKED] Graph instantiation requires npu_worker runtime with QNN C API.")
    print("[LEVEL 5 - BLOCKED] NPU hardware execution requires physical Qualcomm QCS6490 target device.")
    print("================================================================")

def main():
    parser = argparse.ArgumentParser(description="Inspect QNN Context Binary (.bin) across 6 Verification Levels")
    parser.add_argument("--binary", type=str, required=True, help="Path to .bin context binary")
    args = parser.parse_args()

    inspect_binary(args.binary)

if __name__ == "__main__":
    main()
