#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== [Restructure Validation] Syncing Restructured Codebase to Target ===")
    
    # Create remote target tree
    remote_dirs = [
        "app/inference", "app/pipeline", "app/camera", "app/events", "app/monitoring", "app/config",
        "native/npu_worker", "models/production", "models/reference", "config/service",
        "deployment", "scripts/service", "scripts/tools",
        "tests/unit", "tests/integration", "tests/hardware", "tests/performance", "tests/fixtures",
        "docs/architecture", "docs/deployment", "docs/operations", "docs/development", "docs/demo",
        "artifacts/manifests", "artifacts/checksums", "artifacts/reports", "artifacts/restructure"
    ]
    dir_cmd = "mkdir -p " + " ".join([f"/home/work_user2/kawachx_task/{d}" for d in remote_dirs])
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', dir_cmd], check=True)

    # Sync app, native, config, deployment, tests, docs
    sync_items = [
        ("app", "/home/work_user2/kawachx_task/"),
        ("native", "/home/work_user2/kawachx_task/"),
        ("config", "/home/work_user2/kawachx_task/"),
        ("deployment", "/home/work_user2/kawachx_task/"),
        ("tests", "/home/work_user2/kawachx_task/"),
        ("docs", "/home/work_user2/kawachx_task/"),
        ("artifacts", "/home/work_user2/kawachx_task/"),
        ("Makefile", "/home/work_user2/kawachx_task/Makefile"),
        ("README.md", "/home/work_user2/kawachx_task/README.md"),
        ("requirements.txt", "/home/work_user2/kawachx_task/requirements.txt")
    ]
    for src, dst in sync_items:
        subprocess.run(['scp', '-r', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    # Execution and verification commands on target
    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'export PYTHONPATH=/home/work_user2/kawachx_task:$PYTHONPATH; '
        'echo "=== Building native NPU Worker on Target ==="; '
        'cd /home/work_user2/kawachx_task/npu_worker && make clean && make -j$(nproc); '
        'echo "=== Restarting Production Service ==="; '
        'python3 /home/work_user2/kawachx_task/scripts/service/kawach_service.py restart; '
        'sleep 1; '
        'echo "=== Running Hardware Test: test_htp_execution.py ==="; '
        'python3 /home/work_user2/kawachx_task/tests/hardware/test_htp_execution.py; '
        'echo "=== Running Integration Test: test_worker_recovery.py ==="; '
        'python3 /home/work_user2/kawachx_task/tests/integration/test_worker_recovery.py; '
        'echo "=== Running Integration Test: test_pipeline.py ==="; '
        'python3 /home/work_user2/kawachx_task/tests/integration/test_pipeline.py; '
        'echo "=== Service Health Status ==="; '
        'cat /tmp/kawach_health.json; '
        'echo "=== Process Isolation Audit ==="; '
        'python3 /home/work_user2/kawachx_task/scripts/testing/process_isolation.py'
    )
    print("\n=== [Restructure Validation] Executing Validation on Target Box ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run()
