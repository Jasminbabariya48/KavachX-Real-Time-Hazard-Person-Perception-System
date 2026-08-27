#!/usr/bin/env python3
import socket
import struct
import time
import cv2
import numpy as np
import subprocess
import os

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2]
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img

def test_ipc():
    sock_path = "/tmp/kawach_worker.sock"
    
    # 1. Connect to worker
    print(f"Connecting to {sock_path}...")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    for _ in range(20):
        try:
            sock.connect(sock_path)
            break
        except Exception:
            time.sleep(0.2)
    else:
        raise RuntimeError("Failed to connect to kawach_worker socket")
        
    print("Connected successfully to kawach_worker!")
    
    samples = [
        ('fire', '/home/work_user2/kawachx_task/test_images/fire.jpg'),
        ('fire_2', '/home/work_user2/kawachx_task/test_images/fire_2.jpg'),
        ('person', '/home/work_user2/kawachx_task/test_images/person.jpg')
    ]
    
    class_names = ["fire", "smoke", "person"]
    
    for name, img_path in samples:
        img = cv2.imread(img_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        lb_img = letterbox(img_rgb, (640, 640))
        uint8_nchw = np.ascontiguousarray(np.transpose(lb_img, (2, 0, 1))[np.newaxis, :, :, :], dtype=np.uint8)
        
        # Send raw frame (1,228,800 bytes)
        t0 = time.perf_counter()
        sock.sendall(uint8_nchw.tobytes())
        
        # Read status (4 bytes)
        status_data = sock.recv(4)
        status = struct.unpack("=I", status_data)[0]
        
        # Read output tensor (235,200 bytes)
        out_bytes = bytearray()
        needed = 58800 * 4
        while len(out_bytes) < needed:
            chunk = sock.recv(needed - len(out_bytes))
            if not chunk:
                break
            out_bytes.extend(chunk)
            
        t1 = time.perf_counter()
        infer_time_ms = (t1 - t0) * 1000.0
        
        output_tensor = np.frombuffer(out_bytes, dtype=np.float32).reshape(7, 8400)
        
        # Decode boxes with score > 0.25
        cx, cy, w, h = output_tensor[0], output_tensor[1], output_tensor[2], output_tensor[3]
        scores = output_tensor[4:7] # [3, 8400]
        
        max_cls = np.argmax(scores, axis=0)
        max_scores = np.max(scores, axis=0)
        
        mask = max_scores >= 0.25
        dets = []
        for idx in np.where(mask)[0]:
            c = int(max_cls[idx])
            s = float(max_scores[idx])
            x1 = max(0.0, float(cx[idx] - w[idx] / 2.0))
            y1 = max(0.0, float(cy[idx] - h[idx] / 2.0))
            x2 = min(640.0, float(cx[idx] + w[idx] / 2.0))
            y2 = min(640.0, float(cy[idx] + h[idx] / 2.0))
            dets.append((c, s, [x1, y1, x2, y2]))
            
        print(f"\n--- IPC Result for {name} (Status={status}, Total IPC round-trip: {infer_time_ms:.2f} ms) ---")
        print(f"  Raw detections above threshold: {len(dets)}")
        for d in dets[:5]:
            print(f"    Class: {class_names[d[0]]}, Score: {d[1]:.3f}, Box: {[round(v, 1) for v in d[2]]}")

    sock.close()
    print("\nEnd-to-End Worker IPC test: PASS")

if __name__ == "__main__":
    test_ipc()
