#!/usr/bin/env python3
import subprocess

def test_worker(adsp_path):
    print(f"=== Testing ADSP_LIBRARY_PATH: '{adsp_path}' ===")
    cmd = f'export ADSP_LIBRARY_PATH="{adsp_path}"; timeout 5 /home/work_user2/kawachx_task/npu_worker/kawach_worker --backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so --system /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so --model /home/work_user2/kawachx_task/models/3class_calibrated_final.bin --socket /tmp/test_adsp.sock'
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    print("EXIT CODE:", res.returncode)
    return res

test_worker("/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp")
