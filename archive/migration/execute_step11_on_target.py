#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== STEP 11: SYNCING HANDOVER & DEMO SCRIPTS TO TARGET ===")
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'mkdir -p /home/work_user2/kawachx_task/deployment /home/work_user2/kawachx_task/results/step11_final/reports'], check=True)
    
    sync_files = [
        ('deployment/install.sh', '/home/work_user2/kawachx_task/deployment/install.sh'),
        ('deployment/uninstall.sh', '/home/work_user2/kawachx_task/deployment/uninstall.sh'),
        ('deployment/README.md', '/home/work_user2/kawachx_task/deployment/README.md'),
        ('results/step11_final/production_manifest.json', '/home/work_user2/kawachx_task/results/step11_final/production_manifest.json'),
        ('results/step11_final/checksums.sha256', '/home/work_user2/kawachx_task/results/step11_final/checksums.sha256'),
        ('results/step11_final/reports/repository_inventory.json', '/home/work_user2/kawachx_task/results/step11_final/reports/repository_inventory.json'),
        ('results/step11_final/reports/final_acceptance_matrix.json', '/home/work_user2/kawachx_task/results/step11_final/reports/final_acceptance_matrix.json'),
        ('results/step11_final/reports/security_audit.json', '/home/work_user2/kawachx_task/results/step11_final/reports/security_audit.json')
    ]
    for src, dst in sync_files:
        subprocess.run(['scp', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'python3 /home/work_user2/kawachx_task/scripts/service/kawach_service.py restart; '
        'sleep 1; '
        'python3 /home/work_user2/kawachx_task/scripts/testing/bounded_stream_runner.py --test-name "Final_Handover_Demonstration" --source /home/work_user2/kawachx_task/test_images/live_test_stream.mp4 --max-frames 30 --duration-seconds 4.0 --hard-timeout-seconds 6.0; '
        'cat /tmp/kawach_health.json; '
        'python3 /home/work_user2/kawachx_task/scripts/testing/process_isolation.py'
    )
    print("\n=== STEP 11: RUNNING FINAL HANDOVER DEMONSTRATION ON TARGET ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run()
