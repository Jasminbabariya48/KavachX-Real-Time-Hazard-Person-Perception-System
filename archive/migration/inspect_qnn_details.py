#!/usr/bin/env python3
import subprocess

def inspect():
    cmd = (
        'python3 -c "'
        'import json\n'
        'with open(\'/home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8_net.json\') as f:\n'
        '    data = json.load(f)\n'
        'print(\'Top Keys:\', list(data.keys()))\n'
        'tensors = data.get(\'tensors\', {})\n'
        'print(\'Total Tensors:\', len(tensors))\n'
        'for k, v in list(tensors.items())[:10]:\n'
        '    if \'images\' in k or \'output\' in k:\n'
        '        print(\'Tensor:\', k, v.get(\'dims\'), v.get(\'data_type\'), v.get(\'quant_params\'))\n'
        'for k, v in list(tensors.items()):\n'
        '    if \'output0\' in k or k == \'images\':\n'
        '        print(\'Key Tensor:\', k, v.get(\'dims\'), v.get(\'data_type\'), v.get(\'quant_params\'))\n'
        '"'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== TENSOR INSPECTION ===")
    print(res.stdout)
    
    cmd_cpp = 'grep -E "Qnn_Tensor_t|QNN_DATATYPE|images|output0" /home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8.cpp | head -n 30'
    res_cpp = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd_cpp], capture_output=True, text=True)
    print("=== CPP CODE SNIPPETS ===")
    print(res_cpp.stdout)

if __name__ == "__main__":
    inspect()
