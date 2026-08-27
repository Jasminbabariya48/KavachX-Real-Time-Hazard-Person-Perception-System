"""Live Stream Ingestion & Inference Pipeline."""
import time
import threading
from collections import deque
import numpy as np
from app.inference.engine import NpuInferenceEngine
from app.camera.base import BaseFrameSource
from app.events.event_manager import EventManager
from .frame_queue import BoundedFrameQueue

class LiveStreamPipeline:
    def __init__(self, config: dict, frame_source: BaseFrameSource):
        self.config = config
        self.source = frame_source
        self.ipc_socket = config.get("inference", {}).get("ipc_socket_path", "/tmp/kawach_worker.sock")
        self.engine = NpuInferenceEngine(socket_path=self.ipc_socket)
        self.event_mgr = EventManager(config.get("alerting", {}))
        
        self.frame_queue = BoundedFrameQueue(maxsize=config.get("stream", {}).get("queue_maxsize", 2))
        self.is_running = False
        self.capture_thread = None
        self.infer_thread = None
        self.latest_annotated_frame = None
        self.lock = threading.Lock()
        
        self.stats = {
            "captured_frames": 0,
            "processed_frames": 0,
            "dropped_frames": 0,
            "htp_inference_count": 0,
            "cpu_fallback_count": 0,
            "htp_errors": 0,
            "inference_fps": 0.0,
            "recent_latencies_ms": deque(maxlen=100)
        }

    def start(self) -> bool:
        if not self.source.open():
            return False
        if not self.engine.connect():
            self.source.close()
            return False
            
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.infer_thread = threading.Thread(target=self._infer_loop, daemon=True)
        self.capture_thread.start()
        self.infer_thread.start()
        return True

    def _capture_loop(self):
        fps = self.config.get("stream", {}).get("target_fps", 30.0)
        interval = 1.0 / fps if fps > 0 else 0.033
        while self.is_running:
            t0 = time.time()
            ok, frame, ts, f_id = self.source.read_frame()
            if not ok or frame is None:
                break
            self.stats["captured_frames"] += 1
            self.frame_queue.put_latest((frame, ts, f_id))
            elapsed = time.time() - t0
            sleep_t = max(0.0, interval - elapsed)
            if sleep_t > 0: time.sleep(sleep_t)

    def _infer_loop(self):
        fps_counter = 0
        fps_start = time.time()
        while self.is_running:
            try:
                frame, capture_ts, f_id = self.frame_queue.get(timeout=0.1)
            except Exception:
                continue
                
            try:
                res = self.engine.infer_frame(frame, req_id=f_id)
                self.stats["htp_inference_count"] += 1
                self.stats["processed_frames"] += 1
                self.stats["recent_latencies_ms"].append(res.inference_time_ms)
                
                # Dispatch events
                self.event_mgr.process_detections(res.detections, frame)
                
                with self.lock:
                    self.latest_annotated_frame = frame
                    
                fps_counter += 1
                if time.time() - fps_start >= 1.0:
                    self.stats["inference_fps"] = round(fps_counter / (time.time() - fps_start), 1)
                    fps_counter = 0
                    fps_start = time.time()
            except Exception:
                self.stats["htp_errors"] += 1

    def stop(self):
        self.is_running = False
        if self.capture_thread: self.capture_thread.join(timeout=1.0)
        if self.infer_thread: self.infer_thread.join(timeout=1.0)
        self.source.close()
        self.engine.close()
