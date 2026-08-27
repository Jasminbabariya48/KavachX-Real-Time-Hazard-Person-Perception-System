#!/usr/bin/env python3
import subprocess

def test_default_output():
    cmd = (
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation/output_default && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:/home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        '/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator '
        '--model /home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        '--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '--output_dir /home/work_user2/kawachx_task/results/htp_compilation/output_default; '
        'echo "Exit code: $?"; '
        'ls -la /home/work_user2/kawachx_task/results/htp_compilation/output_default/'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== TEST DEFAULT OUTPUT ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    test_default_output()
