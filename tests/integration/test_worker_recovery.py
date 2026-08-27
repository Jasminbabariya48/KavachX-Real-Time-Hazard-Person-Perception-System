"""Integration Test: Worker Survival After Abrupt Disconnect."""
import sys
import os
import time
import socket
import struct
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.inference.engine import NpuInferenceEngine

def test_disconnect_and_recovery():
    print("=== [Integration Test] Worker Recovery Test ===")
    # 1. Connect and abruptly disconnect
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    t0 = time.time()
    while time.time() - t0 < 5.0:
        try:
            s.connect("/tmp/kawach_worker.sock")
            break
        except Exception:
            time.sleep(0.2)
            
    s.sendall(struct.pack("=IIII", 0x4B574158, 999, 1000000, 0) + b"\x00"*100)
    s.close()
    time.sleep(0.5)
    
    # 2. Re-connect fresh engine
    engine = NpuInferenceEngine()
    assert engine.connect(timeout=5.0), "Worker failed to accept new connection after abrupt disconnect"
    res = engine.infer_raw(np.zeros((1, 3, 640, 640), dtype=np.uint8))
    assert res["status"] == 0, "Worker returned failure after disconnect recovery"
    engine.close()
    print("=== [Integration Test] test_worker_recovery: PASS ===")

if __name__ == "__main__":
    test_disconnect_and_recovery()
