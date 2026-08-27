#!/usr/bin/env python3
import subprocess
import json

def inspect_converted():
    cmd = (
        'python3 -c "'
        'import json\n'
        'with open(\'/home/work_user2/kawachx_task/results/qnn_int8_conversion/generated/model_qnn_int8_net.json\') as f:\n'
        '    data = json.load(f)\n'
        'print(\'Graph Name:\', data.get(\'graph\', {}).get(\'name\'))\n'
        'inputs = data.get(\'graph\', {}).get(\'inputs\', [])\n'
        'print(\'Inputs:\', [(i.get(\'name\'), i.get(\'dims\'), i.get(\'data_type\'), i.get(\'quant_params\')) for i in inputs])\n'
        'outputs = data.get(\'graph\', {}).get(\'outputs\', [])\n'
        'print(\'Outputs:\', [(o.get(\'name\'), o.get(\'dims\'), o.get(\'data_type\'), o.get(\'quant_params\')) for o in outputs])\n'
        'nodes = data.get(\'graph\', {}).get(\'nodes\', [])\n'
        'print(\'Total Nodes:\', len(nodes))\n'
        '"'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("=== INSPECTION OF GENERATED QNN MODEL ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    inspect_converted()
