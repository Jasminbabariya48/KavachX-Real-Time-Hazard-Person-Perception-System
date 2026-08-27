#!/usr/bin/env python3
import subprocess
import os
import hashlib

def run_htp_compilation():
    # 1. Prepare target directories
    prep_cmd = (
        'mkdir -p /home/work_user2/kawachx_task/results/htp_compilation/{input,model_lib,output,logs,reports}; '
        'mkdir -p /home/work_user2/kawachx_task/models'
    )
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', prep_cmd], check=True)
    
    # 2. Stage 1: Build model shared library (.so) for aarch64-ubuntu-gcc9.4
    stage1_cmd = (
        'source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh && '
        'qnn-model-lib-generator '
        '-c /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8.cpp '
        '-b /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8.bin '
        '-t aarch64-ubuntu-gcc9.4 '
        '-l libmodel_qnn_int8 '
        '-o /home/work_user2/kawachx_task/results/htp_compilation/model_lib '
        '> /home/work_user2/kawachx_task/results/htp_compilation/logs/model_lib_gen_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation/logs/model_lib_gen_stderr.log'
    )
    
    print("=== Stage 1: Building Model Shared Library (.so) ===")
    res1 = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', stage1_cmd])
    print(f"Stage 1 return code: {res1.returncode}")
    
    # Check model .so
    check_so_cmd = 'ls -la /home/work_user2/kawachx_task/results/htp_compilation/model_lib/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so'
    res_so = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', check_so_cmd], capture_output=True, text=True)
    print("Model SO info:\n", res_so.stdout)
    if res_so.returncode != 0:
        print("Stage 1 failed!")
        return

    # 3. Stage 2: Generate HTP v68 Context Binary
    stage2_cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        '/home/devuser/qairt/2.47.0.260601/bin/aarch64-ubuntu-gcc9.4/qnn-context-binary-generator '
        '--model /home/work_user2/kawachx_task/results/htp_compilation/model_lib/aarch64-ubuntu-gcc9.4/libmodel_qnn_int8.so '
        '--backend /home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so '
        '--binary_file kavachx_3class_int8_htp_v68.bin '
        '--output_dir /home/work_user2/kawachx_task/results/htp_compilation/output '
        '> /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stdout.log '
        '2> /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stderr.log'
    )
    
    print("=== Stage 2: Generating HTP v68 Context Binary ===")
    res2 = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', stage2_cmd])
    print(f"Stage 2 return code: {res2.returncode}")
    
    # 4. Copy generated binary to canonical models/ path on target
    copy_cmd = (
        'cp /home/work_user2/kawachx_task/results/htp_compilation/output/kavachx_3class_int8_htp_v68.bin /home/work_user2/kawachx_task/models/; '
        'ls -la /home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin; '
        'sha256sum /home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin > /home/work_user2/kawachx_task/results/htp_compilation/reports/checksum.txt; '
        'cat /home/work_user2/kawachx_task/results/htp_compilation/reports/checksum.txt; '
        'echo "=== CONTEXT GEN LOGS ==="; cat /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stdout.log /home/work_user2/kawachx_task/results/htp_compilation/logs/context_gen_stderr.log'
    )
    res_final = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', copy_cmd], capture_output=True, text=True)
    print(res_final.stdout)
    if res_final.stderr:
        print("STDERR:\n", res_final.stderr)
        
    # 5. Sync back locally
    os.makedirs('results/htp_compilation/output', exist_ok=True)
    os.makedirs('results/htp_compilation/logs', exist_ok=True)
    os.makedirs('results/htp_compilation/reports', exist_ok=True)
    os.makedirs('models/qnn', exist_ok=True)
    
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin', 'models/qnn/'])
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/models/kavachx_3class_int8_htp_v68.bin', 'results/htp_compilation/output/'])
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/htp_compilation/logs/*', 'results/htp_compilation/logs/'])
    subprocess.run(['scp', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/htp_compilation/reports/*', 'results/htp_compilation/reports/'])

if __name__ == "__main__":
    run_htp_compilation()
