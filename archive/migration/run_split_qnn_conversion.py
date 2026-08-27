#!/usr/bin/env python3
import subprocess
import os

def run_conversion():
    # 1. Create target directories
    prep_cmd = (
        'mkdir -p /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/{input,generated,logs,reports}'
    )
    subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', prep_cmd], check=True)
    
    # 2. Run qnn-onnx-converter
    conv_cmd = (
        'source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh && '
        'qnn-onnx-converter '
        '--input_network /home/work_user2/kawachx_task/models/new_3class_best_FP32_htp_split.onnx '
        '-o /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/generated/model_split_qnn_int8.cpp '
        '--input_list /home/work_user2/kawachx_task/results/qnn_int8_conversion/input/input_list.txt '
        '--act_bw 8 --weight_bw 8 --bias_bw 32 --use_per_channel_quantization '
        '> /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/logs/converter_stdout.log '
        '2> /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/logs/converter_stderr.log; '
        'echo "Converter RC: $?"; '
        'cat /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/logs/converter_stdout.log; '
        'cat /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/logs/converter_stderr.log; '
        'ls -lh /home/work_user2/kawachx_task/results/qnn_int8_split_conversion/generated/'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', conv_cmd], capture_output=True, text=True)
    print("=== SPLIT QNN INT8 CONVERSION OUTPUT ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    run_conversion()
