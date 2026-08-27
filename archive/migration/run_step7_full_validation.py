#!/usr/bin/env python3
import subprocess
import os

def run_step7():
    # 1. Copy cpp and build on target
    subprocess.run(['scp', 'scripts/tools/execute_htp_inference.cpp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/'])
    
    build_and_run = (
        'mkdir -p /home/work_user2/kawachx_task/results/step7_htp_execution/{raw,reports,detections} && '
        'g++ -std=c++17 -O3 '
        '-I/home/devuser/qairt/2.47.0.260601/include/QNN '
        '/home/work_user2/kawachx_task/execute_htp_inference.cpp -ldl '
        '-o /home/work_user2/kawachx_task/execute_htp_inference && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'echo "=== INFERENCE 1: fire.raw ==="; '
        '/home/work_user2/kawachx_task/execute_htp_inference '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '/home/work_user2/kawachx_task/models/3class_calibrated_final.bin '
        '/home/work_user2/kawachx_task/results/qnn_int8_conversion/input/fire.raw '
        '/home/work_user2/kawachx_task/results/step7_htp_execution/raw/fire; '
        'echo "=== INFERENCE 2: fire_2.raw ==="; '
        '/home/work_user2/kawachx_task/execute_htp_inference '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '/home/work_user2/kawachx_task/models/3class_calibrated_final.bin '
        '/home/work_user2/kawachx_task/results/qnn_int8_conversion/input/fire_2.raw '
        '/home/work_user2/kawachx_task/results/step7_htp_execution/raw/fire_2; '
        'echo "=== INFERENCE 3: person.raw ==="; '
        '/home/work_user2/kawachx_task/execute_htp_inference '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '/home/work_user2/kawachx_task/models/3class_calibrated_final.bin '
        '/home/work_user2/kawachx_task/results/qnn_int8_conversion/input/person.raw '
        '/home/work_user2/kawachx_task/results/step7_htp_execution/raw/person; '
        'ls -lh /home/work_user2/kawachx_task/results/step7_htp_execution/raw/'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', build_and_run], capture_output=True, text=True)
    print("=== STEP 7 REAL HTP INFERENCE OUTPUT ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

    # Sync back locally
    os.makedirs('results/step7_htp_execution/raw', exist_ok=True)
    os.makedirs('results/step7_htp_execution/reports', exist_ok=True)
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/step7_htp_execution/raw/*', 'results/step7_htp_execution/raw/'])

if __name__ == "__main__":
    run_step7()
