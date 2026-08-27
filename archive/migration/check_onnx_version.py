#!/usr/bin/env python3
import subprocess

def run_remote(cmd):
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
    return res

run_remote('python3 -c "import onnx, onnx.version; print(onnx.__version__, onnx.version.version)" 2>&1')
