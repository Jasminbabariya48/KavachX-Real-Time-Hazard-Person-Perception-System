#!/usr/bin/env python3
"""
kawach_service.py
-----------------
Production Service Lifecycle Supervisor & Startup Self-Check for KavachX NPU Worker.
Commands:
  start      - Perform deterministic pre-flight self-checks & launch daemon
  stop       - Gracefully terminate daemon and clean up socket/PID files
  restart    - Stop and restart daemon
  status     - Query process, IPC, and health status
  supervise  - Run foreground supervisor with auto-restart recovery
  self-check - Run standalone pre-flight validation suite
"""

import sys
import os
import time
import signal
import socket
import struct
import json
import hashlib
import subprocess

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "production_config.json")
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = "/home/work_user2/kawachx_task/config/production_config.json"

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "service_name": "kawach_worker",
        "qnn_paths": {
            "backend_lib": "/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnHtp.so",
            "system_lib": "/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4/libQnnSystem.so",
            "adsp_library_path": "/home/devuser/qairt/2.47.0.260601/lib/hexagon-v68/unsigned;/vendor/dsp/cdsp;/vendor/lib/rfsa/adsp;/dsp",
            "ld_library_path": "/home/devuser/qairt/2.47.0.260601/lib/aarch64-ubuntu-gcc9.4"
        },
        "model": {
            "context_binary_path": "/home/work_user2/kawachx_task/models/3class_calibrated_final.bin",
            "expected_sha256": "b7868a8c436fcf723fea7f95b3dcfd6f131fbe8ddb02ddf103addbe351dafabc"
        },
        "ipc": {
            "socket_path": "/tmp/kawach_worker.sock",
            "health_file": "/tmp/kawach_health.json",
            "pid_file": "/tmp/kawach_worker.pid",
            "log_file": "/tmp/kawach_worker.log"
        }
    }

def run_self_check(cfg):
    print("=== RUNNING DETERMINISTIC PRE-FLIGHT STARTUP SELF-CHECK ===")
    checks = []
    
    # 1. Check FastRPC Device
    dev_path = "/dev/fastrpc-cdsp"
    if os.path.exists(dev_path):
        can_open = os.access(dev_path, os.R_OK | os.W_OK)
        checks.append({"check": "FastRPC Device Access", "status": "PASS" if can_open else "FAIL", "path": dev_path})
    else:
        checks.append({"check": "FastRPC Device Exists", "status": "FAIL", "path": dev_path})

    # 2. Check QNN Backend and System Libraries
    backend_lib = cfg["qnn_paths"]["backend_lib"]
    system_lib = cfg["qnn_paths"]["system_lib"]
    checks.append({"check": "libQnnHtp.so Exists", "status": "PASS" if os.path.exists(backend_lib) else "FAIL", "path": backend_lib})
    checks.append({"check": "libQnnSystem.so Exists", "status": "PASS" if os.path.exists(system_lib) else "FAIL", "path": system_lib})

    # 3. Check Model File & SHA256 Integrity
    model_path = cfg["model"]["context_binary_path"]
    if not os.path.isabs(model_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(base_dir, model_path)
        if not os.path.exists(model_path):
            model_path = f"/home/work_user2/kawachx_task/{cfg['model']['context_binary_path']}"

    if os.path.exists(model_path):
        h = hashlib.sha256()
        with open(model_path, "rb") as f:
            while chunk := f.read(65536): h.update(chunk)
        calc_sha = h.hexdigest()
        exp_sha = cfg["model"]["expected_sha256"]
        sha_ok = (calc_sha == exp_sha)
        checks.append({"check": "Model File & Checksum Integrity", "status": "PASS" if sha_ok else "FAIL", "sha256": calc_sha})
    else:
        checks.append({"check": "Model File Exists", "status": "FAIL", "path": model_path})

    # 4. Check Worker Binary
    worker_bin = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "npu_worker", "kawach_worker")
    if not os.path.exists(worker_bin):
        worker_bin = "/home/work_user2/kawachx_task/native/worker/kawach_worker"
    checks.append({"check": "Worker Binary Exists", "status": "PASS" if os.path.exists(worker_bin) else "FAIL", "path": worker_bin})

    all_passed = all(c["status"] == "PASS" for c in checks)
    for c in checks:
        print(f"  [{c['status']}] {c['check']}")
        
    return all_passed, checks, worker_bin, model_path

def write_health(cfg, state, details=None):
    health_file = cfg["ipc"]["health_file"]
    data = {
        "service": cfg["service_name"],
        "state": state,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details or {}
    }
    try:
        with open(health_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[service] Warning: Failed to write health file: {e}")

def get_pid(cfg):
    pid_file = cfg["ipc"]["pid_file"]
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            # Check if process is alive
            os.kill(pid, 0)
            return pid
        except Exception:
            return None
    return None

def start_service(cfg, foreground=False):
    pid = get_pid(cfg)
    if pid:
        print(f"[service] kawach_worker is already running (PID {pid})")
        return True

    passed, checks, worker_bin, model_path = run_self_check(cfg)
    if not passed:
        print("[service] FATAL: Pre-flight startup self-check failed! Refusing to start.")
        write_health(cfg, "FAILED", {"checks": checks, "error": "Self-check failed"})
        return False

    sock_path = cfg["ipc"]["socket_path"]
    if os.path.exists(sock_path):
        try: os.unlink(sock_path)
        except Exception: pass

    env = os.environ.copy()
    env["ADSP_LIBRARY_PATH"] = cfg["qnn_paths"]["adsp_library_path"]
    env["LD_LIBRARY_PATH"] = f"{cfg['qnn_paths']['ld_library_path']}:{env.get('LD_LIBRARY_PATH', '')}"

    cmd = [
        worker_bin,
        "--backend", cfg["qnn_paths"]["backend_lib"],
        "--system",  cfg["qnn_paths"]["system_lib"],
        "--model",   model_path,
        "--socket",  sock_path
    ]

    log_path = cfg["ipc"]["log_file"]
    log_fd = open(log_path, "a")

    write_health(cfg, "STARTING", {"command": cmd})
    print(f"[service] Launching {cfg['service_name']} (Logging to {log_path})...")

    proc = subprocess.Popen(cmd, env=env, stdout=log_fd, stderr=subprocess.STDOUT)
    with open(cfg["ipc"]["pid_file"], "w") as pf:
        pf.write(str(proc.pid))

    # Wait up to 4 seconds for socket to be created
    socket_ready = False
    for _ in range(20):
        if os.path.exists(sock_path):
            socket_ready = True
            break
        time.sleep(0.2)
        if proc.poll() is not None:
            break
        time.sleep(0.2)

    if socket_ready:
        print(f"[service] kawach_worker successfully started (PID {proc.pid}) — READY")
        write_health(cfg, "READY", {"pid": proc.pid, "model": model_path, "socket": sock_path})
        return True
    else:
        print(f"[service] FATAL: Process exited prematurely with code {proc.poll()}")
        write_health(cfg, "FAILED", {"error": f"Process exited with code {proc.poll()}"})
        return False

def stop_service(cfg):
    pid = get_pid(cfg)
    if not pid:
        print("[service] kawach_worker is not running")
        # Clean stale files
        for f in [cfg["ipc"]["socket_path"], cfg["ipc"]["pid_file"]]:
            if os.path.exists(f):
                try: os.unlink(f)
                except Exception: pass
        write_health(cfg, "STOPPED")
        return True

    print(f"[service] Stopping kawach_worker (PID {pid})...")
    write_health(cfg, "STOPPING", {"pid": pid})

    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(25):
            try:
                os.kill(pid, 0)
                time.sleep(0.2)
            except OSError:
                break
        else:
            print("[service] Process did not exit cleanly, sending SIGKILL...")
            os.kill(pid, signal.SIGKILL)
    except Exception as e:
        print(f"[service] Error during shutdown: {e}")

    for f in [cfg["ipc"]["socket_path"], cfg["ipc"]["pid_file"]]:
        if os.path.exists(f):
            try: os.unlink(f)
            except Exception: pass

    write_health(cfg, "STOPPED")
    print("[service] kawach_worker stopped successfully")
    return True

def status_service(cfg):
    pid = get_pid(cfg)
    health_file = cfg["ipc"]["health_file"]
    health = {}
    if os.path.exists(health_file):
        try:
            with open(health_file, "r") as f: health = json.load(f)
        except Exception: pass

    sock_path = cfg["ipc"]["socket_path"]
    ipc_ok = False
    if os.path.exists(sock_path) and pid:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(sock_path)
            s.close()
            ipc_ok = True
        except Exception:
            ipc_ok = False

    status_report = {
        "service": cfg["service_name"],
        "running": pid is not None,
        "pid": pid,
        "ipc_socket": sock_path,
        "ipc_responsive": ipc_ok,
        "health_state": health.get("state", "UNKNOWN" if pid else "STOPPED"),
        "health_details": health.get("details", {})
    }

    print("=== KAWACH_WORKER SERVICE STATUS ===")
    print(f"  Status:       {'RUNNING' if pid else 'STOPPED'}")
    print(f"  PID:          {pid or 'N/A'}")
    print(f"  State:        {status_report['health_state']}")
    print(f"  Socket:       {sock_path} ({'ACTIVE' if ipc_ok else 'INACTIVE'})")
    return status_report

def supervise_service(cfg):
    print("=== STARTING KAWACH_WORKER SERVICE SUPERVISOR ===")
    stop_service(cfg)
    
    while True:
        try:
            ok = start_service(cfg)
            if not ok:
                print("[supervisor] Start failed, retrying in 5s...")
                time.sleep(5.0)
                continue
                
            pid = get_pid(cfg)
            while pid and get_pid(cfg):
                time.sleep(1.0)
                
            print("[supervisor] Worker crash or exit detected! Initiating recovery...")
            write_health(cfg, "DEGRADED", {"event": "Worker died unexpectedly, restarting"})
            time.sleep(cfg["lifecycle"]["restart_delay_sec"])
        except KeyboardInterrupt:
            print("\n[supervisor] Interrupted by user, shutting down...")
            stop_service(cfg)
            break

def main():
    cfg = load_config()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "start":
        ok = start_service(cfg)
        sys.exit(0 if ok else 1)
    elif cmd == "stop":
        ok = stop_service(cfg)
        sys.exit(0 if ok else 1)
    elif cmd == "restart":
        stop_service(cfg)
        time.sleep(0.5)
        ok = start_service(cfg)
        sys.exit(0 if ok else 1)
    elif cmd == "status":
        status_service(cfg)
        sys.exit(0)
    elif cmd == "self-check":
        ok, _, _, _ = run_self_check(cfg)
        sys.exit(0 if ok else 1)
    elif cmd == "supervise":
        supervise_service(cfg)
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: kawach_service.py [start|stop|restart|status|self-check|supervise]")
        sys.exit(1)

if __name__ == "__main__":
    main()
