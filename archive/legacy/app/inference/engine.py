"""Production NPU FastRPC IPC Inference Client."""
import time
import socket
import struct
import numpy as np
from typing import Optional
from .types import InferenceResult, Detection
from .preprocessing import prepare_uint8_nchw
from .postprocessing import decode_and_filter_detections

IPC_MAGIC_REQUEST  = 0x4B574158
IPC_MAGIC_RESPONSE = 0x5841574B
DEFAULT_SOCKET_PATH = "/tmp/kawach_worker.sock"

class NpuInferenceEngine:
    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH, conf_threshold: float = 0.25):
        self.socket_path = socket_path
        self.conf_threshold = conf_threshold
        self.sock: Optional[socket.socket] = None
        self.class_names = ["fire", "smoke", "person"]

    def connect(self, timeout: float = 3.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.settimeout(3.0)
                self.sock.connect(self.socket_path)
                return True
            except Exception:
                time.sleep(0.1)
        return False

    def is_connected(self) -> bool:
        return self.sock is not None

    def infer_raw(self, uint8_nchw: np.ndarray, req_id: int = 1) -> dict:
        if not self.sock:
            raise RuntimeError("NPU Worker socket not connected")
        payload = uint8_nchw.tobytes()
        t_send = time.perf_counter()
        
        hdr = struct.pack("=IIII", IPC_MAGIC_REQUEST, req_id, len(payload), 0)
        self.sock.sendall(hdr + payload)
        
        resp_hdr = bytearray()
        while len(resp_hdr) < 28:
            chunk = self.sock.recv(28 - len(resp_hdr))
            if not chunk: raise RuntimeError("Connection closed while reading response header")
            resp_hdr.extend(chunk)
            
        magic, r_id, status, n_dets, infer_us, post_us, data_sz = struct.unpack("=IIIIIII", resp_hdr)
        if magic != IPC_MAGIC_RESPONSE:
            raise RuntimeError(f"Invalid response magic: {hex(magic)}")
            
        out_bytes = bytearray()
        while len(out_bytes) < data_sz:
            chunk = self.sock.recv(data_sz - len(out_bytes))
            if not chunk: raise RuntimeError("Connection closed while reading response tensor")
            out_bytes.extend(chunk)
            
        t_recv = time.perf_counter()
        tensor = np.frombuffer(out_bytes, dtype=np.float32).reshape(7, 8400)
        
        return {
            "status": status,
            "request_id": r_id,
            "infer_ms": infer_us / 1000.0,
            "postproc_ms": post_us / 1000.0,
            "roundtrip_ms": (t_recv - t_send) * 1000.0,
            "tensor": tensor
        }

    def infer_frame(self, raw_bgr_frame: np.ndarray, req_id: int = 1) -> InferenceResult:
        uint8_nchw, r, dw, dh = prepare_uint8_nchw(raw_bgr_frame)
        res = self.infer_raw(uint8_nchw, req_id)
        dets = decode_and_filter_detections(res["tensor"], r, dw, dh, self.conf_threshold, self.class_names)
        
        return InferenceResult(
            status=res["status"],
            request_id=res["request_id"],
            inference_time_ms=res["infer_ms"],
            postprocess_time_ms=res["postproc_ms"],
            roundtrip_time_ms=res["roundtrip_ms"],
            detections=dets
        )

    def close(self):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass
            self.sock = None
