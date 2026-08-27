#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== STEP 9: SYNCING DEPLOYMENT & ACCEPTANCE ARTIFACTS TO TARGET ===")
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'mkdir -p /home/work_user2/kawachx_task/config /home/work_user2/kawachx_task/scripts/service /home/work_user2/kawachx_task/results/step9_production/reports'], check=True)
    
    sync_files = [
        ('config/production_config.json', '/home/work_user2/kawachx_task/config/production_config.json'),
        ('config/kawach_worker.service', '/home/work_user2/kawachx_task/config/kawach_worker.service'),
        ('scripts/service/kawach_service.py', '/home/work_user2/kawachx_task/scripts/service/kawach_service.py'),
        ('scripts/tools/run_step9_acceptance_suite.py', '/home/work_user2/kawachx_task/run_step9_acceptance_suite.py')
    ]
    for src, dst in sync_files:
        subprocess.run(['scp', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'python3 /home/work_user2/kawachx_task/run_step9_acceptance_suite.py; '
        'TEST_RC=$?; '
        'python3 /home/work_user2/kawachx_task/scripts/service/kawach_service.py stop; '
        'exit $TEST_RC'
    )
    print("\n=== STEP 9: RUNNING COMPLETE PRODUCTION ACCEPTANCE GATES ON TARGET ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

    os.makedirs('results/step9_production/reports', exist_ok=True)
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/step9_production/reports/*', 'results/step9_production/reports/'])

if __name__ == "__main__":
    run()
