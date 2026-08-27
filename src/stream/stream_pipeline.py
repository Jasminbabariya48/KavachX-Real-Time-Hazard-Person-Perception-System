"""
stream_pipeline.py
------------------
High-Performance Real-Time Live Stream Pipeline for KavachX.
Connects live FrameSource -> Exact Letterbox Preprocessing -> IPC -> Qualcomm Hexagon v68 HTP -> CPU DFL/NMS -> Alerting -> Live Monitoring Stream.
"""

import time
import socket
import struct
import threading
import queue
import json
import cv2
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

IPC_MAGIC_REQUEST  = 0x4B574158
IPC_MAGIC_RESPONSE = 0x5841574B

def letterbox_with_meta(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2] # [h, w]
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img, r, dw, dh

class StreamIpcClient:
    def __init__(self, socket_path="/tmp/kawach_worker.sock"):
        self.socket_path = socket_path
        self.sock = None

    def connect(self, timeout=5.0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.connect(self.socket_path)
                return True
            except Exception:
                time.sleep(0.1)
        return False

    def infer(self, uint8_nchw, req_id=1):
        if not self.sock: raise RuntimeError("IPC not connected")
        payload = uint8_nchw.tobytes()
        t_ipc_send = time.perf_counter()
        
        # Send IpcRequestHeader (16 bytes) + payload (1,228,800 bytes)
        hdr = struct.pack("=IIII", IPC_MAGIC_REQUEST, req_id, len(payload), 0)
        self.sock.sendall(hdr + payload)
        
        # Read IpcResponseHeader (28 bytes)
        resp_hdr = bytearray()
        while len(resp_hdr) < 28:
            c = self.sock.recv(28 - len(resp_hdr))
            if not c: raise RuntimeError("IPC closed during header read")
            resp_hdr.extend(c)
            
        magic, r_id, status, n_dets, infer_us, post_us, data_sz = struct.unpack("=IIIIIII", resp_hdr)
        if magic != IPC_MAGIC_RESPONSE:
            raise RuntimeError(f"Bad magic: {hex(magic)}")
            
        # Read payload (235,200 bytes float32 tensor [1, 7, 8400])
        out_bytes = bytearray()
        while len(out_bytes) < data_sz:
            c = self.sock.recv(data_sz - len(out_bytes))
            if not c: raise RuntimeError("IPC closed during data read")
            out_bytes.extend(c)
            
        t_ipc_recv = time.perf_counter()
        return {
            "status": status,
            "request_id": r_id,
            "infer_ms": infer_us / 1000.0,
            "postproc_ms": post_us / 1000.0,
            "ipc_roundtrip_ms": (t_ipc_recv - t_ipc_send) * 1000.0,
            "tensor": np.frombuffer(out_bytes, dtype=np.float32).reshape(7, 8400)
        }

    def close(self):
        if self.sock:
            try: self.sock.close()
            except Exception: pass
            self.sock = None

class LiveStreamPipeline:
    def __init__(self, config, frame_source):
        self.config = config
        self.source = frame_source
        self.ipc_client = StreamIpcClient(config.get("ipc", {}).get("socket_path", "/tmp/kawach_worker.sock"))
        
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=config.get("stream", {}).get("queue_size", 2))
        
        # Statistics & Metrics
        self.stats = {
            "captured_frames": 0,
            "processed_frames": 0,
            "dropped_frames": 0,
            "htp_inference_count": 0,
            "cpu_fallback_count": 0,
            "htp_errors": 0,
            "total_alerts": 0,
            "recent_latencies_ms": [],
            "recent_e2e_latencies_ms": [],
            "live_fps": 0.0,
            "inference_fps": 0.0
        }
        
        # Alert state & debouncing
        self.alert_cooldowns = {} # key: class_name -> last_alert_time
        self.recent_alerts = []
        self.latest_annotated_frame = None
        self.lock = threading.Lock()

    def start(self):
        if not self.ipc_client.connect():
            print("[StreamPipeline] Error: Could not connect to kawach_worker IPC")
            return False
            
        if not self.source.open():
            print("[StreamPipeline] Error: Could not open frame source")
            return False
            
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.inference_thread = threading.Thread(target=self._inference_worker, daemon=True)
        
        self.capture_thread.start()
        self.inference_thread.start()
        print("[StreamPipeline] Live Stream Pipeline successfully started")
        return True

    def _capture_worker(self):
        fps = self.config.get("stream", {}).get("capture_fps", 30.0)
        interval = 1.0 / fps if fps > 0 else 0.033
        
        while self.is_running:
            t0 = time.time()
            ok, frame, ts, f_id = self.source.read_frame()
            if not ok or frame is None:
                time.sleep(0.05)
                continue
                
            self.stats["captured_frames"] += 1
            
            # Latest-frame queue strategy: drop older frame if queue full
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                    self.stats["dropped_frames"] += 1
                except queue.Empty: pass
                
            self.frame_queue.put((frame, ts, f_id))
            
            elapsed = time.time() - t0
            sleep_time = max(0.0, interval - elapsed)
            if sleep_time > 0: time.sleep(sleep_time)

    def _inference_worker(self):
        conf_thresh = self.config.get("postprocessing", {}).get("confidence_threshold", 0.25)
        iou_thresh = self.config.get("postprocessing", {}).get("iou_threshold", 0.45)
        cooldown_sec = self.config.get("alerting", {}).get("cooldown_sec", 3.0)
        
        t_fps_start = time.time()
        fps_frame_count = 0
        
        while self.is_running:
            try:
                frame_data = self.frame_queue.get(timeout=0.2)
            except queue.Empty:
                continue
                
            raw_frame, capture_ts, frame_id = frame_data
            t_proc_start = time.perf_counter()
            orig_h, orig_w = raw_frame.shape[:2]
            
            # 1. Exact letterbox preprocessing
            frame_rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
            lb, r, dw, dh = letterbox_with_meta(frame_rgb, (640, 640))
            uint8_nchw = np.ascontiguousarray(np.transpose(lb, (2, 0, 1))[np.newaxis, :, :, :], dtype=np.uint8)
            
            # 2. HTP Hardware Inference via IPC
            try:
                res = self.ipc_client.infer(uint8_nchw, req_id=frame_id)
                self.stats["htp_inference_count"] += 1
            except Exception as e:
                print(f"[StreamPipeline] HTP IPC error: {e}")
                self.stats["htp_errors"] += 1
                # Try reconnecting IPC
                self.ipc_client.close()
                self.ipc_client.connect()
                continue
                
            tensor_7x8400 = res["tensor"]
            
            # 3. CPU Vectorized Decode & Coordinate Unpadding
            cx, cy, w, h = tensor_7x8400[0], tensor_7x8400[1], tensor_7x8400[2], tensor_7x8400[3]
            scores = tensor_7x8400[4:7]
            class_names = self.config.get("postprocessing", {}).get("classes", ["fire", "smoke", "person"])
            
            max_cls = np.argmax(scores, axis=0)
            max_scores = np.max(scores, axis=0)
            mask = max_scores >= conf_thresh
            
            raw_dets = []
            for idx in np.where(mask)[0]:
                c = int(max_cls[idx])
                s = float(max_scores[idx])
                
                # Unpad coordinates back to original image size
                bx1 = (cx[idx] - w[idx] / 2.0 - dw) / r
                by1 = (cy[idx] - h[idx] / 2.0 - dh) / r
                bx2 = (cx[idx] + w[idx] / 2.0 - dw) / r
                by2 = (cy[idx] + h[idx] / 2.0 - dh) / r
                
                bx1 = max(0.0, min(float(orig_w), float(bx1)))
                by1 = max(0.0, min(float(orig_h), float(by1)))
                bx2 = max(0.0, min(float(orig_w), float(bx2)))
                by2 = max(0.0, min(float(orig_h), float(by2)))
                
                raw_dets.append({"class_id": c, "class_name": class_names[c], "score": s, "bbox": [bx1, by1, bx2, by2]})
                
            # NMS
            raw_dets.sort(key=lambda d: d["score"], reverse=True)
            kept_dets = []
            for d1 in raw_dets:
                suppressed = False
                for d2 in kept_dets:
                    if d1["class_id"] == d2["class_id"]:
                        b1, b2 = d1["bbox"], d2["bbox"]
                        ix1, iy1 = max(b1[0], b2[0]), max(b1[1], b2[1])
                        ix2, iy2 = min(b1[2], b2[2]), min(b1[3], b2[3])
                        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
                        union = (b1[2]-b1[0])*(b1[3]-b1[1]) + (b2[2]-b2[0])*(b2[3]-b2[1]) - inter
                        iou = inter / union if union > 0 else 0.0
                        if iou >= iou_thresh:
                            suppressed = True
                            break
                if not suppressed: kept_dets.append(d1)

            t_proc_end = time.perf_counter()
            e2e_lat_ms = (time.time() - capture_ts) * 1000.0
            
            # 4. Debounced Alert Dispatcher
            now = time.time()
            for d in kept_dets:
                c_name = d["class_name"]
                if d["score"] >= self.config.get("alerting", {}).get("event_dispatch_threshold", 0.35):
                    last_alert = self.alert_cooldowns.get(c_name, 0.0)
                    if now - last_alert >= cooldown_sec:
                        self.alert_cooldowns[c_name] = now
                        severity = "CRITICAL" if c_name == "fire" else "WARNING"
                        event_type = "HAZARD_DETECTED" if c_name in ["fire", "smoke"] else "PERSON_DETECTED"
                        evt = {
                            "event_id": f"EVT_{c_name.upper()}_{int(now*1000)}",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
                            "frame_id": frame_id,
                            "event_type": event_type,
                            "severity": severity,
                            "class_name": c_name,
                            "confidence": round(d["score"], 3),
                            "bbox": [round(v, 1) for v in d["bbox"]]
                        }
                        self.recent_alerts.append(evt)
                        if len(self.recent_alerts) > 50: self.recent_alerts.pop(0)
                        self.stats["total_alerts"] += 1

            # 5. Render Annotations for Live Monitoring
            annotated = raw_frame.copy()
            for d in kept_dets:
                bx = [int(v) for v in d["bbox"]]
                color = (0, 0, 255) if d["class_name"] == "fire" else ((0, 165, 255) if d["class_name"] == "smoke" else (0, 255, 0))
                cv2.rectangle(annotated, (bx[0], bx[1]), (bx[2], bx[3]), color, 2)
                lbl = f"{d['class_name']} {d['score']:.2f}"
                cv2.putText(annotated, lbl, (bx[0], max(20, bx[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Draw HUD Overlay
            hud = f"HTP: {res['infer_ms']:.1f}ms | E2E: {e2e_lat_ms:.1f}ms | FPS: {self.stats['inference_fps']:.1f} | Dets: {len(kept_dets)}"
            cv2.putText(annotated, hud, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            with self.lock:
                self.latest_annotated_frame = annotated

            # 6. Update Performance Metrics
            self.stats["processed_frames"] += 1
            self.stats["recent_latencies_ms"].append(res["infer_ms"])
            self.stats["recent_e2e_latencies_ms"].append(e2e_lat_ms)
            if len(self.stats["recent_latencies_ms"]) > 300:
                self.stats["recent_latencies_ms"].pop(0)
                self.stats["recent_e2e_latencies_ms"].pop(0)

            fps_frame_count += 1
            if time.time() - t_fps_start >= 1.0:
                self.stats["inference_fps"] = fps_frame_count / (time.time() - t_fps_start)
                fps_frame_count = 0
                t_fps_start = time.time()

    def get_latest_frame_jpeg(self):
        with self.lock:
            if self.latest_annotated_frame is None:
                # Return placeholder
                dummy = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(dummy, "WAITING FOR LIVE STREAM...", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                _, jpeg = cv2.imencode('.jpg', dummy)
                return jpeg.tobytes()
            _, jpeg = cv2.imencode('.jpg', self.latest_annotated_frame)
            return jpeg.tobytes()

    def stop(self):
        self.is_running = False
        if hasattr(self, 'capture_thread'): self.capture_thread.join(timeout=1.0)
        if hasattr(self, 'inference_thread'): self.inference_thread.join(timeout=1.0)
        self.source.close()
        self.ipc_client.close()
        print("[StreamPipeline] Live Stream Pipeline stopped cleanly")
