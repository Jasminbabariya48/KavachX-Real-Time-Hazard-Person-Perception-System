#!/usr/bin/env python3
import subprocess
import os

def run_stage2():
    cmd = (
        'cp /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8.bin /home/work_user2/kawachx_task/results/htp_compilation/model_lib/ && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:/home/work_user2/kawachx_task/results/htp_compilation/model_lib:$LD_LIBRARY_PATH; '
        '/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator '
        '--model /home/work_user2/kawachx_task/results/htp_compilation/model_lib/libmodel_qnn_int8.so '
        '--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '--binary_file kavachx_3class_int8_htp_v68.bin '
        '--output_dir /home/work_user2/kawachx_task/results/htp_compilation/output '
        '> /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stderr.log; '
        'echo "Context generator exit code: $?"; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stdout.log /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stderr.log; '
        'ls -la /home/work_user2/kawachx_task/results/htp_compilation/output/'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== STAGE 2 CONTEXT BINARY GENERATION ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run_stage2()
