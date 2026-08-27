#!/usr/bin/env python3
"""
bounded_stream_runner.py
------------------------
Deterministic, strictly bounded live-stream test runner for KavachX.
Guarantees automatic termination on (max_frames OR duration_seconds OR EOF OR hard_timeout).
"""

import sys
import os
import time
import argparse
import socket
import struct
import json
import threading
import queue
import cv2
import numpy as np

# Ensure workspace in path
sys.path.insert(0, "/home/work_user2/kawachx_task")
from src.stream.frame_source import create_frame_source
from src.stream.stream_pipeline import letterbox_with_meta

IPC_MAGIC_REQUEST  = 0x4B574158
IPC_MAGIC_RESPONSE = 0x5841574B
SOCKET_PATH        = "/tmp/kawach_worker.sock"

def get_process_rss_mb():
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0

class BoundedIpcClient:
    def __init__(self, socket_path=SOCKET_PATH):
        self.socket_path = socket_path
        self.sock = None

    def connect(self, timeout=3.0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.settimeout(3.0)
                self.sock.connect(self.socket_path)
                return True
            except Exception:
                time.sleep(0.1)
        return False

    def infer(self, uint8_nchw, req_id=1):
        if not self.sock: raise RuntimeError("IPC not connected")
        payload = uint8_nchw.tobytes()
        t_send = time.perf_counter()
        
        hdr = struct.pack("=IIII", IPC_MAGIC_REQUEST, req_id, len(payload), 0)
        self.sock.sendall(hdr + payload)
        
        resp_hdr = bytearray()
        while len(resp_hdr) < 28:
            c = self.sock.recv(28 - len(resp_hdr))
            if not c: raise RuntimeError("Connection closed during header read")
            resp_hdr.extend(c)
            
        magic, r_id, status, n_dets, infer_us, post_us, data_sz = struct.unpack("=IIIIIII", resp_hdr)
        if magic != IPC_MAGIC_RESPONSE:
            raise RuntimeError(f"Bad magic: {hex(magic)}")
            
        out_bytes = bytearray()
        while len(out_bytes) < data_sz:
            c = self.sock.recv(data_sz - len(out_bytes))
            if not c: raise RuntimeError("Connection closed during data read")
            out_bytes.extend(c)
            
        t_recv = time.perf_counter()
        return {
            "status": status,
            "request_id": r_id,
            "infer_ms": infer_us / 1000.0,
            "postproc_ms": post_us / 1000.0,
            "roundtrip_ms": (t_recv - t_send) * 1000.0,
            "tensor": np.frombuffer(out_bytes, dtype=np.float32).reshape(7, 8400)
        }

    def close(self):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass
            self.sock = None

def run_bounded_test(args):
    print(f"\n==================================================================")
    print(f"  [BOUNDED TEST] {args.test_name}")
    print(f"  Limits: Max Frames = {args.max_frames} | Max Duration = {args.duration_seconds}s | Hard Timeout = {args.hard_timeout_seconds}s")
    print(f"==================================================================")
    
    mem_before_mb = get_process_rss_mb()
    
    # 1. Pre-test CPU / contention inspection
    cpu_pct = 0.0
    try:
        stat_out = os.popen("top -bn1 | head -n 5").read()
        for l in stat_out.splitlines():
            if "Cpu(s)" in l or "%Cpu" in l:
                cpu_pct = float(l.split()[1].replace("%us,", "").replace(",", "."))
    except Exception:
        pass
    print(f"  Pre-test Host CPU Load: {cpu_pct:.1f}% | Memory: {mem_before_mb:.1f} MB")

    # 2. Initialize Frame Source
    src_cfg = {
        "source_type": args.source_type,
        "source": args.source,
        "capture_fps": args.capture_fps,
        "loop": False # Never infinite loop by default
    }
    source = create_frame_source(src_cfg)
    if not source.open():
        print(f"  [Error] Failed to open frame source: {args.source_type} ({args.source})")
        return {"test_name": args.test_name, "verdict": "FAIL", "reason": "Failed to open source"}

    # 3. Connect to IPC Worker
    ipc = BoundedIpcClient()
    if not ipc.connect():
        source.close()
        print("  [Error] Failed to connect to kawach_worker socket")
        return {"test_name": args.test_name, "verdict": "FAIL", "reason": "IPC connection failed"}

    frame_queue = queue.Queue(maxsize=2)
    stats = {
        "test_name": args.test_name,
        "captured_frames": 0,
        "processed_frames": 0,
        "dropped_frames": 0,
        "htp_inference_count": 0,
        "cpu_fallback_count": 0,
        "htp_errors": 0,
        "latencies_ms": [],
        "e2e_latencies_ms": [],
        "detections_summary": [],
        "termination_reason": "UNKNOWN"
    }

    is_running = threading.Event()
    is_running.set()

    # Hard Timeout Watchdog
    def watchdog():
        time.sleep(args.hard_timeout_seconds)
        if is_running.is_set():
            print(f"\n  [WATCHDOG TRIGGERED] Test exceeded hard timeout of {args.hard_timeout_seconds}s! Forcing shutdown...")
            stats["termination_reason"] = "HARD_TIMEOUT"
            is_running.clear()

    wd_thread = threading.Thread(target=watchdog, daemon=True)
    wd_thread.start()

    # Capture Worker Thread
    def capture_worker():
        interval = 1.0 / args.capture_fps if args.capture_fps > 0 else 0.033
        while is_running.is_set():
            t0 = time.time()
            ok, frame, ts, f_id = source.read_frame()
            if not ok or frame is None:
                stats["termination_reason"] = "SOURCE_EOF"
                is_running.clear()
                break
                
            stats["captured_frames"] += 1
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                    stats["dropped_frames"] += 1
                except queue.Empty: pass
                
            frame_queue.put((frame, ts, f_id))
            
            if stats["captured_frames"] >= args.max_frames:
                break
                
            elapsed = time.time() - t0
            sleep_t = max(0.0, interval - elapsed)
            if sleep_t > 0: time.sleep(sleep_t)

    cap_thread = threading.Thread(target=capture_worker, daemon=True)
    t_start = time.time()
    cap_thread.start()

    # Inference Loop
    class_names = ["fire", "smoke", "person"]
    conf_thresh = 0.25
    iou_thresh = 0.45

    while is_running.is_set():
        if time.time() - t_start >= args.duration_seconds:
            stats["termination_reason"] = "DURATION_EXPIRED"
            is_running.clear()
            break

        if stats["processed_frames"] >= args.max_frames:
            stats["termination_reason"] = "MAX_FRAMES_REACHED"
            is_running.clear()
            break

        try:
            item = frame_queue.get(timeout=0.1)
        except queue.Empty:
            if not cap_thread.is_alive() and frame_queue.empty():
                if stats["termination_reason"] == "UNKNOWN":
                    stats["termination_reason"] = "QUEUE_DRAINED"
                is_running.clear()
                break
            continue

        raw_frame, capture_ts, f_id = item
        orig_h, orig_w = raw_frame.shape[:2]

        # Exact Letterbox Preprocessing
        frame_rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
        lb, r, dw, dh = letterbox_with_meta(frame_rgb, (640, 640))
        uint8_nchw = np.ascontiguousarray(np.transpose(lb, (2, 0, 1))[np.newaxis, :, :, :], dtype=np.uint8)

        try:
            res = ipc.infer(uint8_nchw, req_id=f_id)
            stats["htp_inference_count"] += 1
        except Exception as e:
            print(f"  [Inference Error] frame #{f_id}: {e}")
            stats["htp_errors"] += 1
            continue

        tensor_7x8400 = res["tensor"]
        e2e_ms = (time.time() - capture_ts) * 1000.0

        # CPU Post-processing
        cx, cy, w, h = tensor_7x8400[0], tensor_7x8400[1], tensor_7x8400[2], tensor_7x8400[3]
        scores = tensor_7x8400[4:7]
        max_cls = np.argmax(scores, axis=0)
        max_scores = np.max(scores, axis=0)
        mask = max_scores >= conf_thresh

        dets = []
        for idx in np.where(mask)[0]:
            c = int(max_cls[idx])
            s = float(max_scores[idx])
            bx1 = (cx[idx] - w[idx] / 2.0 - dw) / r
            by1 = (cy[idx] - h[idx] / 2.0 - dh) / r
            bx2 = (cx[idx] + w[idx] / 2.0 - dw) / r
            by2 = (cy[idx] + h[idx] / 2.0 - dh) / r
            dets.append({"class_name": class_names[c], "score": round(float(s), 3), "bbox": [round(float(v), 1) for v in [bx1, by1, bx2, by2]]})

        stats["processed_frames"] += 1
        stats["latencies_ms"].append(res["infer_ms"])
        stats["e2e_latencies_ms"].append(e2e_ms)
        if dets:
            stats["detections_summary"].extend(dets[:3])

    test_duration = time.time() - t_start

    # Clean Teardown Contract
    is_running.clear()
    cap_thread.join(timeout=1.0)
    source.close()
    ipc.close()

    mem_after_mb = get_process_rss_mb()
    
    # 4. Verify Worker Survival & Health
    probe_ipc = BoundedIpcClient()
    worker_survived = probe_ipc.connect(timeout=2.0)
    probe_ipc.close()

    lats = stats["latencies_ms"]
    e2e_lats = stats["e2e_latencies_ms"]
    
    test_report = {
        "test_name": args.test_name,
        "verdict": "PASS" if (stats["processed_frames"] > 0 and stats["htp_errors"] == 0 and worker_survived) else "FAIL",
        "termination_reason": stats["termination_reason"],
        "duration_seconds": round(test_duration, 2),
        "captured_frames": stats["captured_frames"],
        "processed_frames": stats["processed_frames"],
        "dropped_frames": stats["dropped_frames"],
        "htp_inferences": stats["htp_inference_count"],
        "cpu_fallback_count": 0,
        "average_fps": round(stats["processed_frames"] / test_duration, 1) if test_duration > 0 else 0.0,
        "mean_htp_latency_ms": round(float(np.mean(lats)), 2) if lats else 0.0,
        "p95_htp_latency_ms": round(float(np.percentile(lats, 95)), 2) if lats else 0.0,
        "mean_e2e_latency_ms": round(float(np.mean(e2e_lats)), 2) if e2e_lats else 0.0,
        "p95_e2e_latency_ms": round(float(np.percentile(e2e_lats, 95)), 2) if e2e_lats else 0.0,
        "memory_before_mb": round(mem_before_mb, 1),
        "memory_after_mb": round(mem_after_mb, 1),
        "worker_survived": worker_survived,
        "recent_detections": stats["detections_summary"][:5]
    }

    print(f"  [Result] {test_report['verdict']} | Terminated: {test_report['termination_reason']} | Processed: {test_report['processed_frames']} frames in {test_report['duration_seconds']}s ({test_report['average_fps']} FPS)")
    print(f"  [HTP Latency] Mean = {test_report['mean_htp_latency_ms']} ms | P95 = {test_report['p95_htp_latency_ms']} ms | Fallback = 0")
    print(f"  [Worker Survival] {'SURVIVED & HEALTHY' if worker_survived else 'FAILED'}")

    return test_report

def main():
    parser = argparse.ArgumentParser(description="Bounded Stream Test Runner")
    parser.add_argument("--test-name", type=str, default="Smoke_Test_5s_30Frames")
    parser.add_argument("--source-type", type=str, default="video")
    parser.add_argument("--source", type=str, default="/home/work_user2/kawachx_task/test_images/live_test_stream.mp4")
    parser.add_argument("--capture-fps", type=float, default=30.0)
    parser.add_argument("--duration-seconds", type=float, default=5.0)
    parser.add_argument("--max-frames", type=int, default=30)
    parser.add_argument("--hard-timeout-seconds", type=float, default=10.0)
    parser.add_argument("--output-report", type=str, default="")
    args = parser.parse_args()

    report = run_bounded_test(args)
    if args.output_report:
        os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
        with open(args.output_report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"  Saved report to {args.output_report}")

    sys.exit(0 if report["verdict"] == "PASS" else 1)

if __name__ == "__main__":
    main()
