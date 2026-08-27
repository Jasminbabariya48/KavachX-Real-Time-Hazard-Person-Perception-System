#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== STEP 10.2: SYNCING ACCEPTANCE SUITE TO TARGET ===")
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'mkdir -p /home/work_user2/kawachx_task/scripts/testing /home/work_user2/kawachx_task/results/step10_live_stream/reports'], check=True)
    
    sync_files = [
        ('scripts/testing/run_step10_2_full_acceptance.py', '/home/work_user2/kawachx_task/scripts/testing/run_step10_2_full_acceptance.py')
    ]
    for src, dst in sync_files:
        subprocess.run(['scp', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'python3 /home/work_user2/kawachx_task/scripts/testing/run_step10_2_full_acceptance.py; '
        'TEST_RC=$?; '
        'exit $TEST_RC'
    )
    print("\n=== STEP 10.2: RUNNING FULL BOUNDED ACCEPTANCE SUITE ON TARGET ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

    os.makedirs('results/step10_live_stream/reports', exist_ok=True)
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/step10_live_stream/reports/*', 'results/step10_live_stream/reports/'])

if __name__ == "__main__":
    run()
