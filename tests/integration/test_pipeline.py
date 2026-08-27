"""Integration Test: Full Live Stream Pipeline."""
import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.config.loader import load_production_config
from app.camera.file_source import VideoFileSource
from app.pipeline.pipeline import LiveStreamPipeline

def test_live_stream_pipeline():
    print("=== [Integration Test] Live Stream Pipeline Test ===")
    cfg = load_production_config()
    video_path = "/home/work_user2/kawachx_task/test_images/live_test_stream.mp4"
    if not os.path.exists(video_path):
        video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_data/videos/live_test_stream.mp4"))
        
    src = VideoFileSource({"source": video_path, "capture_fps": 30.0, "loop": True})
    pipe = LiveStreamPipeline(cfg, src)
    
    assert pipe.start(), "Failed to start LiveStreamPipeline"
    time.sleep(2.0)
    
    print(f"  Processed Frames: {pipe.stats['processed_frames']}, HTP Inferences: {pipe.stats['htp_inference_count']}")
    assert pipe.stats["processed_frames"] > 0, "No frames were processed by pipeline"
    assert pipe.stats["htp_errors"] == 0, "HTP errors encountered in pipeline"
    pipe.stop()
    print("=== [Integration Test] test_pipeline: PASS ===")

if __name__ == "__main__":
    test_live_stream_pipeline()
