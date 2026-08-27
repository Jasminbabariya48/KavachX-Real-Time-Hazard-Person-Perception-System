#!/usr/bin/env python3
import subprocess

def run_direct():
    subprocess.run(['scp', 'scripts/tools/generate_htp_binary.cpp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/htp_compilation/'])

    build_and_run = (
        'g++ -std=c++17 -O3 '
        '-I/home/devuser/qairt/2.47.0.260601/include/QNN '
        '-I/home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni '
        '/home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/QnnWrapperUtils.cpp '
        '/home/devuser/qairt/2.47.0.260601/share/QNN/converter/jni/linux/QnnModelPal.cpp '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary.cpp -ldl '
        '-o /home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/results/htp_compilation/generate_htp_binary '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/work_user2/kawachx_task/results/htp_compilation/build_native/libs/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        '/home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin '
        '> /home/work_user2/kawachx_task/results/htp_compilation/logs/direct_gen_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation/logs/direct_gen_stderr.log; '
        'echo "Return Code: $?"; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation/logs/direct_gen_stdout.log /home/work_user2/kawachx_task/results/htp_compilation/logs/direct_gen_stderr.log; '
        'ls -lh /home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', build_and_run], capture_output=True, text=True)
    print("=== DIRECT HTP GENERATION OUTPUT ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run_direct()
