#!/usr/bin/env python3
import subprocess
import os

def run_htp_context_generator():
    cmd = (
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation/output && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:/home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        '/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator '
        '--model /home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        '--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '--binary_file kavachx_3class_int8_htp_v68.bin '
        '--output_dir /home/work_user2/kawachx_task/results/htp_compilation/output '
        '> /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stderr.log; '
        'echo "Context generator exit code: $?"; '
        'echo "=== LOGS ==="; cat /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stdout.log /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stderr.log; '
        'echo "=== OUTPUT DIRECTORY ==="; ls -lh /home/work_user2/kawachx_task/results/htp_compilation/output/'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== HTP CONTEXT BINARY GENERATION ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run_htp_context_generator()
