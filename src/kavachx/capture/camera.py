"""Camera Capture Factory."""
from .video import VideoSource
from .v4l2 import V4L2Source
from .rtsp import RTSPSource

def create_capture_source(cfg: dict):
    stype = cfg.get("source_type", "video").lower()
    if stype == "camera" or stype == "v4l2":
        return V4L2Source(cfg)
    elif stype == "rtsp":
        return RTSPSource(cfg)
    else:
        return VideoSource(cfg)
