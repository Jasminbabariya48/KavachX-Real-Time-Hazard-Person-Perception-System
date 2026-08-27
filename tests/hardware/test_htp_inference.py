"""Hardware Test: Real Qualcomm Hexagon v68 HTP Execution."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from kavachx.ipc.client import IpcClient

def test_hardware_execution():
    client = IpcClient()
    assert client.connect(timeout=5.0), "Could not connect to NPU worker"
    
    dummy = np.zeros((1, 3, 640, 640), dtype=np.uint8)
    res = client.send_inference_request(dummy)
    
    assert res["status"] == 0, "Worker returned non-zero status"
    assert res["infer_ms"] > 0, "Zero inference time reported"
    assert res["tensor"].shape == (7, 8400), "Invalid tensor shape"
    client.close()
    print("[PASS] test_hardware_execution (Qualcomm Hexagon v68 HTP)")

if __name__ == "__main__":
    test_hardware_execution()
