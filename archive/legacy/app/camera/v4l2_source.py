"""V4L2 / USB / CSI Camera Frame Source."""
import time
import cv2
from .base import BaseFrameSource

class CameraSource(BaseFrameSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.device = config.get("source", "/dev/video0")
        self.cap = None
        self.width = config.get("width", 1280)
        self.height = config.get("height", 720)

    def open(self) -> bool:
        dev_idx = int(self.device.replace("/dev/video", "")) if "/dev/video" in str(self.device) else 0
        self.cap = cv2.VideoCapture(dev_idx)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.is_opened = True
        return self.is_opened

    def read_frame(self):
        if not self.is_opened or not self.cap:
            return False, None, 0.0, self.frame_count
        ok, frame = self.cap.read()
        if not ok:
            return False, None, 0.0, self.frame_count
        self.frame_count += 1
        return True, frame, time.time(), self.frame_count

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_opened = False
