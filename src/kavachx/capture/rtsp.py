"""RTSP Network Stream Source with Automatic Reconnection."""
import time
import cv2

class RTSPSource:
    def __init__(self, config: dict):
        self.url = config.get("source", "")
        self.reconnect_backoff = config.get("reconnect_backoff_sec", 1.0)
        self.max_reconnects = config.get("max_reconnect_attempts", 5)
        self.reconnect_count = 0
        self.cap = None
        self.frame_count = 0
        self.is_opened = False

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        self.is_opened = self.cap.isOpened()
        return self.is_opened

    def read(self):
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
