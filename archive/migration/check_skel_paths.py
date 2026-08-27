#!/usr/bin/env python3
import subprocess

def run_cmd(cmd):
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', cmd], capture_output=True, text=True)
    print(f"=== {cmd} ===")
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)

run_cmd('ls -ld /home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned')
run_cmd('ls -la /home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned')
run_cmd('ls -la /vendor/dsp/cdsp 2>/dev/null; ls -la /usr/lib/rfsa/adsp 2>/dev/null; ls -la /lib/firmware 2>/dev/null')
run_cmd('env | grep -E "ADSP|LD_LIBRARY_PATH|QNN|QAIRT"')
