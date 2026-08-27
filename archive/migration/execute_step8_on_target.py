#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== STEP 8: SYNCING SOURCES TO TARGET ===")
    src_files = [
        ('src/npu_worker/ipc_handler.hpp', '/home/work_user2/kawachx_task/npu_worker/ipc_handler.hpp'),
        ('src/npu_worker/ipc_handler.cpp', '/home/work_user2/kawachx_task/npu_worker/ipc_handler.cpp'),
        ('src/npu_worker/qnn_inference.hpp', '/home/work_user2/kawachx_task/npu_worker/qnn_inference.hpp'),
        ('src/npu_worker/qnn_inference.cpp', '/home/work_user2/kawachx_task/npu_worker/qnn_inference.cpp'),
        ('src/npu_worker/main.cpp', '/home/work_user2/kawachx_task/npu_worker/main.cpp'),
        ('scripts/tools/run_step8_comprehensive_validation.py', '/home/work_user2/kawachx_task/run_step8_comprehensive_validation.py')
    ]
    for src, dst in src_files:
        subprocess.run(['scp', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)
        
    cmd = (
        'cd /home/work_user2/kawachx_task/npu_worker && '
        'make clean && make && '
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'pkill -9 kawach_worker 2>/dev/null || true; '
        'rm -f /tmp/kawach_worker.sock; '
        './kawach_worker '
        '--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '--system /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '--model /home/work_user2/kawachx_task/models/3class_calibrated_final.bin '
        '--socket /tmp/kawach_worker.sock > /tmp/worker.log 2>&1 & '
        'WORKER_PID=$!; '
        'sleep 3; '
        'python3 /home/work_user2/kawachx_task/run_step8_comprehensive_validation.py; '
        'TEST_RC=$?; '
        'kill -TERM $WORKER_PID 2>/dev/null || true; '
        'sleep 1; '
        'echo "=== WORKER LOGS ==="; '
        'cat /tmp/worker.log; '
        'exit $TEST_RC'
    )
    print("\n=== STEP 8: RUNNING COMPREHENSIVE VALIDATION ON TARGET ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

    os.makedirs('results/step8_production/reports', exist_ok=True)
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/step8_production/reports/*', 'results/step8_production/reports/'])

if __name__ == "__main__":
    run()
