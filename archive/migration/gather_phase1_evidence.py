#!/usr/bin/env python3
import subprocess
import os
import json

os.makedirs('results/environment', exist_ok=True)

def run_remote(cmd, timeout=60):
    res = subprocess.run(
        ['ssh', '-n', 'work_user2@ssh.kavachx.io', cmd],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    out = res.stdout
    if res.stderr:
        out += "\n--- STDERR ---\n" + res.stderr
    return out

def save_evidence(filename, content):
    path = os.path.join('results/environment', filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Wrote: {path}")

print("--- 1. Gathering Hardware Evidence ---")
hw_out = run_remote("hostname; uname -a; cat /proc/cpuinfo | head -n 40; lscpu; free -h; cat /sys/devices/soc0/soc_id 2>/dev/null; cat /sys/devices/soc0/machine 2>/dev/null; cat /sys/devices/soc0/family 2>/dev/null")
save_evidence('hardware.txt', hw_out)

print("--- 2. Gathering Permissions Evidence ---")
perm_out = run_remote("whoami; id; groups; ls -la /dev/dma_heap/; ls -la /dev/fastrpc*; ls -la /dev/adsprpc* 2>/dev/null; ls -la /dev/kgsl* 2>/dev/null")
save_evidence('permissions.txt', perm_out)

print("--- 3. Gathering QAIRT/QNN SDK Evidence ---")
sdk_out = run_remote("ls -la /home/devuser/qairt/2.47.0.260601; cat /home/devuser/qairt/2.47.0.260601/sdk.yaml 2>/dev/null; head -n 30 /home/devuser/qairt/2.47.0.260601/QAIRT_ReleaseNotes.txt 2>/dev/null")
save_evidence('qnn_sdk.txt', sdk_out)

print("--- 4. Gathering QNN Tools Evidence ---")
tools_out = run_remote("ls -la /home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4 /home/devuser/qairt/2.47.0.260601/bin/x86_64-linux-clang; /home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-net-run --version 2>&1 | head -n 10")
save_evidence('qnn_tools.txt', tools_out)

print("--- 5. Gathering QNN Libraries & HTP v68 Evidence ---")
lib_out = run_remote("ls -la /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4; ls -la /home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned 2>/dev/null; file /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtpV68Stub.so /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnCpu.so 2>/dev/null")
save_evidence('qnn_libraries.txt', lib_out)

print("--- 6. Gathering Toolchain Evidence ---")
tc_out = run_remote("which gcc g++ clang make cmake ninja python3 2>/dev/null; gcc --version | head -n 1; g++ --version | head -n 1; make --version | head -n 1; cmake --version | head -n 1; python3 --version; ldd --version | head -n 1")
save_evidence('toolchain.txt', tc_out)

print("--- 7. Gathering Project & Model Artifacts Evidence ---")
proj_out = run_remote("ls -la ~/kawachx_task; ls -lh ~/kawachx_task/models; ls -la ~/kawachx_task/npu_worker; ls -lh ~/kawachx_task/test_images; file ~/kawachx_task/models/* ~/kawachx_task/test_images/*")
save_evidence('project_inspection.txt', proj_out)

print("Evidence gathering complete.")
