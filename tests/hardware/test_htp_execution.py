"""Hardware Test: Real Qualcomm Hexagon v68 HTP Execution."""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.inference.engine import NpuInferenceEngine

def test_htp_inference():
    print("=== [Hardware Test] Connecting to Hexagon HTP Worker ===")
    engine = NpuInferenceEngine()
    assert engine.connect(timeout=5.0), "Failed to connect to kawach_worker daemon"
    
    dummy_nchw = np.zeros((1, 3, 640, 640), dtype=np.uint8)
    res = engine.infer_raw(dummy_nchw)
    
    print(f"  Inference Result Status: {res['status']}, Infer Latency: {res['infer_ms']:.2f} ms")
    assert res["status"] == 0, "Worker returned non-zero status"
    assert res["infer_ms"] > 0, "Inference latency was 0"
    assert res["tensor"].shape == (7, 8400), "Invalid output tensor shape"
    engine.close()
    print("=== [Hardware Test] test_htp_execution: PASS ===")

if __name__ == "__main__":
    test_htp_inference()
