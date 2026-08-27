"""System Diagnostics & FastRPC Health Checker."""
import os
import subprocess

def run_diagnostics():
    print("=== KavachX System Diagnostics ===")
    print("FastRPC Node:     ", "EXISTS (/dev/fastrpc-cdsp)" if os.path.exists("/dev/fastrpc-cdsp") else "MISSING")
    print("QNN Runtime Path: ", os.environ.get("LD_LIBRARY_PATH", "DEFAULT"))
    print("ADSP Path:        ", os.environ.get("ADSP_LIBRARY_PATH", "DEFAULT"))
    print("Health Status:    ", subprocess.getoutput("cat /tmp/kawach_health.json 2>/dev/null || echo 'NOT RUNNING'"))

if __name__ == "__main__":
    run_diagnostics()
