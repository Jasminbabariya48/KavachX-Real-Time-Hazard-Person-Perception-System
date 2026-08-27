#!/usr/bin/env python3
import subprocess
import os
import json

def run_conversion():
    # 1. Prepare target directories
    setup_cmd = (
        'mkdir -p /home/work_user2/kawachx_task/results/qnn_int8_conversion/{input,config,generated,logs,reports}; '
        'cat << "EOF" > /home/work_user2/kawachx_task/results/qnn_int8_conversion/input/input_list.txt\n'
        'images:=/home/work_user2/kawachx_task/results/int8_calibration/preprocessed/fire_fp32.raw\n'
        'images:=/home/work_user2/kawachx_task/results/int8_calibration/preprocessed/fire_2_fp32.raw\n'
        'images:=/home/work_user2/kawachx_task/results/int8_calibration/preprocessed/person_fp32.raw\n'
        'EOF\n'
    )
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', setup_cmd], check=True)
    
    # 2. Run QNN ONNX Converter
    conv_cmd = (
        'source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh && '
        'qnn-onnx-converter '
        '--input_network /home/work_user2/kawachx_task/models/new_3class_best_FP32.onnx '
        '-o /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8.cpp '
        '--input_list /home/work_user2/kawachx_task/results/qnn_int8_conversion/input/input_list.txt '
        '--act_bw 8 '
        '--weight_bw 8 '
        '--bias_bw 32 '
        '--use_per_channel_quantization '
        '> /home/work_user2/kawachx_task/results/qnn_int8_conversion/logs/converter_stdout.log '
        '2> /home/work_user2/kawachx_task/results/qnn_int8_conversion/logs/converter_stderr.log'
    )
    
    print("=== Executing qnn-onnx-converter on Kavach-EdgeBox ===")
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', conv_cmd])
    print(f"Converter process return code: {res.returncode}")
    
    # 3. Read back logs and artifacts listing
    check_cmd = (
        'echo "=== CONVERTER STDOUT ==="; cat /home/work_user2/kawachx_task/results/qnn_int8_conversion/logs/converter_stdout.log; '
        'echo "=== CONVERTER STDERR ==="; cat /home/work_user2/kawachx_task/results/qnn_int8_conversion/logs/converter_stderr.log; '
        'echo "=== GENERATED FILES ==="; ls -la /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/'
    )
    res_log = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', check_cmd], capture_output=True, text=True)
    print(res_log.stdout)
    
    # 4. Sync results locally
    os.makedirs('results/qnn_int8_conversion/logs', exist_ok=True)
    os.makedirs('results/qnn_int8_conversion/generated', exist_ok=True)
    os.makedirs('results/qnn_int8_conversion/reports', exist_ok=True)
    
    subprocess.run(['scp', '-r', 'work_user2@ssh.kavachx.io:/home/work_user2/kawachx_task/results/qnn_int8_conversion/*', 'results/qnn_int8_conversion/'])

if __name__ == "__main__":
    run_conversion()
