"""Hardware Latency & Throughput Benchmark."""
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from kavachx.ipc.client import IpcClient

def benchmark(num_iterations=100):
    client = IpcClient()
    if not client.connect():
        print("Error: Could not connect to NPU worker daemon")
        return
    dummy = np.zeros((1, 3, 640, 640), dtype=np.uint8)
    lats = []
    print(f"Running {num_iterations} benchmark iterations on Qualcomm Hexagon DSP...")
    for i in range(num_iterations):
        res = client.send_inference_request(dummy, req_id=i+1)
        lats.append(res["infer_ms"])
    client.close()
    
    print(f"Mean Latency: {np.mean(lats):.2f} ms")
    print(f"P95 Latency:  {np.percentile(lats, 95):.2f} ms")
    print(f"Throughput:   {1000.0 / np.mean(lats):.1f} FPS")

if __name__ == "__main__":
    benchmark(50)
