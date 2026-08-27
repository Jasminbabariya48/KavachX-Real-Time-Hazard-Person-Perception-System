#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("=== Syncing finalized repository tree to target ===")
    dirs = [
        'src/kavachx/inference', 'src/kavachx/pipeline', 'src/kavachx/capture', 'src/kavachx/ipc', 'src/kavachx/service', 'src/kavachx/config', 'src/kavachx/common',
        'native/worker', 'models/production', 'models/reference', 'config', 'deployment',
        'tests/unit', 'tests/hardware', 'tests/integration', 'tests/streaming', 'tests/fixtures',
        'tools', 'docs/architecture', 'docs/deployment', 'docs/operations', 'docs/development', 'docs/testing', 'docs/handover',
        'reports/acceptance', 'reports/performance', 'reports/reliability', 'reports/audit'
    ]
    dir_cmd = 'mkdir -p ' + ' '.join([f'/home/work_user2/kawachx_task/{d}' for d in dirs])
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', dir_cmd], check=True)

    sync_items = [
        ('src', '/home/work_user2/kawachx_task/'),
        ('native/worker', '/home/work_user2/kawachx_task/native/'),
        ('config', '/home/work_user2/kawachx_task/'),
        ('deployment', '/home/work_user2/kawachx_task/'),
        ('tests', '/home/work_user2/kawachx_task/'),
        ('tools', '/home/work_user2/kawachx_task/'),
        ('docs', '/home/work_user2/kawachx_task/'),
        ('reports', '/home/work_user2/kawachx_task/'),
        ('Makefile', '/home/work_user2/kawachx_task/Makefile'),
        ('pyproject.toml', '/home/work_user2/kawachx_task/pyproject.toml'),
        ('requirements.txt', '/home/work_user2/kawachx_task/requirements.txt'),
        ('README.md', '/home/work_user2/kawachx_task/README.md')
    ]
    for src, dst in sync_items:
        subprocess.run(['scp', '-r', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    clean_cmd = 'rm -rf /home/work_user2/kawachx_task/app /home/work_user2/kawachx_task/native/npu_worker /home/work_user2/kawachx_task/npu_worker'
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', clean_cmd], check=True)

    print("=== Running Validation on Target ===")
    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'export PYTHONPATH=/home/work_user2/kawachx_task/src:/home/work_user2/kawachx_task:$PYTHONPATH; '
        'echo "[1/6] Building Native Worker..."; '
        'cd /home/work_user2/kawachx_task/native/worker && make clean && make -j$(nproc); '
        'echo "[2/6] Restarting Production Service..."; '
        'python3 /home/work_user2/kawachx_task/tools/service_manager.py restart; '
        'sleep 1; '
        'echo "[3/6] Running Hardware HTP Test..."; '
        'python3 /home/work_user2/kawachx_task/tests/hardware/test_htp_inference.py; '
        'echo "[4/6] Running Stream Integration Test..."; '
        'python3 /home/work_user2/kawachx_task/tests/integration/test_pipeline_integration.py; '
        'echo "[5/6] Running Live Streaming Test..."; '
        'python3 /home/work_user2/kawachx_task/tests/streaming/test_live_stream.py; '
        'echo "[6/6] Verifying Service Health..."; '
        'cat /tmp/kawach_health.json'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
