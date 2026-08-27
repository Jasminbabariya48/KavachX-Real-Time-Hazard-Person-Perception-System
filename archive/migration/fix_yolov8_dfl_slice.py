import onnx
from onnx import helper, TensorProto

def fix_onnx():
    model = onnx.load('/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx')
    graph = model.graph
    
    # Create Split node to replace Slice and Slice_1
    # Input: /model.22/dfl/Reshape_1_output_0
    # Outputs: /model.22/Slice_output_0, /model.22/Slice_1_output_0
    split_node = helper.make_node(
        'Split',
        inputs=['/model.22/dfl/Reshape_1_output_0'],
        outputs=['/model.22/Slice_output_0', '/model.22/Slice_1_output_0'],
        axis=1,
        name='/model.22/dfl/Split_dist'
    )
    
    # Filter out Slice and Slice_1 nodes
    new_nodes = []
    for node in graph.node:
        if node.name in ['/model.22/Slice', '/model.22/Slice_1']:
            if node.name == '/model.22/Slice':
                new_nodes.append(split_node)
            continue
        new_nodes.append(node)
        
    graph.ClearField('node')
    graph.node.extend(new_nodes)
    
    onnx.checker.check_model(model)
    onnx.save(model, '/home/work_user2/kawachx_task/models/model_fixed_split.onnx')
    print("Successfully exported model_fixed_split.onnx with clean Split node!")

if __name__ == "__main__":
    fix_onnx()
