#!/usr/bin/env python3
import subprocess
import time

def run():
    print("Syncing updated npu_worker sources to target...")
    subprocess.run(['scp', 'src/npu_worker/qnn_inference.hpp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/npu_worker/'])
    subprocess.run(['scp', 'src/npu_worker/qnn_inference.cpp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/npu_worker/'])
    subprocess.run(['scp', 'scripts/tools/test_worker_ipc.py', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/'])

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
        'python3 /home/work_user2/kawachx_task/test_worker_ipc.py; '
        'TEST_RC=$?; '
        'kill -TERM $WORKER_PID 2>/dev/null || true; '
        'sleep 1; '
        'echo "=== WORKER LOGS ==="; '
        'cat /tmp/worker.log; '
        'exit $TEST_RC'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== END-TO-END WORKER IPC TEST OUTPUT ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run()
