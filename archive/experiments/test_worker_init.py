#!/usr/bin/env python3
import subprocess
import time

def run_test():
    # Kill any lingering worker
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'killall -9 kawach_worker 2>/dev/null; rm -f /tmp/test_success.sock'])
    
    # Launch worker in background and redirect output to a log file
    start_cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        '/home/work_user2/kawachx_task/npu_worker/kawach_worker '
        '--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '--system /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so '
        '--model /home/work_user2/kawachx_task/models/3class_calibrated_final.bin '
        '--socket /tmp/test_success.sock > /tmp/worker_init.log 2>&1 &'
    )
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', start_cmd])
    
    time.sleep(2)
    
    # Check the log file
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'cat /tmp/worker_init.log; ls -la /tmp/test_success.sock'], capture_output=True, text=True)
    print("=== WORKER STARTUP LOG ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
        
    # Clean up worker
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'killall -9 kawach_worker 2>/dev/null'])

if __name__ == "__main__":
    run_test()
