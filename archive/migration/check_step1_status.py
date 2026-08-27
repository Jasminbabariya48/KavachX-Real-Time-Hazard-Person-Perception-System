#!/usr/bin/env python3
import subprocess
import os

os.makedirs('results/htp_initialization', exist_ok=True)

def run_fresh(cmd):
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True, timeout=60)
    return res.stdout, res.stderr, res.returncode

# 1. Identity & permissions
stdout, stderr, code = run_fresh('id')
with open('results/htp_initialization/id.txt', 'w', encoding='utf-8') as f: f.write(stdout + stderr)

stdout, stderr, code = run_fresh('groups')
with open('results/htp_initialization/groups.txt', 'w', encoding='utf-8') as f: f.write(stdout + stderr)

stdout, stderr, code = run_fresh('getent group render')
with open('results/htp_initialization/render_group.txt', 'w', encoding='utf-8') as f: f.write(stdout + stderr)

stdout, stderr, code = run_fresh('ls -l /dev/fastrpc-cdsp && stat /dev/fastrpc-cdsp')
with open('results/htp_initialization/fastrpc_device.txt', 'w', encoding='utf-8') as f: f.write(stdout + stderr)

# 2. Worker inspection & execution attempt
worker_inspect, _, _ = run_fresh('find /home/work_user2/kawachx_task -type f -name "kawach_worker"; file /home/work_user2/kawachx_task/npu_worker/kawach_worker; ldd /home/work_user2/kawachx_task/npu_worker/kawach_worker')
with open('results/htp_initialization/worker_inspect.txt', 'w', encoding='utf-8') as f: f.write(worker_inspect)
print('WORKER INSPECTION:\n', worker_inspect)

worker_cmd = 'export ADSP_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned:/vendor/dsp/cdsp:/vendor/lib/rfsa/adsp; /home/work_user2/kawachx_task/npu_worker/kawach_worker --backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so --system /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so --model /home/work_user2/kawachx_task/models/3class_calibrated_final.bin --socket /tmp/test_init.sock'
stdout, stderr, code = run_fresh(worker_cmd)
with open('results/htp_initialization/worker_stdout.txt', 'w', encoding='utf-8') as f: f.write(stdout)
with open('results/htp_initialization/worker_stderr.txt', 'w', encoding='utf-8') as f: f.write(stderr)

print('WORKER STDOUT:\n', stdout)
print('WORKER STDERR:\n', stderr)

# 3. Environment
env_out, _, _ = run_fresh('env')
with open('results/htp_initialization/environment.txt', 'w', encoding='utf-8') as f: f.write(env_out)

print("Step 1 evidence collection complete.")
