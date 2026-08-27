"""Live Stream Ingestion & Processing Pipeline."""
import time
import threading
from collections import deque
from kavachx.inference.engine import InferenceEngine
from kavachx.capture.camera import create_capture_source
from .frame_queue import BoundedQueue
from .events import AlertEventManager

class StreamProcessor:
    def __init__(self, config: dict, capture_source=None):
        self.config = config
        self.source = capture_source or create_capture_source(config.get("stream", {}))
        self.engine = InferenceEngine(
            socket_path=config.get("inference", {}).get("ipc_socket_path", "/tmp/kawach_worker.sock"),
            conf_threshold=config.get("inference", {}).get("confidence_threshold", 0.25)
        )
        self.event_mgr = AlertEventManager(config.get("alerting", {}))
        self.queue = BoundedQueue(maxsize=config.get("stream", {}).get("queue_maxsize", 2))
        
        self.is_running = False
        self.cap_thread = None
        self.infer_thread = None
        
        self.stats = {
            "captured_frames": 0,
            "processed_frames": 0,
            "dropped_frames": 0,
            "htp_inferences": 0,
            "htp_errors": 0,
            "fps": 0.0,
            "recent_latencies_ms": deque(maxlen=100)
        }

    def start(self) -> bool:
        if not self.source.open():
            return False
        if not self.engine.connect():
            self.source.close()
            return False
            
        self.is_running = True
        self.cap_thread = threading.Thread(target=self._cap_loop, daemon=True)
        self.infer_thread = threading.Thread(target=self._infer_loop, daemon=True)
        self.cap_thread.start()
        self.infer_thread.start()
        return True

    def _cap_loop(self):
        target_fps = self.config.get("stream", {}).get("target_fps", 30.0)
        interval = 1.0 / target_fps if target_fps > 0 else 0.033
        while self.is_running:
            t0 = time.time()
            ok, frame, ts, f_id = self.source.read()
            if not ok or frame is None:
                break
            self.stats["captured_frames"] += 1
            self.queue.put_latest((frame, ts, f_id))
            elapsed = time.time() - t0
            sleep_t = max(0.0, interval - elapsed)
            if sleep_t > 0: time.sleep(sleep_t)

    def _infer_loop(self):
        fps_cnt = 0
        t_fps = time.time()
        while self.is_running:
            try:
                frame, capture_ts, f_id = self.queue.get(timeout=0.1)
            except Exception:
                continue
                
            try:
                out = self.engine.infer(frame, req_id=f_id)
                self.stats["htp_inferences"] += 1
                self.stats["processed_frames"] += 1
                self.stats["recent_latencies_ms"].append(out.infer_time_ms)
                
                self.event_mgr.process(out.detections)
                
                fps_cnt += 1
                if time.time() - t_fps >= 1.0:
                    self.stats["fps"] = round(fps_cnt / (time.time() - t_fps), 1)
                    fps_cnt = 0
                    t_fps = time.time()
            except Exception:
                self.stats["htp_errors"] += 1

    def stop(self):
        self.is_running = False
        if self.cap_thread: self.cap_thread.join(timeout=1.0)
        if self.infer_thread: self.infer_thread.join(timeout=1.0)
        self.source.close()
        self.engine.close()
