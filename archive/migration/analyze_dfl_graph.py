import onnx
from onnx import helper, shape_inference
import json
import os

def analyze_dfl():
    model_path = '/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx'
    model = onnx.load(model_path)
    graph = model.graph
    
    # Analyze nodes around the head (model.22)
    head_nodes = []
    dfl_nodes = []
    incompatible_nodes = []
    
    for node in graph.node:
        if 'model.22' in node.name or 'dfl' in node.name:
            node_info = {
                "node_name": node.name,
                "op_type": node.op_type,
                "inputs": list(node.input),
                "outputs": list(node.output),
                "attributes": {attr.name: str(helper.get_attribute_value(attr)) for attr in node.attribute}
            }
            head_nodes.append(node_info)
            
            if 'dfl' in node.name or 'Slice' in node.name or node.op_type in ['Slice', 'Div', 'Sub', 'Add', 'Softmax']:
                reason = ""
                handling = ""
                if node.op_type == 'Slice':
                    reason = "Dynamic slice start/end indices computed at runtime from tensor multiplications are not statically determinable by Qualcomm Hexagon v68 HTP compiler in INT8 mode."
                    handling = "Exclude DFL sub-graph from NPU graph; expose raw bounding box distribution [1, 64, 8400] and class probabilities [1, 3, 8400] directly as model outputs. Perform DFL decoding in C++ worker."
                elif 'dfl' in node.name:
                    reason = "Distribution Focal Loss (DFL) decode layer consists of Softmax over 16 bins and Conv/Slice layers that execute much more efficiently on CPU/SIMD in post-processing than on NPU vector pipelines."
                    handling = "Move to C++ worker post-processing."
                
                if reason:
                    node_info["reason_for_incompatibility"] = reason
                    node_info["proposed_handling"] = handling
                    incompatible_nodes.append(node_info)

    # Identify split points:
    # 1. Box regression output: /model.22/Concat_output_0 (shape: [1, 64, 8400])
    # 2. Class probabilities output: /model.22/Sigmoid_output_0 (shape: [1, 3, 8400])
    split_analysis = {
        "model_file": model_path,
        "input_tensor": {
            "name": graph.input[0].name,
            "shape": [d.dim_value for d in graph.input[0].type.tensor_type.shape.dim]
        },
        "original_output": {
            "name": graph.output[0].name,
            "shape": [d.dim_value for d in graph.output[0].type.tensor_type.shape.dim]
        },
        "box_regression_tensor": {
            "tensor_name": "/model.22/Concat_output_0",
            "source_node": "/model.22/Concat",
            "shape": [1, 64, 8400],
            "description": "Concatenated multi-scale bounding box regression distributions (64 channels = 16 bins * 4 coordinates)."
        },
        "class_score_tensor": {
            "tensor_name": "/model.22/Sigmoid_output_0",
            "source_node": "/model.22/Sigmoid",
            "shape": [1, 3, 8400],
            "description": "Sigmoid-activated class probabilities across all 8400 anchor positions for 3 classes."
        },
        "incompatible_dfl_slice_nodes": incompatible_nodes,
        "total_head_nodes": len(head_nodes),
        "total_incompatible_nodes": len(incompatible_nodes),
        "proposed_split_strategy": "Expose /model.22/Concat_output_0 ([1,64,8400]) and /model.22/Sigmoid_output_0 ([1,3,8400]) as top-level graph outputs. Remove downstream DFL decoding nodes (/model.22/dfl/*, /model.22/Slice*, /model.22/Sub*, /model.22/Add*, /model.22/Div*, /model.22/Concat_6, /model.22/Mul_2, /model.22/Concat_7)."
    }

    os.makedirs('/home/work_user2/kawachx_task/results/htp_compilation/reports', exist_ok=True)
    with open('/home/work_user2/kawachx_task/results/htp_compilation/reports/dfl_graph_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(split_analysis, f, indent=2)
    print("Graph analysis written to /home/work_user2/kawachx_task/results/htp_compilation/reports/dfl_graph_analysis.json")

if __name__ == "__main__":
    analyze_dfl()
