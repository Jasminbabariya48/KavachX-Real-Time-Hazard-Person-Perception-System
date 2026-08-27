"""Video File Frame Source."""
import time
import cv2
from .base import BaseFrameSource

class VideoFileSource(BaseFrameSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.filepath = config.get("source", "")
        self.cap = None
        self.fps = config.get("capture_fps", 30.0)
        self.loop = config.get("loop", False)

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.filepath)
        self.is_opened = self.cap.isOpened()
        return self.is_opened

    def read_frame(self):
        if not self.is_opened or not self.cap:
            return False, None, 0.0, self.frame_count
        ok, frame = self.cap.read()
        if not ok:
            if self.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
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
