#!/usr/bin/env python3
"""
process_isolation.py
--------------------
Selective Process Isolation and Environment Pre-Flight Auditor for KavachX.
Identifies only KavachX-specific test/validation scripts without affecting system processes.
"""

import os
import sys
import subprocess
import json

KNOWN_TEST_SCRIPT_PATTERNS = [
    "run_step10",
    "run_step9",
    "run_step8",
    "run_step7",
    "validate_split_model",
    "compare_fp32",
    "benchmark",
    "test_worker"
]

def audit_and_isolate_processes():
    print("=== [Process Isolation] Auditing Target System Processes ===")
    
    # Run ps aux to inspect active processes
    cmd = "ps -eo pid,user,pcpu,pmem,args"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    lines = res.stdout.strip().split("\n")
    
    stale_test_procs = []
    worker_procs = []
    other_kavach_procs = []
    system_procs = []
    
    my_pid = os.getpid()
    
    for line in lines[1:]:
        parts = line.strip().split(None, 4)
        if len(parts) < 5:
            continue
        pid_str, user, cpu_str, mem_str, args = parts
        try:
            pid = int(pid_str)
        except ValueError:
            continue
            
        if pid == my_pid:
            continue
            
        is_kavach = "kawachx" in args or "kawach" in args or "npu_worker" in args
        
        if "kawach_worker" in args and not args.endswith(".py"):
            worker_procs.append({
                "pid": pid, "user": user, "cpu": float(cpu_str), "mem": float(mem_str), "cmd": args
            })
        elif is_kavach:
            is_test_script = any(pat in args for pat in KNOWN_TEST_SCRIPT_PATTERNS)
            proc_info = {"pid": pid, "user": user, "cpu": float(cpu_str), "mem": float(mem_str), "cmd": args}
            if is_test_script:
                stale_test_procs.append(proc_info)
            else:
                other_kavach_procs.append(proc_info)
        else:
            if float(cpu_str) > 10.0:
                system_procs.append({"pid": pid, "user": user, "cpu": float(cpu_str), "cmd": args[:60]})

    print(f"  Active Production Workers found: {len(worker_procs)}")
    print(f"  Stale/Legacy Test Processes found: {len(stale_test_procs)}")
    
    # Selectively terminate only stale test processes
    terminated_procs = []
    for p in stale_test_procs:
        print(f"  -> Safely terminating stale test process PID {p['pid']}: {p['cmd'][:50]}")
        try:
            os.kill(p['pid'], 15) # SIGTERM
            terminated_procs.append(p)
        except Exception as e:
            print(f"     Warning: Could not terminate PID {p['pid']}: {e}")

    report = {
        "timestamp": subprocess.getoutput("date -u +%Y-%m-%dT%H:%M:%SZ"),
        "active_worker_processes": worker_procs,
        "stale_test_processes_detected": stale_test_procs,
        "stale_processes_terminated": terminated_procs,
        "high_cpu_system_processes": system_procs,
        "isolation_status": "CLEAN"
    }
    
    return report

if __name__ == "__main__":
    rep = audit_and_isolate_processes()
    print(json.dumps(rep, indent=2))
