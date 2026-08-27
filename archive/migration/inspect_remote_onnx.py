#!/usr/bin/env python3
import subprocess

def inspect():
    code = """
import onnx
m = onnx.load('/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx')
print("=== OUTPUTS ===")
for o in m.graph.output:
    dims = [d.dim_value for d in o.type.tensor_type.shape.dim]
    print(f"Name: {o.name}, Shape: {dims}")

print("\\n=== LAST 15 NODES ===")
for n in m.graph.node[-15:]:
    print(f"{n.op_type:10s} | {n.name:35s} | in: {n.input} -> out: {n.output}")
"""
    cmd = f'python3 -c "{code}"'
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    inspect()
