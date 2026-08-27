#!/usr/bin/env python3
"""
ONNX Model Inspector for Qualcomm QNN / QCS6490 HTP Deployment
Inspects model metadata, inputs, outputs, tensor shapes, and operators.
Fails cleanly with MODEL_NOT_FOUND if the specified model does not exist.
"""

import argparse
import json
import os
import sys

def inspect_model(model_path: str, output_dir: str):
    if not os.path.exists(model_path):
        print(f"ERROR: MODEL_NOT_FOUND - Model file not found at: {model_path}")
        sys.exit(1)

    try:
        import onnxruntime as ort
    except ImportError:
        print("ERROR: onnxruntime is required for model inspection.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading ONNX model: {model_path}")
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    session = ort.InferenceSession(model_path, session_options, providers=['CPUExecutionProvider'])

    # Inspect Inputs
    inputs_meta = []
    for inp in session.get_inputs():
        inputs_meta.append({
            "name": inp.name,
            "type": inp.type,
            "shape": inp.shape,
            "dynamic_axes": [i for i, dim in enumerate(inp.shape) if isinstance(dim, str) or dim is None or dim < 0]
        })

    # Inspect Outputs
    outputs_meta = []
    for out in session.get_outputs():
        outputs_meta.append({
            "name": out.name,
            "type": out.type,
            "shape": out.shape,
            "dynamic_axes": [i for i, dim in enumerate(out.shape) if isinstance(dim, str) or dim is None or dim < 0]
        })

    metadata = {
        "model_path": os.path.abspath(model_path),
        "file_size_bytes": os.path.getsize(model_path),
        "runtime": "onnxruntime",
        "providers": session.get_providers(),
        "inputs": inputs_meta,
        "outputs": outputs_meta
    }

    metadata_file = os.path.join(output_dir, "model_metadata.json")
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved model metadata to: {metadata_file}")

    # Inspect Operators if onnx package available
    operator_inventory = {
        "model": model_path,
        "operators": []
    }
    try:
        import onnx
        onnx_model = onnx.load(model_path)
        op_counts = {}
        for node in onnx_model.graph.node:
            op_counts[node.op_type] = op_counts.get(node.op_type, 0) + 1
        
        operator_inventory["opset_version"] = onnx_model.opset_import[0].version if onnx_model.opset_import else "Unknown"
        operator_inventory["producer_name"] = onnx_model.producer_name
        operator_inventory["producer_version"] = onnx_model.producer_version
        operator_inventory["total_nodes"] = len(onnx_model.graph.node)
        operator_inventory["operators"] = [{"op_type": k, "count": v} for k, v in sorted(op_counts.items(), key=lambda x: x[1], reverse=True)]
    except ImportError:
        operator_inventory["note"] = "Standard onnx package not installed; detailed graph node extraction skipped."

    op_file = os.path.join(output_dir, "operator_inventory.json")
    with open(op_file, "w") as f:
        json.dump(operator_inventory, f, indent=2)
    print(f"Saved operator inventory to: {op_file}")

def main():
    parser = argparse.ArgumentParser(description="Inspect ONNX Model Metadata for QNN HTP Deployment")
    parser.add_argument("--model", type=str, default="kavachx_testing/models/new_3class_best_FP32.onnx", help="Path to ONNX model")
    parser.add_argument("--output", type=str, default="results/model_inspection", help="Output directory for metadata")
    args = parser.parse_args()

    inspect_model(args.model, args.output)

if __name__ == "__main__":
    main()
