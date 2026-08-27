#!/usr/bin/env python3
import subprocess

def test_gen(extra_args=""):
    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:/home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        f'/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator '
        f'--model /home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        f'--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        f'--binary_file kavachx_3class_int8_htp_v68.bin '
        f'--output_dir /home/work_user2/kawachx_task/results/htp_compilation/output {extra_args}'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(f"=== TEST WITH ARGS: '{extra_args}' ===")
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    print("RETURN CODE:", res.returncode)

test_gen("--htp_socs qcs6490")
