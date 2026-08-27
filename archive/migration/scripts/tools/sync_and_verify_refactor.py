#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== [Sync & Verify] Syncing Refactored Production Tree to Target ===")
    
    # Create remote directories
    remote_dirs = [
        "src/kavachx/inference", "src/kavachx/pipeline", "src/kavachx/capture", "src/kavachx/ipc", "src/kavachx/service", "src/kavachx/config", "src/kavachx/common",
        "native/worker", "models/production", "models/reference", "config", "deployment",
        "tests/unit", "tests/integration", "tests/hardware", "tests/streaming", "tests/fixtures",
        "tools", "docs/architecture", "docs/deployment", "docs/operations", "docs/development", "docs/testing", "docs/handover",
        "reports/acceptance", "reports/performance", "reports/reliability", "reports/audit"
    ]
    dir_cmd = "mkdir -p " + " ".join([f"/home/work_user2/kawachx_task/{d}" for d in remote_dirs])
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', dir_cmd], check=True)

    # Sync folders
    sync_items = [
        ("src", "/home/work_user2/kawachx_task/"),
        ("native/worker", "/home/work_user2/kawachx_task/native/"),
        ("config", "/home/work_user2/kawachx_task/"),
        ("deployment", "/home/work_user2/kawachx_task/"),
        ("tests", "/home/work_user2/kawachx_task/"),
        ("tools", "/home/work_user2/kawachx_task/"),
        ("docs", "/home/work_user2/kawachx_task/"),
        ("Makefile", "/home/work_user2/kawachx_task/Makefile"),
        ("pyproject.toml", "/home/work_user2/kawachx_task/pyproject.toml"),
        ("requirements.txt", "/home/work_user2/kawachx_task/requirements.txt")
    ]
    for src, dst in sync_items:
        subprocess.run(['scp', '-r', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'export PYTHONPATH=/home/work_user2/kawachx_task/src:/home/work_user2/kawachx_task:$PYTHONPATH; '
        'echo "=== [1/5] Building Native C++ Worker (native/worker) ==="; '
        'cd /home/work_user2/kawachx_task/native/worker && make clean && make -j$(nproc); '
        'echo "=== [2/5] Restarting Production Service ==="; '
        'python3 /home/work_user2/kawachx_task/scripts/service/kawach_service.py restart; '
        'sleep 1; '
        'echo "=== [3/5] Running Hardware HTP Test ==="; '
        'python3 /home/work_user2/kawachx_task/tests/hardware/test_htp_inference.py; '
        'echo "=== [4/5] Running Stream Integration Test ==="; '
        'python3 /home/work_user2/kawachx_task/tests/integration/test_pipeline_integration.py; '
        'echo "=== [5/5] Running Live Stream Benchmark Test ==="; '
        'python3 /home/work_user2/kawachx_task/tests/streaming/test_live_stream.py; '
        'echo "=== Service Health ==="; '
        'cat /tmp/kawach_health.json'
    )
    print("\n=== [Sync & Verify] Executing Verification Suite on Target ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run()
