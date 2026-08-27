#!/usr/bin/env python3
import subprocess

def run():
    subprocess.run(['scp', 'scripts/tools/print_quant_encodings.cpp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/'])
    cmd = (
        'g++ -std=c++17 -O3 -I/home/devuser/qairt/2.47.0.260601/include/QNN '
        '/home/work_user2/kawachx_task/print_quant_encodings.cpp -ldl '
        '-o /home/work_user2/kawachx_task/print_quant_encodings && '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'echo "=== 3class_calibrated_final.bin ==="; '
        '/home/work_user2/kawachx_task/print_quant_encodings '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '/home/work_user2/kawachx_task/models/3class_calibrated_final.bin; '
        'echo "=== kawachx_aihub_split.bin ==="; '
        '/home/work_user2/kawachx_task/print_quant_encodings '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '/home/work_user2/kawachx_task/models/kawachx_aihub_split.bin'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run()
