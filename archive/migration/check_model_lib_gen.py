#!/usr/bin/env python3
import subprocess

def run_remote(cmd):
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
    return res

run_remote('source /home/devuser/qairt/2.47.0.260601/bin/envsetup.sh; which qnn-model-lib-generator; qnn-model-lib-generator -h | head -n 35')
