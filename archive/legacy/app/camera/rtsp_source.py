"""RTSP Network Stream Frame Source with Auto-Reconnect."""
import time
import cv2
from .base import BaseFrameSource

class RTSPSource(BaseFrameSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.rtsp_url = config.get("source", "")
        self.cap = None
        self.reconnect_backoff = config.get("reconnect_backoff_sec", 1.0)
        self.max_reconnects = config.get("max_reconnect_attempts", 5)
        self.reconnect_count = 0

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        self.is_opened = self.cap.isOpened()
        return self.is_opened

    def read_frame(self):
        if not self.is_opened or not self.cap:
            if not self._reconnect():
                return False, None, 0.0, self.frame_count
        ok, frame = self.cap.read()
        if not ok:
            if self._reconnect():
                ok, frame = self.cap.read()
            if not ok:
                return False, None, 0.0, self.frame_count
        self.frame_count += 1
        return True, frame, time.time(), self.frame_count

    def _reconnect(self) -> bool:
        self.close()
        if self.reconnect_count >= self.max_reconnects:
            return False
        self.reconnect_count += 1
        time.sleep(self.reconnect_backoff)
        return self.open()

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_opened = False
