#!/usr/bin/env python3
import subprocess
import sys

def run_remote(cmd: str, timeout: int = 120):
    print(f"=== REMOTE CMD: {cmd} ===")
    res = subprocess.run(
        ["ssh", "-n", "work_user2@ssh.kavachx.io", cmd],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
    print(f"EXIT CODE: {res.returncode}")
    return res

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_remote(" ".join(sys.argv[1:]))
    else:
        print("Usage: python scripts/run_remote.py <command>")
