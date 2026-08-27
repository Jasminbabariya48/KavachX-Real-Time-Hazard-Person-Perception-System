#!/usr/bin/env python3
import subprocess
import os

def run():
    print("=== STEP 10: SYNCING STREAM PIPELINE TO TARGET ===")
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', 'mkdir -p /home/work_user2/kawachx_task/src/stream /home/work_user2/kawachx_task/results/step10_live_stream/reports'], check=True)
    
    sync_files = [
        ('config/production_config.json', '/home/work_user2/kawachx_task/config/production_config.json'),
        ('src/stream/frame_source.py', '/home/work_user2/kawachx_task/src/stream/frame_source.py'),
        ('src/stream/stream_pipeline.py', '/home/work_user2/kawachx_task/src/stream/stream_pipeline.py'),
        ('src/stream/live_monitoring_server.py', '/home/work_user2/kawachx_task/src/stream/live_monitoring_server.py'),
        ('scripts/tools/run_step10_live_stream_suite.py', '/home/work_user2/kawachx_task/run_step10_live_stream_suite.py')
    ]
    for src, dst in sync_files:
        subprocess.run(['scp', src, f'work_user2@ssh.kavachx.io:{dst}'], check=True)

    cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'python3 /home/work_user2/kawachx_task/scripts/service/kawach_service.py restart; '
        'sleep 2; '
        'python3 /home/work_user2/kawachx_task/run_step10_live_stream_suite.py; '
        'TEST_RC=$?; '
        'python3 /home/work_user2/kawachx_task/scripts/service/kawach_service.py stop; '
        'exit $TEST_RC'
    )
    print("\n=== STEP 10: RUNNING LIVE STREAM SUITE ON TARGET BOX ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

    os.makedirs('results/step10_live_stream/reports', exist_ok=True)
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/step10_live_stream/reports/*', 'results/step10_live_stream/reports/'])

if __name__ == "__main__":
    run()
