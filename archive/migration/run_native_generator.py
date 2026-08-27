#!/usr/bin/env python3
import subprocess

def run_gen():
    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        '/home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin '
        '> /home/work_user2/kawachx_task/results/htp_compilation/logs/native_gen_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation/logs/native_gen_stderr.log; '
        'echo "Generator exit code: $?"; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation/logs/native_gen_stdout.log /home/work_user2/kawachx_task/results/htp_compilation/logs/native_gen_stderr.log; '
        'ls -lh /home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== NATIVE GENERATOR OUTPUT ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run_gen()
