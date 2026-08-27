import onnx

m = onnx.load('/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx')
print("=== GRAPH OUTPUTS ===")
for o in m.graph.output:
    dims = [d.dim_value for d in o.type.tensor_type.shape.dim]
    print(f"Name: {o.name}, Shape: {dims}")

print("\n=== LAST 20 NODES ===")
for n in m.graph.node[-20:]:
    print(f"{n.op_type:10s} | {n.name:35s} | in: {n.input} -> out: {n.output}")
