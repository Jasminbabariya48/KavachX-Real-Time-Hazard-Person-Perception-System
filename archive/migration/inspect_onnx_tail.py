#!/usr/bin/env python3
import onnx

def inspect_onnx():
    model = onnx.load("models/new_3class_best_FP32.onnx")
    print("Graph outputs:")
    for out in model.graph.output:
        print(" ", out.name, [dim.dim_value for dim in out.type.tensor_type.shape.dim])
        
    print("\nLast 20 nodes in ONNX graph:")
    for node in model.graph.node[-20:]:
        print(f"  Node: {node.name}, Op: {node.op_type}, Inputs: {node.input}, Outputs: {node.output}")

if __name__ == "__main__":
    inspect_onnx()
