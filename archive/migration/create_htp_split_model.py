import onnx
from onnx import helper, TensorProto, shape_inference
import json
import os

def create_split_model():
    orig_path = '/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx'
    out_path = '/home/work_user2/kawachx_task/models/new_3class_best_FP32_htp_split.onnx'
    
    print(f"Loading {orig_path}...")
    model = onnx.load(orig_path)
    graph = model.graph
    
    # We want outputs:
    # 1. '/model.22/Concat_output_0' -> shape [1, 64, 8400]
    # 2. '/model.22/Sigmoid_output_0' -> shape [1, 3, 8400]
    
    target_output_names = {'/model.22/Concat_output_0', '/model.22/Sigmoid_output_0'}
    
    # Trace dependencies backward from target outputs to keep all necessary nodes and initializers
    needed_tensors = set(target_output_names)
    nodes_to_keep = []
    
    # Reverse iteration to find all ancestor nodes
    for node in reversed(graph.node):
        # If any output of this node is in needed_tensors, keep this node and add its inputs
        if any(out in needed_tensors for out in node.output):
            nodes_to_keep.append(node)
            for inp in node.input:
                if inp:
                    needed_tensors.add(inp)
                    
    nodes_to_keep.reverse()
    
    # Filter initializers
    initializers_to_keep = [init for init in graph.initializer if init.name in needed_tensors]
    
    # Define new outputs
    boxes_out = helper.make_tensor_value_info(
        '/model.22/Concat_output_0',
        TensorProto.FLOAT,
        [1, 64, 8400]
    )
    scores_out = helper.make_tensor_value_info(
        '/model.22/Sigmoid_output_0',
        TensorProto.FLOAT,
        [1, 3, 8400]
    )
    
    new_graph = helper.make_graph(
        nodes=nodes_to_keep,
        name='kavachx_3class_split',
        inputs=list(graph.input),
        outputs=[boxes_out, scores_out],
        initializer=initializers_to_keep
    )
    
    new_model = helper.make_model(new_graph, producer_name='kavachx_split_generator', opset_imports=model.opset_import)
    
    # Check model
    onnx.checker.check_model(new_model)
    onnx.save(new_model, out_path)
    print(f"Saved split model to {out_path} (Nodes: {len(nodes_to_keep)}, Initializers: {len(initializers_to_keep)})")

if __name__ == "__main__":
    create_split_model()
