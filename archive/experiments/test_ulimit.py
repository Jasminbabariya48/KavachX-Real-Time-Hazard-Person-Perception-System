#!/usr/bin/env python3
import subprocess

def test_ulimit():
    cmd = (
        'ulimit -s 65536; '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        '/home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== ULIMIT TEST OUTPUT ===")
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    print("RC:", res.returncode)

if __name__ == "__main__":
    test_ulimit()
