"""Streaming Test: Bounded Live Stream Benchmark."""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from kavachx.config.loader import load_config
from kavachx.capture.video import VideoSource
from kavachx.pipeline.processor import StreamProcessor

def test_streaming_benchmark():
    cfg = load_config()
    vid_path = "/home/work_user2/kawachx_task/test_images/live_test_stream.mp4"
    if not os.path.exists(vid_path):
        vid_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_data/videos/live_test_stream.mp4"))
        
    src = VideoSource({"source": vid_path, "capture_fps": 30.0, "loop": True})
    proc = StreamProcessor(cfg, src)
    assert proc.start(), "Could not start stream"
    
    t0 = time.time()
    while (time.time() - t0) < 3.0 and proc.stats["processed_frames"] < 40:
        time.sleep(0.2)
        
    proc.stop()
    assert proc.stats["processed_frames"] > 0
    print(f"[PASS] test_streaming_benchmark ({proc.stats['processed_frames']} frames processed)")

if __name__ == "__main__":
    test_streaming_benchmark()
