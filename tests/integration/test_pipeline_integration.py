"""Integration Test: Stream Processor & Hazard Event Pipeline."""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from kavachx.config.loader import load_config
from kavachx.capture.video import VideoSource
from kavachx.pipeline.processor import StreamProcessor

def test_stream_pipeline():
    cfg = load_config()
    vid_path = "/home/work_user2/kawachx_task/test_images/live_test_stream.mp4"
    if not os.path.exists(vid_path):
        vid_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_data/videos/live_test_stream.mp4"))
        
    src = VideoSource({"source": vid_path, "capture_fps": 30.0, "loop": True})
    proc = StreamProcessor(cfg, src)
    
    assert proc.start(), "Failed to start StreamProcessor"
    time.sleep(2.0)
    
    assert proc.stats["processed_frames"] > 0, "No frames processed"
    assert proc.stats["htp_errors"] == 0, "Inference errors encountered"
    proc.stop()
    print("[PASS] test_stream_pipeline")

if __name__ == "__main__":
    test_stream_pipeline()
