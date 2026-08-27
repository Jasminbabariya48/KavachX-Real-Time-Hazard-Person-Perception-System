#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== STEP 12: SYNCING GO-LIVE SUITE TO TARGET ===")
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'mkdir -p /home/work_user2/kawachx_task/results/step12_go_live/reports'], check=True)
    
    sync_files = [
        ('scripts/tools/run_step12_go_live_suite.py', '/home/work_user2/kawachx_task/run_step12_go_live_suite.py')
    ]
    for src, dst in sync_files:
        subprocess.run(['scp', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'export PYTHONPATH=/home/work_user2/kawachx_task:$PYTHONPATH; '
        'python3 /home/work_user2/kawachx_task/run_step12_go_live_suite.py; '
        'TEST_RC=$?; '
        'exit $TEST_RC'
    )
    print("\n=== STEP 12: RUNNING GO-LIVE ACCEPTANCE SUITE ON TARGET ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

    os.makedirs('results/step12_go_live/reports', exist_ok=True)
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/step12_go_live/reports/*', 'results/step12_go_live/reports/'])

if __name__ == "__main__":
    run()
