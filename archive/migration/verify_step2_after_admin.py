#!/usr/bin/env python3
import subprocess
import os

os.makedirs('results/htp_initialization', exist_ok=True)

def run_fresh(cmd, timeout=60):
    res = subprocess.run(
        ['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return res.stdout, res.stderr, res.returncode

print("=== 1. Fresh SSH Verification of Identity & Groups ===")
id_out, id_err, _ = run_fresh('id && id work_user2')
with open('results/htp_initialization/id_admin_fix.txt', 'w', encoding='utf-8') as f:
    f.write(id_out + id_err)
print("ID:\n", id_out)

groups_out, groups_err, _ = run_fresh('groups')
with open('results/htp_initialization/groups_admin_fix.txt', 'w', encoding='utf-8') as f:
    f.write(groups_out + groups_err)
print("GROUPS:\n", groups_out)

render_out, render_err, _ = run_fresh('getent group render')
with open('results/htp_initialization/render_group_admin_fix.txt', 'w', encoding='utf-8') as f:
    f.write(render_out + render_err)
print("GETENT GROUP RENDER:\n", render_out)

print("=== 2. FastRPC Device Status ===")
dev_out, dev_err, _ = run_fresh('ls -l /dev/fastrpc-cdsp && stat /dev/fastrpc-cdsp')
with open('results/htp_initialization/fastrpc_device_admin_fix.txt', 'w', encoding='utf-8') as f:
    f.write(dev_out + dev_err)
print("DEVICE:\n", dev_out)

print("=== 3. Executing kawach_worker Test ===")
worker_cmd = 'export ADSP_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned:/vendor/dsp/cdsp:/vendor/lib/rfsa/adsp; timeout 5 /home/work_user2/kawachx_task/npu_worker/kawach_worker --backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so --system /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so --model /home/work_user2/kawachx_task/models/3class_calibrated_final.bin --socket /tmp/test_admin_fix.sock'
w_stdout, w_stderr, w_code = run_fresh(worker_cmd)

with open('results/htp_initialization/worker_stdout_admin_fix.txt', 'w', encoding='utf-8') as f:
    f.write(w_stdout)
with open('results/htp_initialization/worker_stderr_admin_fix.txt', 'w', encoding='utf-8') as f:
    f.write(w_stderr)
with open('results/htp_initialization/worker_exit_code_admin_fix.txt', 'w', encoding='utf-8') as f:
    f.write(str(w_code) + "\n")

print("WORKER STDOUT:\n", w_stdout)
print("WORKER STDERR:\n", w_stderr)
print("WORKER EXIT CODE:\n", w_code)
