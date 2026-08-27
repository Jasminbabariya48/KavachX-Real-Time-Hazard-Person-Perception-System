#!/usr/bin/env python3
import subprocess

def test_onnxsim():
    cmd = (
        'python3 -c "'
        'import onnx, onnxsim\n'
        'model = onnx.load(\'/home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx\')\n'
        'model_simp, check = onnxsim.simplify(model)\n'
        'print(\'onnxsim check:\', check)\n'
        'onnx.save(model_simp, \'/home/work_user2/kawachx_task/models/model_simplified.onnx\')\n'
        '" && '
        'python3 -c "'
        'import onnx\n'
        'm = onnx.load(\'/home/work_user2/kawachx_task/models/model_simplified.onnx\')\n'
        'print(\'Outputs:\', [o.name for o in m.graph.output])\n'
        'for n in m.graph.node[-10:]:\n'
        '    print(n.op_type, n.name, n.input, n.output)\n'
        '"'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== ONNX SIMPLIFY ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    test_onnxsim()
