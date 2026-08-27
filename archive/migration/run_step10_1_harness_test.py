#!/usr/bin/env python3
"""
run_step10_1_harness_test.py
----------------------------
Step 10.1 Live-Stream Test Harness Verification.
Executes Process Isolation -> Startup Check -> 5s/30-frame Smoke Test -> Recovery Test -> Cleanup Verification.
"""

import os
import sys
import time
import json
import subprocess

# Ensure workspace in path
sys.path.insert(0, "/home/work_user2/kawachx_task")
from scripts.testing.process_isolation import audit_and_isolate_processes
from scripts.testing.bounded_stream_runner import run_bounded_test

REPORTS_DIR = "/home/work_user2/kawachx_task/results/step10_test_harness"

class Args:
    def __init__(self, test_name, source, duration, max_frames, timeout):
        self.test_name = test_name
        self.source_type = "video"
        self.source = source
        self.capture_fps = 30.0
        self.duration_seconds = duration
        self.max_frames = max_frames
        self.hard_timeout_seconds = timeout
        self.output_report = ""

def run_step10_1_suite():
    print("==================================================================")
    print("  KAVACHX STEP 10.1 — LIVE-STREAM TEST HARNESS VERIFICATION")
    print("==================================================================")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. PROCESS ISOLATION & AUDIT
    # -------------------------------------------------------------
    isolation_report = audit_and_isolate_processes()
    with open(f"{REPORTS_DIR}/process_isolation_report.json", "w") as f:
        json.dump(isolation_report, f, indent=2)
    print("  [Step 1] Process Isolation Complete (Report saved)")

    # -------------------------------------------------------------
    # 2. ENSURE PRODUCTION WORKER SERVICE IS READY
    # -------------------------------------------------------------
    print("\n  [Step 2] Ensuring Production Worker is in READY state...")
    service_script = "/home/work_user2/kawachx_task/scripts/service/kawach_service.py"
    subprocess.run([sys.executable, service_script, "start"], check=True)
    time.sleep(1.0)

    # -------------------------------------------------------------
    # 3. RUN BOUNDED SMOKE TEST (5 Seconds OR 30 Frames)
    # -------------------------------------------------------------
    print("\n  [Step 3] Running Bounded Smoke Test (Limit: 5s OR 30 Frames)...")
    video_path = "/home/work_user2/kawachx_task/test_images/live_test_stream.mp4"
    smoke_args = Args(
        test_name="Smoke_Test_5s_30Frames",
        source=video_path,
        duration=5.0,
        max_frames=30,
        timeout=8.0
    )
    smoke_report = run_bounded_test(smoke_args)
    with open(f"{REPORTS_DIR}/smoke_test_report.json", "w") as f:
        json.dump(smoke_report, f, indent=2)

    # -------------------------------------------------------------
    # 4. RECOVERY TEST (Client Abrupt Disconnect & Worker Survival)
    # -------------------------------------------------------------
    print("\n  [Step 4] Running Client Abrupt Disconnect & Worker Survival Test...")
    import socket
    import struct
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/tmp/kawach_worker.sock")
    # Send partial 100 bytes and close abruptly
    s.sendall(struct.pack("=IIII", 0x4B574158, 999, 1000000, 0) + b"\x00"*100)
    s.close()
    time.sleep(0.5)

    # Verify worker is still alive and accepting requests
    recovery_args = Args(
        test_name="Post_Disconnect_Recovery_Check",
        source=video_path,
        duration=2.0,
        max_frames=10,
        timeout=5.0
    )
    recovery_report = run_bounded_test(recovery_args)
    recovery_passed = (recovery_report["verdict"] == "PASS")
    print(f"  Worker Recovery after Client Disconnect: {'PASS' if recovery_passed else 'FAIL'}")

    # -------------------------------------------------------------
    # 5. POST-TEST CLEANUP VERIFICATION
    # -------------------------------------------------------------
    print("\n  [Step 5] Verifying Post-Test Cleanup & System Health...")
    post_isolation = audit_and_isolate_processes()
    
    # Check if worker is running
    worker_alive = len(post_isolation["active_worker_processes"]) == 1
    no_zombie_tests = len(post_isolation["stale_test_processes_detected"]) == 0
    socket_exists = os.path.exists("/tmp/kawach_worker.sock")

    cleanup_report = {
        "timestamp": subprocess.getoutput("date -u +%Y-%m-%dT%H:%M:%SZ"),
        "worker_alive_and_ready": worker_alive,
        "no_zombie_test_processes": no_zombie_tests,
        "ipc_socket_healthy": socket_exists,
        "smoke_test_verdict": smoke_report["verdict"],
        "recovery_test_verdict": "PASS" if recovery_passed else "FAIL",
        "verdict": "PASS" if (worker_alive and no_zombie_tests and socket_exists and smoke_report["verdict"] == "PASS") else "FAIL"
    }

    with open(f"{REPORTS_DIR}/cleanup_report.json", "w") as f:
        json.dump(cleanup_report, f, indent=2)

    print("\n==================================================================")
    print(f"  STEP 10.1 HARNESS RESULT: {cleanup_report['verdict']}")
    print(f"  Smoke Test: {smoke_report['verdict']} | Terminated: {smoke_report['termination_reason']}")
    print(f"  Processed {smoke_report['processed_frames']} frames in {smoke_report['duration_seconds']}s ({smoke_report['average_fps']} FPS)")
    print(f"  HTP Inferences: {smoke_report['htp_inferences']} | CPU Fallback: {smoke_report['cpu_fallback_count']}")
    print(f"  Worker Survival: {'PASS' if worker_alive else 'FAIL'}")
    print("==================================================================")

if __name__ == "__main__":
    run_step10_1_suite()
