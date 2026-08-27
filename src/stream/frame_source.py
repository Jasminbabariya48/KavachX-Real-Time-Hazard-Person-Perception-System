"""
frame_source.py
---------------
Generic Abstract Frame Source supporting:
- Local Camera (USB / V4L2 / CSI)
- Video File Source (looping/single-pass)
- RTSP Network Stream Source (auto-reconnect with exponential backoff)
"""

import time
import os
import cv2
import numpy as np

class FrameSource:
    def __init__(self, source_config):
        self.config = source_config
        self.is_running = False
        self.frame_id = 0
        self.dropped_frames = 0
        self.reconnect_count = 0

    def open(self):
        raise NotImplementedError

    def read_frame(self):
        """Returns (success: bool, frame: np.ndarray, timestamp: float, frame_id: int)"""
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

class CameraSource(FrameSource):
    def __init__(self, source_config):
        super().__init__(source_config)
        self.device_id = source_config.get("source", 0)
        self.cap = None

    def open(self):
        try:
            dev = int(self.device_id) if str(self.device_id).isdigit() else self.device_id
            self.cap = cv2.VideoCapture(dev)
            if self.cap.isOpened():
                if "width" in self.config: self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["width"])
                if "height" in self.config: self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["height"])
                self.is_running = True
                return True
        except Exception as e:
            print(f"[CameraSource] Error opening camera {self.device_id}: {e}")
        return False

    def read_frame(self):
        if not self.cap or not self.cap.isOpened():
            return False, None, 0.0, 0
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None, 0.0, 0
        self.frame_id += 1
        return True, frame, time.time(), self.frame_id

    def close(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

class VideoFileSource(FrameSource):
    def __init__(self, source_config):
        super().__init__(source_config)
        self.file_path = source_config.get("source", "")
        self.loop = source_config.get("loop", True)
        self.cap = None
        self.fps = source_config.get("capture_fps", 30.0)

    def open(self):
        if not os.path.exists(self.file_path):
            # Check if relative to workspace
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            alt_path = os.path.join(base_dir, self.file_path)
            if os.path.exists(alt_path):
                self.file_path = alt_path
            else:
                self.file_path = f"/home/work_user2/kawachx_task/{self.file_path}"
                
        if not os.path.exists(self.file_path):
            print(f"[VideoFileSource] Warning: Video file not found: {self.file_path}")
            return False
            
        self.cap = cv2.VideoCapture(self.file_path)
        if self.cap.isOpened():
            self.is_running = True
            return True
        return False

    def read_frame(self):
        if not self.cap or not self.cap.isOpened():
            return False, None, 0.0, 0
        ret, frame = self.cap.read()
        if not ret or frame is None:
            if self.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret: return False, None, 0.0, 0
            else:
                return False, None, 0.0, 0
        self.frame_id += 1
        return True, frame, time.time(), self.frame_id

    def close(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

class RTSPSource(FrameSource):
    def __init__(self, source_config):
        super().__init__(source_config)
        self.rtsp_url = source_config.get("source", "")
        self.cap = None
        self.backoff = source_config.get("reconnect_backoff_sec", 1.0)
        self.max_attempts = source_config.get("max_reconnect_attempts", 10)

    def open(self):
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if self.cap.isOpened():
                self.is_running = True
                self.backoff = 1.0
                return True
        except Exception as e:
            print(f"[RTSPSource] Connection error to {self.rtsp_url}: {e}")
        return False

    def read_frame(self):
        if not self.cap or not self.cap.isOpened():
            # Trigger auto-reconnect
            if not self._reconnect():
                return False, None, 0.0, 0

        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("[RTSPSource] Frame read failed / stream dropped. Attempting reconnect...")
            self.dropped_frames += 1
            if not self._reconnect():
                return False, None, 0.0, 0
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return False, None, 0.0, 0

        self.frame_id += 1
        return True, frame, time.time(), self.frame_id

    def _reconnect(self):
        self.close()
        self.reconnect_count += 1
        print(f"[RTSPSource] Reconnecting (Attempt {self.reconnect_count}, backoff {self.backoff:.1f}s)...")
        time.sleep(self.backoff)
        self.backoff = min(self.backoff * 1.5, 10.0)
        return self.open()

    def close(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

def create_frame_source(config):
    s_type = config.get("source_type", "video").lower()
    if s_type in ["camera", "webcam"]:
        return CameraSource(config)
    elif s_type in ["rtsp", "network"]:
        return RTSPSource(config)
    else:
        return VideoFileSource(config)
