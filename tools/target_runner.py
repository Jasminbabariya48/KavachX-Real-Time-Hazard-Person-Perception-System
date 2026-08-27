"""Target Remote Execution & Verification Driver."""
import subprocess
import sys

def execute_remote(cmd: str):
    full_cmd = (
        'export ADSP_LIBRARY_PATH="/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp"; '
        'export LD_LIBRARY_PATH=/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4:$LD_LIBRARY_PATH; '
        'export PYTHONPATH=/home/work_user2/kawachx_task/src:/home/work_user2/kawachx_task:$PYTHONPATH; '
        f'{cmd}'
    )
    res = subprocess.run(['ssh', '-n', '-o', 'ControlMaster=no', 'work_user2@ssh.kavachx.io', full_cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:")
        print(res.stderr)
    return res.returncode

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cat /tmp/kawach_health.json"
    sys.exit(execute_remote(cmd))
