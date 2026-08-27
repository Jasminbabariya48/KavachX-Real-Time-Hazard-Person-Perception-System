"""Inference Engine Interface."""
import numpy as np
from kavachx.ipc.client import IpcClient
from .postprocess import prepare_uint8_nchw
from .decoder import decode_detections
from .model import InferenceOutput

class InferenceEngine:
    def __init__(self, socket_path: str = "/tmp/kawach_worker.sock", conf_threshold: float = 0.25):
        self.client = IpcClient(socket_path=socket_path)
        self.conf_threshold = conf_threshold
        self.class_names = ["fire", "smoke", "person"]

    def connect(self, timeout: float = 3.0) -> bool:
        return self.client.connect(timeout=timeout)

    def infer(self, raw_bgr_frame: np.ndarray, req_id: int = 1) -> InferenceOutput:
        uint8_nchw, r, dw, dh = prepare_uint8_nchw(raw_bgr_frame)
        res = self.client.send_inference_request(uint8_nchw, req_id=req_id)
        dets = decode_detections(res["tensor"], r, dw, dh, self.conf_threshold, self.class_names)
        
        return InferenceOutput(
            status=res["status"],
            request_id=res["request_id"],
            infer_time_ms=res["infer_ms"],
            postproc_time_ms=res["postproc_ms"],
            roundtrip_time_ms=res["roundtrip_ms"],
            detections=dets
        )

    def close(self):
        self.client.close()
