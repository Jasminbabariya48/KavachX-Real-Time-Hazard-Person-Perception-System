#!/usr/bin/env python3
import subprocess

def run_init():
    subprocess.run(['scp', 'scripts/tools/inspect_step7_model.cpp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/'])

    build_and_test = (
        'g++ -std=c++17 -O3 '
        '-I/home/devuser/qairt/2.47.0.260601/include/QNN '
        '/home/work_user2/kawachx_task/inspect_step7_model.cpp -ldl '
        '-o /home/work_user2/kawachx_task/inspect_step7_model && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'echo "=== TESTING 3class_calibrated_final.bin ==="; '
        '/home/work_user2/kawachx_task/inspect_step7_model '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '/home/work_user2/kawachx_task/models/3class_calibrated_final.bin; '
        'echo "=== TESTING kawachx_aihub_split.bin ==="; '
        '/home/work_user2/kawachx_task/inspect_step7_model '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '/home/work_user2/kawachx_task/models/kawachx_aihub_split.bin'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', build_and_test], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run_init()
