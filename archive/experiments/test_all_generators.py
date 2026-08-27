#!/usr/bin/env python3
import subprocess

generators = [
    "/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator",
    "/home/devuser/qairt/2.47.0.260601/bin/aarch64-oe-linux-gcc11.2/qnn-context-binary-generator",
    "/home/devuser/qairt/2.47.0.260601/bin/aarch64-oe-linux-gcc9.3/qnn-context-binary-generator",
]

for gen in generators:
    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:/home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        f'{gen} '
        '--model /home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        '--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '--binary_file kavachx_3class_int8_htp_v68.bin '
        '--output_dir /home/work_user2/kawachx_task/results/htp_compilation/output'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(f"=== TEST GENERATOR: {gen} ===")
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    print("RC:", res.returncode)
